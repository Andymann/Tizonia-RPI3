#!/bin/bash
echo running autostart > autostart.log
while true; do
        python3 tizonia.py
        sleep 5
done
