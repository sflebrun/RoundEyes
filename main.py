##
#  Main program for Round Eyes on two GC9A01 TFT Displays
# 
#  Copyright © 2025, Steven F. LeBrun.  All rights reserved. 
# 


"""
    eyeball2.py
    
    Display an image of an eye ball on two GC9A01 TFT Displays and move left and right
"""

from   machine     import ADC, Pin, SPI
from   micropython import const

import gc9a01py as gc9a01

from   eyeball     import Eyeball
from   eyeBitmap   import extractEye
from   pinUtils    import pinID

from   utime       import sleep, sleep_ms, ticks_ms

# Bitmap (Python File format) of purple eye (just the iris)
import peye

DEBUG_MODE = False

## Define Left Eye, Right Eye, and Common Pins

PIN_CS_LEFT     =  Pin(13, mode=Pin.OUT)
PIN_CS_RIGHT    =  Pin(12, mode=Pin.OUT)

PIN_RESET_LEFT  =  Pin(22, mode=Pin.OUT)
PIN_RESET_RIGHT =  Pin(20, mode=Pin.OUT)

PIN_CLK         =  Pin(18, mode=Pin.OUT)
PIN_MOSI        =  Pin(19, mode=Pin.OUT)
PIN_DC          =  Pin(21, mode=Pin.OUT)
PIN_RESET       =  Pin(26, mode=Pin.OUT)
PIN_BACKLIGHT   =  Pin(17, mode=Pin.OUT)


## Button for changing Mode
PIN_MODE        = Pin(3, mode=Pin.IN, pull=Pin.PULL_UP )

## Potentiometer Pins
PIN_ADC_LEFT    =  Pin(27, mode=Pin.IN, pull=Pin.PULL_DOWN)
PIN_ADC_RIGHT   =  Pin(26, mode=Pin.IN, pull=Pin.PULL_DOWN)

potLeft         =  ADC(PIN_ADC_LEFT)
potRight        =  ADC(PIN_ADC_RIGHT)

# BAUD_RATE       =  600000000   # 600kHz
BAUD_RATE       =  1000000000   # 600kHz
SPI_BLOCK       =  0

DISPLAY_WIDTH   = const(240)
DISPLAY_HEIGHT  = const(240)

BACKGROUND      = gc9a01.WHITE

# Mode:  0 == Center Still
#        1 == Auto Left and Right
#        2 == Auto Up and Down
#        3 == Potentiometer Control

CENTER_STILL     = const(0)
AUTO_HORIZONTAL  = const(1)
AUTO_VERTICAL    = const(2)
MANUAL_CONTROL   = const(3)

mode = CENTER_STILL

#
# The expected time it takes for the button to stop bouncing.
# This variabe is in milliseconds.
BOUNCE_TIME_MS = 50 # 50 milliseconds debounce time

# Push Button Pin Debouncing
#
# Watches Button values until it stablizes on the same value
# for 50ms.  It does not matter whether that value is HIGH or LOW.
#
# Returns the final, stable, Pin value.
def buttonDebounce( pin: Pin ):
    global BOUNCE_TIME_MS
    curr_value = pin.value()
    period     = 100 # stable within 50 ms

    active = 0
    while ( active < period ):
        if ( pin.value() == curr_value ):
            # Pin value did not change, increment ms counter
            active += 1
        else:
            # Pin value did change.  Use the new pin value as the
            # current value.  Reset ms counter to start new period
            # of watching.
            active = 0
            curr_value = pin.value()
        sleep_ms(1)

    return curr_value
    # End of buttonDebounce()

# Since bouncing can cause multiple interrupts, we need to ignore interrupts
# that occur within a certain time period after the first interrupt.
# 
# firstInterruptTime is the time in milliseconds of the first interrupt in this sequence.
# D

