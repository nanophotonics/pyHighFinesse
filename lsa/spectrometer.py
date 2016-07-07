import ctypes
from os.path import join

# Load DLL into memory.
foldername = "C:\\Program Files\\HighFinesse\\Laser Spectrum Analyser - LSA " \
             "2036\\Projects\\Headers\\C"
wlm_data_file = join(foldername, "wlmData.lib")
print(wlm_data_file)
hllDll = ctypes.CDLL(wlm_data_file)
