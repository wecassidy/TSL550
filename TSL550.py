from __future__ import division
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

    # Sweep mode statuses
    SWEEP_OFF = 0
    SWEEP_RUNNING = 1
    SWEEP_PAUSED = 2
    SWEEP_TRIGGER_WAIT = 3
    SWEEP_JUMP = 4

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

    def _set_var(self, name, precision, val):
        """
        Generic function to set a floating-point variable on the
        laser, or return the current value.
        """

        if val is not None:
            command = ("{}{:."+str(precision)+"f}").format(name, val)
        else:
            command = name

        response = self.write(command)
        return float(response)

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

        return self._set_var("WA", 4, val)

    def frequency(self, val=None):
        """
        Tune the laser to a new wavelength. If a value is not
        specified, return the current one. Units: THz.
        """

        return self._set_var("FQ", 5, val)

    def power_mW(self, val=None):
        """
        Set the output optical power in milliwatts. If a value is not
        specified, return the current one.
        """

        return self._set_var("LP", 2, val)

    def power_dBm(self, val=None):
        """
        Set the output optical power in decibel-milliwatts. If a value
        is not specified, return the current one.
        """

        return self._set_var("OP", 2, val)

    def power_auto(self):
        """Turn on automatic power control."""

        self.power_control = "auto"
        self.write("AF")

    def power_manual(self):
        """Turn on manual power control."""

        self.power_control = "manual"
        self.write("AO")

    def sweep_wavelength(self, start, stop, duration, number=1, delay=0
                         continuous=True, step_size=1, twoway=True, trigger=False):

        # Set start and end wavelengths
        self.sweep_start_wavelength(start)
        self.sweep_end_wavelength(stop)

        # Set timing
        self.sweep_delay(delay)
        if continuous: # Calculate speed
            speed = abs(stop - start) / duration

            if twoway: # Need to go twice as fast to go up then down in the same time
                speed *= 2

            self.sweep_speed(speed)
        else: # Calculate time per step
            steps = abs(stop - start) / step_size
            time = duration / steps

            if twoway: # Need to go twice as fast to go up then down in the same time
                time /= 2

            self.sweep_step_time(time)

        self.sweep_set_mode(continuous=continuous, twoway=twoway, trigger=trigger, const_freq_step=False)

        if not self.is_on: # Make sure the laser is on
            self.on()

        self.sweep_start(number)

    def sweep_frequency(self, start, stop, duration, number=1, delay=0
                         continuous=True, step_size=1, twoway=True, trigger=False):

        # Set start and end wavelengths
        self.sweep_start_frequency(start)
        self.sweep_end_frequency(stop)

        # Set timing
        self.sweep_delay(delay)
        if continuous: # Calculate speed
            speed = abs(stop - start) / duration

            if twoway: # Need to go twice as fast to go up then down in the same time
                speed *= 2

            self.sweep_speed(speed)
        else: # Calculate time per step
            steps = abs(stop - start) / step_size
            time = duration / steps

            if twoway: # Need to go twice as fast to go up then down in the same time
                time /= 2

            self.sweep_step_time(time)

        self.sweep_set_mode(continuous=continuous, twoway=twoway, trigger=trigger, const_freq_step=True)

        if not self.is_on: # Make sure the laser is on
            self.on()

        self.sweep_start(number)

    def sweep_start(self, num=1):
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

    def sweep_stop(self, immediate=True):
        """
        Prematurely quit a sweep. If the parameter immediate is True,
        the sweep will stop at once. If the parameter is False and the
        sweep is continuous, the sweep will stop once if finishes the
        current sweep.
        """

        if immediate:
            self.sweep_pause()

        self.write("SQ")

    def sweep_status(self):
        """
        Check on the current condition of the sweeping function. It
        will return one of TSL550.SWEEP_OFF, TSL550.SWEEP_RUNNING,
        TSL550.SWEEP_PAUSED, TSL550.SWEEP_TRIGGER_WAIT,
        TSL550.SWEEP_JUMP. The first three states are
        self-explanatory, but the last two require more detail. If the
        status is TSL550.SWEEP_TRIGGER_WAIT, that means that the sweep
        has been set to start on an external trigger and that trigger
        has not yet been received. If the status is TSL550.SWEEP_JUMP,
        that means that the laser is transitioning between the end of
        one sweep and the start of the next in one-way sweep mode.
        """

        return int(self.write("SK"))

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

    def sweep_speed(self, val=None):
        """
        Set the speed of the continuous sweep, in nm/s. If a new value
        is not provided, the current one will be returned.
        """

        return self._set_var("SN", 1, val)

    def sweep_step_wavelength(self, val=None):
        """
        Set the size of each step in the stepwise sweep. If a new
        value is not provided, the current one will be returned.
        Units: nm
        """

        return self._set_var("WW", 4, val)

    def sweep_step_frequency(self, val=None):
        """
        Set the size of each step in the stepwise sweep when constant
        frequency intervals are enabled. If a new value is not
        provided, the current one will be returned. Units: THz
        """

        return self._set_var("WF", 5, val)

    def sweep_step_time(self, val=None):
        """
        Set the duration of each step in the stepwise sweep. If a new
        value is not provided, the current one will be returned.
        """

        return self._set_var("SB", 1, val)

    def sweep_delay(self, val=None):
        """
        Set the time between consecutive sweeps in continuous mode. If
        a new value is not provided, the current one will be returned. Units: s
        """

        return self._set_var("SA", 1, val)

    def sweep_start_wavelength(self, val=None):
        return self._set_var("SS", 4, val)

    def sweep_start_frequency(self, val=None):
        return self._set_var("FS", 5, val)

    def sweep_end_wavelength(self, val=None):
        return self._set_var("SE", 4, val)

    def sweep_end_frequency(self, val=None):
        return self._set_var("FF", 5, val)
