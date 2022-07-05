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

    return your ip.

"""
class DTCommand(DTCommandAbs):
    @staticmethod
    def command(shell, args):
        prog = "dts fleet myip"

        # try to import zeroconf
        try:
            from zeroconf import ServiceBrowser, Zeroconf
        except ImportError:
            dtslogger.error("{} requires zeroconf. Use pip to install it.")
            return
        zeroconf = Zeroconf()
        # perform discover
        myip = get_ip.myip()
        print(myip)

