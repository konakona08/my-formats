# FWI1 Image format, my own image format (LZ+RLE+Bit-encoding)
# File: fwI1common.py
# Purpose: FWI1 common type

from construct import *
from operator import length_hint

_FWI1_MainHdr = Struct(
    "magic" / Int16ul, #must be read from file or written to file
    "version" / Int8ul,
    "width" / Int16ul,
    "height" / Int16ul,
    "size" / Int32ul #total size of compressed image
)

_FWI1_DataHdr = Struct(
    "cmd_size" / Int32ul, #must be max of 65535 at best
    "len_size" / Int32ul, #must be max of 65535 at best
    "lit_size" / Int32ul  #must be max of 65535 at best
)

MAGIC = 0x4946

#### for python only

def FWI1_16to8(img_data):
    out = bytearray(length_hint(img_data)<<2)
    for i in range(0, length_hint(img_data)):
        out[i<<1] = img_data[i]&0xff
        out[(i<<1)+1] = img_data[i]>>8
    return out

######################################

class FWI1Header():
    def __init__(self, data):
        if data == None:
            #create null header
            self.width = 0
            self.height = 0
            self.size = 0
        else:
            hdr = _FWI1_MainHdr.parse(data)

            if hdr.magic != MAGIC:
                raise ValueError("Invalid magic number")

            if hdr.version != 1:
                raise ValueError("Invalid version number")

            self.width = hdr.width
            self.height = hdr.height
            self.size = hdr.size

    def get_width(self):
        return self.width

    def get_height(self):
        return self.height

    def get_size(self):
        return self.size

    def get_hdr_size(self):
        return _FWI1_MainHdr.sizeof()

    def write_to_hdr(self, w, h, size):
        hdr = _FWI1_MainHdr.build(dict(magic=MAGIC, version=1, width=w, height=h, size=size))
        return hdr

    def __str__(self):
        return f"FWI1Header(width={self.width}, height={self.height}, size={self.size})"
