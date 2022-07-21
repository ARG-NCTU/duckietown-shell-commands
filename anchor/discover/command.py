import argparse
import json
import logging
import os
import time
import re

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
dp_yaml_path = get_ip.find_duckiepond_devices_yaml("duckiepond-devices-machine.yaml")
dp_dict = get_ip.dp_load_config(dp_yaml_path)
uwb = [0,0,0,0,0,0,0,0]

'''
uwb_distance part

'''
def subscribe_callback1(message):
    global dp_dict
    global uwb
    #print(uwb_distance)
    if message['data'] != 0 and message['data'] < 10000:
        #print("anchor1" + " " +str(message['data']))
        dp_dict['anchor1']['rpi_1']['uwb'] = message['data']
        uwb[0] = message['data']
def subscribe_callback2(message):
    global dp_dict
    global uwb
    if message['data'] != 0 and message['data'] < 10000:
        #print("anchor2" + " " +str(message['data']))
        dp_dict['anchor2']['rpi_1']['uwb'] = message['data']
        uwb[1] = message['data']
def subscribe_callback3(message):
    global dp_dict
    global uwb
    if message['data'] != 0 and message['data'] < 10000:
        #print("anchor3" + " " +str(message['data']))
        dp_dict['anchor3']['rpi_1']['uwb'] = message['data']
        uwb[2] = message['data']
def subscribe_callback4(message):
    global dp_dict
    global uwb
    if message['data'] != 0 and message['data'] < 10000:
        #print("anchor4" + " " +str(message['data']))
        dp_dict['anchor4']['rpi_1']['uwb'] = message['data']
        uwb[3] = message['data']
def subscribe_callback5(message):
    global dp_dict
    global uwb
    if message['data'] != 0 and message['data'] < 10000:
        #print("anchor4" + " " +str(message['data']))
        dp_dict['anchor5']['rpi_1']['uwb'] = message['data']
        uwb[4] = message['data']
def subscribe_callback6(message):
    global dp_dict
    global uwb
    if message['data'] != 0 and message['data'] < 10000:
        #print("anchor4" + " " +str(message['data']))
        dp_dict['anchor6']['rpi_1']['uwb'] = message['data']
        uwb[5] = message['data']
def subscribe_callback7(message):
    global dp_dict
    global uwb
    if message['data'] != 0 and message['data'] < 10000:
        #print("anchor4" + " " +str(message['data']))
        dp_dict['anchor7']['rpi_1']['uwb'] = message['data']
        uwb[6] = message['data']
        
def subscribe_callback8(message):
    global dp_dict
    global uwb
    if message['data'] != 0 and message['data'] < 10000:
        #print("anchor4" + " " +str(message['data']))
        dp_dict['anchor8']['rpi_1']['uwb'] = message['data']
        uwb[7] = message['data']




def get_distance(ip,):
    global dp_dict

    try:
        client = roslibpy.Ros(host = ip, port = 9090)
        client.run()
        #print('Is ROS connected?', client.is_connected)
    
        if ip == '192.168.1.12': topic_name = "/anchor01/distance"
        elif ip == '192.168.1.22': topic_name = "/anchor02/distance"
        elif ip == '192.168.1.32': topic_name = "/anchor03/distance"
        elif ip == '192.168.1.42': topic_name = "/anchor04/distance"
        elif ip == '192.168.1.52': topic_name = "/anchor05/distance"
        elif ip == '192.168.1.62': topic_name = "/anchor06/distance"
        elif ip == '192.168.1.72': topic_name = "/anchor07/distance"
        elif ip == '192.168.1.82': topic_name = "/anchor08/distance"

        topic_type = client.get_topic_type(topic_name)
        #print('type_is ' + topic_type)
        listener = roslibpy.Topic(client, topic_name, topic_type, throttle_rate=100)

        if ip == '192.168.1.12': listener.subscribe(subscribe_callback1)
        elif ip == '192.168.1.22': listener.subscribe(subscribe_callback2)
        elif ip == '192.168.1.32': listener.subscribe(subscribe_callback3)
        elif ip == '192.168.1.42': listener.subscribe(subscribe_callback4)
        elif ip == '192.168.1.52': listener.subscribe(subscribe_callback5)
        elif ip == '192.168.1.62': listener.subscribe(subscribe_callback6)
        elif ip == '192.168.1.72': listener.subscribe(subscribe_callback7)
        elif ip == '192.168.1.82': listener.subscribe(subscribe_callback8)
    except:
        print()
        


