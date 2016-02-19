# Basic smbus test.  This is pretty ugly and meant to be run against a ADS1x15
# and some output inspected by a Saleae logic analyzer.  TODO: Refactor into
# something that can test without hardware?
import binascii

import Adafruit_PureIO.smbus as smbus


DEVICE_ADDR = 0x48
REGISTER    = 0x01


# Test open and close.
i2c = smbus.SMBus()
i2c.open(1)
val = i2c.read_byte(DEVICE_ADDR)
print('read_byte from 0x{0:0X}: 0x{1:0X}'.format(REGISTER, val))
i2c.close()

# Test initializer open.
i2c = smbus.SMBus(1)
val = i2c.read_byte(DEVICE_ADDR)
print('read_byte from 0x{0:0X}: 0x{1:0X}'.format(REGISTER, val))
i2c.close()

# Test various data reads.
with smbus.SMBus(1) as i2c:
    val = i2c.read_byte(DEVICE_ADDR)
    print('read_byte from 0x{0:0X}: 0x{1:0X}'.format(REGISTER, val))
    val = i2c.read_byte_data(DEVICE_ADDR, REGISTER)
    print('read_byte_data from 0x{0:0X}: 0x{1:0X}'.format(REGISTER, val))
    val = i2c.read_word_data(DEVICE_ADDR, REGISTER)
    print('read_word_data from 0x{0:0X}: 0x{1:04X}'.format(REGISTER, val))
    val = i2c.read_i2c_block_data(DEVICE_ADDR, REGISTER, 2)
    print('read_i2c_block_data from 0x{0:0X}: 0x{1}'.format(REGISTER, binascii.hexlify(val)))

# Test various data writes.
with smbus.SMBus(1) as i2c:
    i2c.write_byte(DEVICE_ADDR, REGISTER)
    i2c.write_byte_data(DEVICE_ADDR, REGISTER, 0x85)
    i2c.write_word_data(DEVICE_ADDR, REGISTER, 0x8385)
    i2c.write_i2c_block_data(DEVICE_ADDR, REGISTER, [0x85, 0x83])
    #i2c.write_block_data(DEVICE_ADDR, REGISTER, [0x85, 0x83])
    i2c.write_quick(DEVICE_ADDR)

# Process call test.
with smbus.SMBus(1) as i2c:
    val = i2c.process_call(DEVICE_ADDR, REGISTER, 0x8385)
    print('process_call from 0x{0:0X}: 0x{1:04X}'.format(REGISTER, val))
