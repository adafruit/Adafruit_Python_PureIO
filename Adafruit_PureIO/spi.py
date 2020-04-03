# Copyright (c) 2020 Adafruit Industries
# Author: Melissa LeBlanc-Williams
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""SPI interface that mimics the SpiDev API."""

from ctypes import c_uint8, c_uint16, c_uint32, cast, pointer, POINTER
from ctypes import create_string_buffer, Structure, string_at, addressof
from fcntl import ioctl
import struct
import os.path
import array

# SPI C API constants (from linux kernel headers)
# pylint: disable=bad-whitespace
SPI_CPHA        = 0x01
SPI_CPOL        = 0x02
SPI_CS_HIGH     = 0x04
SPI_LSB_FIRST   = 0x08
SPI_THREE_WIRE  = 0x10
SPI_LOOP        = 0x20
SPI_NO_CS       = 0x40
SPI_READY       = 0x80
SPI_TX_DUAL     = 0x100
SPI_TX_QUAD     = 0x200
SPI_RX_DUAL     = 0x400
SPI_RX_QUAD     = 0x800

SPI_MODE_0 = 0
SPI_MODE_1 = SPI_CPHA
SPI_MODE_2 = SPI_CPOL
SPI_MODE_3 = SPI_CPHA | SPI_CPOL

SPI_CHUNK_SIZE = 4096
# pylint: enable=bad-whitespace

def _ioc_encode(direction, number, structure):
    """
    ioctl command encoding helper function
    Calculates the appropriate spidev ioctl op argument given the direction,
    command number, and argument structure in python's struct.pack format.
    Returns a tuple of the calculated op and the struct.pack format
    See Linux kernel source file /include/uapi/asm-generic/ioctl.h
    """
    ioc_magic = ord('k')
    ioc_nrbits = 8
    ioc_typebits = 8
    ioc_sizebits = 14  # XXX: 13 on PPC, MIPS, Sparc, and Alpha
    ioc_nrshift = 0
    ioc_typeshift = ioc_nrshift + ioc_nrbits
    ioc_sizeshift = ioc_typeshift + ioc_typebits
    ioc_dirshift = ioc_sizeshift + ioc_sizebits

    size = struct.calcsize(structure)

    op = (direction << ioc_dirshift) | (ioc_magic << ioc_typeshift) | \
         (number << ioc_nrshift) | (size << ioc_sizeshift)

    return direction, op, structure

class SPI(object):
    """
    struct spi_ioc_transfer {
        __u64           tx_buf;
        __u64           rx_buf;
        __u32           len;
        __u32           speed_hz;
        __u16           delay_usecs;
        __u8            bits_per_word;
        __u8            cs_change;
        __u8            tx_nbits;
        __u8            rx_nbits;
        __u16           pad;
    """
    _IOC_TRANSFER_FORMAT = "QQIIHBBBBH"

    _IOC_WRITE = 1
    _IOC_READ = 2

    # _IOC_MESSAGE is a special case, so we ony need the ioctl number
    _IOC_MESSAGE = _ioc_encode(_IOC_WRITE, 0, _IOC_TRANSFER_FORMAT)[1]

    _IOC_RD_MODE = _ioc_encode(_IOC_READ, 1, "B")
    _IOC_WR_MODE = _ioc_encode(_IOC_WRITE, 1, "B")

    _IOC_RD_LSB_FIRST = _ioc_encode(_IOC_READ, 2, "B")
    _IOC_WR_LSB_FIRST = _ioc_encode(_IOC_WRITE, 2, "B")

    _IOC_RD_BITS_PER_WORD = _ioc_encode(_IOC_READ, 3, "B")
    _IOC_WR_BITS_PER_WORD = _ioc_encode(_IOC_WRITE, 3, "B")

    _IOC_RD_MAX_SPEED_HZ = _ioc_encode(_IOC_READ, 4, "I")
    _IOC_WR_MAX_SPEED_HZ = _ioc_encode(_IOC_WRITE, 4, "I")

    _IOC_RD_MODE32 = _ioc_encode(_IOC_READ, 5, "I")
    _IOC_WR_MODE32 = _ioc_encode(_IOC_WRITE, 5, "I")

    def __init__(self, device, max_speed_hz=None, bits_per_word=None, phase=None,
                 polarity=None, cs_high=None, lsb_first=None,
                 three_wire=None, loop=None, no_cs=None, ready=None):
        """Create spidev interface object.

        Args:
            device: Tuple of (bus, device) or string of device path
            max_speed_hz: Optional target bus speed in Hz.
            bits_per_word: Optional number of bits per word.

        Raises:
            IOError: The spidev device could not be opened (check permissions)
        """
        if isinstance(device, tuple):
            (bus, dev) = device
            device = "/dev/spidev{:d}.{:d}".format(bus, dev)

        if not os.path.exists(device):
            raise IOError("{} does not exist".format(device))

        self.handle = os.open(device, os.O_RDWR)

        if max_speed_hz is not None:
            self.max_speed_hz = max_speed_hz

        if bits_per_word is not None:
            self.bits_per_word = bits_per_word

        if phase is not None:
            self.phase = phase

        if polarity is not None:
            self.polarity = polarity

        if cs_high is not None:
            self.cs_high = cs_high

        if lsb_first is not None:
            self.lsb_first = lsb_first

        if three_wire is not None:
            self.three_wire = three_wire

        if self.loop is not None:
            self.loop = loop

        if self.no_cs is not None:
            self.no_cs = no_cs

        if self.ready is not None:
            self.ready = ready

    def _ioctl(self, ioctl_data, data=None):
        """ioctl helper function.

        Performs an ioctl on self.handle. If the ioctl is an SPI read type
        ioctl, returns the result value.

        Args:
            ioctl_data: Tuple of (direction, op structure), where direction
            is one of SPI._IOC_READ or SPI._IOC_WRITE, op is the
            pre-computed ioctl op (see _ioc above) and structure is the
            Python format string for the ioctl arguments.

        Returns:
            If ioctl_data specifies an SPI._IOC_READ, returns the result.
            For SPI._IOC_WRITE types, returns None
        """
        (direction, ioctl_bytes, structure) = ioctl_data
        if direction == SPI._IOC_READ:
            arg = array.array(structure, [0])
            ioctl(self.handle, ioctl_bytes, arg, True)
            return arg[0]
        else:
            arg = struct.pack("=" + structure, data)
            ioctl(self.handle, ioctl_bytes, arg)
            return

    def _get_mode_field(self, field):
        """Helper function to get specific spidev mode bits

        Args:
            field: Bit mask to apply to spidev mode.

        Returns:
            bool(mode & field). True if specified bit is 1, otherwise False
        """
        return True if self._ioctl(SPI._IOC_RD_MODE) & field else False

    def _set_mode_field(self, field, value):
        """Helper function to set a spidev mode bit

        Args:
            field: Bitmask of bit(s) to set to value
            value: True to set bit(s) to 1, false to set bit(s) to 0
        """
        mode = self._ioctl(SPI._IOC_RD_MODE)
        if value:
            mode |= field
        else:
            mode &= ~field
        self._ioctl(SPI._IOC_WR_MODE, mode)

    @property
    def phase(self):
        """SPI clock phase bit

        False: Sample at leading edge of clock
        True: Sample at trailing edge of clock
        """
        return self._get_mode_field(SPI_CPHA)

    @phase.setter
    def phase(self, phase):
        self._set_mode_field(SPI_CPHA, phase)

    @property
    def polarity(self):
        """SPI polarity bit

        False: Data sampled at rising edge, data changes on falling edge
        True: Data sampled at falling edge, data changes on rising edge
        """
        return self._get_mode_field(SPI_CPOL)

    @polarity.setter
    def polarity(self, polarity):
        self._set_mode_field(SPI_CPOL, polarity)

    @property
    def cs_high(self):
        """SPI chip select active level

        True: Chip select is active high
        False: Chip select is active low
        """
        return self._get_mode_field(SPI_CS_HIGH)

    @cs_high.setter
    def cs_high(self, cs_high):
        self._set_mode_field(SPI_CS_HIGH, cs_high)

    @property
    def lsb_first(self):
        """Bit order of SPI word transfers

        False: Send MSB first
        True: Send LSB first
        """
        return self._get_mode_field(SPI_LSB_FIRST)

    @lsb_first.setter
    def lsb_first(self, lsb_first):
        self._set_mode_field(SPI_LSB_FIRST, lsb_first)

    @property
    def three_wire(self):
        """SPI 3-wire mode

        True: Data is read and written on the same line (3-wire mode)
        False: Data is read and written on separate lines (MOSI & MISO)
        """
        return self._get_mode_field(SPI_THREE_WIRE)

    @three_wire.setter
    def three_wire(self, three_wire):
        self._set_mode_field(SPI_THREE_WIRE, three_wire)

    @property
    def loop(self):
        """SPI loopback mode"""
        return self._get_mode_field(SPI_LOOP)

    @loop.setter
    def loop(self, loop):
        self._set_mode_field(SPI_LOOP, loop)

    @property
    def no_cs(self):
        """No chipselect. Single device on bus."""
        return self._get_mode_field(SPI_NO_CS)

    @no_cs.setter
    def no_cs(self, no_cs):
        self._set_mode_field(SPI_NO_CS, no_cs)

    @property
    def ready(self):
        """Slave pulls low to pause"""
        return self._get_mode_field(SPI_READY)

    @ready.setter
    def ready(self, ready):
        self._set_mode_field(SPI_READY, ready)

    @property
    def max_speed_hz(self):
        """Maximum SPI transfer speed in Hz.

        Note that the controller cannot necessarily assign the requested
        speed.
        """
        return self._ioctl(SPI._IOC_RD_MAX_SPEED_HZ)

    @max_speed_hz.setter
    def max_speed_hz(self, max_speed_hz):
        self._ioctl(SPI._IOC_WR_MAX_SPEED_HZ, max_speed_hz)

    @property
    def bits_per_word(self):
        """Number of bits per word of SPI transfer.

        A value of 0 is equivalent to 8 bits per word
        """
        return self._ioctl(SPI._IOC_RD_BITS_PER_WORD)

    @bits_per_word.setter
    def bits_per_word(self, bits_per_word):
        self._ioctl(SPI._IOC_WR_BITS_PER_WORD, bits_per_word)

    @property
    def mode(self):
        return self._ioctl(SPI._IOC_RD_MODE)

    @mode.setter
    def mode(self, mode):
        self._ioctl(SPI._IOC_WR_MODE, mode)

    def writebytes(self, data, max_speed_hz=0, bits_per_word=0, delay=0):
        """Perform half-duplex SPI write.

        Args:
            data: List of words to write
            max_speed_hz: Optional temporary bitrate override in Hz. 0 (default)
                uses existing spidev max_speed_hz setting.
            bits_per_word: Optional temporary bits_per_word override. 0
                (default) will use the current bits_per_word setting.
            delay: Optional delay in usecs between sending the last bit and
                deselecting the chip select line. 0 (default) for no delay.
        """
        data = array.array('B', data).tostring()
        #length = len(data)
        chunks = [data[i:i+SPI_CHUNK_SIZE] for i in range(0, len(data), SPI_CHUNK_SIZE)]
        for chunk in chunks:
            length = len(chunk)
            transmit_buffer = create_string_buffer(chunk)
            spi_ioc_transfer = struct.pack(SPI._IOC_TRANSFER_FORMAT,
                                           addressof(transmit_buffer), 0,
                                           length, max_speed_hz, delay,
                                           bits_per_word, 0, 0, 0, 0)
            ioctl(self.handle, SPI._IOC_MESSAGE, spi_ioc_transfer)

    def readbytes(self, length, max_speed_hz=0, bits_per_word=0, delay=0):
        """Perform half-duplex SPI read as a binary string

        Args:
            length: Integer count of words to read
            max_speed_hz: Optional temporary bitrate override in Hz. 0 (default)
                uses existing spidev max_speed_hz setting.
            bits_per_word: Optional temporary bits_per_word override. 0
                (default) will use the current bits_per_word setting.
            delay: Optional delay in usecs between sending the last bit and
                deselecting the chip select line. 0 (default) for no delay.

        Returns:
            List of words read from device
        """
        receive_buffer = create_string_buffer(length)
        spi_ioc_transfer = struct.pack(SPI._IOC_TRANSFER_FORMAT, 0,
                                       addressof(receive_buffer),
                                       length, max_speed_hz, delay, bits_per_word, 0,
                                       0, 0, 0)
        ioctl(self.handle, SPI._IOC_MESSAGE, spi_ioc_transfer)
        return [ord(byte) for byte in string_at(receive_buffer, length)]

    def transfer(self, data, max_speed_hz=0, bits_per_word=0, delay=0):
        """Perform full-duplex SPI transfer

        Args:
            data: List of words to transmit
            max_speed_hz: Optional temporary bitrate override in Hz. 0 (default)
                uses existing spidev max_speed_hz setting.
            bits_per_word: Optional temporary bits_per_word override. 0
                (default) will use the current bits_per_word setting.
            delay: Optional delay in usecs between sending the last bit and
                deselecting the chip select line. 0 (default) for no delay.

        Returns:
            List of words read from SPI bus during transfer
        """
        data = array.array('B', data).tostring()
        length = len(data)
        transmit_buffer = create_string_buffer(data)
        receive_buffer = create_string_buffer(length)
        spi_ioc_transfer = struct.pack(SPI._IOC_TRANSFER_FORMAT,
                                       addressof(transmit_buffer),
                                       addressof(receive_buffer),
                                       length, max_speed_hz, delay, bits_per_word, 0,
                                       0, 0, 0)
        ioctl(self.handle, SPI._IOC_MESSAGE, spi_ioc_transfer)
        return [byte for byte in string_at(receive_buffer, length)]

    def close(self):
        pass