threads = []
ip = ['192.168.1.12','192.168.1.22','192.168.1.32','192.168.1.42','192.168.1.52','192.168.1.62','192.168.1.72','192.168.1.82']
for i in range(7):
    threads.append(threading.Thread(target = get_distance, args = (ip[i],)))
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
        global uwb
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
            "Dashboard",  # Down [grey], Up [green]
            # TODO: Busy is not used at this time, disabling it
            # "Busy",  # No [grey], Yes [green]
        ]
        columns = list(map(lambda c: " %s " % c, columns))
        header = ["ip","hostname"]  + columns + ["rpi2 / tvl","hostname", "uwb"]
        data = []

        dp_dict['anchor1']['rpi_1']['uwb'] = uwb[0]
        dp_dict['anchor2']['rpi_1']['uwb'] = uwb[1]
        dp_dict['anchor3']['rpi_1']['uwb'] = uwb[2]
        dp_dict['anchor4']['rpi_1']['uwb'] = uwb[3]
        dp_dict['anchor5']['rpi_1']['uwb'] = uwb[4]
        dp_dict['anchor6']['rpi_1']['uwb'] = uwb[5]
        dp_dict['anchor7']['rpi_1']['uwb'] = uwb[6]
        dp_dict['anchor8']['rpi_1']['uwb'] = uwb[7]


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
                    if (anchor=='anchor7') or (anchor=='anchor8'):
                        row = (
                            [anchor, 
                            dp_dict[anchor]['rpi_1']['ip'],
                            dp_dict[anchor]['rpi_1']['hostname']]
                             + statuses +
                            [dp_dict[anchor]['tvl']['ip'],
                            "tvl",
                            dp_dict[anchor]['rpi_1']['uwb']]
                        )
                    else:
                        row = (
                            [anchor, 
                            dp_dict[anchor]['rpi_1']['ip'],
                            dp_dict[anchor]['rpi_1']['hostname']]
                            + statuses +
                            [dp_dict[anchor]['rpi_2']['ip'],
                            dp_dict[anchor]['rpi_2']['hostname'],
                            dp_dict[anchor]['rpi_1']['uwb']]
                        )
                    data.append(row) 
            if gotit == False:
                if (anchor=='anchor7') or (anchor=='anchor8'):
                    row = (
                        [anchor, 
                        dp_dict[anchor]['rpi_1']['ip'],
                        dp_dict[anchor]['rpi_1']['hostname'],
                        "no connect",
                        "no connect",
                        dp_dict[anchor]['tvl']['ip'],
                        "tvl",
                        dp_dict[anchor]['rpi_1']['uwb']]
                    )
                else:
                    row = (
                        [anchor, 
                        dp_dict[anchor]['rpi_1']['ip'],
                        dp_dict[anchor]['rpi_1']['hostname'],
                        "no connect",
                        "no connect",
                        dp_dict[anchor]['rpi_2']['ip'],
                        dp_dict[anchor]['rpi_2']['hostname'],
                        dp_dict[anchor]['rpi_1']['uwb']]
                    )
                data.append(row)        
        # clear terminal
        os.system("cls" if os.name == "nt" else "clear")
        # print table
        print("load config {}".format(dp_yaml_path))
        print("NOTE: Only devices flashed using duckietown-shell-commands v4.1.0+ are supported.\n")
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
