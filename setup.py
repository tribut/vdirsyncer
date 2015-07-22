# -*- coding: utf-8 -*-
'''
Vdirsyncer is a synchronization tool for vdir. See the README for more details.
'''

# Packagers: Vdirsyncer's version is automatically detected using
# setuptools-scm, but that one is not a runtime dependency.
#
# Do NOT use the GitHub's tarballs, those don't contain any version information
# detectable for setuptools-scm. Rather use the PyPI ones.


from setuptools import find_packages, setup


setup(
    name='vdirsyncer',
    use_scm_version={
        'write_to': 'vdirsyncer/version.py',
    },
    setup_requires=['setuptools_scm'],
    author='Markus Unterwaditzer',
    author_email='markus@unterwaditzer.net',
    url='https://github.com/untitaker/vdirsyncer',
    description='Synchronize calendars and contacts',
    license='MIT',
    long_description=open('README.rst').read(),
    packages=find_packages(exclude=['tests.*', 'tests']),
    include_package_data=True,
    entry_points={
        'console_scripts': ['vdirsyncer = vdirsyncer.cli:main']
    },
    install_requires=[
        # https://github.com/mitsuhiko/click/issues/200
        'click',
        'click_log',
        'click_threading',
        'requests',
        'lxml>=3.0',
        # https://github.com/sigmavirus24/requests-toolbelt/pull/28
        'requests_toolbelt>=0.4.0',
        'atomicwrites'
    ],
    extras_require={'keyring': ['keyring']}
)
