from ctypes import cdll
from os.path import join, exists

FOLDERNAME = "C:\Program Files\HighFinesse\Laser Spectrum Analyser - LSA 2036\Projects\\64"
WLM_DATA_FILE = "wlmData.dll"
WLM_DATA_PATH = join(FOLDERNAME, WLM_DATA_FILE)


class Spectrometer(object):
    def __init__(self):
        if exists(WLM_DATA_PATH):
            print(WLM_DATA_PATH)
            self.lib = cdll.LoadLibrary(WLM_DATA_PATH)
            connection = self.lib.Instantiate()
            if connection == 0:
                raise IOError("No Spectrometer found!")
        else:
            raise OSError("wlmData.dll not found in "+FOLDERNAME)

    @property
    def frequency(self):
        return self.lib.GetFrequency()

    @property
    def version(self):
        return self.lib.GetWLMVersion()

if __name__ == "__main__":
    spectrometer = Spectrometer()
    print(spectrometer.frequency)
    print(spectrometer.version)

