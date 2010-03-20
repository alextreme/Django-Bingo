#!/bin/sh

# Remove cruft, de-SVN

rm -rf env
rm -r initial_data*.json
find -name '*.svn' -exec rm -rf {} \;
