# FWI1 Image format, my own image format (LZ+RLE+Bit-encoding)
# File: fwI1common.py
# Purpose: FWI1 common type

from construct import *

_FWI1_MainHdr = Struct(
    "magic" / Int16ul, #must be read from file or written to file
    "version" / Int8ul,
    "width" / Int16ul,
    "height" / Int16ul,
    "size" / Int32ul #total size of compressed image
)

_FWI1_DataHdr = Struct(
    "cmd_size" / Int32ul, #must be max of 65535 at best
    "len_size" / Int32ul  #must be max of 65535 at best
)