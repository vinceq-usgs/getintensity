#!/usr/bin/env python

import os.path
import configparser
import numpy as np
import vcr

from getintensity.tools import IntensityParser
import getintensity.emsc as emsc


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
        config.read_file(f)

    return config


def test_emsc_file():
    eventid = 'unknown'
    datadir = get_datadir()
    config = get_config()
    iparser = IntensityParser(eventid=eventid, config=config, network='emsc')

    # Test reading an emsc ZIP file
    testfile = os.path.join(datadir, '20190330_0000065.txt')
    df, msg = iparser.get_dyfi_dataframe_from_file(testfile)
    assert len(df) == 49
    np.testing.assert_almost_equal(df['INTENSITY'].sum(), 151.2, decimal=1)
    np.testing.assert_equal(df['NRESP'].sum(), 227)


def test_emsc_zip():
    # Test output from EMSC testimonials feed

    eventid = 'nc72282711'
    extid = '20140824_0000036'
    datadir = get_datadir()
    config = get_config()

    tape_file1 = os.path.join(datadir, 'vcr_emsc_zip.yaml')

    iparser = IntensityParser(eventid=eventid, config=config, network='emsc')
    with vcr.use_cassette(tape_file1):
        df, msg = iparser.get_dyfi_dataframe_from_network(extid)

    np.testing.assert_almost_equal(df['INTENSITY'].sum(), 221.7, decimal=1)
    np.testing.assert_equal(df['NRESP'].sum(), 426)

    return


def test_emsc_retrieve():
    # Test output from EMSC name server

    eventid = 'nc72282711'
    extid = '20140824_0000036'
    datadir = get_datadir()
    config = get_config()

    tape_file1 = os.path.join(datadir, 'vcr_emsc_eventid.yaml')

    iparser = IntensityParser(eventid=eventid, config=config, network='emsc')
    with vcr.use_cassette(tape_file1):
        extid = emsc.get_extid_from_emsc(iparser, eventid)

    assert extid == '20140824_0000036'

    return
