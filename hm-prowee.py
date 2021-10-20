#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2016-2021 Christoph Heuel <christoph@heuel-web.de>
# Distributed under terms of the MIT license.
#
"""
Manage Homgear Heater Devices
"""
import xmlrpc.client
import ssl
import json
import getpass
import argparse
import configparser
import os
import sys


MAX_POINTS = 13
MAX_ENDTIME = 1440

# Homegear constants
HG_FILTER_BY_TYPE_ID = 3
HG_HEATERS_TYPE_ID = "0x95"


class ConfigError(Exception):
    pass


def pp(jsontext):
    """Pretty print json text"""
    print(json.dumps(jsontext, sort_keys=True, indent=4,
                     separators=(',', ': ')))


def list_heaters(xmlc, args):
    """List heater devices from server"""
    try:
        heaters = xmlc.getPeerId(HG_FILTER_BY_TYPE_ID, HG_HEATERS_TYPE_ID)
    except Exception:
        print("Can't load list of devices!")
        exit(1)
    print("{0:4} {1}".format("ID", "Name"))
    for i in heaters:
        print("{0:4} {1}".format(i, xmlc.getName(i)))


def print_paramsets(xmlc, args):
    """Print parameterset for specific device id"""
    pp(xmlc.getParamset(int(args.id), 0, "MASTER"))


def print_temp_config(xmlc, args):
    """Print temp config file for specific device id"""
    params = xmlc.getParamset(int(args.id), 0, "MASTER")
    weekdays = ["monday", "tuesday", "wednesday", "thursday", "friday",
                "saturday", "sunday"]

    for weekday in weekdays:
        elements = []

        for i in range(1, MAX_POINTS+1):
            temperature_key = "TEMPERATURE_{0}_{1}".format(weekday.upper(), i)
            endtime_key = "ENDTIME_{0}_{1}".format(weekday.upper(), i)

            temperature_value = params[temperature_key]
            endtime_value = params[endtime_key]

            elements.append("{0:.1f} > {1};".format(
                temperature_value,
                calculate_timedef_from_minutes(endtime_value)))

            if endtime_value == MAX_ENDTIME:
                break

        print("{0} = {1}".format(weekday.upper(), " ".join(elements)))


def calculate_minutes_from_midnight(timedef):
    """Calculate from time the minites from midnight

    :param timedef: Time to calculate minutes from midnight. Eg. '07:00'
    :returns: Minutes from midnight"""
    hour_minutes = timedef.split(":")
    if not len(hour_minutes) == 2:
        raise TypeError("{0} is not in format HH:MM!".format(timedef))
    hours = int(hour_minutes[0])
    minutes = hours*60 + int(hour_minutes[1])
    if minutes > MAX_ENDTIME:
        minutes = MAX_ENDTIME
    return minutes


def calculate_timedef_from_minutes(minutes):
    """Calculate time from minutes from midnight

    :param timedef: Minutes from midnight for calculation"""
    return "{0:02}:{1:02}".format(int(minutes / 60), minutes % 60)


def parse_temperature_item(item):
    """Parse item for time and temperature

    :param item: Definition, eg. '17.0 > 07:00'
    :returns: dict with temperature and minutes"""
    temp_time_tupel = item.split(">")
    temperature = float(temp_time_tupel[0].strip())
    minutes_from_midnight = calculate_minutes_from_midnight(
        temp_time_tupel[1].strip())
    return {'minutes_from_midnight': minutes_from_midnight,
            'temperature': temperature}


def parse_temperature_definition(temp_def_raw):
    """Parse list of temperature definitions

    :param temp_def_raw: List separated by ';' of temperature/time definitions
    :returns: list of hashes with temperature/time definitions"""
    temp_def_list = filter(None, temp_def_raw.split(";"))
    temp_array = []
    for i in temp_def_list:
        temp_array.append(parse_temperature_item(i))
    return temp_array


def read_from_file(filename):
    """Read config file

    :param filename: Filename to read from
    :returns: Parsed definition of each line"""
    lines = []
    with open(filename, "r") as config:
        lines = config.read().splitlines()

    deflist = {}
    for i in lines:
        if i.startswith("#"):
            continue
        line_array = i.split("=")
        weekday = line_array[0].strip()
        temp_def = parse_temperature_definition(line_array[1])
        deflist[weekday] = temp_def

    return deflist


