#!/usr/bin/env python

import os.path
import configparser
import numpy as np

from getintensity.tools import IntensityParser


def get_datadir():
    # this returns the test data directory

    homedir = os.path.dirname(os.path.abspath(__file__))
    datadir = os.path.join(homedir, 'data')
    return datadir


def get_config():

    homedir = os.path.dirname(os.path.abspath(__file__))
    configfile = os.path.join(homedir, '..', 'config.ini')
    config = configparser.ConfigParser()

    with open(configfile, 'r') as f:
        config = config.read_file(f)

    return config


def test_ga_file():
    eventid = 'unknown'
    datadir = get_datadir()
    config = get_config()
    iparser = IntensityParser(eventid=eventid, config=config, network='ga')

    # Test reading a dyfi format file
    testfile = os.path.join(datadir, 'felt_reports_1km_filtered.geojson')
    df, msg = iparser.get_dyfi_dataframe_from_file(testfile)
    assert len(df) == 126
    np.testing.assert_almost_equal(df['INTENSITY'].sum(), 471.3)
    np.testing.assert_equal(df['NRESP'].sum(), 1316)

    # Test reading a dyfi format file
    testfile = os.path.join(datadir, 'felt_reports_10km_filtered.geojson')
    df, msg = iparser.get_dyfi_dataframe_from_file(testfile)
    assert len(df) == 62
    np.testing.assert_equal(df['INTENSITY'].sum(), 201.3)
    np.testing.assert_equal(df['NRESP'].sum(), 1525)

    return


def test_ga_retrieve():

    return
