import dbus
import re
import psutil
import threading
import time
import subprocess
import RPi.GPIO as GPIO
import xml.etree.ElementTree as ET

from random import randrange
from threading import Timer
from urllib.request import urlopen
from pygame import mixer

lst_playlist = []


class RepeatedTimer(object):
    def __init__(self, interval, function, *args, **kwargs):
        self._timer = None
        self.interval = interval
        self.function = function
        self.args = args
        self.kwargs = kwargs
        self.is_running = False
        self.start()

    def _run(self):
        self.is_running = False
        self.start()
        self.function(*self.args, **self.kwargs)

    def start(self):
        if not self.is_running:
            self._timer = Timer(self.interval, self._run)
            self._timer.start()
            self.is_running = True

    def stop(self):
        self._timer.cancel()
        self.is_running = False


def hello(name):
    print("Hello %s!" % name)


def getPlayer():
    player = None
    try:
        bus = dbus.SessionBus()
        for service in bus.list_names():
            if re.match('org.mpris.MediaPlayer2.tizonia.', service):
                player = dbus.SessionBus().get_object(service, '/com/aratelia/tiz/tizonia')
    finally:
        return player


def killTizonia():
    PROCNAME = "tizonia"
    for proc in psutil.process_iter():
        if proc.name() == PROCNAME:
            proc.kill()


def startTizonia(playlistID):
    # Reset Timer
    t = time.time()+23

    mixer.music.play(-1)
    print('Starting with Playlist ' + lst_playlist[playlistID])
    output = subprocess.call(
        'lxterminal -e tizonia --spotify-playlist-id ' + lst_playlist[playlistID] + ' -s &', cwd='/home/pi/', shell=True)
    print(output)


def doIfHigh(channel):
    # Zugriff auf Variable i ermöglichen
    # global i
    # Wenn Eingang HIGH ist, Ausgabe im Terminal erzeugen
    print("Eingang " + str(channel) + " HIGH")
    global sCmd
    if channel == 11:
        sCmd = 'n'
    if channel is 8:
        print('Playlist Index 0')
        sCmd = 'p0'
    if channel is 10:
        print('Playlist Index 1')
        sCmd = 'p1'
    if channel is 12:
        print('Playlist Index 2')
        sCmd = 'p2'
    if channel is 16:
        print('Playlist Index 3')
        sCmd = 'p3'
    if channel is 18:
        print('Playlist Index 4')
        sCmd = 'p4'


try:
    var_url = urlopen(
        'https://raw.githubusercontent.com/Andymann/Tizonia-RPI3/master/tizonia.xml')
    tree = ET.parse(var_url)

    root = tree.getroot()
    print('Playlist IDs:')

    if len(root) >= 5:
        print('XML ist gross genug')

    for playlist in root.findall('playlist'):
        name = playlist.get('name')
        plid = playlist.find('id').text
        print(name + "  " + plid)
        lst_playlist.append(plid)
except:
    print('Error while parsing xml from web')

t = time.time()
GPIO.setmode(GPIO.BOARD)

GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(8, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(12, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

GPIO.add_event_detect(11, GPIO.RISING, callback=doIfHigh, bouncetime=1000)
GPIO.add_event_detect(8, GPIO.RISING, callback=doIfHigh, bouncetime=1000)
GPIO.add_event_detect(10, GPIO.RISING, callback=doIfHigh, bouncetime=1000)
GPIO.add_event_detect(12, GPIO.RISING, callback=doIfHigh, bouncetime=1000)
GPIO.add_event_detect(16, GPIO.RISING, callback=doIfHigh, bouncetime=1000)
GPIO.add_event_detect(18, GPIO.RISING, callback=doIfHigh, bouncetime=1000)


idActive = -1


mixer.init()
mixer.music.load('/home/pi/Music/jeopardy.mp3')
# mixer.music.play(-1)

sCmd = 'NONO'
while True:

    if time.time()-t > 4:
        # run your task here every n seconds
        t = time.time()
        if not getPlayer() is None:
            try:
                stat = getPlayer().Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus',
                                       dbus_interface='org.freedesktop.DBus.Properties')
                print(stat)
                if 'Playing' in stat:
                    # mixer.music.fadeout()
                    # mixer.music.rewind()
                    mixer.music.stop()

            except Exception as err:
                print('Exception:')
        else:
            print('Interval query: Tizonia not running')
            if idActive is -1:
                ir = randrange(5)
                print('picking random playlist:' + str(ir))
                startTizonia(ir)
            else:
                print(
                    'There is an already selected Playlist. Gonna try with Playlist ID ' + str(idActive))
                startTizonia(idActive)

    # sCmd = 'T'  # (input())
    if sCmd in ['n1', 'N1']:
        bus = dbus.SessionBus()
        for service in bus.list_names():
            if re.match('org.mpris.MediaPlayer2.tizonia.', service):
                player = dbus.SessionBus().get_object(service, '/com/aratelia/tiz/tizonia')
                player.Next(dbus_interface='org.mpris.MediaPlayer2.Player')
    if sCmd in ['k1', 'K1']:
        bus = dbus.SessionBus()
        for service in bus.list_names():
            if re.match('org.mpris.MediaPlayer2.tizonia.', service):
                player = dbus.SessionBus().get_object(service, '/com/aratelia/tiz/tizonia')
                player.Kill(dbus_interface='org.mpris.MediaPlayer2.Player')
    if sCmd in ['v1', 'V1']:
        bus = dbus.SessionBus()
        for service in bus.list_names():
            if re.match('org.mpris.MediaPlayer2.tizonia.', service):
                player = dbus.SessionBus().get_object(service, '/com/aratelia/tiz/tizonia')
                volume = player.Get('org.mpris.MediaPlayer2.Player', 'Volume',
                                    dbus_interface='org.freedesktop.DBus.Properties')
                print(volume)
    if sCmd in ['n', 'N']:
        print('Command: NEXT')
        if not getPlayer() is None:
            getPlayer().Next(dbus_interface='org.mpris.MediaPlayer2.Player')
        sCmd = 'NONO'
    if sCmd in ['v', 'V']:
        if not getPlayer is None:
            vol = getPlayer().Get('org.mpris.MediaPlayer2.Player', 'Volume',
                                  dbus_interface='org.freedesktop.DBus.Properties')
            print(vol)
            sCmd = 'NONO'
    if sCmd in ['q', 'Q']:
        # print("Query")
        if not getPlayer() is None:
            stat = getPlayer().Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus',
                                   dbus_interface='org.freedesktop.DBus.Properties')
            print(stat)
            # if not stat.upper() in ['PLAYING', 'STOPPED', 'PAUSED']:
            #    print('Tizonia not running')
        else:
            print('Tizonia not running')
            sCmd = 'NONO'
    if sCmd in ['x', 'X']:
        killTizonia()
        sCmd = 'NONO'

    if sCmd in ['p0', 'P0']:
        sCmd = 'NONO'
        # global idActive
        idActive = 0
        killTizonia()
        time.sleep(2.3)
        startTizonia(0)
    if sCmd in ['p1', 'P1']:
        sCmd = 'NONO'
        # global idActive
        idActive = 1
        killTizonia()
        time.sleep(2.3)
        startTizonia(1)
    if sCmd in ['p2', 'P2']:
        sCmd = 'NONO'
        # global idActive
        idActive = 2
        killTizonia()
        time.sleep(2.3)
        startTizonia(2)
    if sCmd in ['p3', 'P3']:
        sCmd = 'NONO'
        # global idActive
        idActive = 3
        killTizonia()
        time.sleep(2.3)
        startTizonia(3)
    if sCmd in ['p4', 'P4']:
        sCmd = 'NONO'
        # global idActive
        idActive = 4
        killTizonia()
        time.sleep(2.3)
        startTizonia(4)
    time.sleep(.1)
