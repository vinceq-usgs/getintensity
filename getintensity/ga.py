# Copy some functionality from shakemap.coremods.dyfi_dat

import pandas as pd
import numpy as np
import json
from io import StringIO
import re
import urllib.request as request
import urllib.error as urlerror

from libcomcat.classes import DetailEvent

from getintensity.comcat import _parse_dyfi_geocoded_json

source = 'Geoscience Australia (Felt report)'
TIMEOUT = 60


MIN_RESPONSES = 3  # minimum number of DYFI responses per grid

def get_dyfi_dataframe_from_ga(self, extid):
    df = None
    msg = ''

    config = self.config['ga']
    template = config['fetcher_template']
    template = template.replace('[EID]', extid)
    df_by_geotype = {}

    print('Attempting to find GA ID with', extid)
    for geotype in ('10km', '1km'):
        filename = 'felt_reports_%s_filtered.geojson' % geotype
        url = template
        url = url.replace('[EID]', extid)
        url = url.replace('[FILE]', filename)
        try:
            print('Attempting URL:')
            print(url)
            fh = request.urlopen(url, timeout=TIMEOUT)
            data = fh.read()
            fh.close()
            print('Retrieved %s from GA' % filename)
        except urlerror.HTTPError as e:
            print('Could not get data for %s from GA. Stopping.' % filename)
            print('HTTPError: %s %s' % (e.code, e.reason))
            exit()

        df = _parse_dyfi_geocoded_json(data)
        print('File %s has %i stations.' % (filename, len(df)))
        df_by_geotype[geotype] = df

    if len(df_by_geotype) < 1:
        msg = 'Could not get geojson data from GA'
        return None, msg

    # Choose the most number of stations
    sortedlist = sorted(df_by_geotype.values(), key=len)
    df = sortedlist[-1]

    return df, ''


def getextid_from_ga(eventid):

    print('Not yet implemented')
    raise
