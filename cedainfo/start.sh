#!/bin/bash
#
# Starts cedainfo Django application. If it is already running then shuts down running instance and restarts.
#
# Script is a modified version of the script found at http://docs.djangoproject.com/en/dev/howto/deployment/fastcgi/
#
PROJDIR="/home/badc/software/infrastructure/cedainfo/cedainfo"
PIDFILE="$PROJDIR/cedainfo.pid"
SOCKET="/var/www/fastcgi/cedadb.sock"

cd $PROJDIR
if [ -f $PIDFILE ]; then
    kill `cat -- $PIDFILE`
    rm -f -- $PIDFILE
fi


/usr/local/bin/python2.5 manage.py runfcgi socket=$SOCKET daemonize=true pidfile=$PIDFILE
chmod 770 $SOCKET
