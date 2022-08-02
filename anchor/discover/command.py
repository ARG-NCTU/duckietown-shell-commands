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
import roslibpy
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
dp_yaml_path = get_ip.find_duckiepond_devices_yaml("duckiepond-devices-machine.yaml")
dp_dict = get_ip.dp_load_config(dp_yaml_path)
anchors = get_ip.dp_get_devices(dp_yaml_path, 'anchor*')
boat_status = {'anchor1':'connecting', 'anchor2': 'connecting', 'anchor3': 'connecting', 'anchor4': 'connecting', 'anchor5': 'connecting', 'anchor6': 'connecting', 'anchor7': 'connecting','anchor8': 'connecting'}


'''
boat alive part
'''
def boat_callback(message):
    global boat_status
    boat_status['anchor' + str(message['data'][4])] = message['data']

def get_boat_status(ip,):
    try:
        boat  =  websocket.ros_socket(ip)

        topic_name_boat = "/anchor"+ ip[-2] +"/status"
        boat.subscriber(topic_name_boat, boat_callback, 100)
    except:
       pass

'''
roslibpy threading part
'''
threads = []
for anchor in anchors:
    threads.append(threading.Thread(target = get_boat_status, args = (dp_dict[anchor]['rpi_1']['ip'],)))
for i in range(len(threads)):
    threads[i].start()


'''
dts part

'''

class AnchorListener:
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

        for service in self.supported_services:
            hostnames_for_service: List[str] = list(self.services[service])
            hostnames.update(hostnames_for_service)
        # create hostname -> robot_type map
        hostname_to_type = defaultdict(lambda: "ND")
        for device_hostname in self.services["DT::ROBOT_TYPE"]:
            dev = self.services["DT::ROBOT_TYPE"][device_hostname]
            if len(dev["txt"]) and "type" in dev["txt"]:
                try:
                    hostname_to_type[device_hostname] = dev["txt"]["type"]
                except:  # XXX: complain a bit
                    pass
        # create hostname -> robot_configuration map
        hostname_to_config = defaultdict(lambda: "ND")
        for device_hostname in self.services["DT::ROBOT_CONFIGURATION"]:
            dev = self.services["DT::ROBOT_CONFIGURATION"][device_hostname]
            if len(dev["txt"]) and "configuration" in dev["txt"]:
                try:
                    hostname_to_config[device_hostname] = dev["txt"]["configuration"]
                except:
                    pass
        # prepare table
        columns = [
            "anchor",
            "boat heart beat"
        ]
        columns = list(map(lambda c: " %s " % c, columns))
        header = ["ip"]  + columns
        data = []

        for anchor in anchors:
            gotit = False
            for device_hostname in list(sorted(hostnames)):
                if dp_dict[anchor]['rpi_1']['hostname'] == device_hostname:
                    statuses = []
                    for column in columns:
                        text, color, bg_color = column_to_text_and_color(column, device_hostname, self.services, anchor)
                        column_txt = fill_cell(text, len(column), color, bg_color)
                        statuses.append(column_txt)
                    gotit = True
                    row = (
                        [anchor, 
                        dp_dict[anchor]['rpi_1']['ip']]
                        + statuses
                    )
                    data.append(row)
                    if boat_status[anchor][-5:] == 'alive': #main code 1Hz alive -> dead, thread 10Hz dead -> alive, if boat is dead, thread will dead
                        boat_status[anchor] = 'connecting'
            if gotit == False:
                row = (
                    [anchor, 
                    dp_dict[anchor]['rpi_1']['ip'],
                    "disconnect",
                    "anchor disconnect"]
                )
                data.append(row)        
        # clear terminal
        os.system("cls" if os.name == "nt" else "clear")
        # print table
        print(datetime.now())
        print("ARG define command : dts anchor discover")
        #print("Config : {}\n".format(dp_yaml_path))
        #print("NOTE: Only devices flashed using duckietown-shell-commands v4.1.0+ are supported.\n")
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
        listener = AnchorListener(args=parsed)
        ServiceBrowser(zeroconf, "_duckietown._tcp.local.", listener)

        while True:
            if dtslogger.level > logging.DEBUG:
                listener.print()
            time.sleep(1.0 / REFRESH_HZ)


def column_to_text_and_color(column, hostname, services, anchor):
    column = column.strip()
    text, color, bg_color = "ND", "white", "grey"
    #  -> Status
    if column == "anchor":
        if hostname in services["DT::PRESENCE"]:
            text, color, bg_color = "Ready", "white", "green"
        if hostname in services["DT::BOOTING"]:
            text, color, bg_color = "Booting", "white", "yellow"
    if column == "boat heart beat":
        if boat_status[anchor] == 'connecting':
            text, color, bg_color = boat_status[anchor], "white", "red"
        else:
            text, color, bg_color = boat_status[anchor], "white", "green"
    # ----------
    return text, color, bg_color

