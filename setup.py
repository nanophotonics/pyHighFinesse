#!/usr/bin/env python

from setuptools import setup, find_packages


setup(name='pyHighFinesse',
      version='0.1',
      description='A python interface to High Finesse Wavelength Meters and '
                  'Spectrometers',
      author='Catherine Holloway',
      author_email='milankie@gmail.com',
      url='https://github.com/CatherineH/pyHighFinesse',
      zip_safe=False,
      install_requirements=['pandas'],
      packages=find_packages()
      )