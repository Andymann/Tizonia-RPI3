from pygame import mixer
from urllib.request import urlopen
from threading import Timer
from random import randrange
import xml.etree.ElementTree as ET
import RPi.GPIO as GPIO
import subprocess
import time
import threading
import psutil
import re
import dbus
import sys

TIMERVALUE = .01
STATE_NONE = -2
STATE_UNDEFINED = -1
STATE_PLAYING = 1
STATE_BOOTING = 2
STATE_LOADINGPLAYLIST = 3
STATE_STARTINGTIZONIA = 4
STATE_STOPPED = 5

iLastButton = -1
iCounter = 0
iBlinkCounter = 0
bLed = True
iState = STATE_UNDEFINED
iErrorCounter = 0

lst_playlist = []
iActivePlaylist = -1
iTimerCounter = -1


def initGpio():
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

    GPIO.add_event_detect(11, GPIO.RISING, callback=doIfHigh, bouncetime=500)
    GPIO.add_event_detect(8, GPIO.RISING, callback=doIfHigh, bouncetime=500)
    GPIO.add_event_detect(10, GPIO.RISING, callback=doIfHigh, bouncetime=500)
    GPIO.add_event_detect(12, GPIO.RISING, callback=doIfHigh, bouncetime=500)
    GPIO.add_event_detect(16, GPIO.RISING, callback=doIfHigh, bouncetime=500)
    GPIO.add_event_detect(18, GPIO.RISING, callback=doIfHigh, bouncetime=500)


def doIfHigh(channel):
    global iLastButton
    iLastButton = channel


def buttonPressed(pButton):
    global iActivePlaylist
    # print('buttonPressed:' + str(pButton))
    if pButton == 11:
        if not getPlayer() is None:
            getPlayer().Next(dbus_interface='org.mpris.MediaPlayer2.Player')
        else:
            print('buttonPressed: Skip aber Tizonia ist nicht gestartet')
            # Problem
            sys.exit()
    if pButton == 8:
        iActivePlaylist = 0
        killTizonia()
        startTizonia(iActivePlaylist)
    if pButton == 10:
        iActivePlaylist = 1
        killTizonia()
        startTizonia(iActivePlaylist)
    if pButton == 12:
        iActivePlaylist = 2
        killTizonia()
        startTizonia(iActivePlaylist)
    if pButton == 16:
        iActivePlaylist = 3
        killTizonia()
        startTizonia(iActivePlaylist)
    if pButton == 18:
        iActivePlaylist = 4
        killTizonia()
        startTizonia(iActivePlaylist)


def processState():
    global iState
    global iErrorCounter
    global bLed
    if iState == STATE_UNDEFINED:
        global iBlinkCounter
        iBlinkCounter = iBlinkCounter + 1
        if iBlinkCounter == 100:
            iBlinkCounter = 0
            bLed = not bLed
            GPIO.output(13, bLed)
    if iState == STATE_LOADINGPLAYLIST:
        iBlinkCounter = iBlinkCounter + 1
        if iBlinkCounter == 25:
            iBlinkCounter = 0
            bLed = not bLed
            GPIO.output(13, bLed)
    if iState == STATE_STOPPED:
        bLed = False
        print('processState:Stopped')
        GPIO.output(13, not bLed)  # Inverse Logik
        iState = STATE_NONE
    if iState == STATE_STARTINGTIZONIA:
        # Tizonia wurde aufgerufen, die Fahrstuhlmusik spielt.
        # Es kann jetzt beliebig lange dauern, bis die
        # Playlist geladen wurde und die Audiowiedergabe beginnt.
        #
        # Bis dahin ergibt eine Query auf den Player das Ergebnis 'Stopped', danach 'Playing'
        global iTimerCounter
        if iTimerCounter < 100:
            iTimerCounter = iTimerCounter + 1
        else:
            # print('processState: starting. Zeit fuer Query')
            bLed = not bLed
            GPIO.output(13, bLed)
            iTimerCounter = 0
            if not getPlayer() is None:
                stat = getPlayer().Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus',
                                       dbus_interface='org.freedesktop.DBus.Properties')
                # print('status:' + str(stat))  # z.B. 'Playing
                if 'Stopped' in str(stat):
                    pass
                if 'Playing' in str(stat):
                    # print('Tizonia spielt Musik. Stoppe Fahrstuhlmusik')
                    mixer.Channel(0).stop()
                    bLed = True
                    GPIO.output(13, not bLed)
                    iState = STATE_PLAYING
                iErrorCounter = 0
            else:
                print('Tizonia not running')
                # Das kann passieren, wenn der Aufruf und die Abfrage zeitlich she rnah beieinander sind.
                # Wenn das mehr als zweimal nacheinander geschieht, wird es kritisch.
                iErrorCounter = iErrorCounter + 1
    if iState == STATE_PLAYING:
        # Alle 2 Sekunden oder so mal schauen, was gerade so los ist
        if iTimerCounter < 200:
            iTimerCounter = iTimerCounter + 1
        else:
            iTimerCounter = 0
            if not getPlayer() is None:
                stat = getPlayer().Get('org.mpris.MediaPlayer2.Player', 'PlaybackStatus',
                                       dbus_interface='org.freedesktop.DBus.Properties')
                # print('MODE_PLAYING. Echter Status:' +
                #      str(stat))  # z.B. 'Playing
                iErrorCounter = 0
            else:
                print('MODE_PLAYING aber Tizonia laeuft nicht!')
                # Hier haben wir theoretisch ein Problem
                # Wir beenden, das Script drumherum kuemmert sich um einen Neuistart nach 5 Sekunden
                iErrorCounter = iErrorCounter + 1


