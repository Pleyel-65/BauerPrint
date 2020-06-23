#!/bin/bash
SCRIPT=$(readlink -f $0)
SCRIPTPATH=`dirname $SCRIPT`
cd $SCRIPTPATH
echo $SCRIPTPATH
venv/bin/python3 $SCRIPTPATH script/main.py