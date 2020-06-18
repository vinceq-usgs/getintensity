import os
from distutils.core import setup
import os.path
import versioneer

# This should be handled by conda when we install a platform-specific
# compiler
# os.environ['CC'] = 'gcc'

setup(name='getintensity',
      version=versioneer.get_version(),
      description='External intensity data fetcher for Shakemap',
      author='Vince Quitoriano',
      author_email='vinceq@contractor.usgs.gov',
      url='http://github.com/vinceq-usgs/getintensity',
      packages=[
          'getintensity'
      ],
      package_data={
          'getintensity': [
              os.path.join('tests', '*'),
          ]
      },
      scripts=[
          'bin/getintensity']
      )