firstInterruptTime   = 0
DELTA_INTERRUPT_TIME = 200  # Minimum time between interrupts in milliseconds
#
# Button Interrupt Handler
# 
# Wait for button to stablize, then change mode.
# Also, ignore any interrupts that occur within DELTA_INTERRUPT_TIME
# milliseconds of the first interrupt in this sequence.
#
def buttonHandler( pin: Pin ):
    global irisRight, irisLeft, mode
    global firstInterruptTime, DELTA_INTERRUPT_TIME

    # Make sure enough time has passed since the last interrupt for
    # this interrupt to be handled.
    currentTime = ticks_ms()

    if ( (currentTime - firstInterruptTime) < DELTA_INTERRUPT_TIME ):
        if ( DEBUG_MODE ):
            print("Ignoring interrupt on GPIO {} due to time delta".format(pinID(pin)))
        return  # Ignore this interrupt as it is too close to the last one
    
    # Wait out button bounce
    pinValue = buttonDebounce(pin)
    
    # If pin HIGH
    if ( pinValue == 1 ):
        # Nothing to do.
        return
    
    mode += 1
    
    if ( mode > MANUAL_CONTROL ):
        mode = 0
               
    if ( DEBUG_MODE ):
        print("New Mode: ", mode)
        
    return
    # End of buttonHandler()
   



## Setup Button Interrupt Handler
PIN_MODE.irq(handler=buttonHandler, trigger=Pin.IRQ_FALLING)


spi = SPI(SPI_BLOCK, sck=PIN_CLK, mosi=PIN_MOSI, baudrate=BAUD_RATE)

# Create Display Objects for Left and Right Eyes
eyeRight   = gc9a01.GC9A01( spi,
                            dc=PIN_DC,
                            cs=PIN_CS_RIGHT,
                            reset=PIN_RESET_RIGHT,
                            backlight=PIN_BACKLIGHT,
                            rotation=0)

eyeLeft    = gc9a01.GC9A01( spi,
                            dc=PIN_DC,
                            cs=PIN_CS_LEFT,
                            reset=PIN_RESET_LEFT,
                            backlight=PIN_BACKLIGHT,
                            rotation=0)

eyeRight.fill(gc9a01.RED | gc9a01.BLUE)  # Purple
eyeLeft.fill( gc9a01.RED | gc9a01.BLUE)  # Purple

##
## Create and initialize to Eyeball objects.
##
## One for the left and one for the right.  Both share the same image buffer
##
print("eyeball: [", peye.WIDTH, "x", peye.HEIGHT, "], Colors: ", len(peye.PALETTE), " = ", peye.COLORS)
print("Bitmap Size: ", len(peye.BITMAP), " pixels, Buffer Size: ", peye.WIDTH * peye.HEIGHT * 2, " bytes")

#eyeBuffer = getBufferFromBitmap( peye )
#
# Extracting bitmap buffer external to the Eyeball class allows
# both eyeballs to share the same buffer, saving memory.
#   
eyeBuffer = extractEye( peye )

irisRight = Eyeball( eyeBuffer, peye.WIDTH, peye.HEIGHT, eyeRight, DISPLAY_WIDTH, DISPLAY_HEIGHT)
irisLeft  = Eyeball( eyeBuffer, peye.WIDTH, peye.HEIGHT, eyeLeft,  DISPLAY_WIDTH, DISPLAY_HEIGHT)

irisRight.show()
irisLeft.show()


led = Pin("LED", Pin.OUT)
onFlag = False
cnt    = 0

def moveAutomatic():
    global  eyeRight, irisRight
    global  eyeLeft,  irisLeft
    
    irisRight.moveEyeball( False )
    irisLeft.moveEyeball(  False )
    return
    

atTargetRight = False
atTargetLeft  = False

