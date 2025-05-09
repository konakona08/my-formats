# FWI1 Image format, my own image format (LZ+RLE+Bit-encoding)
# File: fwI1.py
# Purpose: FWI1 main library

from enum import Enum
from FWI1D import FWI1Decoder
from FWI1E import FWI1Encoder
from FWI1Common import _FWI1_MainHdr
import argparse

MAGIC = 0x4946

# class' type enum (bool)
class FWI1_Type(Enum):
    Decode = 0
    Encode = 1

# FWI1 class
class FWI1():
    # __init__ -> Initializes the FWI1 object
    def __init__(self, type = FWI1_Type.Decode):
        self.type = type
        if self.type == FWI1_Type.Decode:
            self.decoder = FWI1Decoder()
        elif self.type == FWI1_Type.Encode:
            self.encoder = FWI1Encoder()
        else:
            raise ValueError("Cannot init!!! type is not 0 or 1")
    
    # decode -> Decodes the FWI1 file
    def decode(self, file: bytes|bytearray|str, out_file: bytes|bytearray|str):
        if self.type == FWI1_Type.Decode:
            with open(file, "rb") as f:
                data = f.read()
            dec_data,w,h = self.decoder.decode(data)
            with open(out_file, "wb") as f:
                for i in range(0, len(dec_data)):
                    f.write(bytes([dec_data[i]&0xff]))
                    f.write(bytes([dec_data[i]>>8]))
        else:
            raise ValueError("Cannot decode!!! FWI1 class is not decode")
    
    # encode -> Encodes the FWI1 file
    def encode(self, file: bytes|bytearray|str, out_file: bytes|bytearray|str):
        if self.type == FWI1_Type.Encode:
            enc_data,w,h = self.encoder.encode(file)
            hdr = _FWI1_MainHdr.build(dict(magic = MAGIC, version=1, width=w, height=h, size=len(enc_data)))
            with open(out_file, "wb") as f:
                f.write(hdr)
                f.write(enc_data)
        else:
            raise ValueError("Cannot encode!!! FWI1 class is not encode")

    # __str__ -> Returns the string representation of the FWI1 object
    def __str__(self):
        return f"FWI1(type={self.type})"

    # __repr__ -> Returns the string representation of the FWI1 object
    def __repr__(self):
        return self.__str__()

    # get_type -> Returns the type of the FWI1 object
    def get_type(self):
        return self.type

    # __del__ -> Destroys the FWI1 object
    def __del__(self):
        if self.type == FWI1_Type.Decode:
            del self.decoder
        elif self.type == FWI1_Type.Encode:
            del self.encoder

#main
if __name__ == "__main__":
    ap = argparse.ArgumentParser("fwi1")
    
    ap.add_argument("--decode", "-d", help="Decode the FWI1 file", action="store_true")
    ap.add_argument("--encode", "-e", help="Encode the FWI1 file", action="store_true")
    ap.add_argument("out_file")
    ap.add_argument("in_file")

    args = ap.parse_args()

    fwi = FWI1(FWI1_Type.Decode if args.decode else FWI1_Type.Encode)
    if fwi.get_type() == FWI1_Type.Decode:
        fwi.decode(args.in_file, args.out_file)
    elif fwi.get_type() == FWI1_Type.Encode:
        fwi.encode(args.in_file, args.out_file)
