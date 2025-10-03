##
# Eyeball Class
#
# Handles one display with an eyeball bitmap that can move around
# the display area.
# 
#  Copyright © 2025, Steven F. LeBrun.  All rights reserved. 
# 

"""
    eyeball.py
    
    Module: Class that contains information about an eye ball bitmap.
"""

from machine import ADC,  Pin

## Potentiometer Pins
# PIN_ADC_LEFT    =  Pin(27, mode=Pin.IN, pull=Pin.PULL_DOWN)
# PIN_ADC_RIGHT   =  Pin(26, mode=Pin.IN, pull=Pin.PULL_DOWN)
# 
# potLeft         =  ADC(PIN_ADC_LEFT)
# potRight        =  ADC(PIN_ADC_RIGHT)
potMin          =  const(0)
potMax          =  const(65535)

## Debug mode on if True
DEBUG_MODE = False

##
## Class Eyeball
##
class Eyeball:
    '''
    Class that tracks eyeball bitmap and its movement
    
    Direction values:
       Horizontal :  > 0 - Right
                     = 0 - No Movement
                     < 0 - Left
                     
       Vertical    : > 0 - Up
                     = 0 - No Movement
                     < 0 - Down
    '''
    
    MOVE_STOP  =  0
    MOVE_RIGHT =  1
    MOVE_LEFT  = -1
    MOVE_UP    = -1
    MOVE_DOWN  =  1
    
    def __init__(self, eyeBuffer, width, height, display, maxX=240,  maxY=240, background=0xFFFF):
        self.buffer     = eyeBuffer
        self.width      = width
        self.height     = height
        self.maxX       = maxX
        self.maxY       = maxY
        self.display    = display
        self.background = background
        
        # Set initial step size to 1
        self.stepX      = 1
        self.stepY      = 1
        
        # Set initial directions to No Movement
        self.horizontal = self.MOVE_STOP
        self.vertical   = self.MOVE_STOP
        
        # Determine center of display
        self.CENTER_X   = int( (self.maxX - self.width)  / 2)
        self.CENTER_Y   = int( (self.maxY - self.height) / 2)

         # Center Eye and make stationary
        self.moveCenter()
               
        # Determine Potentiometer
        #    Assuming potMin is zero
        self.factorX    = potMax / (self.maxX - self.width)
        self.factorY    = potMax / (self.maxY - self.height)
        
        self.delta      = 1 # destination is the same if within +/- delta

        # Initialize display to background color
        self.display.fill(self.background)
        
        
    def print(self):
        print("Width:           ", self.width)
        print("Height:          ", self.height)
        print("Speed:           ", self.speed)
        print("Step:            ", self.step)
        print("X:               ", self.x)
        print("Y:               ", self.y)
        print("Display Width:   ", self.maxX)
        print("Display Height:  ", self.maxY)
        
    def clear(self):
        self.display.fill(self.background)
        
    def show(self):
        self.display.blit_buffer( self.buffer, self.x, self.y, self.width, self.height )
        
        
    def setDirection( self, newHorizontal = 0, newVertical = 0 ):
        self.horizontal = self.triState(newHorizontal)
        self.vertical   = self.triState(newVertical)
        
        
    def move( self, stopAtTarget ):
        # If step size places X outside of Display, reverse direction if not stopping at target
        if ( stopAtTarget and (self.x == self.targetX ) ):
            self.horizontal = self.MOVE_STOP
            if ( DEBUG_MODE ):
                print("Stopping at X = ", self.x)
            
        if ( self.horizontal != self.MOVE_STOP ):
            if ( self.horizontal == self.MOVE_RIGHT ):
                # Moving right
                if ( (self.x + self.stepX + self.width) >= self.maxX ):
                    # Reverse direction
                    self.horizontal = self.MOVE_LEFT
            else:
                # Moving left
                if ( (self.x - self.stepX) < 0 ):
                    # Reverse Direction
                    self.horizontal = self.MOVE_RIGHT
          
        if ( stopAtTarget and ( self.y == self.targetY ) ):
            self.vertical = 0
            if ( DEBUG_MODE ):
                print("Stopping at Y = ", self.y)
            
        if ( self.vertical != self.MOVE_STOP ):
            if ( self.vertical == self.MOVE_UP ):
                # Moving up
                if ( ( self.y - self.stepY ) < 0 ):
                    # Reverse Direction
                    self.vertical = self.MOVE_DOWN
            else:
                # Moving Down
                if ( ( self.y + self.stepY + self.height ) >= self.maxY ):
                    # Reverse Direction
                    self.vertical = self.MOVE_UP
                    
        if ( self.horizontal != self.MOVE_STOP ):
            if ( self.horizontal == self.MOVE_RIGHT ):
                # Move Right
                self.x += self.stepX
            else:
                # Move Left
                self.x -= self.stepX
                
        if ( self.vertical != self.MOVE_STOP ):
            if ( self.vertical == self.MOVE_UP ):
                # Move Up
                self.y -= self.stepY
            else:
                # Move Down
                self.y += self.stepY
                
        return
    
    def moveCenter(self):
        self.x           = self.CENTER_X
        self.y           = self.CENTER_Y
        self.targetX     = self.x
        self.targetY     = self.y
        self.horizontal  = 0
        self.vertical    = 0
    
    def atDestination(self):
        if ( self.x == self.targetX and self.y == self.targetY ):
            return True
        return False
   
    def triState( self, value ):
        if ( value == 0 ):
            return 0
        if ( value < 0 ):
            return -1
        return 1
    
    def setDirection(self, newHorizontal, newVertical ):
        self.horizontal = self.triState(newHorizontal)
        self.vertical   = self.triState(newVertical)
    
    
    def setDestination( self, newX, newY ):
        self.targetX = newX
        self.targetY = newY
        
    def changeDestination( self, xPot, yPot ):
        # Change Pot value from [0..36535] to [0..max[X/Y]]
        newX  = int( xPot / self.factorX )
        newY  = int( yPot / self.factorY )
        
        noChangeX = False
        noChangeY = False
        
        if ( newX >= (self.targetX - self.delta) and newX <= (self.targetX + self.delta) ):
            # Within jitter of potentiometer.  Ignore change
            newX = self.targetX
            noChangeX = True
            
        if ( newY >= (self.targetY - self.delta) and newY <= (self.targetY + self.delta) ):
            # Within jitter of potentiometer.  Ignore change
            newY = self.targetY
            noChangeY = True
            
        # If no change in destination (target) then nothing to do
        if ( noChangeX and noChangeY ):
            return
           
        # Set new Target Destination
        self.targetX = newX
        self.targetY = newY
        
        # Determine direction to get there
        self.autoDirection()
         
        if ( DEBUG_MODE ):
            print("New Target: (", self.x, ", ", self.y, ") ==> (", newX, ", ", newY, "), [", self.horizontal, ", ", self.vertical, "]")
        
        return

    def autoDirection(self):
        # Assume (x,y) and (targetX, targetY) are set but direction is not
        # Determine direction to get there
        
        newHorizontal = 0
        if ( self.x < self.targetX ):
            newHorizontal =  1
        elif ( self.x > self.targetX ):
            newHorizontal = -1
            
        newVertical = 0
        if ( self.y < self.targetY ):
            newVertical = -1
        elif ( self.y > self.targetY ):
            newVertical =  1
        
        self.setDirection( newHorizontal, newVertical )
            
    OldX = -1
    OldY = -1

    def moveEyeball( self, stopAtTarget=False ):
        global OldX, OldY
        # Get position before move
        OldX = self.x
        OldY = self.y
    
        # Move (x,y) of Iris to new position
        self.move( stopAtTarget )
    
        # Clear Horizontal Afterimage
        if ( self.horizontal != 0 ):
            y = OldY
            height = self.height
            width  = self.stepX
            if ( self.horizontal > 0 ):
                # Moving right
                x      = OldX
            else:
                # Moving left
                x      = OldX + self.width - self.stepX
            
            self.display.fill_rect( x, y, width, height,  self.background )
    
        # Clear Vertical Afterimage
        if ( self.vertical != 0 ):
            x      = OldX
            height = self.stepY + 1
            width  = self.width
            if ( self.vertical > 0 ):
                # Moving Up
                y  = OldY + self.height - self.stepY
            else:
                # Moving Down
                y  = OldY
            
            self.display.fill_rect( x, y, width, height, self.background )

        
        # Draw Eyeball in new position
        self.show()
        # End of moveEyeball()
