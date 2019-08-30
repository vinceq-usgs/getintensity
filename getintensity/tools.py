# Copy some functionality from shakemap.coremods.dyfi_dat

import pandas as pd
import numpy as np
import json
from io import StringIO

from libcomcat.classes import DetailEvent

COMCAT_TEMPLATE = 'https://earthquake.usgs.gov/fdsnws/event/1/query?' \
                  'eventid=[EID]&format=geojson'

# For legacy DYFI events only (cdi_geo.txt files)
DYFI_COLUMNS_REPLACE = {
    'Geocoded box': 'station',
    'CDI': 'intensity',
    'Latitude': 'lat',
    'Longitude': 'lon',
    'No. of responses': 'nresp',
    'Hypocentral distance': 'distance'
}

OLD_DYFI_COLUMNS_REPLACE = {
    'ZIP/Location': 'station',
    'CDI': 'intensity',
    'Latitude': 'lat',
    'Longitude': 'lon',
    'No. of responses': 'nresp',
    'Epicentral distance': 'distance'
}


MIN_RESPONSES = 3  # minimum number of DYFI responses per grid


def get_dyfi_dataframe_from_file(eventid, inputfile, network=None):
    df = None
    msg = ''

    # Try to figure out the network so we can parse properly
    if not network:
        if '.zip' in inputfile:
            # Looks like EMSC ZIP file
            msg = 'This looks like an EMSC ZIP file. Please unzip \
                this and rerun this program on the unzipped (.txt) file.'
            return None, None, msg
        elif '.csv' in inputfile:
            network = 'emsc'
        elif '.geojson' in inputfile and 'felt_reports' in inputfile:
            network = 'ga'
        elif '.geojson' in inputfile and 'dyfi_' in inputfile:
            network = 'neic'
        elif 'cdi_geo.txt' in inputfile:
            network = 'neic'

    if '.geojson' in inputfile:
        parser = _parse_geocoded_json
    elif 'csv' in inputfile or 'txt' in inputfile:
        parser = _parse_geocoded_csv
    else:
        msg = 'Unknown file type for %s' % inputfile
        return None, None, msg

    with open(inputfile, 'rb') as f:
        rawdata = f.read()
        df = parser(rawdata)

    if df is None:
        msg = 'Could not read file %s' % inputfile
        return None, None, msg

    return network, postprocess(df), ''


def get_dyfi_dataframe_from_comcat(extid):
    df = None
    msg = ''

    if isinstance(extid, DetailEvent):
        detail = extid
    else:
        url = COMCAT_TEMPLATE.replace('[EID]', extid)
        print('Checking URL:', url)
        detail = DetailEvent(url)
    if detail is None:
        msg = 'Error getting data from Comcat'
        return None, msg

    df, msg = _parse_dyfi_detail(detail)
    if df is None:
        msg = msg or 'Error parsing Comcat data'
        return None, msg

    return postprocess(df), None


def get_dyfi_dataframe_from_network():
    df = None
    msg = ''
    return postprocess(df)


def get_network_from_id(extid):
    network = None
    return network


def get_extid_from_network(network):
    extid = None
    return extid


def postprocess(df):

    df['netid'] = 'DYFI'
    df['source'] = "USGS (Did You Feel It?)"
    df.columns = df.columns.str.upper()

    return df


def _parse_dyfi_detail(detail):

    if not detail.hasProduct('dyfi'):
        msg = '%s has no DYFI product at this time.' % detail.url
        dataframe = None
        return dataframe, msg

    dyfi = detail.getProducts('dyfi')[0]

    # search the dyfi product, see which of the geocoded
    # files (1km or 10km) it has.  We're going to select the data from
    # whichever of the two has more entries with >= 3 responses,
    # preferring 1km if there is a tie.
    df_10k = pd.DataFrame({'a': []})
    df_1k = pd.DataFrame({'a': []})

    # get 10km data set, if exists
    if len(dyfi.getContentsMatching('dyfi_geo_10km.geojson')):
        bytes_10k, _ = dyfi.getContentBytes('dyfi_geo_10km.geojson')
        df_10k = _parse_geocoded_json(bytes_10k)
        print('Found dyfi_geo_10km.geojson with', len(df_10k), 'stations.')

    # get 1km data set, if exists
    if len(dyfi.getContentsMatching('dyfi_geo_1km.geojson')):
        print('Found dyfi_geo_1km.geojson')
        bytes_1k, _ = dyfi.getContentBytes('dyfi_geo_1km.geojson')
        df_1k = _parse_geocoded_json(bytes_1k)
        print('Found dyfi_geo_1km.geojson with', len(df_1k), 'stations.')

    if len(df_1k) >= len(df_10k):
        df = df_1k
    else:
        df = df_10k

    if not len(df):
        # try to get the text file data set
        if not len(dyfi.getContentsMatching('cdi_geo.txt')):
            return (None, 'No geocoded datasets are available for this event.')

        bytes_geo, _ = dyfi.getContentBytes('cdi_geo.txt')
        df = _parse_geocoded_csv(bytes_geo)

    return df, ''


def _parse_geocoded_csv(bytes_data):
    # the dataframe we want has columns:
    # 'intensity', 'distance', 'lat', 'lon', 'station', 'nresp'
    # the cdi geo file has:
    # Geocoded box, CDI, No. of responses, Hypocentral distance,
    # Latitude, Longitude, Suspect?, City, State

    # download the text file, turn it into a dataframe

    text_geo = bytes_data.decode('utf-8')
    lines = text_geo.split('\n')
    columns = lines[0].split(':')[1].split(',')
    columns = [col.strip() for col in columns]

    fileio = StringIO(text_geo)
    df = pd.read_csv(fileio, skiprows=1, names=columns)
    if 'ZIP/Location' in columns:
        df = df.rename(index=str, columns=OLD_DYFI_COLUMNS_REPLACE)
    else:
        df = df.rename(index=str, columns=DYFI_COLUMNS_REPLACE)
    df = df.drop(['Suspect?', 'City', 'State'], axis=1)
    df = df[df['nresp'] >= MIN_RESPONSES]

    return df


def _parse_geocoded_json(bytes_data):

    text_data = bytes_data.decode('utf-8')
    jdict = json.loads(text_data)
    if len(jdict['features']) == 0:
        return None
    prop_columns = list(jdict['features'][0]['properties'].keys())
    columns = ['lat', 'lon'] + prop_columns
    arrays = [[] for col in columns]
    df_dict = dict(zip(columns, arrays))
    for feature in jdict['features']:
        for column in prop_columns:
            if column == 'name':
                prop = feature['properties'][column]
                prop = prop[0:prop.find('<br>')]
            else:
                prop = feature['properties'][column]

            df_dict[column].append(prop)
        # the geojson defines a box, so let's grab the center point
        lons = [c[0] for c in feature['geometry']['coordinates'][0]]
        lats = [c[1] for c in feature['geometry']['coordinates'][0]]
        clon = np.mean(lons)
        clat = np.mean(lats)
        df_dict['lat'].append(clat)
        df_dict['lon'].append(clon)

    df = pd.DataFrame(df_dict)
    df = df.rename(index=str, columns={
        'cdi': 'intensity',
        'dist': 'distance',
        'name': 'station',
        'stddev': 'intensity_stddev'
    })
    if df is not None:
        df = df[df['nresp'] >= MIN_RESPONSES]

    return df
