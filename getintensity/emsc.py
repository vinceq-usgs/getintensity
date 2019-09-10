#! /usr/bin/env python

import urllib.request as request
import urllib.error as urlerror
import json
import zipfile
from io import BytesIO

source = 'European-Mediterranean Seismic Center'
TIMEOUT = 60
MIN_RESPONSES = 3  # minimum number of DYFI responses per grid


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
        print('Retrieved %s from ' % filename)
    except urlerror.HTTPError as e:
        print('Could not get data for %s from EMSC. Stopping.' % filename)
        print('HTTPError: %s %s' % (e.code, e.reason))
        exit()

     csvdata = parsezip(rawdata)
     if not csvdata:
         msg = 'Could not unzip raw data'
         return None, msg
     df =  _parse_and_geocode_emsc_csv(csvdata)
     if not df:
         msg = 'Could not decode EMSC data'
         return None, msg
     return df, None


def parsezip(bufferstr):
    """
    parse binary object as zip file
    """

    z = zipfile.ZipFile(BytesIO(bufferstr))
    filenames = z.namelist()

    if len(filenames)>1:
        print('WARNING: >1 files found, using only the first available.')

    data = z.read(filenames[0])
    return data


def _parse_and_geocode_emsc_csv(rawdata):

    df = _parse_emsc_raw(rawdata)
    df = _emsc_correction(df)
    df = _geocode(df)

    return df


def _parse_emsc_raw(emscdata):

    # the emsc file has:
    # lon, lat, iraw, icorr
    text_geo = emscdata.decode('utf-8')
    fileio = StringIO(text_geo)

    # the dataframe we want has columns:
    # 'intensity', 'lat', 'lon', 'station', 'nresp'
    df = pd.read_csv(fileio, skiprows=4, names=EMSC_COLUMNS)
    df['lat']=df['lat'].round(decimals=3)
    df['lon']=df['lon'].round(decimals=3)

    # This adds a 'station' column
    nstations = np.arange(df.shape[0])
    stations = ["%i" % (n+1) for n in nstations]
    df['STATION'] = stations
    df['NRESP'] = 1
    return df


def _emsc_correction(emscdata):

    df = _parse_emsc_raw(emscdata)

    df['netid'] = 'EMSC'
    df['source'] = "EMSC"
    df.columns = df.columns.str.upper()

    if 'INTENSITY_STDDEV' not in df.columns:

        # From Bossu et al, SRL 2016 88 (1): 72–81.
        # doi: https://doi.org/10.1785/0220160120
        def _compute_stddev(df):
            ii = df['INTENSITY']
            stddevs = np.ones_like(ii) * 0.49
            stddevs[ii>=3.15] = 0.36
            return stddevs

        df['INTENSITY_STDDEV'] = _compute_stddev(df)

    return (df, '')


def calculate_station_column(df):

    nstations = np.arange(df.shape[0])
    stations = ["%i" % (n+1) for n in nstations]
    return stations


def getextid_from_emsc(eventid):

    print('Not yet implemented')
    raise
