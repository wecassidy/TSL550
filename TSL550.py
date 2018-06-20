import sys

import serial

class TSL550:
    def __init__(self, address, baudrate=9600, terminator="\r"):
        """
        Connect to the TSL550. Address is the serial port, baudrate
        can be set on the device, terminator is the string the marks
        the end of the command.
        """

        self.device = serial.Serial(address, baudrate=baudrate, timeout=0)

        if sys.version_info.major >= 3: # Python 3 compatibility: convert to bytes
            terminator = terminator.encode("ASCII")
        self.terminator = terminator

        # Make sure the laser is off
        self.off()

        # Set power management to auto
        self.power_auto()

    def write(self, command):
        """
        Write a command to the TSL550. Returns the response (if any).
        """

        # Convert to bytes (Python 3 compatibility)
        if sys.version_info.major >= 3:
            command = command.encode("ASCII")

        # Write the command
        self.device.write(command + self.terminator)

        # Read response
        response = ""
        in_byte = self.device.read()
        while in_byte != self.terminator:
            if sys.version_info.major >= 3:
                response += in_byte.decode("ASCII")
            else:
                response += in_byte

            in_byte = self.device.read()

        return response

    def on(self):
        """Turn on the laser diode"""

        self.is_on = True
        self.write("LO")

    def off(self):
        """Turn off the laser diode"""

        self.is_on = False
        self.write("LF")

    def wavelength(self, val=None):
        """
        Tune the laser to a new wavelength. If a value is not
        specified, return the current one. Units: nm.
        """

        if val is not None:
            command = "WA{:.4f}".format(val) # Put the value rounded to 4 decimal places
        else:
            command = "WA"

        response = self.write(command)
        return float(response)

    def frequency(self, val=None):
        """
        Tune the laser to a new wavelength. If a value is not
        specified, return the current one. Units: THz.
        """

        if val is not None:
            command = "FQ{:.4f}".format(val) # Put the value rounded to 4 decimal places
        else:
            command = "FQ"

        response = self.write(command)
        return float(response)

    def power_mW(self, val=None):
        """
        Set the output optical power in milliwatts. If a value is not
        specified, return the current one.
        """

        if val is not None:
            command = "LP{:.2f}".format(val)
        else:
            command = "LP"

        response = self.write(command)
        return float(response)

    def power_dBm(self, val=None):
        """
        Set the output optical power in decibel-milliwatts. If a value
        is not specified, return the current one.
        """

        if val is not None:
            command = "OP{:.2f}".format(val)
        else:
            command = "OP"

        response = self.write(command)
        return float(response)

    def power_auto(self):
        """Turn on automatic power control."""

        self.power_control = "auto"
        self.write("AF")

    def power_manual(self):
        """Turn on manual power control."""

        self.power_control = "manual"
        self.write("AO")
