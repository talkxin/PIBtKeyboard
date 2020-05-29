#!/usr/bin/python
#
# YAPTB Bluetooth keyboard emulation service
# keyboard copy client.
# Reads local key events and forwards them to the btk_server DBUS service
#
# Adapted from www.linuxuser.co.uk/tutorials/emulate-a-bluetooth-keyboard-with-the-raspberry-pi
#
#
import os  # used to all external commands
import sys  # used to exit the script
import dbus
import dbus.service
import dbus.mainloop.glib
import time
import evdev  # used to get input from the keyboard
from evdev import *
import keymap  # used to map evdev input to hid keodes
import threading
import ConfigParser
import ast


# Define a client to listen to local key events
class Keyboard(threading.Thread):

    def __init__(self, eventx):
        # save action
        self.action = []
        # special action 1
        self.action1 = [39, 224, 226, 227]
        # special action 2
        self.action2 = [46, 224, 226, 227]
        # the structure for a bt keyboard input report (size is 10 bytes)
        threading.Thread.__init__(self)
        self.state = [
            0xA1,  # this is an input report
            0x01,  # Usage report = Keyboard
            # Bit array for Modifier keys
            [0,  # Right GUI - Windows Key
                 0,  # Right ALT
                 0,  # Right Shift
                 0,  # Right Control
                 0,  # Left GUI
                 0,  # Left ALT
                 0,  # Left Shift
                 0],  # Left Control
            0x00,  # Vendor reserved
            0x00,  # rest is space for 6 keys
            0x00,
            0x00,
            0x00,
            0x00,
            0x00]

        print "setting up DBus Client"
        self.bus = dbus.SystemBus()
        # self.btkservice = self.bus.get_object('org.yaptb.btkbservice','/org/yaptb/btkbservice')
        # self.iface = dbus.Interface(self.btkservice,'org.yaptb.btkbservice')
        self.iface = self.bus.get_object(
            "org.btservice.keyboard", "/org/btservice/keyboard")

        print "waiting for keyboard"

        # keep trying to key a keyboard
        have_dev = False
        while have_dev == False:
            try:
                # try and get a keyboard - should always be event0 as
                # we're only plugging one thing in
                self.dev = InputDevice(eventx)
                have_dev = True
            except OSError:
                print "Keyboard not found, waiting 3 seconds and retrying"
                time.sleep(3)
            print "found a keyboard"

    def change_state(self, event):
        evdev_code = ecodes.KEY[event.code]
        modkey_element = keymap.modkey(evdev_code)

        if modkey_element > 0:
            if self.state[2][modkey_element] == 0:
                self.state[2][modkey_element] = 1
            else:
                self.state[2][modkey_element] = 0
        else:
            # Get the keycode of the key
            hex_key = keymap.convert(ecodes.KEY[event.code])
            # Loop through elements 4 to 9 of the inport report structure
            for i in range(4, 10):
                if self.state[i] == hex_key and event.value == 0:
                    # print "Code 0 so we need to depress it"
                    self.state[i] = 0x00
                elif self.state[i] == 0x00 and event.value == 1:
                    # print "if the current space if empty and the key is being pressed"
                    self.state[i] = hex_key
                    break

    def special_action(self, event):
        hex_key = keymap.convert(ecodes.KEY[event.code])
        if event.value == 0:
            self.action = []
        else:
            self.action.append(hex_key)
            self.action.sort()
            if cmp(self.action, self.action1) == 0:
                print "research"
                pid = self.getServicePID()
                if pid is not None:
                    os.system("kill -9 "+pid)
                os.system("sh "+os.getenv('__HOME')+"/start.sh search &")
                os.system("kill -9 "+str(os.getpid()))
            elif cmp(self.action, self.action2) == 0:
                print "next"
                nextmac = self.getNext()
                print(nextmac)
                pid = self.getServicePID()
                if pid is not None:
                    os.system("kill -9 "+pid)
                if nextmac is not None:
                    os.system("sh "+os.getenv('__HOME') +
                              "/start.sh "+self.getNext()+" &")
                else:
                    os.system("sh "+os.getenv('__HOME')+"/start.sh &")

                os.system("kill -9 "+str(os.getpid()))

    def getServicePID(self):
        try:
            conf = ConfigParser.ConfigParser()
            conf.read(os.getenv('__HOME') + "/blue.ini")
            return conf.get("RUNER", "service")
        except Exception:
            return None

    def getNext(self):
        try:
            conf = ConfigParser.ConfigParser()
            conf.read(os.getenv('__HOME') + "/blue.ini")
            nowmac = conf.get("RUNER", "now")
            default = conf.get("BIND", "default")
            device = conf.get("BIND", "device")
            if nowmac is None:
                return None
            elif device is None:
                return None
            else:
                ldevice = ast.literal_eval(device)
                ll = 0
                lens = len(ldevice)
                if nowmac != default:
                    ll = ldevice.index(nowmac)+1
                while True:
                    if ll < lens:
                        rmac = ldevice[ll]
                        ll = ll+1
                        return rmac
                    else:
                        return None

                return None
        except Exception:
            return None

    # poll for keyboard events

    def run(self):
        for event in self.dev.read_loop():
            # only bother if we hit a key and its an up or down event
            if event.type == ecodes.EV_KEY and event.value < 2:
                self.special_action(event)
                self.change_state(event)
                self.send_input()

    # forward keyboard events to the dbus service

    def send_input(self):
        try:
            bin_str = ""
            element = self.state[2]
            for bit in element:
                bin_str += str(bit)
            self.iface.send_keys(int(bin_str, 2), self.state[4:10])
        except Exception:
            print "keyboard Disconnect"
            self.iface.relisten()


def connect():
    kb0 = Keyboard("/dev/input/event0")
    kb0.start()
    kb2 = Keyboard("/dev/input/event2")
    kb2.start()


if __name__ == "__main__":
    while True:
        try:
            connect()
            print "Setting up keyboard"
            break
        except Exception:
            time.sleep(3)

    # time.sleep(sys.maxsize)
    led = open('/sys/class/leds/led0/brightness', 'w', buffering=0)
    while True:
        led.write('0')
        time.sleep(3)
        led.write('1')
        time.sleep(3)
