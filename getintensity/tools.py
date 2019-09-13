# Copy some functionality from shakemap.coremods.dyfi_dat

import re

import getintensity.comcat as comcat
import getintensity.emsc as emsc
import getintensity.ga as ga


MIN_RESPONSES = 3  # minimum number of responses per block


class IntensityParser:

    def __init__(self, config=None, eventid=None,
                 extid=None, network=None):

        self.config = config
        self.eventid = eventid
        self.extid = extid
        self.network = network

        return

    def get_dyfi_dataframe_from_file(self, inputfile,
                                     eventid=None, network=None):
        df = None
        msg = ''
        eventid = eventid or self.eventid
        network = network or self.network

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
            parser = emsc.process_emsc_csv
        else:
            msg = 'Unknown file type for %s' % inputfile
            return None, msg, None

        with open(inputfile, 'rb') as f:
            rawdata = f.read()
            df = parser(rawdata)

        if df is None:
            msg = 'Could not read file %s' % inputfile
            return None, msg, None

        return network, self.postprocess(df, network), ''

    def get_dyfi_dataframe_from_network(self, extid=None, network=None):
        df = None
        getter = None
        msg = ''
        extid = extid or self.extid or self.eventid
        network = network or self.network

        if network == 'neic':
            getter = comcat.get_dyfi_dataframe_from_comcat
        elif network == 'ga':
            getter = ga.get_dyfi_dataframe_from_ga
        elif network == 'emsc':
            getter = emsc.get_dyfi_dataframe_from_emsc
        else:
            msg = 'Unknown network %s' % network

        if getter:
            df, msg = getter(self, extid)
        if msg:
            return None, msg

        processed = self.postprocess(df, network)
        return processed, ''

    @classmethod
    def get_network_from_id(cls, extid):
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

    def get_extid_from_network(self, eventid, network):
        if network == 'neic':
            return eventid
        elif network == 'ga':
            extid_retriever = ga.get_extid_from_ga
        elif network == 'emsc':
            extid_retriever = emsc.get_extid_from_emsc

        self.extid = extid_retriever(self, eventid)
        return self.extid

    # TODO: Move this to network-specific modules
    @classmethod
    def postprocess(cls, df, network=None):

        netid = 'DYFI'
        source = comcat.source
        if not network and hasattr(cls, 'network'):
            network = cls.network

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
