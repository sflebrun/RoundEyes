#
# pinUtils.py -- Utility functions for pin manipulation
#

from machine import Pin 

# Determines which pin GPIO number is associated with the Pin object.
#
# str(pin) ==> "Pin(GPIO#, mode=IN/OUT, pull=UP/DOWN/NONE)"
# 
# Returns the GPIO number as an integer.  If it cannot be determined,
# a -1 is returned.
#
def pinID(pin: Pin):
    # First remove the string "Pin(" from the beginning of the string.")"

    print("Pin: ", str(pin))

    # Extract "GPIOxx" from the string (first 4 characters are "Pin(")
    text = str(pin)[4:]
    offset = text.find(",")
    if ( offset > 0 ):
        text = text[0:offset]
    else:
        text = "Unknown"

    # If the PinNum is just an integer (no GPIO prefix), then its length will
    # be less than 3 characters.
    try:
        if ( len(text) < 3 ):
            gpioPin = int(text)
        else:
            # The PinNum is in the format "GPIOxx" where xx is the GPIO number.
            # We need to extract the number from the string.
            gpioPin = int(text[4:])
    except: # ValueError:
        gpioPin = -1 

    return gpioPin
    # End of pinID()

