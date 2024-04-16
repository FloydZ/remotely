#!/usr/bin/env python3
""" build script """

from remotely import __version__, __author__, __email__
from setuptools import setup
from setuptools.command.install import install
from setuptools.command.develop import develop
from setuptools.command.egg_info import egg_info


def read_text_file(path):
    """ read ta file """
    import os
    with open(os.path.join(os.path.dirname(__file__), path)) as f:
        return f.read()
    
    
class CustomInstallCommand(install):
    """ install script """
    def run(self):
        install.run(self)


class CustomDevelopCommand(develop):
    """ develop script """
    def run(self):
        develop.run(self)


class CustomEggInfoCommand(egg_info):
    """ custom script """
    def run(self):
        egg_info.run(self)


setup(
    name="remotely",
    version=__version__,
    description="execute python code on an remote machine",
    long_description=read_text_file("README.md"),
    author=__author__,
    author_email=__email__,
    url="https://github.com/FloydZ/remotly",
    packages=["remotely"],
    package_data={},
    keywords=[ "benchmark" ],
    install_requires=["setuptools"],
    requires=[],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "Operating System :: OS Independent",
	    "Programming Language :: Python",
	    "Programming Language :: Python :: 3",
        "Topic :: Scientific/Engineering",
        "Topic :: Software Development",
        "Topic :: Software Development :: Assemblers",
        "Topic :: Software Development :: Documentation"
    ])
