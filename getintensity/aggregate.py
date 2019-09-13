import math
import geojson

from .thirdparty.utm import from_latlon, to_latlon, OutOfRangeError

PRECISION = 6  # Maximum precision of lat/lon coordinates of output


def aggregate(df, producttype, minresps=0):
    """

    :synopsis: Aggregate entries into geocoded boxes
    :param entries: :obj:`list` of dict entries
    :param producttype: The product type (geo_1km, geo_10km)
    :param bool debug: If true, store debugging info
    :returns: `GeoJSON` :py:obj:`FeatureCollection`, see below

    The return value is a list of geocoded blocks.
    one feature for each aggregated location.
    Each Feature in the `GeoJSON` FeatureCollection has an `id`
    attribute (the UTM string) and the following properties:

    ==========  =========================================================
    location    UTM string
    center      Center of this location, for plotting (`GeoJSON Point`)
    nresp       number of responses in this location
    intensity   aggregated intensity for this location
    ==========  =========================================================

    The `FeatureCollection` also has the following properties:

    ======  ========================================
    name    Same as :py:attr:`producttype`
    id      Same as :py:attr:`producttype`
    nresp   Total number of responses from each valid location
    maxint  Maximum intensity from each valid location
    ======  ========================================

    """

    # producttype is either 'geo_1km', '10km'
    if '_1km' in producttype or producttype == '1km':
        resolutionMeters = 1000

    elif '_10km' in producttype or producttype == '10km':
        resolutionMeters = 10000

    else:
        resolutionMeters = None

    if not resolutionMeters:
        raise ValueError('Aggregate: got unknown type ' + producttype)

    # Loop through each entry, compute the bin it belongs to

    def _getutm(x):
        # Get UTM for each location
        return getUtmFromCoordinates(x.LAT, x.LON, resolutionMeters)
    df['LOCATION'] = df.apply(_getutm, axis=1)

    # Drop rows with no location data
    df = df[~df['LOCATION'].isnull()]
    print('Geocoded %s got %i entries with valid locations.' %
          (producttype, len(df.index)))

    by_locs = df.groupby('LOCATION')
    agg_df = by_locs.agg(INTENSITY=('INTENSITY', 'mean'),
                         NRESP=('INTENSITY', 'count'))
    agg_df = agg_df[agg_df['NRESP'] >= minresps]
    print('Aggregated to %i locations with %i+ responses.' %
          (len(agg_df.index), minresps))

    # Get center of each UTM location
    def _getCenter(row):
        results = getUtmPolyFromString(row.name, resolutionMeters)
        if not results:
            return None, None
        # This returns lon/lat; need to reverse it
        data = results['center']['coordinates'][::-1]
        return data

    # getUtmPolyFromString returns lon/lat
    agg_df[['LAT', 'LON']] = agg_df.apply(
                _getCenter, axis=1, result_type='expand')

    return agg_df


# --------------------
# UTM Helper Functions
# ---------------------

def getUtmFromCoordinates(lat, lon, span):
    """

    :synopsis: Convert lat/lon coordinates to UTM string
    :param float lat: Latitude
    :param float lon: Longitude
    :param span: (optional) Size of the UTM box (see below)
    :returns: UTM string with the correct resolution

    Convert lat/lon coordinates into a UTM string using the :py:obj:`UTM`
    package. If :py:obj:`span` is specified, the output resolution is degraded
    via the :py:obj:`floor` function.

    :py:obj:`span` accepts the values 'geo_10km', 'geo_1km', or the size of
    the UTM box in meters (should be a power of 10).

    This will NOT filter the location based on precision of the input
    coordinates.

    """

    span = _floatSpan(span)

    try:
        loc = from_latlon(lat, lon)
    except OutOfRangeError:
        # Catchall for any location that cannot be geocoded
        return None

    x, y, zonenum, zoneletter = loc
    x = myFloor(x, span)
    y = myFloor(y, span)

    if not x or not y or not zonenum:
        print('WARNING: Cannot get UTM for', lat, lon)
        return None

    utm = '{} {} {} {}'.format(x, y, zonenum, zoneletter)
    return utm


def _floatSpan(span):

    if span == 'geo_1km' or span == '1km' or span == 1000:
        span = 1000
    elif span == 'geo_10km' or span == '10km' or span == 10000:
        span = 10000
    else:
        raise TypeError('Invalid span value ' + str(span))

    return span


def getUtmPolyFromString(utm, span):
    """

    :synopsis: Compute the (lat/lon) bounds and center from a UTM string
    :param utm: A UTM string
    :param int span: The size of the UTM box in meters
    :return: :py:obj:`dict`, see below

    Get the bounding box polygon and center point for a UTM string suitable
    for plotting.

    The return value has two keys:

    ======    ========================
    center    A GeoJSON Point object
    bounds    A GeoJSON Polygon object
    ======    ========================

    """

    x, y, zone, zoneletter = utm.split()
    x = int(x)
    y = int(y)
    zone = int(zone)

    # Compute bounds. Need to reverse-tuple here because the
    # to_latlon function returns lat/lon and geojson requires lon/lat.
    # Rounding needed otherwise lat/lon coordinates are arbitrarily long

    ebound = zone*6-180
    # wbound = ebound - 6

    def _reverse(tup, eastborder=None):

        (y, x) = tup
        if eastborder and x > ebound:
            x = ebound
        x = round(x, PRECISION)
        y = round(y, PRECISION)
        return (x, y)

    p1 = _reverse(to_latlon(x, y, zone, zoneletter))
    p2 = _reverse(to_latlon(x, y+span, zone, zoneletter))
    p3 = _reverse(to_latlon(x+span, y+span, zone, zoneletter), 'e')
    p4 = _reverse(to_latlon(x+span, y, zone, zoneletter), 'e')
    bounds = geojson.Polygon([[p1, p2, p3, p4, p1]])

    # Compute center
    cx = int(x)+span/2
    cy = int(y)+span/2
    clat, clon = to_latlon(cx, cy, zone, zoneletter)
    clat = round(clat, PRECISION)
    clon = round(clon, PRECISION)
    center = geojson.Point((clon, clat))

    return ({'center': center, 'bounds': bounds})


# -------------------------
# Utility Functions
# -------------------------

def myFloor(x, multiple):
    """

    :synopsis: Round down to a multiple of 10/100/1000...
    :param float x: A number
    :param int multiple: Power of 10 indicating how many places to round
    :returns: int

    This emulates the `math.floor` function but
    rounding down a positive power of 10 (i.e. 10, 100, 1000...)

    For example, myFloor(1975,100) returns 1900.

    """

    y = x/multiple
    return int(math.floor(y) * multiple)
