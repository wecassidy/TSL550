import sys

import serial

class TSL550:
    def __init__(self, address, baudrate=9600, terminator="\r"):
        """
        Connect to the TSL550. Address is the serial port, baudrate
        can be set on the device, terminator is the string the marks
        the end of the command.
        """

        self.device = serial.Serial(address, baudrate=baudrate, timeout=1)
        self.terminator = terminator

        # Make sure the laser is off
        self.off()

    def write(self, command):
        """
        Write a command to the TSL550. Returns the response (if any).
        """

        # Add the terminator
        command = command + self.terminator

        # Convert to bytes (Python 3 compatibility)
        if sys.version_info.major >= 3:
            command = command.encode("ASCII")

        # Write the command
        self.device.write(command)

        # Read response
        response = self.device.readlines()

        return response

    def on(self):
        """Turn on the laser diode"""

        self.on = True
        self.write("LO")

    def off(self):
        """Turn off the laser diode"""

        self.on = False
        self.write("LF")
