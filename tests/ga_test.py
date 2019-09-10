#!/usr/bin/env python

import tempfile
import os.path
import vcr
import configparser
import numpy as np
from shutil import rmtree
import warnings

from getintensity.tools import IntensityParser
import getintensity.ga as ga


def get_datadir():
    # this returns the test data directory

    homedir = os.path.dirname(os.path.abspath(__file__))
    datadir = os.path.join(homedir, 'data')
    return datadir


def get_config():

    homedir = os.path.dirname(os.path.abspath(__file__))
    configfile = os.path.join(homedir, '..', 'config.ini')
    config = configparser.ConfigParser()

    with open(configfile,'r') as f:
        config = config.read_file(f)

    return config


def test_ga_file():
    eventid = 'unknown'
    datadir = get_datadir()
    config = get_config()

    # Test reading a comcat file
    iparser = IntensityParser(eventid=eventid, config=config)
    testfile = os.path.join(datadir, 'felt_reports_1km.geojson')
    df, msg, network = iparser.get_dyfi_dataframe_from_file(testfile)

    assert len(df) == 113
    assert df['SOURCE'][0] == 'Geoscience Australia (Felt report)'
    np.testing.assert_almost_equal(df['INTENSITY'].sum(), 427.9)
    np.testing.assert_equal(df['NRESP'].sum(), 1146)


def test_ga_retrieve():


    return
