# Interactive basic test for Adafruit_PureIO.smbus module.
# Intended to be run on NTC's C.H.I.P. single-board computer.
#   (see https://getchip.com).
# Instructions:
#   sudo python test_chip.py

import Adafruit_PureIO.smbus as smbus

AXP209_DEV_BUS = 0  # I2C bus for AXP209 power controller chip
AXP209_DEV_ADDR = 0x34  # I2C address for AXP209 power controller chip
STATUS_LED_REG = 0x93  # AXP209 register for GPIO2, drives status LED
RESET_REG = 0x4a  # AXP209 register containing reset status bits
SHORT_PRESS_MASK = 0x02  # bit of RESET_REG indicating a short reset

a = raw_input("Status LED should be on.  (y/n): ")
assert(a.upper() == "Y")

bus = smbus.SMBus(AXP209_DEV_BUS, dangerous=True)
bus.write_byte_data(AXP209_DEV_ADDR, STATUS_LED_REG, 0)
bus.close()

a = raw_input("Status LED should now be off.  (y/n): ")
assert(a.upper() == "Y")

# read the "short press" status bit:

bus = smbus.SMBus()
bus.open(AXP209_DEV_BUS, dangerous=True)
reset_reg = bus.read_byte_data(AXP209_DEV_ADDR, RESET_REG)
short_press = ((reset_reg & SHORT_PRESS_MASK) == SHORT_PRESS_MASK)
assert(not short_press)
bus.close()

a = raw_input("BRIEFLY press the reset button, then press enter: ")

bus = smbus.SMBus(AXP209_DEV_BUS, dangerous=True)
bus.open(AXP209_DEV_BUS, dangerous=True)  # should work to re-open it
reset_reg = bus.read_byte_data(AXP209_DEV_ADDR, RESET_REG)
short_press = ((reset_reg & SHORT_PRESS_MASK) == SHORT_PRESS_MASK)
assert(short_press)

# Clear the "short press" bit.
bus.write_byte_data(AXP209_DEV_ADDR, RESET_REG, 2)
reset_reg = bus.read_byte_data(AXP209_DEV_ADDR, RESET_REG)
short_press = ((reset_reg & SHORT_PRESS_MASK) == SHORT_PRESS_MASK)
assert(not short_press)
bus.close()

# Make sure non-dangerous mode throws exception.

bus = smbus.SMBus(AXP209_DEV_BUS)
err = None
try:
    bus.write_byte_data(AXP209_DEV_ADDR, STATUS_LED_REG, 1)
except IOError, e:
    err = e.errno
assert(err == 16)
bus.close()

a = raw_input("Status LED should still be off.  (y/n): ")
assert(a.upper() == "Y")

# Leave status LED on.

bus = smbus.SMBus(AXP209_DEV_BUS, dangerous=True)
bus.write_byte_data(AXP209_DEV_ADDR, STATUS_LED_REG, 1)
bus.close()

a = raw_input("Status LED should now be on.  (y/n): ")
assert(a.upper() == "Y")

print "All tests successful!"
