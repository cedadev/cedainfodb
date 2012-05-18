#!/bin/bash
#
# Script to start and stop cedainfodb. This is suitable as using as an "init.d" script, but must be run as user 'badc'
#

PYTHON="/home/badc/software/infrastructure/cedainfo_releases/venv/bin/python"
PROJDIR="/home/badc/software/infrastructure/cedainfo/cedainfo"
PIDFILE="$PROJDIR/cedainfo.pid"
SOCKET="/var/www/fastcgi/cedadb.sock"
LOG_DIR="/var/www/cedainfo_site/logs"

APP="cedainfo Django server"

cd $PROJDIR

stop ()
{
   if [ -f $PIDFILE ]; then
       echo "stopping $APP..."
       kill `cat -- $PIDFILE`
       rm -f -- $PIDFILE
       rm -f $SOCKET
   else
      echo "Looks like $APP is not running (pid file $PIDFILE not found)"      
   fi
}

start ()
{

   if [ -f $PIDFILE ]; then
      stop
   fi
   
      umask 007

      CMD="$PYTHON manage.py runfcgi socket=$SOCKET outlog=$LOG_DIR/django.out errlog=$LOG_DIR/django.err daemonize=true pidfile=$PIDFILE"

#
#     Run as user 'badc'
#
      if [ $(whoami) != 'badc' ]
      then
         su badc -c "$CMD" ;
      else
         $CMD
      fi
      
      #
      # For some reason umask does not seem to work, so we wait a few seconds then change the permission on the created socket file
      #
      echo "Please wait..."
      sleep 10
      chown badc:badcint $SOCKET
      chmod 770 $SOCKET

      chown badc:badcint $PIDFILE
      exit 0


}


status ()
{

  if [ -f $PIDFILE ]; then
       echo "$APP is running with following pid:"
       pid=`cat -- $PIDFILE`
       echo $pid

  else
     echo "$APP NOT running (pid file $PIDFILE not found)"
     exit 0

  fi   
}

case "$1" in
  start)
    start
    ;;
  stop)
    stop
    ;;
  restart)
    stop
    start
    ;;
  status)
    status
    ;;
  *)
    echo "Usage: start|stop|restart|status"
esac
