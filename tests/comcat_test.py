#!/usr/bin/env python

import tempfile
import os.path
import vcr
import numpy as np
from shutil import rmtree

import getintensity.tools as gi
import getintensity.comcat as comcat

from libcomcat.search import get_event_by_id
from impactutils.io.table import dataframe_to_xml


def get_datadir():
    # where is this script?
    homedir = os.path.dirname(os.path.abspath(__file__))
    datadir = os.path.join(homedir, 'data')
    return datadir


def test_comcat_data():
    # test extraction from comcat event data. The VCR files are
    # example Comcat event datastreams.

    datadir = get_datadir()

    # This event has both geo_1km and geo_10km
    eventid = 'ci14607652'
    tape_file1 = os.path.join(datadir, 'vcr_comcat_geojson.yaml')

    with vcr.use_cassette(tape_file1):
        detail = get_event_by_id(eventid)
        df, msg = comcat.get_dyfi_dataframe_from_comcat(detail)
        df = gi.postprocess(df, 'neic')

    np.testing.assert_almost_equal(df['INTENSITY'].sum(), 4510.1)

    reference = 'USGS Did You Feel It? System'
    tempdir = tempfile.mkdtemp(prefix='tmp.', dir=datadir)
    outfile = os.path.join(tempdir, 'dyfi_dat.xml')
    dataframe_to_xml(df, outfile, reference)
    # dataframe_to_xml(df, datadir + '/tmp.keepthis.xml', reference)

    outfilesize = os.path.getsize(outfile)
    # Longer size is for file with nresp field
    assert outfilesize == 183953 or outfilesize == 172852
    rmtree(tempdir)

    # This event has only text data
    eventid = 'ci14745580'
    tape_file2 = os.path.join(datadir, 'vcr_comcat_txt.yaml')

    with vcr.use_cassette(tape_file2):
        detail = get_event_by_id(eventid)
        df, msg = comcat.get_dyfi_dataframe_from_comcat(detail)
        df = gi.postprocess(df, 'neic')

    np.testing.assert_almost_equal(df['INTENSITY'].sum(), 800.4)


def test_comcat_file():
    eventid = 'nc72282711'
    datadir = get_datadir()

    # Test reading a comcat file
    testfile = os.path.join(datadir, 'nc72282711_dyfi_geo_10km.geojson')
    df, msg, network = gi.get_dyfi_dataframe_from_file(eventid, testfile)

    assert len(df) == 203
    np.testing.assert_equal(df['INTENSITY'].sum(), 705.3)
    np.testing.assert_equal(df['NRESP'].sum(), 16202)

    # Test that stddev and resp carry throuh
    try:
        np.testing.assert_almost_equal(df['INTENSITY_STDDEV'].sum(), 39.548)

        reference = 'TEST'
        tempdir = tempfile.mkdtemp(prefix='tmp.', dir=datadir)
        outfile = os.path.join(tempdir, 'dyfi_dat.xml')

        # Make sure output file includes stddev
        dataframe_to_xml(df, outfile, reference)
        # dataframe_to_xml(df, datadir + '/tmp.withstddev.xml', reference)
        with open(outfile, 'r') as f:
            textdata = f.read()
            assert 'stddev' in textdata
            rmtree(tempdir)

    except AssertionError:
        msg = 'A newer version of impactutils is required to process \
intensity parameters. If you do not work with intensity data, \
you can safely ignore this warning.'
        print(msg)


if __name__ == '__main__':
    os.environ['CALLED_FROM_PYTEST'] = 'True'
    test_comcat_data()
    test_comcat_file()
