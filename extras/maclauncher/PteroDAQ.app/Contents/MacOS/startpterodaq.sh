#!/usr/bin/env bash -i
PYBIN=`type -P python3`
if [ -z $PYBIN ]; then PYBIN=`type -P python2`; fi
if [ -z $PYBIN ]; then PYBIN=`type -P python`; fi
if [ -z $PYBIN ]; then exit; fi
rm -f $(dirname "$0")/guipython
ln -s `$PYBIN -c 'import sys; print(sys.prefix)'`/Resources/Python.app/Contents/MacOS/Python $(dirname "$0")/guipython
$(dirname "$0")/guipython $(dirname "$0")/../../../../../daq
