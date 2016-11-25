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


#class LinewidthMeasurement(object):
#    """
#    An empty object to populate with Linewidth Measurement values. See
#    Wavemeter.linewidth
#    """
#    def __init__(self):
#        self.air_wavelength = None
#        self.vacuum_wavelength = None
#        self.frequency = None
#        self.photon_energy = None
#        self.wavenumber = None


class Wavemeter(object):
    """
    A class for interacting with HighFinesse/Angstrom devices through the wlm driver
    and lsa server.
    """
    def __init__(self):
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
        if result:
            print '\nMeasurement is active'
        else:
            print '\nMeasurement is NOT active'
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
#        response = setter(getattr(self, 'cCtrl'+states[new_val]))
        print states[new_val]        
        response = setter('cCtrl'+states[new_val])
        self.check_error(response, error_type='set')

#    @property
#    def frequency(self):
#        """
#        Query the frequency of the light with the largest amplitude after grating
#        analysis.
#        :return: frequency (Hz)
#        :rtype: float
#        """
#        if not self.active:
#            self.active = True
#        sleep(0.5)
#        get_frequency = self.lib.GetFrequency
#        get_frequency.restype = c_double
#        frequency = get_frequency(0)
#        self.check_error(frequency, error_type='read')
#        return float(frequency.value)

#    @property
#    def interval(self):
#        """
#        Get the current time interval between measurements, in ms.
#        :return: the time interval, in ms
#        :rtype: int
#        """
#        getter = self.lib.GetInterval
#        getter.restype = c_long
#        interval = getter(0)
#        self.check_error(interval, error_type='read')
#        return int(interval.value)

#    @interval.setter
#    def interval(self, new_val):
#        """
#        Set the time interval between measurements
#        :param new_val: the time interval, in milliseconds
#        :type new_val: int
#        """
#        setter = self.lib.SetInterval
#        setter.restype = c_long
#        response = setter(new_val)
#        self.check_error(response, error_type='set')

#    @property
#    def wavelength_range(self):
#        """
#        Get the current wavelength range of analysis
#        :return: a tuple with minimum and maximum wavelength ranges, in nm
#        :rtype: tuple
#        """
#        getter = self.lib.GetRange
#        getter.restype = c_long
#        _wavelength_range = getter(0)
#        self.check_error(_wavelength_range, error_type='read')
#        for compare_range in self.ranges:
#            if compare_range[0] == _wavelength_range:
#                return compare_range
#        return "range not found: ", _wavelength_range

#    @wavelength_range.setter
#    def wavelength_range(self, new_val):
#        """
#        Set the current wavelength range of analysis
#        :param new_val: an int between 0-3, depending on the spectrometer
#        :type new_val: int
#        """
#        error = self.lib.SetRange(new_val)
#        self.check_error(error, error_type='set')


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
        print '\nWavelength (nm) = ' + str(wavelength)
        return float(wavelength)
        

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
        print '\nT (C) = ' + str(temperature)
        return float(temperature)

#    @property
#    def spectrum(self, wide_mode=1):
#        """
#        A dataframe with the current spectrum with analysis
#        :param wide_mode: specify either a small selection (0) or the full range (1).
#        This may vary between instruments
#        :type wide_mode: int
#        :return: A dataframe with the spectrum, with wavelength in nm, and intensity (
#        frac)
#        :rtype: pandas.DataFrame
#        """
#        setter = self.lib.SetAnalysisMode
#        setter.restype = c_long
#        setter_success = setter(True)
#        self.check_error(setter_success, 'set')
#        setter = self.lib.SetAnalysis
#        setter.restype = c_long
#        setter_success = setter(getattr(self, 'cSignalAnalysis'),
#                                getattr(self, 'cAnalysisEnable'))
#        self.check_error(setter_success, 'set')
#        setter = self.lib.SetWideMode
#        setter.restype = c_short
#        # set the LSA in 'precise' mode, this may vary between wavemeters
#        setter_success = setter(wide_mode)
#        self.check_error(setter_success, 'set')
#
#        results = {}
#        parts = [{'wavelength': 'X', 'intensity': 'Y'},
#                 {'size': 'ItemSize', 'count': 'ItemCount', 'address': ''}]
#        for axis in parts[0]:
#            results[axis] = {}
#            for value in parts[1]:
#                getter = getattr(self.lib, 'GetAnalysis'+parts[1][value])
#                getter.restype = c_long
#                component_arg = getattr(self, 'cSignalAnalysis'+parts[0][axis])
#                results[axis][value] = getter(component_arg)
#
#        # parse values into a dataframe
#        spectrum_list = []
#        memory_values = {}
#        for axis in parts[0]:
#            access_size = DATATYPE_MAP[results[axis]['size']]*results[axis]['count']
#            memory_values[axis] = cast(results[axis]['address'],
#                                       POINTER(access_size))
#        for i in range(0, results['wavelength']['count']):
#            spectrum_list.append({'wavelength': memory_values['wavelength'].contents[i],
#                                  'intensity': memory_values['intensity'].contents[i]})
#        spectrum = DataFrame(spectrum_list)
#        return spectrum

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
        
        print '\nVersion: '
        for i in range(0, 4):
            part = getter(i)
            self.check_error(part, error_type='read')
            values.append(part)
            print param[i] + ': ' + str(values[i])
#        return param, values
        return values

#    @property
#    def linewidth(self):
#        """
#        Get the results of the linewidth measurement
#        :return: a LinewidthMeasurement object, containing the vacuum wavelength in
#        nm, the air wavelength in nm, the frequency in Hz, the wave number, the photon
#        energy in eV
#        :rtype: LinewidthMeasurement
#        """
#        get_linewidth = self.lib.GetLinewidth
#        get_linewidth.restype = c_double
#        _linewidth_measurement = LinewidthMeasurement()
#        linewidth_measurements = {'vacuum_wavelength': 'WavelengthVac',
#                                  'air_wavelength': 'WavelengthAir',
#                                  'frequency': 'Frequency', 'wavenumber': 'Wavenumber',
#                                  'photon_energy': 'PhotonEnergy'}
#        for measurement in linewidth_measurements:
#            param = getattr(self, 'cReturn'+linewidth_measurements[measurement])
#            self.check_error(param, error_type='read')
#            param = float(param.value)
#            setattr(_linewidth_measurement, measurement, param)
#        return _linewidth_measurement

    @property
    def amplitude(self):
        """
        Get the amplitudes off of the two gratings, as the minimum, maximum and average
        :return: a list of dicts, with Min, Max and Avg
        :rtype: list of dicts
        """
        get_amplitude_num = self.lib.GetAmplitudeNum
        get_amplitude_num.restype = c_long
        amplitudes = {}
        parts = ['Min', 'Max', 'Avg']
        for i in range(1, self.num_channels+1):
            amplitudes[i] = {}
            for part in parts:
                amplitudes[i][part] = get_amplitude_num(i, getattr(self, 'c'+part+str(
                    i)))
        return amplitudes

    @property
    def num_channels(self):
        """
        The number of available wavemeter channels. This number varies between
        instruments.
        :return: the number of available channels
        :rtype: int
        """
        return 2

if __name__ == "__main__":
    print(__doc__)
    wlm = Wavemeter()
    wlm.version
    wlm.temperature
    
#    wlm.active
#    wlm.active_setter(1)    
#    wlm.active
#    wlm.wavelength
#    wlm.active_setter(0)
#    wlm.active
    
    wlm.active
    wlm.active(1)    
    wlm.active
    wlm.wavelength
    wlm.active(0)
    wlm.active