def getXml():
    global iState
    iState == STATE_LOADINGPLAYLIST
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
            iState = STATE_UNDEFINED
            return True
        else:
            print('XML zu klein')
            iState = STATE_UNDEFINED
            return False
    except:
        print('Error while parsing xml from web')
        iState = STATE_UNDEFINED
        return True


def killTizonia():
    print('Terminating Tizonia ...')
    GPIO.output(13, 1)  # OFF
    PROCNAME = "tizonia"
    for proc in psutil.process_iter():
        if proc.name() == PROCNAME:
            proc.kill()
            print('Tizonia process killed')
    global iState
    iState = STATE_STOPPED
    # print('done')


def getPlayer():
    player = None
    try:
        bus = dbus.SessionBus()
        for service in bus.list_names():
            if re.match('org.mpris.MediaPlayer2.tizonia.', service):
                player = dbus.SessionBus().get_object(service, '/com/aratelia/tiz/tizonia')
    finally:
        return player


def startTizonia(playlistID):
    global iState
    iState = STATE_STARTINGTIZONIA
    # print('starting Fahrstuhlmusik')
    sound1 = mixer.Sound('/home/pi/Music/jeopardy.wav')
    mixer.Channel(0).play(sound1, -1)
    print('Starting with Playlist ' + lst_playlist[playlistID])
    output = subprocess.call(
        'lxterminal -e tizonia --spotify-playlist-id ' + lst_playlist[playlistID] + ' -s &', cwd='/home/pi/', shell=True)
    # wenn output == 0 ist erstmal alles in Ordnung
    # es kann aber jetzt noch dauern, bis die Playlist eingelesen wurde und die
    # Audiowiedergabe beginnt.
    print('Tizonia started. Status:' + str(output))


def queryButtons():
    global iLastButton
    global iCounter
    if not iLastButton == -1:
        iCounter = iCounter + 1
        if iCounter == 15:
            if GPIO.input(iLastButton) == 1:
                tmpButton = iLastButton
                iLastButton = -1
                buttonPressed(tmpButton)
            else:
                print('Button released oder Fehlalarm')
                iCounter = 0
            iLastButton = -1
            iCounter = 0


print('Program started...')
mixer.init()
initGpio()
iCounter = 0
iErrorCounter = 0
iLastButton = -1
if getXml() == True:
    iActivePlaylist = randrange(5)
    print('Autostart. picking random playlist:' + str(iActivePlaylist))
    killTizonia()
    startTizonia(iActivePlaylist)
    while True:
        queryButtons()
        processState()
        time.sleep(TIMERVALUE)
        if iErrorCounter > 5:
            killTizonia()
            sys.exit()
