#!/bin/bash
SCRIPT=$(readlink -f $0)
SCRIPTPATH=`dirname $SCRIPT`
cd $SCRIPTPATH
echo $SCRIPTPATH
.venv/Scripts/python.exe script/main.py