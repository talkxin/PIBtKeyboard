#!/usr/bin/python
#
# YAPTB Bluetooth keyboard emulator DBUS Service
#
# Adapted from
# www.linuxuser.co.uk/tutorials/emulate-bluetooth-keyboard-with-the-raspberry-pi
#
#

from __future__ import absolute_import, print_function

from optparse import OptionParser, make_option
import os
import sys
import uuid
import dbus
import dbus.service
import dbus.mainloop.glib
import time
import bluetooth
from bluetooth import *
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
import ConfigParser
import ast
import threading


#
# define a bluez 5 profile object for our keyboard
#
class BTKbBluezProfile(dbus.service.Object):
    fd = -1

    @dbus.service.method("org.bluez.Profile1", in_signature="", out_signature="")
    def Release(self):
        print("Release")
        mainloop.quit()

    @dbus.service.method("org.bluez.Profile1", in_signature="", out_signature="")
    def Cancel(self):
        print("Cancel")

    @dbus.service.method("org.bluez.Profile1", in_signature="oha{sv}", out_signature="")
    def NewConnection(self, path, fd, properties):
        self.fd = fd.take()
        print("NewConnection(%s, %d)" % (path, self.fd))
        for key in properties.keys():
            if key == "Version" or key == "Features":
                print("  %s = 0x%04x" % (key, properties[key]))
            else:
                print("  %s = %s" % (key, properties[key]))

    @dbus.service.method("org.bluez.Profile1", in_signature="o", out_signature="")
    def RequestDisconnection(self, path):
        print("RequestDisconnection(%s)" % (path))

        if (self.fd > 0):
            os.close(self.fd)
            self.fd = -1

    def __init__(self, bus, path):
        dbus.service.Object.__init__(self, bus, path)


#
# create a bluetooth device to emulate a HID keyboard,
# advertize a SDP record using our bluez profile class
#
class BTKbDevice(threading.Thread):
    # change these constants
    # MY_ADDRESS="00:1A:7D:DA:71:13"
    MY_DEV_NAME = "PiZW_BTKb"
    KEYBOARD_HOME = os.path.abspath(os.path.join(sys.path[0], os.path.pardir))
    # define some constants
    P_CTRL = 17  # Service port - must match port configured in SDP record
    P_INTR = 19  # Service port - must match port configured in SDP record#Interrrupt port
    # dbus path of  the bluez profile we will create
    PROFILE_DBUS_PATH = "/bluez/btservice/btkb_profile"
    # file path of the sdp record to laod
    SDP_RECORD_PATH = sys.path[0] + "/sdp_record.xml"
    BLUE_INI = KEYBOARD_HOME + "/blue.ini"
    UUID = "00001124-0000-1000-8000-00805f9b34fb"

    def __init__(self, default):

        print("Setting up BT device")
        self.default = default
        self.init_bt_device()
        self.init_bluez_profile()
        threading.Thread.__init__(self)

    def run(self):
        self.listen()

    # configure the bluetooth hardware device
    def init_bt_device(self):
        print("Configuring for name "+BTKbDevice.MY_DEV_NAME)
        # set the device class to a keybord and set the name
        os.system("hciconfig hcio class 0x002540")
        os.system("hciconfig hcio name " + BTKbDevice.MY_DEV_NAME)
        # make the device discoverable
        os.system("hciconfig hcio piscan")

    # set up a bluez profile to advertise device capabilities from a loaded service record
    def init_bluez_profile(self):

        print("Configuring Bluez Profile")
        # setup profile options
        service_record = self.read_sdp_service_record()

        opts = {
            "ServiceRecord": service_record,
            "Role": "server",
            "RequireAuthentication": False,
            "RequireAuthorization": False
        }

        # retrieve a proxy for the bluez profile interface
        bus = dbus.SystemBus()
        manager = dbus.Interface(bus.get_object(
            "org.bluez", "/org/bluez"), "org.bluez.ProfileManager1")
        profile = BTKbBluezProfile(bus, BTKbDevice.PROFILE_DBUS_PATH)
        manager.RegisterProfile(
            BTKbDevice.PROFILE_DBUS_PATH, BTKbDevice.UUID, opts)
        print("Profile registered ")

    # read and return an sdp record from a file

    def read_sdp_service_record(self):
        print("Reading service record")
        try:
            fh = open(BTKbDevice.SDP_RECORD_PATH, "r")
        except:
            sys.exit("Could not open the sdp record. Exiting...")

        return fh.read()

    # listen for incoming client connections
    # ideally this would be handled by the Bluez 5 profile
    # but that didn't seem to work

    def listen(self):
        if(self.default == "default"):
            mac = self.getMac()
            if mac is None:
                print("research")
                self.research()
            else:
                self.relisten(mac)
        elif(self.default == "search"):
            self.research()
        else:
            self.relisten(self.default)

    def research(self):
        print("Waiting for research")
        self.scontrol = BluetoothSocket(L2CAP)
        self.sinterrupt = BluetoothSocket(L2CAP)
        # bind these sockets to a port - port zero to select next available
        self.scontrol.bind(("", self.P_CTRL))
        self.sinterrupt.bind(("", self.P_INTR))
        # Start listening on the server sockets
        self.scontrol.listen(1)  # Limit of 1 connection
        self.sinterrupt.listen(1)
        self.ccontrol, cinfo = self.scontrol.accept()
        self.setMac(cinfo[0])
        # set now connect
        self.setRuner(cinfo[0])
        print("==============================")
        print("Got a connection on the control channel from " + cinfo[0])
        self.scontrol.close()
        self.sinterrupt.close()
        self.relisten(cinfo[0])

    def relisten(self, cinfo):
        try:
            print("Waiting for connections")
            self.ccontrol = BluetoothSocket(L2CAP)
            self.cinterrupt = BluetoothSocket(L2CAP)
            self.ccontrol.connect((cinfo, self.P_CTRL))
            self.cinterrupt.connect((cinfo, self.P_INTR))
            print("--------------------------")
            print("Got a connection on the control channel from " + cinfo)
            # set now connect
            self.setRuner(cinfo)
        except BluetoothError as e:
            code = e.message[1:len(e.message)-1].split(",")[0]
            if(code == "112"):
                time.sleep(3)
                self.relisten(cinfo)
            elif(code == "52"):
                self.delmac()
                self.listen()
            else:
                self.delmac()
                self.listen()

    def setRuner(self, mac):
        conf = ConfigParser.ConfigParser()
        conf.read(BTKbDevice.BLUE_INI)
        conf.set("RUNER", "now", mac)
        conf.write(open(BTKbDevice.BLUE_INI, "w"))

    def getMac(self, macpath="default"):
        try:
            conf = ConfigParser.ConfigParser()
            conf.read(BTKbDevice.BLUE_INI)
            return conf.get("BIND", macpath)
        except Exception:
            return None

    def setMac(self, mac):
        deviceMac = self.getMac("device")
        defaultMac = self.getMac()
        macname = "default"
        # if ini file is not exists
        if defaultMac is None or defaultMac == mac:
            macname = "default"
            deviceMac = mac
        else:
            macname = "device"
            if deviceMac is None:
                deviceMac = []
            else:
                deviceMac = ast.literal_eval(deviceMac)
            if deviceMac.count(mac) < 1:
                deviceMac.append(mac)

        conf = ConfigParser.ConfigParser()
        conf.read(BTKbDevice.BLUE_INI)
        if not conf.has_section("BIND"):
            conf.add_section("BIND")
        conf.set("BIND", macname, str(deviceMac))
        conf.write(open(BTKbDevice.BLUE_INI, "w"))

    def delmac(self, macname="default"):
        conf = ConfigParser.ConfigParser()
        conf.read(BTKbDevice.BLUE_INI)
        conf.remove_option("BIND", macname)
        conf.write(open(BTKbDevice.BLUE_INI, "w"))

    # send a string to the bluetooth host machine

    def send_string(self, message):
        self.cinterrupt.send(message)


