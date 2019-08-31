#!/usr/bin/env python

import tempfile
import os.path
import vcr
import numpy as np
from shutil import rmtree

import getintensity.tools as gi
from libcomcat.search import get_event_by_id
from impactutils.io.table import dataframe_to_xml


def get_datadir():
    # where is this script?
    homedir = os.path.dirname(os.path.abspath(__file__))
    datadir = os.path.join(homedir, 'data')
    return datadir


def test_ga_file():
    datadir = get_datadir()

    # Test reading a comcat file
    testfile = os.path.join(datadir, 'felt_reports_1km.geojson')
    df, msg, network = gi.get_dyfi_dataframe_from_file(None, testfile)

    assert len(df) == 113
    assert df['SOURCE'][0] == 'Geoscience Australia (Felt report)'
    np.testing.assert_almost_equal(df['INTENSITY'].sum(), 427.9)
    np.testing.assert_equal(df['NRESP'].sum(), 1146)



def test_ga_retrieve():

    return
