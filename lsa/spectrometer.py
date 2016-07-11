from ctypes import cdll, c_double, c_long, c_int, c_short, cast, POINTER
from pandas import DataFrame
from os.path import join, exists
from time import sleep

#FOLDERNAME = "C:\Program Files\HighFinesse\Laser Spectrum Analyser - LSA
# 2036\Projects\\64"
FOLDERNAME = "C:\Windows\System32"
WLM_DATA_FILE = "wlmData.dll"
WLM_DATA_PATH = join(FOLDERNAME, WLM_DATA_FILE)
HEADER_FOLDERNAME = "C:\Program Files\HighFinesse\Laser Spectrum Analyser - LSA 2036\Projects\Headers\C"
HEADER_FILE = "wlmData.h"
HEADER_PATH = join(HEADER_FOLDERNAME, HEADER_FILE)
SERVER_PATH = "C:\Program Files\HighFinesse\Laser Spectrum Analyser - LSA 2036\LSA.exe"

DATATYPE_MAP = {2:c_int, 4:c_long, 8:c_double}

class SpectrometerException(Exception):
    pass


class Spectrometer(object):
    def __init__(self):
        self.errors_list = {}
        self.parse_header()
        if exists(WLM_DATA_PATH):
            self.lib = cdll.LoadLibrary(WLM_DATA_PATH)
            control_show = self.lib.ControlWLM(self.cCtrlWLMShow, 0, 0)
            print("control show: ", control_show)
            while not self.lib.Instantiate(self.cInstCheckForWLM):
                pass
            connection = self.lib.Instantiate()
            print("connection: ", connection)
            print("version: ", self.version, self.ErrWlmMissing)
            print("frequency: ", self.frequency)
            print("wavelength: ", self.wavelength)
            print("interval: ", self.interval)
            print("range: ", self.range, self.ranges)
            #control_hide = self.lib.ControlWLMEx(self.cCtrlWLMHide, 0, 0)
            #print("control returns: ", control_hide)
            print("pattern: ", self.spectrum)
            #if connection == 0:
            #    raise IOError("No Spectrometer found!")
        else:
            raise OSError("wlmData.dll not found in "+FOLDERNAME)

    def parse_header(self):
        self.ranges = []
        if exists(HEADER_PATH):
            f_in = open(HEADER_PATH, "r")
            begin_read = False
            for line in f_in.readlines():
                if line.find("Constants") > 0:
                    begin_read = True
                if begin_read:
                    if line.find("const int") > 0:
                        values = line.split("const int")[1].replace(";", "") \
                                     .replace("\t","").replace("\n", "") \
                                     .split("//")[0].split(" = ")
                        try:
                            # first, attempt to parse as int
                            setattr(self, values[0], int(values[1], 0))
                        except ValueError as e:
                            parts = values[1].split(" + ")
                            # if that fails, parse as a value
                            try:
                                value = 0
                                for part in parts:
                                    try:
                                        value += int(part, 0)
                                    except ValueError as interr:
                                        value += getattr(self, part)
                                setattr(self, values[0], value)
                            except Exception as e:
                                print("could not parse values: ", values, e)
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

                        # for the UV2 t l, the ranges to not line up with the values
                        # in the gui.
                        '''
                        if values[0].find("cRange") == 0:
                            lower = int(values[0].split("_")[1])
                            upper = int(values[0].split("_")[2])
                            self.ranges.append((getattr(self, values[0]), (lower,
                                                                           upper)))
                        '''
                        self.ranges = [(0, (190, 260)), (1, (250, 330)), (2, (320, 420))]

    def check_error(self, error_code, error_type='read'):
        """
        Check whether the value matches an error code
        :param error_code: the returned value from the call. Must be a float or int.
        :return: nothing
        """
        error_code = int(error_code)
        for error in self.errors_list[error_type]:
            if error_code == getattr(self, error):
                raise SpectrometerException(error)

    @property
    def active(self):
        return self.lib.GetOperationState(0)

    @active.setter
    def active(self, new_val):
        if new_val:
            response = self.lib.Operation(self.cCtrlStartMeasurement)
        else:
            response = self.lib.Operation(self.cCtrlStopAll)
        print(response)

    @property
    def frequency(self):
        if not self.active:
            self.active = True
        sleep(0.5)
        get_frequency = self.lib.GetFrequency
        get_frequency.restype = c_double
        frequency = get_frequency(0)
        self.check_error(frequency)
        return frequency

    @property
    def interval(self):
        return self.lib.GetInterval(0)

    @property
    def range(self):
        # unfortunately, these values do not appear to match up with the GUI
        range = self.lib.GetRange(0)
        for compare_range in self.ranges:
            if compare_range[0] == range:
                return compare_range
        return ("range not found: ", range)

    @range.setter
    def range(self, new_val):
        return self.lib.SetRange(new_val)

    @property
    def wavelength(self):
        if not self.active:
            self.active = True
        sleep(0.5)
        get_wavelength = self.lib.GetWavelength
        get_wavelength.restype = c_double
        wavelength = get_wavelength(0)
        # check for errors
        self.check_error(wavelength)
        return wavelength

    @property
    def temperature(self):
        get_temperature = self.lib.GetTemperature
        get_temperature.restype = c_double
        return get_temperature(0)


    @property
    def spectrum(self):
        setter = self.lib.SetAnalysisMode
        setter.restype = c_long
        set_mode_success = setter(True)
        self.check_error(set_mode_success, 'set')
        setter = self.lib.SetAnalysis
        setter.restype = c_long
        setter_success = setter(self.cSignalAnalysis, self.cAnalysisEnable)
        self.check_error(setter_success, 'set')
        setter = self.lib.SetWideMode
        setter.restype = c_short
        # set the LSA in 'precise' mode, this may vary between spectrometers
        setter_success = setter(1)
        self.check_error(setter_success, 'set')

        results = {}
        parts = [{'wavelength':'X', 'intensity':'Y'},
                 {'size':'ItemSize', 'count':'ItemCount', 'address':''}]
        for axis in parts[0]:
            results[axis] = {}
            for value in parts[1]:
                getter = getattr(self.lib, 'GetAnalysis'+parts[1][value])
                getter.restype = c_long
                component_arg = getattr(self, 'cSignalAnalysis'+parts[0][axis])
                results[axis][value] = getter(component_arg)

        # parse values into a dataframe
        spectrum = []
        memory_values = {}
        for axis in parts[0]:
            access_size = DATATYPE_MAP[results[axis]['size']]*results[axis]['count']
            memory_values[axis] = cast(results[axis]['address'],
                                       POINTER(access_size))
        for i in range(0, results['wavelength']['count']):
            spectrum.append({'wavelength': memory_values['wavelength'].contents[i],
                             'intensity': memory_values['intensity'].contents[i]})
        spectrum = DataFrame(spectrum)
        return spectrum

    @property
    def version(self):
        wm_type = self.lib.GetWLMVersion(0)
        version_num = self.lib.GetWLMVersion(1)
        revision_num = self.lib.GetWLMVersion(2)
        compile_num = self.lib.GetWLMVersion(3)
        return (wm_type, version_num, revision_num, compile_num)

    @property
    def linewidth(self):
        get_linewidth = self.lib.GetLinewidth
        get_linewidth.restype = c_double
        wavelength_vac = get_linewidth(self.cReturnWavelengthVac)
        wavelength_air = get_linewidth(self.cReturnWavelengthAir)
        frequency = get_linewidth(self.cReturnFrequency)
        wavenumber = get_linewidth(self.cReturnWavenumber)
        photon_energy = get_linewidth(self.cReturnPhotonEnergy)
        return(wavelength_vac, wavelength_air, frequency, wavenumber, photon_energy)

    @property
    def amplitude(self):
        get_amplitude_num = self.lib.GetAmplitudeNum
        get_amplitude_num.restype = c_long
        amplitudes = {}
        parts = ['Min', 'Max', 'Avg']
        for i in range(1, self.num_channels+1):
            amplitudes[i] = {}
            for part in parts:
                amplitudes[i][part] = get_amplitude_num(i, getattr(self,'c'+part+str(i)))
        return amplitudes

    @property
    def num_channels(self):
        return 2




if __name__ == "__main__":
    spectrometer = Spectrometer()
    while True:
        print(spectrometer.wavelength, spectrometer.temperature, spectrometer.spectrum)
        sleep(1)

