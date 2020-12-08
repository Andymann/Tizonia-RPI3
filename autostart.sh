#!/bin/bash
echo running autostart > autostart.log

OID=$(wget -q -nv -O - https://raw.githubusercontent.com/Andymann/Tizonia-RPI3/master/updateID.txt >/dev/null 2>/dev/null | grep -v '#')
LID=$(grep -v '#' updateID.txt)
if [ ! -z "$OID" ]; then
	if (test $OID -eq $LID); then 
		#echo "gleich"	
		#values are identical: No  update
	; else 
		#echo "ungleich"
		#values differ: update required
		rm tizonia.py.old >/dev/null 2>/dev/null
		mv tizonia.py tizonia.py.old >/dev/null 2>/dev/null
		https://raw.githubusercontent.com/Andymann/Tizonia-RPI3/master/tizonia.py

		#Remove previous updateID.txt and fetch the updated one
		rm updateID.txt >/dev/null 2>/dev/null
		wget https://raw.githubusercontent.com/Andymann/Tizonia-RPI3/master/updateID.txt
	;fi
; else
	#echo "Variable nicht gesetzt
	#probably offline
;fi


while true; do
        python3 tizonia.py
        sleep 5
done
