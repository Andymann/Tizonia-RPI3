#!/bin/bash


############################################################################
#
# Version 002    18.09.2020    Best to not boot with an attached Monitor
#
############################################################################
#
# Ideas: Using Souindmeter etc. to identify tracks that are played silently
#
############################################################################
# Add export DISPLAY=":0"
# to .bashrc
############################################################################

#Shortcuts for later call
PL_ROCKPARTY="37i9dQZF1DX8FwnYE6PRvL"
PL_SHYFX="0oUXKipJxVQQGPnf67l1V7"
PL_SUMMERROCK="37i9dQZF1DWYQE7bByhrad"
PL_METAL="37i9dQZF1DWTcqUzwhNmKv"
PL_INDIEROCK="3rCbh3pcaB6yQGmcB4I0yf"
PL_EINHORN="2JOsWhMtXZIb6E1qWAa3ry"

#For a "random" Playlist on startup
array[0]=$PL_ROCKPARTY
array[1]=$PL_SHYFX
array[2]=$PL_SUMMERROCK
array[3]=$PL_INDIEROCK
array[4]=$PL_EINHORN


#export DISPLAY=:0
while true; do
	ISRUNNING="0"
	size=${#array[@]}
	index=$(($RANDOM % $size))

	if [ $# -eq 0 ]
	then
		ACTIVEPL=${array[$index]}
		echo No argument given. Random Playlist $ACTIVEPL
	else
		ACTIVEPL=$1
		echo Playlist ID given as argument: $ACTIVEPL
	fi

	killall -TERM tizonia 2> /dev/null
	echo $DATE > tizonia.log
	echo STARTING TIZONIA ON RPI >> tizonia.log
	sleep 1
	while [ $ISRUNNING -eq 0 ]
	do
		# In order to keep CPU down we need to run Tizonia in another Terminal
		echo Running Tizonia with shuffled Playlist ID $ACTIVEPL >> tizonia.log
		lxterminal -e tizonia --spotify-playlist-id $ACTIVEPL -s &
		sleep 3

		#Query for a BASICALLY existing instance of Tizonia
		dbus-send --print-reply --dest=$(dbus-send --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus.ListNames|grep "org.mpris.MediaPlayer2.tizonia"| cut -d '"' -f 2) /com/aratelia/tiz/tizonia org.freedesktop.DBus.Properties.Get string:org.mpris.MediaPlayer2.Player string:"PlaybackStatus"|awk -F'"' '{ print $2 }' NF=NF RS= OFS= | grep -i -E 'PLAYING|PAUSED|STOPPED'
		
		if [ $? -eq 0 ]; then
			ISRUNNING="1"
			echo Tizonia started successfully >> tizonia.log
		else
			echo No instance of Tizonia running yet. Next Try in 3 >> tizonia.log
			sleep 5
			# Maybe some counter needed. after 10 tries there should be a fallback, message, etc.
			# maybe a mail or something
		fi
	done

	# Being here means there is a running instance of Tizonia.
	# It might take some time (up to ~1 minute) to gather all data and
	# actually start running.
	#
	# Dbus-Query then results in a 'Stopped'
	# This could be used to play some 'Please hold the line'-kind of track
	sleep 5
	VAR_STATUS=$(dbus-send --print-reply --dest=$(dbus-send --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus.ListNames|grep "org.mpris.MediaPlayer2.tizonia"| cut -d '"' -f 2) /com/aratelia/tiz/tizonia org.freedesktop.DBus.Properties.Get string:org.mpris.MediaPlayer2.Player string:"PlaybackStatus"|awk -F'"' '{ print $2 }' NF=NF RS= OFS= | grep -i -E 'PLAYING|PAUSED|STOPPED')
	echo Status: $VAR_STATUS

	while [ "$VAR_STATUS" = "Stopped" ]
	do
		echo "still stopped after 5 seconds"
		sleep 5
		VAR_STATUS=$(dbus-send --print-reply --dest=$(dbus-send --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus.ListNames|grep "org.mpris.MediaPlayer2.tizonia"| cut -d '"' -f 2) /com/aratelia/tiz/tizonia org.freedesktop.DBus.Properties.Get string:org.mpris.MediaPlayer2.Player string:"PlaybackStatus"|awk -F'"' '{ print $2 }' NF=NF RS= OFS= | grep -i -E 'PLAYING|PAUSED|STOPPED')
		# We should try another one after some attempts
	done

	echo Status is now $VAR_STATUS

	#Some kind of Hertbeat
	while [ "$VAR_STATUS" = "Playing" ]
	# Status does NOT change when being offline
	# Up to 30(+) seconds are buffered. Tizonia automagically gets back online
	# and proceeds streaming audio.
	# We might dewal with this situation in later releases.
	do
		sleep 10
		VAR_STATUS=$(dbus-send --print-reply --dest=$(dbus-send --print-reply --dest=org.freedesktop.DBus /org/freedesktop/DBus org.freedesktop.DBus.ListNames|grep "org.mpris.MediaPlayer2.tizonia"| cut -d '"' -f 2) /com/aratelia/tiz/tizonia org.freedesktop.DBus.Properties.Get string:org.mpris.MediaPlayer2.Player string:"PlaybackStatus"|awk -F'"' '{ print $2 }' NF=NF RS= OFS= | grep -i -E 'PLAYING|PAUSED|STOPPED')
		echo "Heartbeat Status:" $VAR_STATUS
	done

	echo TIZONIA STOPPED. Restarting in 10 seconds
	sleep 10
done
