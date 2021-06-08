#!/bin/bash
#echo running autostart > autostart.log
rm -r "/var/tmp/tizonia-pi-spotify-"*
pkill tizonia

DIR="$( cd "$( dirname "$0" )" && pwd )"
#OID=$(wget -q -nv -O - https://raw.githubusercontent.com/Andymann/Tizonia-RPI3/master/updateID.txt >/dev/null 2>/dev/null | grep -v '#')
OID=$(wget -q -nv -O - https://raw.githubusercontent.com/Andymann/Tizonia-RPI3/master/updateID.txt 2>/dev/null | grep -v '#')
LID=$(grep -v '#' $DIR/updateID.txt)
if [ ! -z "$OID" ]; then
	if (test $OID -eq $LID); then
		echo "gleich"	
		#values are identical: No  update
	else
		#echo "ungleich"
		#values differ: update required
		rm $DIR/tizonia.py.old >/dev/null 2>/dev/null
		mv $DIR/tizonia.py $DIR/tizonia.py.old >/dev/null 2>/dev/null
		wget --directory-prefix=$DIR https://raw.githubusercontent.com/Andymann/Tizonia-RPI3/master/tizonia.py

		#Remove previous updateID.txt and fetch the updated one
		rm $DIR/updateID.txt >/dev/null 2>/dev/null
		wget --directory-prefix=$DIR https://raw.githubusercontent.com/Andymann/Tizonia-RPI3/master/updateID.txt
	fi
else
	echo "Variable nicht gesetzt oder offline"
	#probably offline
fi


while true; do
	python3 $DIR/tizonia.py
	sleep 5
done
