+---------------+----------------------+
| Linux build   | |Travis|             |
+---------------+----------------------+
| Code quality  | |Codacy|             |
+---------------+----------------------+
| Code coverage | |CodeCov|            |
+---------------+----------------------+
| Azure builds  | |Azure|              |
+---------------+----------------------+


.. |Travis| image:: https://travis-ci.org/vinceq-usgs/getintensity.svg?branch=master
    :target: https://travis-ci.org/vinceq-usgs/getintensity
    :alt: Travis Build Status

.. |Codacy| image:: https://api.codacy.com/project/badge/Grade/589ee237b1b94ad99977dd82c643f1ac
    :target: https://www.codacy.com/manual/vinceq-usgs/getintensity?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=vinceq-usgs/getintensity&amp;utm_campaign=Badge_Grade

.. |CodeCov| image:: https://codecov.io/gh/vinceq-usgs/getintensity/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/vinceq-usgs/getintensity
    :alt: Code Coverage Status

.. |Azure| image:: https://dev.azure.com/vinceq-usgs/getintensity/_apis/build/status/vinceq-usgs.getintensity?branchName=master
   :target: https://dev.azure.com/vinceq-usgs/getintensity/_build/latest?definitionId=2&branchName=master
   :alt: Azure DevOps Build Status

getintensity
============


Documentation
-------------

Download DYFI data from Comcat or an external source and turn it into a
ShakeMap intensity input file. This can automatically download from Comcat,
Geosciences Australia (GA event ID required), and EMSC (automatic lookup from
the USGS ID).

Usage::

  getintensity EVENTID [--extid  EXTERNALID] [--network NETWORK]
  getintensity EVENTID [--inputfile FILENAME]

For example::

  getintensity us70004jxe                 # will read from Comcat
  getintensity us70004jxe --network ga    # will attempt to find GA ID
  getintensity us70004jxe --network emsc  # will attempt to find EMSC ID
  getintensity us70004jxe --extid ga2019nsodfc --network ga
  getintensity us70004jxe --inputfile felt_reports_1km.geojson --network ga

Supported networks:
  
- neic:    National Earthquake Information Center (USA) (default)
- ga:      Geosciences Australia
- emsc:    European-Mediterranean Seismic Center

If --network is missing, this will attempt to guess it from extid or 
input filename. If neither is provided, 'neic' is assumed.


Installation and Dependencies
-----------------------------

- Mac OSX or Linux operating systems
- bash shell, gcc, git, curl
- On OSX, Xcode and command line tools
- The ``install.sh`` script installs this package and all other dependencies,
  including python 3.5 and the required python libraries.

Impactutils
:::::::::::

Impactutils (https://github.com/hearne/shakemap) is automatically installed.

      The current conda 'impactutils' package (as of 2019/09/19) does not support
      output files with 'nresponses' and 'intensity_stddev'; these columns
      will be missing from the output files unless the latest impactutils is
      installed.

      To support this functionality:

      - Install the latest 'impactutils' from the GitHub repository at:

        http://github.com/usgs/impactutils.

      - Create a symlink to the impactutils directory from the repo home directory. e.g.::

        cd repos/getintensity
        ln -s /path/to/impactutils impactutils

      - Check that the top of the directory has these lines::

        import os
        sys.path.insert(0, os.getcwd())

      This section will be unnecessary once the conda impactutils installation is updated.

Shakemap
::::::::

ShakeMap (https://github.com/usgs/shakemap) support is optional. 

**Without ShakeMap installed** (default),
output files will be written to the current directory.

**With ShakeMap installed,** open the getintensity config.ini file and set 'use_shakemap_path' to 'on'. Then 
output files will be written to the ShakeMap profile of correct event.