# define a dbus service that emulates a bluetooth keyboard
# this will enable different clients to connect to and use
# the service
class BTKbService(dbus.service.Object):

    def __init__(self, default):
        print("Setting up service")
        # set up as a dbus service
        bus_name = dbus.service.BusName(
            "org.btservice.keyboard", bus=dbus.SystemBus())
        dbus.service.Object.__init__(self, bus_name, "/org/btservice/keyboard")
        # create and setup our device
        self.device = BTKbDevice(default)
        # start listening for connections
        self.device.start()

    @dbus.service.method('org.btservice.keyboard', in_signature='yay')
    def send_keys(self, modifier_byte, keys):
        try:
            cmd_str = ""
            cmd_str += chr(0xA1)
            cmd_str += chr(0x01)
            cmd_str += chr(modifier_byte)
            cmd_str += chr(0x00)
            count = 0
            for key_code in keys:
                if(count < 6):
                    cmd_str += chr(key_code)
                count += 1

            self.device.send_string(cmd_str)
        except Exception as e:
            print(e)

    @dbus.service.method('org.btservice.keyboard')
    def relisten(self):
        self.device.listen()


def setPID(pid=os.getpid()):
    conf = ConfigParser.ConfigParser()
    conf.read(BTKbDevice.BLUE_INI)
    if not conf.has_section("RUNER"):
        conf.add_section("RUNER")
    conf.set("RUNER", "service", os.getpid())
    conf.write(open(BTKbDevice.BLUE_INI, "w"))


# main routine
if __name__ == "__main__":
    # we an only run as root
    if not os.geteuid() == 0:
        sys.exit("Only root can run this script")
    default = None
    if len(sys.argv) > 1:
        default = str(sys.argv[1])
    setPID()
    DBusGMainLoop(set_as_default=True)
    myservice = BTKbService(default)
    mainloop = GLib.MainLoop()
    mainloop.run()
