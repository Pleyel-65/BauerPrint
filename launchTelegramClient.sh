#!/bin/bash
SCRIPT=$(readlink -f $0)
SCRIPTPATH=`dirname $SCRIPT`
cd $SCRIPTPATH
echo $SCRIPTPATH
venv/bin/python3 script/telegram_client.py &
wait
