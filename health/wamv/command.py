import argparse
import json
import logging
import os
import time
import re
from datetime import datetime

from arg_robotics_tools import get_ip
from arg_robotics_tools import websocket_rosbridge as websocket
import sys

from collections import defaultdict
from typing import List, Set

from dt_shell import DTCommandAbs, dtslogger
from utils.table_utils import fill_cell, format_matrix

import threading

#from wand.image import Image
#from wand.drawing import Drawing

#import cv2
#import roslibpy
#from utils.duckiepond_utils import find_duckiepond_devices_yaml, dp_print_boats

REFRESH_HZ = 1.0

usage = """
## Basic usage

    Discovers Duckiepond robots in the xbee network.

    To find out more, use `dts duckiepond discover -h`.

        $ dts duckiepond discover [options]

"""


'''
global variables
'''
sensortowers = ['uav', 'wamv', '_lidartower', '_zedtower_left', '_zedtower_mid', '_zedtower_right']
#columns = ["H.B.","ZEDm","D435","LIDAR","mmWave","GPS","gripper"]
sensortower_status = {'uav': ['-1', '-1', '-1', '-1', '-1', '-1', '-1'], 'wamv': ['-1', '-1', '-1', '-1', '-1', '-1', '-1'], '_lidartower': ['-1', '-1', '-1', '-1', '-1', '-1', '-1'], '_zedtower_left': ['-1', '-1', '-1', '-1', '-1', '-1', '-1'], '_zedtower_mid': ['-1', '-1', '-1', '-1', '-1', '-1', '-1'], '_zedtower_right': ['-1', '-1', '-1', '-1', '-1', '-1', '-1']}
threads = []

'''
sensortower get status part
'''
def sensor_callback(message):
    name_id = message['data'].split('@')[0]
    sensortower_status[name_id] =  message['data'].split('@')[1].split(':')
    #print(sensortower_status)

def sensor_check(ip, sensor_tower_id):
    try:
        socket_sensor = websocket.ros_socket(ip, 9090)
        socket_sensor.subscriber('/health/' + sensor_tower_id, sensor_callback, 100)
    except:
        print('ERROR of connecting')

'''
roslibpy threading part
'''
for sensortower  in sensortowers:
    threads.append(threading.Thread(target = sensor_check, args = ('127.0.0.1', sensortower,)))
for i in range(len(threads)):
    threads[i].start()



'''
dts part

'''
class WamvListener:
    services = defaultdict(dict)
    supported_services = [
        "DT::ONLINE",
        "DT::PRESENCE",
        "DT::BOOTING",
        "DT::ROBOT_TYPE",
        "DT::ROBOT_CONFIGURATION",
        "DT::DASHBOARD",
    ]

    def __init__(self, args):
        print(sys.path)
        self.args = args

    def process_service_name(self, name):
        name = name.replace("._duckietown._tcp.local.", "")
        service_parts = name.split("::")
        if len(service_parts) != 3 or service_parts[0] != "DT":
            return None, None
        name = "{}::{}".format(service_parts[0], service_parts[1])
        server = service_parts[2]
        return name, server

    def remove_service(self, zeroconf, type, name):
        dtslogger.debug("SERVICE_REM: %s (%s)" % (str(name), str(type)))
        name, server = self.process_service_name(name)
        if not name:
            return
        del self.services[name][server]

    def add_service(self, zeroconf, type, sname):
        dtslogger.debug("SERVICE_ADD: %s (%s)" % (str(sname), str(type)))
        name, server = self.process_service_name(sname)
        if not name:
            return
        dtslogger.debug("SERVICE_ADD: %s (%s)" % (str(name), str(server)))
        info = zeroconf.get_service_info(type, sname)
        if info is None:
            return
        dtslogger.debug("SERVICE_ADD: %s" % (str(info)))
        txt = json.loads(list(info.properties.keys())[0].decode("utf-8")) if len(info.properties) else dict()
        self.services[name][server] = {"port": info.port, "txt": txt}

    def update_service(self, *args, **kwargs):
        pass

    def print(self):
        # get all discovered hostnames
        hostnames: Set[str] = set()
        # prepare table
        columns = [
            "H.B.",
            "ZEDm",
            "D435",
            "LIDAR",
            "mmWave",
            "GPS",
            "gripper"
        ]
        columns = list(map(lambda c: " %s " % c, columns))
        header = columns
        data = []
        for sensortower in sensortowers:
            statuses = []
            for column in columns:
                text, color, bg_color = column_to_text_and_color(column, 'hostname', self.services, sensortower)
                column_txt = fill_cell(text, len(column), color, bg_color)
                statuses.append(column_txt)
            row = ([sensortower] + statuses )
            data.append(row)
        # clear terminal
        os.system("cls" if os.name == "nt" else "clear")
        # print table
        print(datetime.now())
        print("ARG define command : dts health wamv")
        print()
        print(format_matrix(header, data, "{:^{}}", "{:<{}}", "{:>{}}", "\n", " | "))
        
