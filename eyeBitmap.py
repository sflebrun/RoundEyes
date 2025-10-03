# eyeBitmap.py
#
# Utility functions for handling the eye bitmap data
#
# 
#  Copyright © 2025, Steven F. LeBrun.  All rights reserved. 
# 

# extractEye( eyeBitmapFile )
#
# Generates a bytearray from a Python file containing the eye bitmap data.
# The file is loaded using the import statement and is expected to contain
# the following variables:
#
# WIDTH   - width of the bitmap in pixels
# HEIGHT  - height of the bitmap in pixels
# PALETTE - list of RGB tuples representing the color palette
# COLORS  - number of colors in the palette
# BPP     - bits per pixel (1, 2, 4, or 8)
# BITMAP  - list of integers representing the bitmap pixel data
#           The data in the BITMAP list is packed according to the BPP value.
#
# Returns a bytearray containing the pixel data in RGB565 format.
def extractEye( eyeBitmapFile ):
    width   = eyeBitmapFile.WIDTH
    height  = eyeBitmapFile.HEIGHT
    palette = eyeBitmapFile.PALETTE
    colors  = eyeBitmapFile.COLORS
    bpp     = eyeBitmapFile.BPP
    bitmap  = eyeBitmapFile.BITMAP

   # masks = { 1:0x01, 2:0x03, 3:0x7, 4:0x0F, 5:0x1F, 6:0x3F, 7:0x7F, 8:0xFF }
    masks = bytearray([ 0xFF, 0x7F, 0x3F, 0x1F, 0x0F, 0x07, 0x03, 0x01 ])
    byteSize = 8  # Number of bits in a byte

    # Create an empty buffer for the full pixel color data so that we don't
    # have to keep appending to the bytearray (which is slow)
    bufferSize = width * height * 2  # 2 bytes per pixel for RGB565
    buffer = bytearray( bufferSize )

    # Extract bpp bits from Bitmap to get the color index for each pixel,
    # element in buffer. The color index is then used to look up the RGB
    # value in the palette, which is converted to RGB565 and stored in
    # the buffer.

    bitMapIndex = 0   # Index into the bitmap list
    bitIndex    = 0   # Bit index within the current byte
    bufIndex    = 0   # Index into the output buffer

    # Outer Loop - once for each pixel in the bitmap
    while (bufIndex < bufferSize):
        colorIndex = 0
        bitsNeeded = bpp
        bitShift   = 0

        # Inner Loop - extract enough bits to make up the color index
        while (bitsNeeded > 0):
            # If bitIndex is greater than byteSize, move to the next byte
            if ( bitIndex >= byteSize ):
                bitMapIndex += 1
                bitIndex = 0

            # Get the current byte from the bitmap
            thisByte = bitmap[ bitMapIndex ]

            # Get rid of bits at the front of the byte (MSB bits) that are not
            # needed. We only want to look at the bits from bitIndex to the LSB
            #print("bitIndex: {}, thisByte: {:02X}".format( bitIndex, thisByte ) )
            ByteBits = thisByte & masks[bitIndex]

            bitsAvailable = byteSize - bitIndex
            bitsToExtract = min( bitsNeeded, bitsAvailable )

            # if we don't need all the bits available, shift the bits to the
            # right to get rid of the unwanted LSB bits
            if ( bitsToExtract < bitsAvailable ):
                # Shift bits to get rid of unwanted LSB bits
                ByteBits = ByteBits >> ( bitsAvailable - bitsToExtract )

            # merge extracted bits into colorIndex after shifting colorIndex
            # to make room for the new bits
            colorIndex = ( colorIndex << bitsToExtract ) | ByteBits
            bitsNeeded -= bitsToExtract

            bitIndex += bitsToExtract
            # End of inner loop

        # We now have the color index for the pixel, so look up the RGB
        # value in the palette and convert it to RGB565 format.
        if ( colorIndex >= colors ):
            # Error - color index out of range
            msg = "Error: Color index {} out of range (max {}). Bitmap[{}], Buffer[{}]".format( 
                colorIndex, colors-1, bitMapIndex, bufIndex )
            raise ValueError( msg ) 
        
        # Get the RGB value from the palette
        color = palette[ colorIndex ]
        buffer[bufIndex + 1] = color >> byteSize
        buffer[bufIndex]     = color &  0xFF 
        bufIndex += 2
        # End of outer loop

    return buffer
    # end of extractEye()


