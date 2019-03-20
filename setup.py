from setuptools import setup

import versioneer

setup(
    name='ev3dev-testfs',
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    namespace_packages=['ev3dev'],
    packages=['ev3dev.testfs'],
    setup_requires=['pytest-runner'],
    test_requires=['pytest'],
)
