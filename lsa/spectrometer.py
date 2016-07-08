from ctypes import cdll, c_double, byref, addressof
from os.path import join, exists
from subprocess import Popen, PIPE
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


class Spectrometer(object):
    def __init__(self):
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
        return get_frequency(0)

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
        return wavelength

    @property
    def temperature(self):
        get_temperature = self.lib.GetTemperature
        get_temperature.restype = c_double
        return get_temperature(0)


    @property
    def spectrum(self):
        size_x = self.lib.GetAnalysisItemSize(self.cSignalAnalysisX)
        count_x = self.lib.GetAnalysisItemCount(self.cSignalAnalysis)
        address_x = self.lib.GetAnalysis(self.cSignalAnalysisX)
        size_y = self.lib.GetAnalysisItemSize(self.cSignalAnalysisY)
        count_y = self.lib.GetAnalysisItemCount(self.cSignalAnalysis)
        address_y = self.lib.GetAnalysis(self.cSignalAnalysisY)
        return (size_x, count_x, address_x, size_y, count_y, address_y)

    @property
    def version(self):
        wm_type = self.lib.GetWLMVersion(0)
        version_num = self.lib.GetWLMVersion(1)
        revision_num = self.lib.GetWLMVersion(2)
        compile_num = self.lib.GetWLMVersion(3)
        return (wm_type, version_num, revision_num, compile_num)

if __name__ == "__main__":
    spectrometer = Spectrometer()
    while True:
        print(spectrometer.wavelength, type(spectrometer.wavelength), spectrometer.temperature)
        sleep(1)