def manualControl():
    global lastRight, lastLeft, atTargetRight, atTargetLeft
     
    # Determine where target destination is
    left  = potLeft.read_u16()
    right = potRight.read_u16()
    
    irisRight.changeDestination(left, right)
    irisLeft.changeDestination( left, right)

    stopAtTarget = (mode == MANUAL_CONTROL)
    # Draw new eyes if no at destination
    if ( not irisRight.atDestination() ):
        irisRight.moveEyeball(stopAtTarget)
        atTargetRight = False
    else:
        if (DEBUG_MODE and not atTargetRight):
            print("Right Eye at Target")
            atTargetRight = True

        
    if ( not irisLeft.atDestination() ):
        irisLeft.moveEyeball( stopAtTarget )
        atTargetLeft = False
    else:
        if (DEBUG_MODE and not atTargetLeft):
            print("Left  Eye at Target")
            atTargetLeft = True
        
    return
   
def debugPrint( currMode, imageLeft, imageRight ):
    if ( not DEBUG_MODE ):
        return
    
    modeStr = "Unknown Mode: " + str(currMode)
    if ( currMode == AUTO_HORIZONTAL ):
        modeStr = "Auto Horizontal"
    elif ( currMode == AUTO_VERTICAL ):
        modeStr = "Auto Vertical"
    elif ( currMode == MANUAL_CONTROL ):
        modeStr = "Manual Control"
    print("Mode: ", modeStr)

    print("Left  Iris: (", imageLeft.x, ", ", imageLeft.y, ") ==> (", imageLeft.targetX, ", ", imageLeft.targetY, "), [",
          imageLeft.horizontal, ", ", imageLeft.vertical, "]")

    print("Right Iris: (", imageRight.x, ", ", imageRight.y, ") ==> (", imageRight.targetX, ", ", imageRight.targetY, "), [",
          imageRight.horizontal, ", ", imageRight.vertical, "]")
    
def newMode():
    global mode, irisLeft, irisRight, eyeRight, eyeLeft
    
    # Clear old iris from display
    irisRight.clear()
    irisLeft.clear()
    
    # Center each eye
    irisRight.moveCenter()
    irisLeft.moveCenter()
    
    # Set Directions based on mode
    if ( mode == AUTO_HORIZONTAL ):
        irisRight.setDirection( -1, 0 )
        irisRight.setDestination( -1, irisRight.CENTER_Y )
        irisLeft.setDirection(  -1, 0 )
        irisLeft.setDestination(   -1, irisLeft.CENTER_Y )
    elif ( mode == AUTO_VERTICAL ):
        irisRight.setDirection( 0, 1 )
        irisRight.setDestination( irisRight.CENTER_X, -1 )
        irisLeft.setDirection(  0, 1 )
        irisLeft.setDestination(  irisLeft.CENTER_X, -1 )
    elif ( mode == CENTER_STILL ):
        irisRight.setDirection( 0, 0 )
        irisLeft.setDirection(  0, 0 )
        irisRight.moveCenter()
        irisLeft.moveCenter()
    else:
        irisRight.autoDirection()
        irisLeft.autoDirection()
        
    # Display eyes
    irisRight.show()
    irisLeft.show()
        
    debugPrint( mode, irisLeft, irisRight )
        
   
          

oldMode = -1 # Not a valid value which will trigger a flush display on the first loop

print("Enter forever loop")

try:
    while True:
        if ( onFlag ):
            led.off()
            onFlag = False
        else:
            led.on()
            onFlag = True
        
        if ( oldMode != mode ):
            oldMode = mode
            newMode()            
        
        if ( mode == AUTO_HORIZONTAL or mode == AUTO_VERTICAL):
            moveAutomatic()
        elif ( mode == CENTER_STILL ):
            # Nothing to do.  Eyes are centered and still.
            pass
        else:
            manualControl()

        sleep_ms(50)

except KeyboardInterrupt:
    print("Keyboard Interrupt")
finally:
    eyeRight.fill(BACKGROUND)
    eyeLeft.fill(BACKGROUND)
 

print("Done")


