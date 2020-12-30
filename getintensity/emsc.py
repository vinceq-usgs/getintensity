#! /usr/bin/env python

import urllib.request as request
import urllib.error as urlerror
import pandas as pd
import numpy as np
import zipfile
import json
from io import BytesIO, StringIO

from getintensity.aggregate import aggregate

netid = 'INTENSITY'
source = 'European-Mediterranean Seismic Center'
reference = 'EMSC (aggregated)'
default_outfile = 'emsc_ii_dat.xml'

EMSC_COLUMNS = ['LON', 'LAT', 'INTENSITY_UNCORRECTED', 'INTENSITY']
TIMEOUT = 60
MIN_RESPONSES = 3  # minimum number of DYFI responses per grid


# This should be called as a method of IntensityParser, hence the 'self'
def get_dyfi_dataframe_from_emsc(self, extid):
    df = None
    msg = ''

    config = self.config['emsc']
    template = config['fetcher_template']
    template = template.replace('[EID]', extid)

    url = template
    url = url.replace('[EID]', extid)
    try:
        print('Attempting URL:')
        print(url)
        fh = request.urlopen(url, timeout=TIMEOUT)
        rawdata = fh.read()
        fh.close()
        print('Retrieved %s from EMSC' % extid)
    except urlerror.HTTPError as e:
        print('Could not get data for %s from EMSC. Stopping.' % extid)
        print('HTTPError: %s %s' % (e.code, e.reason))
        exit()

    csvdata = parse_zip(rawdata)
    if not csvdata:
        msg = 'Could not unzip raw data'
        return None, msg

    rawfile = 'raw/rawdata.emsc.%s.csv' % extid
    with open(rawfile, 'w') as f:
        f.write(csvdata.decode('utf-8'))

    df = process_emsc_csv(csvdata)
    if df is None:
        msg = 'Could not decode EMSC data'
        return None, msg
    return df, None


# This should be called as a method of IntensityParser, hence the 'self'
def get_extid_from_emsc(self, inputid):

    config = self.config['emsc']
    url = config['search_template']
    url = url.replace('[EID]', inputid)

    try:
        print('Attempting URL:')
        print(url)
        fh = request.urlopen(url, timeout=TIMEOUT)
        rawdata = fh.read()
        fh.close()
    except urlerror.HTTPError as e:
        print('Error accessing EMSC Eventid server. Stopping.')
        print('HTTPError: %s %s' % (e.code, e.reason))
        return None

    try:
        rawdata = rawdata.decode('utf-8')
        jsondata = json.loads(rawdata)
        extid = jsondata[0]['id']
    except:
        print('Unable to unpack EMSC Eventid server.')
        return

    rawfile = 'raw/rawid.emsc.%s.json' % extid
    with open(rawfile, 'w') as f:
        f.write(json.dumps(jsondata))
    print('Saving raw data in', rawfile)
    print('Retrieved', extid, 'from EMSC Eventid server.')
    return extid


def parse_zip(bufferstr):
    """
    parse binary object as zip file
    """

    z = zipfile.ZipFile(BytesIO(bufferstr))
    filenames = z.namelist()
    if not filenames:
        print('No names found.')
        with open('tmp.badzipfile.zip', 'wb') as f:
            f.write(bufferstr)
        exit()

    if len(filenames) > 1:
        print('WARNING: >1 file found, using only the first available.')

    data = z.read(filenames[0])
    return data


def process_emsc_csv(rawdata):

    df = _parse_emsc_raw(rawdata)
    df_10km = aggregate(df, producttype='geo_10km', minresps=MIN_RESPONSES)
    df_1km = aggregate(df, producttype='geo_1km', minresps=MIN_RESPONSES)
    if len(df_10km) > len(df_1km):
        df = df_10km
        print('Using 10km aggregation.')
    else:
        df = df_1km
        print('Using 1km aggregation.')

    # This adds a 'station' column e.g. EMSC.UTM:(667000 7742000 50 K)
    df['STATION'] = 'EMSC.UTM:(' + df.index + ')'

    return df


def _parse_emsc_raw(emscdata):

    text_geo = emscdata.decode('utf-8')
    fileio = StringIO(text_geo)

    # the emsc file has:
    # lon, lat, iraw, icorr
    df = pd.read_csv(fileio, skiprows=4, names=EMSC_COLUMNS)
    df['LAT'] = df['LAT'].round(decimals=3)
    df['LON'] = df['LON'].round(decimals=3)

    return df


def _compute_stddev_bossu(df):
    # From Bossu et al, SRL 2016 88 (1): 72–81.
    # doi: https://doi.org/10.1785/0220160120
    # This is no longer used; instead, compute stddev via
    # Worden et al. using nresps
    ii = df['INTENSITY']
    stddevs = np.ones_like(ii) * 0.49
    stddevs[ii >= 3.15] = 0.36
    return stddevs
