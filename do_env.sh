#!/bin/sh

# Make sure python-virtualenv and python-pip have been installed
# Run this from the root of the project

virtualenv env
pip install -E env/ -r ./stable-env.txt

