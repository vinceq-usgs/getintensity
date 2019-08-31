# Copy some functionality from shakemap.coremods.dyfi_dat

import re

import getintensity.comcat as comcat
import getintensity.emsc as emsc
import getintensity.ga as ga


MIN_RESPONSES = 3  # minimum number of responses per block


def get_dyfi_dataframe_from_file(eventid, inputfile, network=None):
    df = None
    msg = ''

    # Try to figure out the network so we can parse properly
    if not network:
        if '.zip' in inputfile:
            # Looks like EMSC ZIP file
            msg = 'This looks like an EMSC ZIP file. Please unzip \
                this and rerun this program on the unzipped (.txt) file.'
            return None, msg, None
        elif re.search('felt_reports_', inputfile):
            network = 'ga'
        elif re.search('dyfi_geo_', inputfile):
            network = 'neic'
        elif 'cdi_geo.txt' in inputfile:
            network = 'emsc'
        elif re.search('\d{8}_\d{7}.txt', inputfile):
            network = 'emsc'

    if '.geojson' in inputfile:
        parser = comcat._parse_dyfi_geocoded_json
    elif network == 'neic' and ('.csv' in inputfile or '.txt' in inputfile):
        parser = comcat._parse_dyfi_geocoded_csv
    elif network == 'emsc' and ('.csv' in inputfile or '.txt' in inputfile):
        parser = emsc._parse_emsc_geocoded_csv
    else:
        msg = 'Unknown file type for %s' % inputfile
        return None, msg, None

    with open(inputfile, 'rb') as f:
        rawdata = f.read()
        df = parser(rawdata)

    if df is None:
        msg = 'Could not read file %s' % inputfile
        return None, msg, None

    return postprocess(df, network), '', network


def get_dyfi_dataframe_from_network(eventid, extid, network):
    df = None
    getter = None
    msg = ''

    if network == 'neic':
        getter = comcat.get_dyfi_dataframe_from_comcat(extid)
    elif network == 'ga':
        getter = ga.get_dyfi_dataframe_from_ga(extid)
    elif network == 'emsc':
        getter = emsc.get_dyfi_dataframe_from_emsc(extid)
    else:
        msg = 'Unknown network %s' % network

    if getter:
        df, msg = getter(extid)
    if msg:
        return None, msg

    processed = postprocess(df, network)
    return processed, ''


def get_network_from_id(extid):
    network = None
    if extid[0:2] == 'ga':
        network = 'ga'
    elif re.match('\d{6}', extid):
        network = 'emsc'
    elif re.match('[^ 0-9]{2}', extid):
        network = 'neic'

    if network:
        print('Guessing %s to be an %s network ID.' % (extid, network))
    else:
        print('Cannot guess network from id. Stopping.', extid)
        exit()

    return network


def get_extid_from_network(eventid, network):
    if network == 'neic':
        return eventid
    elif network == 'ga':
        extid_retriever = ga.get_extid_from_ga
    elif network == 'emsc':
        extid_retriever = emsc.get_extid_from_emsc

    return extid_retriever(eventid)


# TODO: Move this to network-specific modules
def postprocess(df, network=None):

    netid = 'DYFI'
    source = comcat.source

    if network == 'ga':
        netid = 'GA'
        source = ga.source

        if 'UTM' in df['location'][0]:
            df['station'] = df['location']
        else:
            df['station'] = 'UTM:(' + df['location'] + ')'
        df = df.drop(columns=['location'])
    elif network == 'emsc':
        netid = 'EMSC'
        source = emsc.source

    df['netid'] = netid
    df['source'] = source
    df.columns = df.columns.str.upper()

    return df
