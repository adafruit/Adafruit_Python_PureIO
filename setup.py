"""A setuptools based setup module.

See:
https://packaging.python.org/en/latest/distributing.html
https://github.com/pypa/sampleproject
"""

from setuptools import setup

# To use a consistent encoding
from codecs import open
from os import path

here = path.abspath(path.dirname(__file__))

# Import the README and use it as the long-description.
# Note: this will only work if 'README.md' is present in your MANIFEST.in file!
with open(path.join(here, "README.rst"), encoding="utf-8") as f:
    long_description = "\n" + f.read()

setup(
    name="Adafruit_PureIO",
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    description="Pure python (i.e. no native extensions) access to Linux IO    including I2C and SPI. Drop in replacement for smbus and spidev modules.",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    # The project's main homepage.
    url="https://github.com/adafruit/Adafruit_Python_PureIO",
    # Author details
    author="Adafruit Industries",
    author_email="circuitpython@adafruit.com",
    python_requires=">=3.5.0",
    # If your package is a single module, use this instead of 'packages':
    install_requires=[],
    license="MIT",
    # Full list: https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries",
        "Topic :: System :: Hardware",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.4",
        "Programming Language :: Python :: 3.5",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    keywords="adafruit blinka micropython pureio ioctl spi i2c python",
    packages=["Adafruit_PureIO"],
)
