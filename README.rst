pyHighFinesse
-------------

.. image:: https://raw.githubusercontent.com/CatherineH/pyHighFinesse/master/example/matplotlib_graph.png
    :align: center
    :alt: spectrum data plotted in Matplotlib

Python interface to `High Finesse`_ devices. These interfaces work by importing the static libraries provided by High Finesse.

.. _High Finesse: http://www.highfinesse.com 

Installation (Windows only)
===========================

First, install the WLM drivers and LSA software on your computer. These can be obtained from High Finesse.

Then, clone and install this repository

.. code:: bash

  git clone https://github.com/CatherineH/pyHighFinesse
  cd pyHighFinesse
  python setup.py install
