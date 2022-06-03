#!/usr/bin/env python3
import rospy
import numpy as np
import struct
import pickle
import time
from digi.xbee.devices import DigiMeshDevice
from digi.xbee.exception import *
from digi.xbee.models.address import *
from digi.xbee.packets.base import DictKeys
from digi.xbee.packets.common import ATCommPacket, ATCommResponsePacket
from digi.xbee.models.mode import OperatingMode
from datetime import datetime
import os, sys
import pytest
import yaml

with open("xbee.yaml", 'r') as stream:
	try:
		vehicles = yaml.safe_load(stream)
		print(vehicles)

	except yaml.YAMLError as exc:
		print(exc)

PORT = "/dev/ttyUSB0"
BAUD_RATE = 115200
device = DigiMeshDevice(PORT, BAUD_RATE)
device.open(force_settings=True)

def xbee_connection(ADDRESS):
	pack = pickle.dumps( [] )
	try :
		device.send_data_64( XBee64BitAddress.from_hex_string(ADDRESS), pack)
		return True
	except:
		return False


def test():
	error = []
	for i,usage in enumerate(vehicles.values()):
		for address in usage.values():
			result = xbee_connection(address)
			if not result:
				print('nano', i+1, " xbee fail:" + "(" + address + ")")
				assert not result, "errors occured:\n{}".format("\n".join(error))
