from ez_setup import use_setuptools
use_setuptools()
from setuptools import setup, find_packages

classifiers = ['Development Status :: 4 - Beta',
               'Operating System :: POSIX :: Linux',
               'License :: OSI Approved :: MIT License',
               'Intended Audience :: Developers',
               'Programming Language :: Python :: 2.7',
               'Programming Language :: Python :: 3',
               'Topic :: Software Development',
               'Topic :: System :: Hardware']

setup(name              = 'Adafruit_PureIO',
      version           = '0.0.1',
      author            = 'Tony DiCola',
      author_email      = 'tdicola@adafruit.com',
      description       = 'Pure python (i.e. no native extensions) access to Linux IO including I2C and SPI.  Drop in replacement for smbus and spidev modules.',
      license           = 'MIT',
      classifiers       = classifiers,
      packages          = find_packages())
