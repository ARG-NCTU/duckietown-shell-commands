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
#from utils.duckiepond_utils import find_duckiepond_devices_yaml, dp_print_boats

REFRESH_HZ = 1.0

usage = """
## Basic usage

    Discovers Duckiepond robots in the xbee network.

    To find out more, use `dts duckiepond discover -h`.

        $ dts duckiepond discover [options]

"""

class xbee_listener:

    def __init__(self, args):
        print(sys.path)

        self.args = args
        self.dp_yaml_path = get_ip.find_duckiepond_devices_yaml("duckiepond-devices-machine.yaml")

    def print(self):
        header = [
            "['nano']['ip']", 
            "boat xbee_tx", 
            "boat xbee_rx", 
            "anch xbee_tx", 
            "anch xbee_rx",
            "states"]
    
        data = []
        dp_dict = get_ip.dp_load_config(self.dp_yaml_path)
        boats = get_ip.dp_get_devices(self.dp_yaml_path, 'boat*')
    
        for boat in boats:
            anchor = dp_dict[boat]['xbee']['xbee_pair'] 
            anchor_tx = dp_dict[anchor]['rpi_1']['xbee_tx']
            anchor_rx = ""
            if 'rpi_2' in dp_dict[anchor]:
                anchor_rx = dp_dict[anchor]['rpi_2']['xbee_rx']
            elif 'tvl' in dp_dict[anchor]:
                anchor_rx = 'tvl ' + dp_dict[anchor]['tvl']['ip']
    
            row = (
                [boat, 
                 dp_dict[boat]['nano']['ip'], 
                 dp_dict[boat]['nano']['xbee_tx'], 
                 dp_dict[boat]['rpi']['xbee_rx'], 
                 anchor_tx,
                 anchor_rx,
                 "todo"]
            )
            data.append(row)
     
        # clear terminal
        os.system("cls" if os.name == "nt" else "clear")
        print("load config {}".format(self.dp_yaml_path))
        print(format_matrix(header, data, "{:^{}}", "{:<{}}", "{:>{}}", "\n", " | "))
    
class DiscoverListener:
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
        # clear terminal
        os.system("cls" if os.name == "nt" else "clear")
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
            "Status",  # Booting [yellow], Ready [green]
            # TODO: Internet check is kind of unstable at this time, disabling it
            # "Internet",  # No [grey], Yes [green]
            "Dashboard",  # Down [grey], Up [green]
            # TODO: Busy is not used at this time, disabling it
            # "Busy",  # No [grey], Yes [green]
        ]
        columns = list(map(lambda c: " %s " % c, columns))
        header = ["Type", "Model"] + columns + ["Hostname"]
        data = []

        for device_hostname in list(sorted(hostnames)):
            # filter by robot type
            robot_type = hostname_to_type[device_hostname]
            robot_configuration = hostname_to_config[device_hostname]
            if self.args.filter_type and robot_type != self.args.filter_type:
                continue
            # prepare status list
            statuses = []
            for column in columns:
                text, color, bg_color = column_to_text_and_color(column, device_hostname, self.services)
                column_txt = fill_cell(text, len(column), color, bg_color)
                statuses.append(column_txt)
            # prepare row
            row = (
                [device_hostname, robot_type, robot_configuration]
                + statuses
                + [str(device_hostname) + ".local"]
            )
            data.append(row)

        # print table
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

        # perform discover
        listener = xbee_listener(args=parsed)
        #listener = DiscoverListener(args=parsed)
        
        while True:
            if dtslogger.level > logging.DEBUG:
                listener.print()
            time.sleep(1.0 / REFRESH_HZ)


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
