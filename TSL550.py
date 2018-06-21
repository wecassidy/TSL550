import sys

import serial

class TSL550:
    # continuous, two-way, external trigger, constant frequency interval
    SWEEP_MODE_MAP = {
        (True, False, False, False): 1,
        (True, True, False, False): 2,
        (False, False, False, False): 3,
        (False, True, False, False): 4,
        (False, False, False, True): 5,
        (False, True, False, True): 6,
        (True, False, True, False): 7,
        (True, True, True, False): 8,
        (False, False, True, False): 9,
        (False, True, True, False): 10,
        (False, False, True, True): 11,
        (False, True, True, True): 12
    }
    SWEEP_MODE_MAP_REV = {num: settings for settings, num in SWEEP_MODE_MAP.items()}

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
        self.is_on = False
        self.off()

        # Set power management to auto
        self.power_control = "auto"
        self.power_auto()

        # Set sweep mode to continuous, two-way, trigger off
        self.sweep_set_mode()

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
            command = "FQ{:.5f}".format(val) # Put the value rounded to 4 decimal places
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

    def sweep(self, num=1):
        """
        Sweep between two wavelengths one or more times. Set the start
        and end wavelengths with
        sweep_(start|end)_(wavelength|frequency), and the sweep
        operation mode with sweep_set_mode.
        """

        self.write("SZ{:d}".format(num)) # Set number of sweeps
        self.write("SG") # Start sweeping

    def sweep_pause(self):
        """
        Pause the sweep. Use sweep_resume to resume.
        """

        self.write("SP")

    def sweep_resume(self):
        """
        Resume a paused sweep.
        """

        self.write("SR")

    def sweep_set_mode(self, continuous=True, twoway=True, trigger=False, const_freq_step=False):
        r"""
        Set the mode of the sweep. Options:

        - Continuous or stepwise:
                /        _|
               /  vs   _|
              /      _|
        - Two-way:
                /\        /   /
               /  \  vs  /   /
              /    \    /   /
        - Constant frequency interval (requires stepwise mode)
        - Start from external trigger
        """

        try:
            mode = TSL550.SWEEP_MODE_MAP[(continuous, twoway, trigger, const_freq_step)]
        except KeyError:
            raise AttributeError("Invalid sweep configuration.")

        self.write("SM{}".format(mode))

    def sweep_get_mode(self):
        """
        Return the current sweep configuration as a dictionary. See
        sweep_set_mode for what the parameters mean.
        """

        mode_num = int(self.write("SM"))
        mode_settings = TSL550.SWEEP_MODE_MAP_REV[mode_num]

        return {
            "continuous": mode_settings[0],
            "twoway": mode_settings[1],
            "trigger": mode_settings[2],
            "const_freq_step": mode_settings[3]
        }

    def sweep_start_wavelength(self, val=None):
        if val is not None:
            command = "SS{:.4f}".format(val)
        else:
            command = "SS"

        response = self.write(command)
        return float(response)

    def sweep_start_frequency(self, val=None):
        if val is not None:
            command = "FS{:.5f}".format(val)
        else:
            command = "FS"

        response = self.write(command)
        return float(response)

    def sweep_end_wavelength(self, val=None):
        if val is not None:
            command = "SE{:.4f}".format(val)
        else:
            command = "SE"

        response = self.write(command)
        return float(response)

    def sweep_end_frequency(self, val=None):
        if val is not None:
            command = "FF{:.5f}".format(val)
        else:
            command = "FF"

        response = self.write(command)
        return float(response)
