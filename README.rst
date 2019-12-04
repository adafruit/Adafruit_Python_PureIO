Introduction
============

Pure python (i.e. no native extensions) access to Linux IO including I2C and SPI.  
Drop in replacement for smbus and spidev modules.

Installation
============

On supported GNU/Linux systems like the Raspberry Pi, you can install the driver locally `from
PyPI <https://pypi.org/project/adafruit-circuitpython-motorkit/>`_. To install for current user:

.. code-block:: shell

    pip3 install Adafruit-PureIO

To install system-wide (this may be required in some cases):

.. code-block:: shell

    sudo pip3 install Adafruit-PureIO

To install in a virtual environment in your current project:

.. code-block:: shell

    mkdir project-name && cd project-name
    python3 -m venv .env
    source .env/bin/activate
    pip3 install Adafruit-PureIO
