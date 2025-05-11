# FWI1 Image format, my own image format (LZ+RLE+Bit-encoding)
# File: fwI1.py
# Purpose: FWI1 main library

from enum import Enum
from FWI1D import FWI1Decoder
from FWI1E import FWI1Encoder
from FWI1Common import _FWI1_MainHdr
import argparse
from PIL import Image
import os

MAGIC = 0x4946

# class' type enum (bool)
class FWI1_Type(Enum):
    Decode = 0
    Encode = 1

# FWI1 class
class FWI1():
    # __init__ -> Initializes the FWI1 object
    def __init__(self, type = FWI1_Type.Decode, data: bytes|bytearray|str = None):
        self.type = type
        if self.type == FWI1_Type.Decode:
            self.decoder = FWI1Decoder(data)
        elif self.type == FWI1_Type.Encode:
            self.encoder = FWI1Encoder()
        else:
            raise ValueError("Cannot init!!! type is not 0 or 1")
    
    # decode -> Decodes the FWI1 file
    def decode(self, out_file):
        if self.type == FWI1_Type.Decode:
            for a, frame in enumerate(self.decoder):
                frame.save(f"{os.path.splitext(out_file)[0]}_{self.decoder.curr_frame}.png")
        else:
            raise ValueError("Cannot decode!!! FWI1 class is not decode")
    
    # encode -> Encodes the FWI1 file
    def encode(self, files: list[str], out_file):
        if self.type == FWI1_Type.Encode:

            out = open(out_file, "wb")

            #check if img has equal w and h
            if len(files) == 0:
                raise ValueError("Cannot encode!!! No files to encode")
            
            w,h = Image.open(files[0]).size
            
            for file in files:
                img = Image.open(file)
                if img.size != (w,h):
                    raise ValueError("Cannot encode!!! All images must have the same size")

            data = bytearray()

            for a in range(len(files)):
                print(a)
                data.extend(self.encoder.encode(files[a], prev_file=files[a-1] if a-1 >= 0 else None))
            out.write(_FWI1_MainHdr.build(dict(magic=MAGIC, version=1, width=w, height=h, size=len(data))))
            out.write(data)

            out.close()

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
    ap.add_argument("in_file", nargs="*")

    args = ap.parse_args()

    fwi = FWI1(FWI1_Type.Decode if args.decode else FWI1_Type.Encode, data=args.in_file[0])
    if fwi.get_type() == FWI1_Type.Decode:
        fwi.decode(args.out_file)
    elif fwi.get_type() == FWI1_Type.Encode:
        if len(args.in_file) == 0:
            raise ValueError("Cannot encode!!! No files to encode")
        ### build array
        data = []
        for file in args.in_file:
            data.append(file)
        fwi.encode(data, args.out_file)
