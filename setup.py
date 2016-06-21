#!/usr/bin/python2

from distutils.core import setup

setup(
    name='Velma',
    version='0.0.2',
    author='Alex Thewsey',
    url='https://github.com/athewsey/pyvelma',
    packages=['velma','velma.test'],
    package_data={'velma': ['data/*.txt']},
    scripts=[
        'bin/DemoVelmaAssistant.py',
        'bin/DemoVelmaDebug.py',
        'bin/DemoVelmaOpponent.py',
    ],
    description='An A.I./assistant for the game of "Cluedo".',
    long_description=open('README.md').read(),
    install_requires=[
        "matplotlib >= 1.1.0",
        "numpy >= 1.6.1",
        "scipy >= 0.9.0",
    ],
    platforms=['POSIX'],
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: End Users/Desktop'
        'Natural Language :: English',
        'Operating System :: POSIX',
        'Programming Language :: Python :: 2.7',
        'Topic :: Games/Entertainment :: Board Games',
    ],
    tests_require=['pytest'],
)
