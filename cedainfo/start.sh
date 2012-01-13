#!/bin/bash
#
# Script to start and stop cedainfo Django server, suitable for use as an init.d script
#
### BEGIN INIT INFO
# Provides:			cedainfodb
# Required-Start:		
# Should-Start:			
# Should-Stop:			
# Required-Stop:		
# Default-Start:		3 5
# Default-Stop:			0 1 2 6
# Short-Description:		cedainfodb Django application
# Description:			Starts cedainfodb Django application
### END INIT INFO

PYTHON="/usr/local/bin/python2.7"
PROJDIR="/home/badc/software/infrastructure/cedainfo_releases/development/cedainfo"
PIDFILE="$PROJDIR/cedainfo.pid"
SOCKET="/var/www/fastcgi/cedadb_dev.sock"

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

      CMD="$PYTHON manage.py runfcgi socket=$SOCKET daemonize=true pidfile=$PIDFILE"
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