class DTCommand(DTCommandAbs):
    @staticmethod
    def command(shell, args):
        prog = "dts anchor discover"

        # try to import zeroconf
        try:
            from zeroconf import ServiceBrowser, Zeroconf
        except ImportError:
            dtslogger.error("{} requires zeroconf. Use pip to install it.")
            return

        # parse arguments
        parser = argparse.ArgumentParser(prog=prog, usage=usage)

        parser.add_argument(
            "--type",
            dest="filter_type",
            default=None,
            choices="",
            help="Filter devices by type",
        )

        parsed = parser.parse_args(args)
        zeroconf = Zeroconf()
        # perform discover
        listener = WamvListener(args=parsed)
        ServiceBrowser(zeroconf, "_duckietown._tcp.local.", listener)

        while True:
            if dtslogger.level > logging.DEBUG:
                listener.print()
            time.sleep(1.0 / REFRESH_HZ)

def column_to_text_and_color(column, hostname, services, sensortower):
    column = column.strip()
    text, color, bg_color = "try", "white", "red"
    #  -> Status
    if column == "H.B.":
        if sensortower_status[sensortower][0] == '0':
            text, color, bg_color = 'no', "white", "grey"
        elif sensortower_status[sensortower][0] == '1':
            text, color, bg_color = 'alive', "white", "green"
    if column == "ZEDm":
        if sensortower_status[sensortower][1] == '0':
            text, color, bg_color = 'no', "white", "grey"
        elif sensortower_status[sensortower][1] == '1':
            text, color, bg_color = 'alive', "white", "green"
    if column == "D435":
        if sensortower_status[sensortower][2] == '0' :
            text, color, bg_color = 'no', "white", "grey"
        elif sensortower_status[sensortower][2] == '1':
            text, color, bg_color = 'alive', "white", "green"
    if column == "LIDAR":
        if sensortower_status[sensortower][3] == '0' :
            text, color, bg_color = 'no', "white", "grey"
        elif sensortower_status[sensortower][3] == '1':
            text, color, bg_color = 'alive', "white", "green"
    if column == "mmWave":
        if sensortower_status[sensortower][4] == '0' :
            text, color, bg_color = 'no', "white", "grey"
        elif sensortower_status[sensortower][4] == '4':
            text, color, bg_color = 'alive', "white", "green"
    if column == "GPS":
        if sensortower_status[sensortower][5] == '0' :
            text, color, bg_color = 'no', "white", "grey"
        elif sensortower_status[sensortower][5] == '1':
            text, color, bg_color = 'alive', "white", "green"
    if column == "gripper":
        if sensortower_status[sensortower][6] == '0' :
            text, color, bg_color = 'no', "white", "grey"
        elif sensortower_status[sensortower][6] == '1':
            text, color, bg_color = 'alive', "white", "green"
    # ----------
    return text, color, bg_color
