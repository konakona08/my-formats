# FWI1 Image format, my own image format (LZ+RLE+Bit-encoding)
# File: fwI1d.py
# Purpose: FWI1 decoder class

from PIL import Image
from FWI1Common import _FWI1_DataHdr,_FWI1_MainHdr
from operator import length_hint

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

MAGIC = 0x4946

def FWI1_read(bits):
    global cmdbits, currbits, cmdp, cmd_parse_size
    while currbits < bits:
        cmdbits = ((cmdbits<<8)|cmdp[cmd_parse_size]) & 0xffffffff
        cmd_parse_size+=1
        currbits += 8
    currbits -= bits
    return (cmdbits>>currbits) & ((1<<(bits))-1)

def FWI1_write16(len, rgb565, out_image):
    global dec_size, dec_write
    for i in range(0, len):
        out_image[dec_write] = rgb565
        dec_write += 1
        dec_size -= 1

def FWI1_write16_lz(len, offs, out_image):
    global dec_size, dec_write
    for i in range(0, len):
        out_image[dec_write] = out_image[dec_write-offs]
        dec_write += 1
        dec_size -= 1

class FWI1Decoder():
    def decode(self, data):
        global cmdp, lenp, litp, cmd_parse_size, len_parse_size, lit_parse_size, dec_size

        hdr = _FWI1_MainHdr.parse(data)

        if hdr.magic != MAGIC:
            raise ValueError("Invalid magic number")

        if hdr.version != 1:
            raise ValueError("Invalid version number")

        data = data[_FWI1_MainHdr.sizeof():]
        
        info_hdr = _FWI1_DataHdr.parse(data)

        cmdp = data[_FWI1_DataHdr.sizeof():_FWI1_DataHdr.sizeof() + info_hdr.cmd_size]
        lenp = data[_FWI1_DataHdr.sizeof() + info_hdr.cmd_size:_FWI1_DataHdr.sizeof() + info_hdr.cmd_size + info_hdr.len_size]
        litp = data[_FWI1_DataHdr.sizeof() + info_hdr.cmd_size + info_hdr.len_size:]

        last_off = 0
        last_len = 0

        dec_size = hdr.width * hdr.height
        out_image = [0]*dec_size
        dec_write = 0

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
                
                FWI1_write16(1, rgb565, out_image)
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

                FWI1_write16(len_wval, rgb565, out_image)
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
                FWI1_write16_lz(len, off, out_image)
            
        return out_image, hdr.width, hdr.height