def set_temp_to_homegear(xmlc, id, definition_list):
    """Send list of definitions to ID

    :param id: ID to receive definition
    :param definition_list: List of temperature/time definitions"""
    send_dict = {}
    last_temperature = 17.0
    for weekday, templist in definition_list.items():
        for i in range(1, MAX_POINTS+1):
            temperature_key = "TEMPERATURE_{0}_{1}".format(weekday.upper(), i)
            endtime_key = "ENDTIME_{0}_{1}".format(weekday.upper(), i)
            if i > len(templist):
                temperature_value = last_temperature
                endtime_value = MAX_ENDTIME
            else:
                temperature_value = templist[i-1]["temperature"]
                endtime_value = templist[i-1]["minutes_from_midnight"]
                last_temperature = temperature_value

            send_dict[temperature_key] = float(temperature_value)
            send_dict[endtime_key] = endtime_value
            if endtime_value == MAX_ENDTIME:
                break
    print(send_dict)
    xmlc.putParamset(int(id), 0, "MASTER", send_dict)


def set_temp_config(xmlc, args):
    """Read file and send to server

    :param id: ID to receive values
    :param template_file: File to read from"""
    config_from_file = read_from_file(args.file)
    set_temp_to_homegear(xmlc, args.id, config_from_file)


def _map_cli_config(mapping, args, ini):
    res_config = {}
    for i in mapping:
        if i in args and args[i]:
            res_config[i] = args[i]
        elif ini and i in ini:
            res_config[i] = ini[i]
        else:
            raise ConfigError(f"Config/Argument for {i} set!")
    return res_config


def get_config_and_args():
    parser = argparse.ArgumentParser(description='Communicate with homegear.')
    parser.add_argument("-s", "--server", help="server to use")
    parser.add_argument("-u", "--user", help="user")
    parser.add_argument("-p", "--port", help="xmlrpc port")
    parser.add_argument("-P", "--password", help="password for server/user, if"
                        " empty or not set in the configuration, ask user")
    parser.add_argument("-c", "--config", help="configuration file instead of "
                        "default config")
    subparsers = parser.add_subparsers()

    list_p = subparsers.add_parser("list", help="Print list of devices")
    list_p.set_defaults(func=list_heaters)

    cconfig_p = subparsers.add_parser("print-config",
                                      help="Print current config")
    cconfig_p.add_argument("id")
    cconfig_p.set_defaults(func=print_paramsets)

    ptemp_c = subparsers.add_parser(
        "print-temp", help="Print current temperature configuration")
    ptemp_c.add_argument("id")
    ptemp_c.set_defaults(func=print_temp_config)

    settemp_p = subparsers.add_parser(
        "set-temp", help="Set Device Temperature Configuration")
    settemp_p.add_argument("id")
    settemp_p.add_argument("file")
    settemp_p.set_defaults(func=set_temp_config)

    args = parser.parse_args()

    if "func" not in args:
        print("No Command given", file=sys.stderr)
        parser.print_usage()
        exit(1)

    ini_config = configparser.ConfigParser()
    if args.config:
        ini_config.read(args.config)
    else:
        ini_config.read(os.path.expanduser("~/.config/hm-prowee/config"))

    sec_config = ini_config["main"] if "main" in ini_config else None

    try:
        res_config = _map_cli_config(["server", "user", "port"],
                                     vars(args), sec_config)
    except ConfigError as e:
        print(e, file=sys.stderr)
        exit(1)

    if args.password:
        res_config["password"] = args.password
    elif sec_config and "password" in sec_config:
        res_config["password"] = sec_config["password"]
    else:
        res_config["password"] = getpass.getpass()

    return (res_config, args)


def main():
    (cfg, args) = get_config_and_args()

    ctx = ssl._create_unverified_context()

    xmlc = xmlrpc.client.ServerProxy(f"https://{cfg['user']}:{cfg['password']}"
                                     f"@{cfg['server']}:{cfg['port']}/",
                                     context=ctx)

    try:
        version = xmlc.getVersion()
        print(f"Successfully connected to server {cfg['server']}"
              f", running version {version}", file=sys.stderr)
    except Exception:
        print("Connection not successful, please check your parameters.")
        exit(1)

    args.func(xmlc, args)


if __name__ == "__main__":
    main()
