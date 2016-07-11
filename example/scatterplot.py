from lsa import spectrometer
import matplotlib.pyplot as plt

reading = spectrometer.Spectrometer()

spectrumdata = reading.spectrum
spectrum = spectrumdata.set_index('wavelength')
_ax = spectrum.plot()
_ax.legend_.remove()
_ax.set_title('LSA Analysis output')
_ax.set_xlabel("Wavelength (nm)")
_ax.set_ylabel("Intensity")
plt.show()
