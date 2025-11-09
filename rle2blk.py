#!/usr/bin/env python3

import copy
import sys
import re
import argparse

lookup_block = {
        0 : ' ' , 1 : '\u2580', 2 : '\u2584', 3 : '\u2588',
        32 : '\U0001fb8e', 64 : '\U0001fb8f', 96 : '\U0001fb90',
        65 : '\U0001fb91', 34 : '\U0001fb92'
        }

lookup_lif = {
        0 : '.', 1 : 'o', 32 : '?', 3 : 'X', 4 : '+'
        }

lookup_char = {v: k for k, v in lookup_lif.items()}
lookup_char['b'] = 0
lookup_char['A'] = 1

def make_lif(bitmap):
    """Turn bitmap list into a lif pattern"""
    width = len(bitmap[0])
    height = len(bitmap)
    lif_string = ""
    lif = []
    for i in range(0,height) :
        for j in range(0,width) :
            key = bitmap[i][j]
            lif.append(lookup_lif[key])
        lif.append('\n')
    lif_string += "".join(lif)
    return lif_string
    
def make_blk(bitmap, minwidth):
    """Turn bitmap list into a unicode block form"""

    width = len(bitmap[0])
    height = len(bitmap)
    if (width < minwidth):
        return ""
    blk_string = ""
    block = []
    for i in range(0,height,2) :
        for j in range(0,width) :
            key = bitmap[i][j]
            key += 2 * bitmap[i+1][j] if i+1<height else 0
            block.append(lookup_block[key])
        block.append('\n')
    blk_string += "".join(block)
    return blk_string

def make_braille(bitmap_raw,maxwidth):
    """Turn bitmap list into unicode braille chararacters"""

    width = len(bitmap_raw[0])
    height = len(bitmap_raw)
    bitmap = [[1 if x == 1 else 0 for x in sublist] for sublist in bitmap_raw]
    
    blk_string = ""
    braille = []
    for i in range(0,height,4) :
        for j in range(0,width,2) :
            key = bitmap[i][j]
            key += 8 * bitmap[i][j+1] if j+1<width else 0
            if (i+1<height):
                key += 2 * bitmap[i+1][j]
                key += 16 * bitmap[i+1][j+1] if j+1<width else 0
            if (i+2<height):
                key += 4 * bitmap[i+2][j]
                key += 32 * bitmap[i+2][j+1] if j+1<width else 0
            if (i+3<height):
                key += 64 * bitmap[i+3][j]
                key += 128 * bitmap[i+3][j+1] if j+1<width else 0
            braille.append(chr(0x2800+key))
        braille.append('\n')
    blk_string += "".join(braille)
    return blk_string

class RLE2Bitmap:
    def __init__(self, minwidth = 0, minheight = 0, output = 0):
        self.width = 0
        self.height = 0
        self.x = 0
        self.y = 0
        self.bitmap = []
        self.minwidth = minwidth
        self.minheight = minheight
        self.output = output
        self.lineptr = 0
        self.count = 0

    def dimset(self):
        return ((self.width != 0) & (self.height != 0))

    def setdim(self, ls):
        self.x = 0
        self.y = 0
        values = ls.split(',')
        self.width = int(list(re.findall(r'\d+', values[0]))[0])
        self.height = int(list(re.findall(r'\d+', values[1]))[0])
        if (self.height < self.minheight):
            self.cleardim()
            return
        self.bitmap = [[0 for i in range(self.width)] for j in range(self.height)]
        
    def cleardim(self):
        self.width = 0
        self.height = 0

    def process(self, ls):
        self.lineptr += 1
        if (ls.startswith('x')):
            self.setdim(ls)
        else:
            if self.dimset():
                n = 0
                for c in ls:
                    if (c.isdigit()):
                        n = 10 * n + ord(c) - ord('0')
                    else:
                        if (n == 0):
                            n = 1
                        if ((c == 'b') or (c == '.')):
                            self.x += n
                            n = 0
                        if (c == '$'):
                            self.x = 0
                            self.y += n
                            n = 0
                        if (c == '!'):
                            self.count += 1
                            if self.output==1:
                                print(make_braille(self.bitmap,self.minwidth))
                            else:
                                if self.output==2:
                                    print(make_lif(self.bitmap))
                                else:
                                    print(make_blk(self.bitmap,self.minwidth))
                            print(self.count, self.lineptr)
                            self.cleardim()
                            return
                        if (c == 'o') or (c == 'A'):
                            for i in range(self.x, self.x + n):
                                self.bitmap[self.y][i] = lookup_char[c]
                            self.x += n
                            n = 0 
                        if (c == '?'):
                            for i in range(self.x, self.x + n):
                                self.bitmap[self.y][i] = lookup_char[c]
                            self.x += n
                            n = 0 
                        if (c == 'X'):
                            for i in range(self.x, self.x + n):
                                self.bitmap[self.y][i] = lookup_char[c]
                            self.x += n
                            n = 0 

def main():
    parser = argparse.ArgumentParser(
        description = 'Displays RLE patterns in a file as Unicode '
                      'block [default], braille block or lif output.',
        formatter_class = argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-b', '--braille', action = 'store_true',
        help = 'output using unicode Braille')
    parser.add_argument('-l', '--lif', action = 'store_true',
        help = 'output using lif pattern')
    parser.add_argument('file', type = str,
        help = 'file containing RLE patterns')
    parser.add_argument('-mw', '--min_width', type = int, default = 0,
        help = 'minimum width for patterns to get displayed')
    parser.add_argument('-mh', '--min_height', type = int, default = 0,
        help = 'minimum height for patterns to get displayed')
    args = parser.parse_args(sys.argv[1:])

    if args.braille:
        output = 1
    else:
        if args.lif:
            output = 2
        else:
            output = 0 
    rbm = RLE2Bitmap(args.min_width, args.min_height, output)
    with open(args.file,'r') as file_rle:
        for line_str in file_rle:
            rbm.process(line_str.rstrip('\n'))

if __name__ == "__main__":
    main()

