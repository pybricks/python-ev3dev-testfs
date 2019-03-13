from distutils.core import setup

import versioneer

setup(name='ev3dev-testfs',
      version=versioneer.get_version(),
      cmdclass=versioneer.get_cmdclass(),
      packages=['ev3dev.testfs'])
