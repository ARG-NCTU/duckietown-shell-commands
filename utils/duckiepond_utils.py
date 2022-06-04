#!/usr/bin/env python3
import os, sys
import os.path
import pytest
import yaml
import re
from utils.table_utils import fill_cell, format_matrix

def find_duckiepond_devices_yaml(yaml_filename="duckiepond-devices.yaml"):

    dp_yaml_path = ""

    for root, dirs, files in os.walk(os.path.expanduser('~')):
        for name in files:
            if name == yaml_filename:
                dp_yaml_path = os.path.abspath(os.path.join(root, name))
                break

    return dp_yaml_path

def dp_load_config(dp_yaml_path):

    dp_dict = {}

    with open(dp_yaml_path, 'r') as stream:
        try:
            dp_dict = yaml.safe_load(stream)
            #devices.append(vehicles.keys())
            #devices.append(vehicles['boat1']['rpi'])
            #for veh in vehicles.values():
            #    print(veh)
        except yaml.YAMLError as exc:
            print(exc)

    return dp_dict

def dp_get_devices(dp_yaml_path, pattern='boat*'):

    dp_dict = dp_load_config(dp_yaml_path)

    boats = []
    for key in dp_dict.keys():
        match = re.match(pattern, key)
        if match:
            boats.append(key)

    return boats

def dp_get_xbee_tx_rx(dp_yaml_path, device):

    dp_dict = dp_load_config(dp_yaml_path)

    tx = ""
    rx = ""
    if re.match('boat*', device):
        tx = dp_dict[device]['nano']['xbee_tx']
        rx = dp_dict[device]['rip']['xbee_rx']

def dp_print_boats(dp_yaml_path):

    header = [
        "['nano']['ip']", 
        "['xbee_tx']", 
        "['xbee_rx']", 
        "Status", "States"]

    data = []
    dp_dict = dp_load_config(dp_yaml_path)

    #print("load config {}".format(dp_yaml_path))

    boats = dp_get_devices(dp_yaml_path, 'boat*')
    #print("load boats: {}".format(boats))

    for boat in boats:
        row = (
            [boat, 
             dp_dict[boat]['nano']['ip'], 
             dp_dict[boat]['nano']['xbee_tx'], 
             dp_dict[boat]['rpi']['xbee_rx'], 
             "status", 
             "states"]
        )
        data.append(row)

    print(format_matrix(header, data, "{:^{}}", "{:<{}}", "{:>{}}", "\n", " | "))

def dp_print_anchors(dp_yaml_path):

    header = [
        "['rpi_1']['ip']", 
        "['xbee_tx']", 
        "['xbee_rx']", 
        "Status", "States"]

    data = []
    dp_dict = dp_load_config(dp_yaml_path)

    #print("load config {}".format(dp_yaml_path))

    anchors = dp_get_devices(dp_yaml_path, 'anchor*')
    #print("load anchors: {}".format(anchors))

    for anchor in anchors:
        row = (
            [anchor, 
             dp_dict[anchor]['rpi_1']['ip'], 
             "",
             "",
             "status", 
             "states"]
        )
        data.append(row)

    print(format_matrix(header, data, "{:^{}}", "{:<{}}", "{:>{}}", "\n", " | "))


def ssh_ping_nano(hostname):
    response = os.system("ssh $USER@" + hostname + " ping -c 1 192.168.0.100")
    return response

def ssh_ping_rpi(hostname):
    response = os.system("ssh $USER@" + hostname + " ping -c 1 192.168.0.101")
    return response

def test_ssh_intranet():
    error = []
    for ip in hostnames:
        num = ssh_ping_rpi(ip)
        if num!=0:
            error.append("ssh ping rpi error " + ip)
        num = ssh_ping_nano(ip)
        if num!=0:
            error.append("ssh ping nano error " + ip)
    assert not error, "errors occured:\n{}".format("\n".join(error))

def ssh_connection(hostname):
    response = os.system("ssh $USER@" + hostname + " date")
    return response

def test_ssh():
    error = []
    for ip in hostnames:
        num = ssh_connection(ip)
        if num != 0:
            error.append("ssh error " + ip)
    assert not error, "errors occured:\n{}".format("\n".join(error))

def ip_connection(hostname):
    response = os.system("ping -c 1 " + hostname)
    return response

def test_ping():
    error = []
    for ip in hostnames:
        num = ip_connection(ip)
        if num != 0:
            error.append("Network Error " + ip)
    assert not error, "errors occured:\n{}".format("\n".join(error))

def ssh_rostopic(hostname):
    response = os.system('ssh $USER@' + hostname + ' "source /opt/ros/melodic/setup.bash && rostopic list"')
    return response

def test_rostopic():
    error = []
    for ip in hostnames:
        num = ssh_rostopic(ip)
        if num != 0:
            error.append("ssh rostopic list error " + ip)
    assert not error, "errors occured:\n{}".format("\n".join(error))
