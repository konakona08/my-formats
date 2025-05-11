# FWI1 Image format, my own image format (LZ+RLE+Bit-encoding)
# File: fwI1d.py
# Purpose: FWI1 decoder class

from PIL import Image
from FWI1Common import _FWI1_DataHdr,_FWI1_MainHdr, FWI1Header, FWI1_16to8
from operator import length_hint
import typing

# decoder data
cmdbits = 0
currbits = 0
cmdp = bytearray() #init-ed as bytearray
cmd_parse_size = 0
cmd_size = 0
lenp = bytearray() #init-ed as bytearray
len_size = 0
len_parse_size = 0
litp = bytearray() #init-ed as bytearray
lit_size = 0
lit_parse_size = 0

dec_size = 0
dec_write = 0

def FWI1_read(bits):
    global cmdbits, currbits, cmdp, cmd_parse_size
    while currbits < bits:
        cmdbits = ((cmdbits<<8)|cmdp[cmd_parse_size]) & 0xffffffff
        cmd_parse_size+=1
        currbits += 8
    currbits -= bits
    return (cmdbits>>currbits) & ((1<<(bits))-1)

def FWI1_write16(len, rgb565, out_data):
    global dec_size, dec_write
    for i in range(0, len):
        try:
            out_data[dec_write] = rgb565
            dec_write += 1
            dec_size -= 1
        except Exception as e:
            pass

def FWI1_write16_lz(len, offs, out_data):
    global dec_size, dec_write
    for i in range(0, len):
        try:
            out_data[dec_write] = out_data[dec_write-offs]
            dec_write += 1
            dec_size -= 1
        except Exception as e:
            pass

def FWI1_int_decode(frame, w, h, out_data):
    global cmdp, lenp, litp, cmd_parse_size, len_parse_size, lit_parse_size, dec_size
    global dec_write, cmd_parse_size, len_parse_size, lit_parse_size
    global cmdbits, currbits

    cmdp = frame["cmd"]
    lenp = frame["len"]
    litp = frame["lit"]

    last_off = 0
    last_len = 0

    cmd_parse_size = 0
    len_parse_size = 0
    lit_parse_size = 0

    dec_write = 0

    cmdbits = 0
    currbits = 0

    dec_size = w*h

    while dec_size>0:
        cmd_type = FWI1_read(2)
        if cmd_type == 0:
            found = FWI1_read(1)

            if found == 1:
                wbits = FWI1_read(4)
                wval = FWI1_read(wbits+2)
                wval += (((1 << wbits) - 1) << 2)

                rgb565 = litp[wval << 1] | litp[(wval << 1) + 1] << 8
            else:
                rgb565 = litp[lit_parse_size] | litp[lit_parse_size + 1] << 8
                lit_parse_size += 2

            FWI1_write16(1, rgb565, out_data)
        elif cmd_type == 1:
            len_wbits = FWI1_read(5)
            len_wval = FWI1_read(len_wbits)
            len_wval +=1

            found = FWI1_read(1)

            if found == 1:
                wbits = FWI1_read(4)
                wval = FWI1_read(wbits+2)
                wval += (((1 << wbits) - 1) << 2)
                rgb565 = litp[wval << 1] | litp[(wval << 1) + 1] << 8
            else:
                rgb565 = litp[lit_parse_size] | litp[lit_parse_size + 1] << 8
                lit_parse_size += 2

            FWI1_write16(len_wval, rgb565, out_data)
        elif cmd_type == 2:
            off = last_off
            len = last_len

            new_off = FWI1_read(1)
            new_len = FWI1_read(1)

            if new_off == 1:
                wbits = FWI1_read(4)
                wval = FWI1_read(wbits+2)
                off = wval + (((1 << wbits) - 1) << 2)
                last_off = off
			
            if new_len == 1:
                std_len = FWI1_read(1)
                if std_len == 1:
                    len = lenp[len_parse_size] + 1
                    len_parse_size += 1
                else:
                    len = lenp[len_parse_size] | lenp[len_parse_size + 1] << 8
                    len_parse_size += 2
            last_len = len
            FWI1_write16_lz(len, off, out_data)
        elif cmd_type == 3:
            std_len = FWI1_read(1)
            if std_len == 1:
                skip_len = lenp[len_parse_size] + 1
                len_parse_size += 1
            else:
                skip_len = lenp[len_parse_size] | lenp[len_parse_size + 1] << 8
                len_parse_size += 2
            
            dec_write += skip_len
            dec_size -= skip_len

class FWI1Decoder():
    def __init__(self, data: typing.Union[bytes, bytearray, str]):        
        if type(data) == str:
            data = open(data, "rb").read()

        self._data = bytes(data)
        try:
            fwi_hdr = FWI1Header(self._data)
        except ValueError as e:
            raise ValueError("Invalid FWI1 header")
            
        self.width = fwi_hdr.get_width()
        self.height = fwi_hdr.get_height()
        self.size = fwi_hdr.get_size()

        self.dec_image = [0]*self.width*self.height

        self.frames = 0

        self.curr_frame = 0

        self.img_cmp_data = []

        my_img_data = self._data[fwi_hdr.get_hdr_size():]
        curr_parse_sz = 0
        #get image data frame....
        while curr_parse_sz < self.size:
            info_hdr = _FWI1_DataHdr.parse(my_img_data)
            hdr_size = _FWI1_DataHdr.sizeof()
            my_img_data = my_img_data[hdr_size:]
            try:
                self.img_cmp_data.append({
                    "cmd": my_img_data[:info_hdr.cmd_size],
                    "cmd_size": info_hdr.cmd_size,
                    "len": my_img_data[info_hdr.cmd_size:info_hdr.cmd_size+info_hdr.len_size],
                    "len_size": info_hdr.len_size,
                    "lit": my_img_data[info_hdr.cmd_size+info_hdr.len_size:info_hdr.cmd_size+info_hdr.len_size+info_hdr.lit_size],
                    "lit_size": info_hdr.lit_size
                })
                curr_parse_sz += info_hdr.cmd_size + info_hdr.len_size + info_hdr.lit_size + hdr_size
                my_img_data = my_img_data[info_hdr.cmd_size + info_hdr.len_size + info_hdr.lit_size:]
                self.frames += 1
            except Exception as e:
                break
        

    def decode(self):
        FWI1_int_decode(self.img_cmp_data[self.curr_frame], self.width, self.height, self.dec_image)

        return Image.frombytes("RGB", (self.width, self.height), FWI1_16to8(self.dec_image), "raw", "BGR;16", 0, 1)

    def __iter__(self):
        self.curr_frame = 0
        return self

    def __next__(self):
        if self.curr_frame >= self.frames: raise StopIteration()
        
        print(self.curr_frame)
        frame = self.decode()
        self.curr_frame += 1

        return frame



