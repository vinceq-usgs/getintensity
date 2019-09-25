# Copy some functionality from shakemap.coremods.dyfi_dat

import re
from numpy import exp

import getintensity.comcat as comcat
import getintensity.emsc as emsc
import getintensity.ga as ga


class IntensityParser:

    def __init__(self, config=None, eventid=None,
                 extid=None, network=None):

        self.config = config
        self.eventid = eventid
        self.extid = extid
        self.network = network

        # These need to be filled out by postprocess()
        self.netid = None
        self.source = None
        self.reference = None
        self.default_outfile = None

        return

    def get_dyfi_dataframe_from_file(self, inputfile,
                                     eventid=None, network=None):
        if not eventid:
            eventid = self.eventid
        if not network:
            network = self.network

        if not network:
            # Try to figure out the network so we can parse properly
            if '.zip' in inputfile:
                msg = 'This looks like an EMSC ZIP file. Please unzip \
                    this and rerun this program on the unzipped (.txt) file.'
                return None, msg
            elif re.search('felt_reports_', inputfile):
                network = 'ga'
            elif re.search('dyfi_geo_', inputfile):
                network = 'neic'
            elif 'cdi_geo.txt' in inputfile:
                network = 'neic'
            elif re.search(r'\d{8}_\d{7}.txt', inputfile):
                network = 'emsc'
            else:
                return None, 'No network found for %s.' % inputfile
            self.network = network

        is_csv = re.search(r'\.csv$|\.txt$', inputfile)
        if '.geojson' in inputfile:
            parser = comcat._parse_dyfi_geocoded_json
        elif network == 'neic' and is_csv:
            parser = comcat._parse_dyfi_geocoded_csv
        elif network == 'emsc' and is_csv:
            parser = emsc.process_emsc_csv
        else:
            return None, 'Unknown file type for ' % inputfile

        with open(inputfile, 'rb') as f:
            df = parser(f.read())
            if df is None:
                return None, 'Could not read file %s' % inputfile

        return self.postprocess(df, self.network)

    def get_dyfi_dataframe_from_network(self, extid=None, network=None):
        if not extid:
            return None, 'Cannot access external network without extid'
        if not network:
            network = self.network

        getters = {
            'neic': comcat.get_dyfi_dataframe_from_comcat,
            'ga':   ga.get_dyfi_dataframe_from_ga,
            'emsc': emsc.get_dyfi_dataframe_from_emsc
        }
        if network in getters:
            getter = getters[network]
            df, msg = getter(self, extid)
        else:
            return None, 'No support for network: ' + network

        if df is None:
            return None, msg
        return self.postprocess(df, network)

    @classmethod
    def get_network_from_id(cls, extid):
        if extid[0:2] == 'ga':
            network = 'ga'
        elif re.match(r'\d{6}', extid):
            network = 'emsc'
        elif re.match(r'[^ 0-9]{2}', extid):
            network = 'neic'
        else:
            print('Cannot guess network from id. Stopping.', extid)
            exit()

        print('Guessing %s to be network: %s.' % (extid, network))
        return network

    def get_extid_from_network(self, eventid=None, network=None):
        if not eventid:
            eventid = self.eventid
        if not network:
            network = self.network

        if network == 'neic':
            return eventid
        elif network == 'ga':
            extid_retriever = ga.get_extid_from_ga
        elif network == 'emsc':
            extid_retriever = emsc.get_extid_from_emsc

        return extid_retriever(self, eventid)

    def postprocess(self, df, network=None):
        # - From the network module, define:
        #     netid, source, reference, default_outfile
        # - Convert column names to uppercase
        # - Calculate stddev from nresps
        if not network:
            return None, 'Cannot postprocess without network'

        module_list = {'neic': comcat,
                       'emsc': emsc,
                       'ga': ga}

        if network in module_list:
            module = module_list[network]
        else:
            return None, 'Cannot postprocess unknown network %s' % network

        # Get network-specific attributes
        for attrib in ('netid', 'source', 'reference', 'default_outfile'):
            setattr(self, attrib, getattr(module, attrib))

        # Try network-specific postprocess, if it exists
        try:
            _postprocess_func = getattr(module, 'postprocess')
            _postprocess_func(df)
        except AttributeError:
            pass

        # These are set from network module
        df['netid'] = self.netid
        df['source'] = self.source

        df.columns = df.columns.str.upper()
        if 'NRESP' in df.columns and 'INTENSITY_STDDEV' not in df.columns:
            df['INTENSITY_STDDEV'] = self._compute_stddev(df)

        return df, None

    @classmethod
    def _compute_stddev(cls, df):
        # Worden 2012  BSSA 102-1 Feb. 2012, doi: 10.1785/0120110156
        nresps = df['NRESP']
        stddevs = exp(nresps * (-1/24.02)) * 0.25 + 0.09
        return stddevs
