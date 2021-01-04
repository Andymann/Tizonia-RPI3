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
    print('Teminating Tizonia ...')
    GPIO.output(13, 1)  # OFF
    PROCNAME = "tizonia"
    for proc in psutil.process_iter():
        if proc.name() == PROCNAME:
            proc.kill()
            print('Tizonia process killed')


def isRunning():
    PROCNAME = "tizonia"
    for proc in psutil.process_iter():
        if proc.name() == PROCNAME:
            print("isRunning: True")
            GPIO.output(13, 0)  # ON
            return True
    print("isRunning: False")
    return False


def startTizonia(playlistID):
    # Reset Timer
    global t
    t = time.time()+4
    print('starting Fahrstuhlmusik')
    # mixer.sound.play(-1)
    # mixer.Channel(0).play(-1)
    mixer.Channel(0).play('/home/pi/Music/jeopardy.mp3', -1)
    print('Starting with Playlist ' + lst_playlist[playlistID])
    output = subprocess.call(
        'lxterminal -e tizonia --spotify-playlist-id ' + lst_playlist[playlistID] + ' -s &', cwd='/home/pi/', shell=True)
    print(output)
    print('Tizonia started...')


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

global t
t = time.time()
GPIO.setmode(GPIO.BOARD)

GPIO.setup(11, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(8, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(10, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(12, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(16, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
GPIO.setup(18, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# ----GREEN Led
GPIO.setup(13, GPIO.OUT)
GPIO.output(13, 1)  # OFF

GPIO.add_event_detect(11, GPIO.RISING, callback=doIfHigh, bouncetime=5000)
GPIO.add_event_detect(8, GPIO.RISING, callback=doIfHigh, bouncetime=5000)
GPIO.add_event_detect(10, GPIO.RISING, callback=doIfHigh, bouncetime=5000)
GPIO.add_event_detect(12, GPIO.RISING, callback=doIfHigh, bouncetime=5000)
GPIO.add_event_detect(16, GPIO.RISING, callback=doIfHigh, bouncetime=5000)
GPIO.add_event_detect(18, GPIO.RISING, callback=doIfHigh, bouncetime=5000)


idActive = -1


mixer.init()
# channel1 = pygame.mixer.Channel(0) # argument must be int
# sound1 = pygame.mixer.Sound('/home/pi/Music/jeopardy.mp3')

# channel1.play(sound1, loops = -1)
# pygame.mixer.find_channel().play(sound1)

# mixer.music.load('/home/pi/Music/jeopardy.mp3')


ir = randrange(5)
print('Autostart. picking random playlist:' + str(ir))
startTizonia(ir)

sCmd = 'NONO'
while True:

    if time.time()-t > 4:
        # run your task here every n seconds
        t = time.time()
        # if not getPlayer() is None:
        #    try:
        #        stat = getPlayer().Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus',
        #                               dbus_interface='org.freedesktop.DBus.Properties')
        #        print(stat)
        #        if 'Playing' in stat:
        #            mixer.music.stop()
        #
        #    except Exception as err:
        #        print('Exception:')
        if isRunning():
            try:
                stat = getPlayer().Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus',
                                       dbus_interface='org.freedesktop.DBus.Properties')
                print(stat)
                if 'Playing' in stat:
                    print('Stopping Fahrstuhlmusik...')
                    # mixer.music.stop()
                    mixer.Channel(0).stop()

            except Exception as err:
                print('Exception while querying Tizonia instance:')
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
    if sCmd in ['n', 'N']:
        print('Command: NEXT')
        if not getPlayer() is None:
            getPlayer().Next(dbus_interface='org.mpris.MediaPlayer2.Player')
        # global sCmd
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
        global sCMD
        sCmd = 'NONO'

    if sCmd in ['p0', 'P0']:
        # global sCMD
        sCmd = 'NONO'
        idActive = 0
        killTizonia()
        time.sleep(2.3)
        startTizonia(0)
    if sCmd in ['p1', 'P1']:
        # global sCMD
        sCmd = 'NONO'
        idActive = 1
        killTizonia()
        time.sleep(2.3)
        startTizonia(1)
    if sCmd in ['p2', 'P2']:
        # global sCMD
        sCmd = 'NONO'
        idActive = 2
        killTizonia()
        time.sleep(2.3)
        startTizonia(2)
    if sCmd in ['p3', 'P3']:
        # global sCMD
        sCmd = 'NONO'
        idActive = 3
        killTizonia()
        time.sleep(2.3)
        startTizonia(3)
    if sCmd in ['p4', 'P4']:
        # global sCMD
        sCmd = 'NONO'
        idActive = 4
        killTizonia()
        time.sleep(2.3)
        startTizonia(4)

    time.sleep(.1)
