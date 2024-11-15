#!/usr/bin/env python

import setuptools

if __name__ == "__main__":
    setuptools.setup(    package_data={
        'taxon2wikipedia': ['data/*'],
    },)
