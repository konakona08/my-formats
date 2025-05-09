# FWI1 Image format, my own image format (LZ+RLE+Bit-encoding)
# File: fwI1e.py
# Purpose: FWI1 encoder class

from PIL import Image
from FWI1Common import _FWI1_DataHdr
from operator import length_hint

#global data
cmd = None #init-ed as bytearray
cmd_size = 0
len = None #init-ed as bytearray
len_size = 0
lit = []
lit_size = 0

#encode
in8bit = None #init-ed as bytearray
indices = []
off_tmp = [0]*256
offs = 0
currbits = 32
bwrite = 0

#defines for encoder

MATCH_OFFS_BITS = 16
MATCH_LEN_BITS = 16

def BITS_MAX(bits):
    return ((1<<bits)-1)

def MATCH_16ALIGN(n):
    return (n&(~1))

def MATCH_OFFS_MAX():
    return MATCH_16ALIGN(BITS_MAX(MATCH_OFFS_BITS))-3

def MATCH_LEN_MAX():
    return MATCH_16ALIGN(BITS_MAX(MATCH_LEN_BITS))

#encoder functions for write/read

def FWI1_write(v, bits):
    global currbits, bwrite, cmd, cmd_size
    if currbits < bits:
        bdiff = bits - currbits 
        bwrite |= (v >> bdiff) 
        cmd[cmd_size] = (bwrite>>24)&0xff
        cmd[cmd_size+1] = ((bwrite>>16)&0xff)
        cmd[cmd_size+2] = ((bwrite>>8)&0xff)
        cmd[cmd_size+3] = (bwrite & 0xff)
        cmd_size+=4
        currbits = 32 - bdiff 
        bwrite = (v << currbits) 
    else:
        if currbits == 0:
            cmd[cmd_size] = (bwrite>>24)&0xff
            cmd[cmd_size+1] = ((bwrite>>16)&0xff)
            cmd[cmd_size+2] = ((bwrite>>8)&0xff)
            cmd[cmd_size+3] = (bwrite & 0xff)
            cmd_size+=4
            currbits = 32 
            bwrite = 0 
        currbits -= bits 
        bwrite |= (v <<currbits) 

def FWI1_read16(s):
    global indices, in8bit, off_tmp, offs
    for tl in range(0,(s)<<1):
        indices[(in8bit[offs] << 8) + off_tmp[in8bit[offs]]] = offs
        off_tmp[in8bit[offs]] = (off_tmp[in8bit[offs]] + 1) & 0xff
        offs += 1

def FWI1_bitdown(n):
    bitout = 0
    stored_val = 0

    while (bitout <= 16):
        bitout+=1
        if (n < ((((1 << bitout) - 1)) << 2)):
            bitout-=1
            break
    stored_val = n - (((1 << bitout) - 1) << 2);
    return bitout, stored_val

def FWI1_countbits(n):
    count = 0 
    while n > 0:
        n>>=1
        count+=1
    return count

def FWI1_Imageto565(image):
    if image.mode != "RGB":
        image = image.convert("RGB")

    data = []
    size = image.width*image.height*3
    idata = image.tobytes()
    for i in range(0, size, 3):
        r = idata[i]
        g = idata[i+1]
        b = idata[i+2]
        data.append((r>>3<<11)|(g>>2<<5)|(b>>3))
    return data

def FWI1_16to8(img_data):
    out = bytearray(length_hint(img_data)<<2)
    for i in range(0, length_hint(img_data)):
        out[i<<1] = img_data[i]&0xff
        out[(i<<1)+1] = img_data[i]>>8
    return out


