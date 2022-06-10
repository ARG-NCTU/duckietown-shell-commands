import re
import math
from termcolor import colored
from arg_robotics_tools import get_ip

class Format(object):
    ALIGN_LEFT = "{:<{}}"
    CENTER = "{:^{}}"
    ALIGN_RIGHT = "{:>{}}"


def format_matrix(
    header,
    matrix,
    top_format=Format.CENTER,
    left_format=Format.ALIGN_LEFT,
    cell_format=Format.ALIGN_LEFT,
    row_delim="\n",
    col_delim=" | ",
):
    table = [[""] + header] + matrix
    print_table = table
    if isinstance(cell_format, str):
        cell_format = len(header) * [cell_format]
    elif isinstance(cell_format, (list, tuple)):
        if len(cell_format) != len(header):
            raise ValueError("Length of cell_format must be equal to length of header")
    else:
        raise ValueError(f"Type of cell_format {type(cell_format)} not supported.")
    cell_format = len(header) * [cell_format] if isinstance(cell_format, str) else cell_format
    table_format = [["{:^{}}"] + len(header) * [top_format]] + (len(matrix) + 1) * [
        [left_format] + cell_format
    ]

    # fix spacing and string sizes when `termcolor` is used
    ln = lambda s: len(re.sub(rb"(\x1b|\[\d{1,2}m)*", b"", str(s).encode("utf-8")))
    fmt = lambda f, s, w: f.format(fill_cell(s, w, text_len=ln(s), format=f), w)
    # compute columns' widths
    col_widths = [
        max(ln(fmt(format, cell, 0)) for format, cell in zip(col_format, col))
        for col_format, col in zip(zip(*table_format), zip(*table))
    ]
    # add header separator
    print_table = [print_table[0], ["-" * l for l in col_widths]] + print_table[1:]
    # print table
    return row_delim.join(
        col_delim.join(fmt(format, cell, width) for format, cell, width in zip(row_format, row, col_widths))
        for row_format, row in zip(table_format, print_table)
    )


def fill_cell(text, width, foreground=None, background=None, text_len=None, format=None):
    text = str(text)
    text_len = text_len if text_len else len(text)
    s1 = math.floor((float(width) - text_len) / 2.0)
    s2 = math.ceil((float(width) - text_len) / 2.0)
    if format == "{:<{}}":
        s1, s2 = 0, s1 + s2
    if format == "{:>{}}":
        s1, s2 = s1 + s2, 0
    s = " " * s1 + text + " " * s2
    if not foreground or not background:
        return s
    return colored(s, foreground, "on_" + background)

def dp_print_boats(dp_yaml_path):

    header = [
        "['nano']['ip']", 
        "boat xbee_tx", 
        "boat xbee_rx", 
        "anch xbee_tx", 
        "anch xbee_rx"]

    data = []
    dp_dict = get_ip.dp_load_config(dp_yaml_path)

    #print("load config {}".format(dp_yaml_path))

    boats = get_ip.dp_get_devices(dp_yaml_path, 'boat*')
    #print("load boats: {}".format(boats))

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
             "states"]
        )
        data.append(row)

    print(format_matrix(header, data, "{:^{}}", "{:<{}}", "{:>{}}", "\n", " | "))

