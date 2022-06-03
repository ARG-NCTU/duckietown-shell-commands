#!/usr/bin/env python3
import os, sys
import pytest
import yaml

hostnames = []

def load_config():

    with open("scuderia.yaml", 'r') as stream:
        try:
            vehicles = yaml.safe_load(stream)
            for box in vehicles.values():
                for ip in box.values():
                    hostnames.append(ip)
                    print(ip)
        except yaml.YAMLError as exc:
            print(exc)

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