class FWI1Encoder():
    def encode(self, file):
        global cmd, cmd_size, len, len_size, lit, lit_size, in8bit, indices, offs
        
        img = Image.open(file)
        w,h = img.width, img.height
        data = FWI1_Imageto565(img)

        lzoff = 0
        lzlen = 0
        rllen = 0
        in8bit = FWI1_16to8(data)

        indices = [0] * ((65536)<<3)

        cmd = bytearray(length_hint(data)<<2)
        cmd_size = 0
        len = bytearray(length_hint(data)<<1)
        len_size = 0
        lit = [0]*length_hint(data)
        lit_size = 0

        offs = 0
        szi = length_hint(data)<<1

        lzpoffs = 0
        lzplen = 0
        lzoff = 0
        lzlen = 0
        while offs<szi:
            indices_off = in8bit[offs]<<8
            lzlen = 0
            if (szi-offs) > MATCH_LEN_MAX():
                sb_offs = off_tmp[in8bit[offs]]

                while sb_offs >= 0:
                    lznoff = offs - indices[indices_off+sb_offs]
                    
                    if (lznoff&1) == 0:
                        if lznoff > MATCH_16ALIGN(MATCH_OFFS_MAX()):
                            break

                        lznlen = 1
                        #bug in python implementation
                        #offs > 0, else will falsely flag as an LZ match
                        while lznlen < MATCH_LEN_MAX() and offs > 0:
                            if in8bit[indices[indices_off+sb_offs] + lznlen] != in8bit[offs + lznlen]:
                                break
                            lznlen += 1

                        if lznlen > lzlen:
                            lzoff = lznoff
                            lzlen = lznlen

                            if (lznlen > MATCH_LEN_MAX()):
                                lzlen = MATCH_LEN_MAX()
                                break

                    sb_offs -= 1

            if (MATCH_16ALIGN(lzlen) < 4):
                cby = in8bit[offs] | in8bit[offs+1]<<8
                
                rllen = 0
                offs += 2

                while (offs<szi) and (in8bit[offs] | (in8bit[offs+1]<<8)) == cby:
                    FWI1_read16(1)
                    rllen += 1

                if rllen > 0: #RLE
                    FWI1_write(1, 2)
                    FWI1_write(FWI1_countbits(rllen), 5)
                    FWI1_write(rllen, FWI1_countbits(rllen))
                else: #Lit
                    FWI1_write(0, 2)

                a = 0
                found = False

                while a < (lit_size>>1) and a < 4092:
                    if lit[a] == cby:
                        found = True
                        break
                    a += 1

                if found:
                    FWI1_write(1, 1)
                    w_bits, w_val = FWI1_bitdown(a)
                    FWI1_write(w_bits, 4)
                    FWI1_write(w_val, w_bits+2)
                else:
                    FWI1_write(0, 1)
                    lit[lit_size>>1] = cby
                    lit_size += 2
            else: #LZ
                lzoff >>= 1
                lzlen >>= 1

                FWI1_read16(lzlen)
                FWI1_write(2, 2)
                FWI1_write(0 if lzpoffs == lzoff else 1, 1)
                FWI1_write(0 if lzplen == lzlen else 1, 1)

                if lzpoffs != lzoff:
                    w_bits, w_val = FWI1_bitdown(lzoff)
                    FWI1_write(w_bits, 4)
                    FWI1_write(w_val, w_bits+2)
                if lzplen != lzlen:
                    FWI1_write(0 if lzlen > 256 else 1, 1)
                    if lzlen > 256:
                        len[len_size] = lzlen&0xff
                        len[len_size+1] = lzlen>>8
                        len_size += 2
                    else:
                        len[len_size] = lzlen-1
                        len_size += 1

                lzpoffs = lzoff
                lzplen = lzlen
                
                indices[indices_off + off_tmp[in8bit[offs]]] = offs - 1

        #flush cmd bits
        cmd[cmd_size] = (bwrite>>24)&0xff
        cmd[cmd_size+1] = ((bwrite>>16)&0xff)
        cmd[cmd_size+2] = ((bwrite>>8)&0xff)
        cmd[cmd_size+3] = (bwrite & 0xff)
        cmd_size+=4

        out_dat = bytearray((_FWI1_DataHdr.sizeof() + cmd_size + lit_size + len_size))
        out_dat_size = 0
        # write header -> cmd -> len -> lit
        hdr = _FWI1_DataHdr.build(dict(cmd_size=cmd_size, len_size=len_size))
        out_dat[:length_hint(hdr)] = hdr
        out_dat_size += length_hint(hdr)

        for i in range(0, cmd_size, 1):
            out_dat[out_dat_size] = cmd[i]
            out_dat_size += 1

        for i in range(0, len_size, 1):
            out_dat[out_dat_size] = len[i]
            out_dat_size += 1

        for i in range(0, lit_size, 2):
            out_dat[out_dat_size] = lit[i>>1]&0xff
            out_dat[out_dat_size+1] = lit[i>>1]>>8
            out_dat_size += 2

        return out_dat, w, h