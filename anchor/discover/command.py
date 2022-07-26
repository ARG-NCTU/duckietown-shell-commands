import argparse
import json
import logging
import os
import time
import re
from datetime import datetime

from arg_robotics_tools import get_ip
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
uwb_distance = [0,0,0,0,0,0,0,0]
uwb_id = {'27238': 0, '22025': 1, '26436': 3, '27208':4, '27142':5, '27210':7}
boat_status = {'anchor1':'connecting', 'anchor2': 'connecting', 'anchor3': 'connecting', 'anchor4': 'connecting', 'anchor5': 'connecting', 'anchor6': 'connecting', 'anchor7': 'connecting','anchor8': 'connecting'}

'''
uwb_distance part

'''
def distance_callback(message):
    global distance
    global uwb_id
    if len(message['rangeArray']) !=0 :
        if message['rangeArray'][0]['distance'] != 0 and message['rangeArray'][0]['distance'] < 20000:
            index = uwb_id[str(message['rangeArray'][0]['self_id'])]
            uwb_distance[int(index)] = message['rangeArray'][0]['distance']


def get_distance(ip,):
    global uwb_distance
    try:
        client = roslibpy.Ros(host = ip, port = 9090)
        client.run()
       #print('Is ROS connected?', client.is_connected)
    
        topic_name = "/anchor0"+ ip[-2] +"/ranges"

        topic_type = client.get_topic_type(topic_name)
        #print('type_is ' + topic_type)
        listener = roslibpy.Topic(client, topic_name, topic_type, throttle_rate=100)
        listener.subscribe(distance_callback)
    except:
        #print("cannot connect to Ros")
        print(" ")

'''
boat alive part
'''
def boat_callback(message):
    global boat_status
    boat_status['anchor' + str(message['data'][4])] = message['data']

def get_boat_status(ip,):
    try:
        client = roslibpy.Ros(host = ip, port = 9090)
        client.run()
       #print('Is ROS connected?', client.is_connected)
    
        topic_name_boat = "/anchor"+ ip[-2] +"/status"

        topic_type_boat = client.get_topic_type(topic_name_boat)
        listener_boat = roslibpy.Topic(client, topic_name_boat, topic_type_boat, throttle_rate=100)
        listener_boat.subscribe(boat_callback)
    except:
       # print("cannot connect to Ros")
       print(" ")

'''
roslibpy threading part
'''
threads = []
ip = ['192.168.1.42','192.168.1.52','192.168.1.62','192.168.1.82']
for i in range(4):
    threads.append(threading.Thread(target = get_distance, args = (ip[i],)))
for i in range(4):
    threads.append(threading.Thread(target = get_boat_status, args = (ip[i],)))
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

        anchors = get_ip.dp_get_devices(dp_yaml_path, 'anchor*')
        
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
            "Status",  # Booting [yellow], Ready [green]
            # TODO: Internet check is kind of unstable at this time, disabling it
            # "Internet",  # No [grey], Yes [green]
        ]
        columns = list(map(lambda c: " %s " % c, columns))
        header = ["ip","hostname"]  + columns + ["boat heart bit", "uwb"]
        data = []

        for i in range(8):
            if uwb_distance[i] != 0:
                dp_dict['anchor' + str(i+1)]['rpi_1']['uwb'] = uwb_distance[i]


        for anchor in anchors:
            gotit = False
            for device_hostname in list(sorted(hostnames)):
                if dp_dict[anchor]['rpi_1']['hostname'] == device_hostname:
                    statuses = []
                    for column in columns:
                        text, color, bg_color = column_to_text_and_color(column, device_hostname, self.services)
                        column_txt = fill_cell(text, len(column), color, bg_color)
                        statuses.append(column_txt)
                    gotit = True
                    row = (
                        [anchor, 
                        dp_dict[anchor]['rpi_1']['ip'],
                        dp_dict[anchor]['rpi_1']['hostname']]
                        + statuses +
                        [boat_status[anchor],
                        dp_dict[anchor]['rpi_1']['uwb']]
                    )
                    data.append(row)
                    if boat_status[anchor][-5:] == 'alive': #main code 1Hz alive -> dead, thread 10Hz dead -> alive, if boat is dead, thread will dead
                        boat_status[anchor] = 'connecting'
            if gotit == False:
                row = (
                    [anchor, 
                    dp_dict[anchor]['rpi_1']['ip'],
                    dp_dict[anchor]['rpi_1']['hostname'],
                    "no connect",
                    "anchor no connect",
                    "no uwb data"]
                )
                data.append(row)        
        # clear terminal
        os.system("cls" if os.name == "nt" else "clear")
        # print table
        print(datetime.now())
        print("ARG define command : dts anchor discover")
        print("Config : {}\n".format(dp_yaml_path))
        #print("NOTE: Only devices flashed using duckietown-shell-commands v4.1.0+ are supported.\n")
        print(format_matrix(header, data, "{:^{}}", "{:<{}}", "{:>{}}", "\n", " | "))

class DTCommand(DTCommandAbs):
    @staticmethod
    def command(shell, args):
        prog = "dts fleet discover"

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
            time.sleep(2.0 / REFRESH_HZ)


def column_to_text_and_color(column, hostname, services):
    column = column.strip()
    text, color, bg_color = "ND", "white", "grey"
    #  -> Status
    if column == "Status":
        if hostname in services["DT::PRESENCE"]:
            text, color, bg_color = "Ready", "white", "green"
        if hostname in services["DT::BOOTING"]:
            text, color, bg_color = "Booting", "white", "yellow"
    #  -> Dashboard
    if column == "Dashboard":
        text, color, bg_color = "Down", "white", "grey"
        if hostname in services["DT::DASHBOARD"]:
            text, color, bg_color = "Up", "white", "green"
    #  -> Internet
    if column == "Internet":
        text, color, bg_color = "No", "white", "grey"
        if hostname in services["DT::ONLINE"]:
            text, color, bg_color = "Yes", "white", "green"
    #  -> Busy
    if column == "Busy":
        text, color, bg_color = "No", "white", "grey"
        if hostname in services["DT::BUSY"]:
            text, color, bg_color = "Yes", "white", "green"
    # ----------
    return text, color, bg_color


