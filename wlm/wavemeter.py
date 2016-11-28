"""
A module for interacting with Angstrom/High Finesse wavemeters, via the wlm driver and lsa server.

Written by Ana Andres-Arroyo (aa938@cam.ac.uk), adapted from pyHighFinesse
"""

from ctypes import cdll, c_double, c_long, c_int, c_short, cast, POINTER
from os.path import join, exists
from time import sleep
from pandas import DataFrame


SYSTEM_FOLDERNAME = "C:\\Program Files (x86)\\HighFinesse\\Wavelength Meter WS6 3194\\Projects\\64"
WLM_DATA_FILE = "wlmData.dll"
WLM_DATA_PATH = join(SYSTEM_FOLDERNAME, WLM_DATA_FILE)
LSA_FOLDERNAME = "C:\\Program Files (x86)\\HighFinesse\Wavelength Meter WS6 3194"
HEADER_PATH = join(LSA_FOLDERNAME, "Projects\\Headers\\C", "wlmData.h")
SERVER_PATH = join(LSA_FOLDERNAME, "wlm_ws6.exe")
DATATYPE_MAP = {2: c_int, 4: c_long, 8: c_double}


class WavemeterException(Exception):
    """
    An Exception for repeating WLM errors
    """
    pass


class Wavemeter(object):
    """
    A class for interacting with HighFinesse/Angstrom devices through the wlm driver
    and lsa server.
    """
    def __init__(self, verbosity=True):
        print("\nAttempting to connect to the HighFinesse wavemeter...\n")
        
        self.verbosity = verbosity
        self.errors_list = {}
        self.wavelength_ranges = []
        self.parse_header()
        if exists(WLM_DATA_PATH):
            self.lib = cdll.LoadLibrary(WLM_DATA_PATH)
            control_show = self.lib.ControlWLM(getattr(self, 'cCtrlWLMShow'), 0, 0)
            self.check_error(control_show, 'set')
            while not self.lib.Instantiate(getattr(self, 'cInstCheckForWLM')):
                pass
            connection = self.lib.Instantiate()
            self.check_error(connection, 'set')
        else:
            raise OSError("wlmData.dll not found in "+SYSTEM_FOLDERNAME)

    def check_error(self, error_code, error_type='read'):
        """
        Check whether the value matches an error code
        :param error_code: the returned value from the call. Must be a float or int.
        :return: nothing
        """
        error_code = int(error_code)
        for error in self.errors_list[error_type]:
            if error_code == getattr(self, error):
                raise WavemeterException(error)


    def parse_header(self):
        """
        Parse the values in the wlmData.h C header.
        :return: Nothing, values are added as attributes to the Wavemeter object
        """
        self.ranges = []
        if not exists(HEADER_PATH):
            raise OSError('Header file not found at '+HEADER_PATH)
        f_in = open(HEADER_PATH, "r")
        begin_read = False
        for line in f_in.readlines():
            if line.find("Constants") > 0:
                begin_read = True
            if begin_read and line.find("const int") > 0:
                values = line.split("const int")[1].replace(";", "") \
                             .replace("\t", "").replace("\n", "") \
                             .split("//")[0].split(" = ")
                try:
                    # first, attempt to parse as int
                    setattr(self, values[0], int(values[1], 0))
                except ValueError:
                    parts = values[1].split(" + ")
                    # if that fails, parse as a value
                    value = 0
                    for part in parts:
                        try:
                            value += int(part, 0)
                        except ValueError:
                            value += getattr(self, part)
                    setattr(self, values[0], value)
                if values[0].find("Err") == 0:
                    if 'read' not in self.errors_list.keys():
                        self.errors_list['read'] = []
                    self.errors_list['read'].append(values[0])
                if values[0].find("ResERR") == 0:
                    if 'set' not in self.errors_list.keys():
                        self.errors_list['set'] = []
                    # no not append the "NoErr" Error
                    if getattr(self, values[0]) != 0:
                        self.errors_list['set'].append(values[0])

        # for the UV2 t l, the cRange values do not correspond to
        # values from the lsa, and are therefore ignored.
        self.wavelength_ranges = [(0, (190, 260)), (1, (250, 330)),
                                  (2, (320, 420))]


    @property
    def active(self):
        """
        Is there an active measurement in the Wavemeter?
        :return: 0 if no measurement active, 1, if a measurement is active
        :rtype: int
        """
        getter = self.lib.GetOperationState
        getter.restype = c_long
        result = getter(0)
        if self.verbosity:
            if result:
                print 'Measurement is active \n'
            else:
                print 'Measurement is NOT active \n'
        return int(result)

    @active.setter
    def active(self, new_val):
        """
        Start or stop the active measurement
        :param new_val: the command to start or stop
        :type new_val: boolean or int
        """
        states = {0: 'StopAll', 1: 'StartMeasurement'}
        setter = self.lib.Operation
        setter.restype = c_long
        response = setter(getattr(self, 'cCtrl'+states[new_val]))
        if self.verbosity:
            print states[new_val] + '\n'   
        self.check_error(response, error_type='set')
        
    @property
    def temperature(self):
        """
        The current operating temperature of the wavemeter
        :return: temperature, in degrees C
        :rtype: float
        """
        get_temperature = self.lib.GetTemperature
        get_temperature.restype = c_double
        temperature = get_temperature(0)
        self.check_error(temperature, error_type='read')
        if self.verbosity:
            print 'T (C) = ' + str(temperature) + '\n'
        return float(temperature)
        
    @property
    def version(self):
        """
        Get the versioning information about the wavelength meter
        :return: a list, containing the wavelength meter type, version number,
        revision number, and compile number
        :rtype: list
        """
        getter = self.lib.GetWLMVersion
        getter.restype = c_long
        param = []
        param.append('Wavelength Meter Type')
        param.append('Version Number')
        param.append('Revision Number')
        param.append('Compile Number')
        values = []
        
        if self.verbosity:
            print 'Version: '
            for i in range(0, 4):
                part = getter(i)
                self.check_error(part, error_type='read')
                values.append(part)
                print param[i] + ': ' + str(values[i])
            print '\n'
#        return param, values
        return values
        
    @property
    def wavelength(self):
        """
        Get the current wavelength
        :return: wavelength, in nm
        :rtype: float
        """
        get_wavelength = self.lib.GetWavelength
        get_wavelength.restype = c_double
        wavelength = get_wavelength(0)
        self.check_error(wavelength, error_type='read')
        if self.verbosity:
            print 'Wavelength (nm) = ' + str(wavelength) + '\n'
#            print 'wlm wavelength (nm): ' + str(wavelength) + '\n'
        return float(wavelength)


if __name__ == "__main__":
    print(__doc__)
    wlm = Wavemeter()
    wlm.version
    wlm.temperature
       
    wlm.active
    wlm.active = 1
    wlm.active
    wlm.wavelength
    wlm.active = 0
    wlm.active