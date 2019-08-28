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

.. |CodeCov| image:: https://codecov.io/gh/vinceq-usgs/getintensity/branch/master/graph/badge.svg
    :target: https://codecov.io/gh/vinceq-usgs/getintensity
    :alt: Code Coverage Status

.. |Codacy| image:: https://api.codacy.com/project/badge/Grade/1f771008e85041b89b97b6d12d85298a
    :target: https://www.codacy.com/app/vinceq-usgs/shakemap?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=vinceq-usgs/getintensity&amp;utm_campaign=Badge_Grade

.. |Azure| image:: https://dev.azure.com/vinceq-usgs/getintensity/_apis/build/status/vinceq-usgs.getintensity?branchName=master
   :target: https://dev.azure.com/vinceq-usgs/getintensity/_build/latest?definitionId=2&branchName=master
   :alt: Azure DevOps Build Status

getintensity
============


Documentation
-------------


Introduction
------------

Tool to download intensity data from outside sources and convert them into
Shakemap input.

Installation and Dependencies
-----------------------------

- Mac OSX or Linux operating systems
- bash shell, gcc, git, curl
- On OSX, Xcode and command line tools
- The ``install.sh`` script installs this package and all other dependencies,
  including python 3.5 and the required python libraries.
