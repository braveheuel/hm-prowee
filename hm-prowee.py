#! /usr/bin/env python3
# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2016 Christoph Heuel <mail@christoph-heuel.net>
# Distributed under terms of the MIT license.
#
"""
Usage:
    hm-prowee -u <user> -s <server> -p <port> list
    hm-prowee -u <user> -s <server> -p <port> print-config <id>
    hm-prowee -u <user> -s <server> -p <port> set-temp <id> <file>
"""
import xmlrpc.client
import ssl
import json
from docopt import docopt
import getpass

MAX_POINTS = 13
MAX_ENDTIME = 1440

def pp(jsontext):
    print(json.dumps(jsontext, sort_keys=True, indent=4, separators=(',', ': ')))

def list_devices():
    try:
        heaters = xmlc.getPeerId(4, "HM-CC-RT-DN")
    except:
        print("Can't load list of Devices!")
        exit(1)
    for i in heaters:
        print(xmlc.getDeviceInfo(i))

def print_paramsets(id):
    pp(xmlc.getParamset(int(id), 0, "MASTER"))

def calculate_minutes_from_midnight(timedef):
    l = timedef.split(":")
    if not len(l) == 2:
        raise TypeError("{0} is not in format HH:MM!".format(timedef))
    hours = int(l[0])
    minutes = hours*60 + int(l[1])
    if minutes > MAX_ENDTIME:
        minutes = MAX_ENDTIME
    return minutes

def parse_temperature_item(item):
    temp_time_tupel = item.split(">")
    temperature = float(temp_time_tupel[0].strip())
    minutes_from_midnight = calculate_minutes_from_midnight(temp_time_tupel[1].strip())
    return { 'minutes_from_midnight' : minutes_from_midnight, 'temperature' : temperature}

def parse_temperature_definition(temp_def_raw):
    temp_def_list = filter(None, temp_def_raw.split(";"))
    l = []
    for i in temp_def_list:
        l.append(parse_temperature_item(i))
    return l

def read_from_file(filename):
    lines = []
    with open(filename, "r") as config:
        lines = config.read().splitlines()

    deflist = {}
    for i in lines:
        l = i.split("=")
        weekday = l[0].strip()
        temp_def = parse_temperature_definition(l[1])
        deflist[weekday] = temp_def

    return deflist

def set_temp_to_homegear(id, definition_list):
    paramset_list = []
    last_temperature = 17.0
    for weekday, templist in definition_list.items():
        for i in range(1, MAX_POINTS+1):
            temp_dict = {}
            endtime_dict = {}
            temperature_key = "TEMPERATURE_{0}_{1}".format(weekday.upper(), i)
            endtime_key = "ENDTIME_{0}_{1}".format(weekday.upper(), i)
            if i > len(templist):
                temperature_value = last_temperature
                endtime_value = MAX_ENDTIME
            else:
                temperature_value = templist[i-1]["temperature"]
                endtime_value = templist[i-1]["minutes_from_midnight"]
                last_temperature = temperature_value

            temp_dict[temperature_key] = float(temperature_value)
            endtime_dict[endtime_key] = endtime_value
            paramset_list.append(temp_dict)
            paramset_list.append(endtime_dict)
            if endtime_value == MAX_ENDTIME:
                break
    for i in paramset_list:
        print("Sending", i, "...")
        xmlc.putParamset(int(id), 0, "MASTER", i)

def set_temp_config(id, template_file):
    config_from_file = read_from_file(template_file)
    set_temp_to_homegear(id, config_from_file)

if __name__ == "__main__":
    arguments = docopt(__doc__)
    ctx = ssl._create_unverified_context()

    passwd = getpass.getpass()

    xmlc = xmlrpc.client.ServerProxy("https://{0}:{1}@{2}:{3}/".format(arguments['<user>'], passwd, arguments['<server>'], arguments['<port>']), context=ctx)
    if arguments['list']:
        list_devices()
    elif arguments['print-config']:
        print_paramsets(arguments["<id>"])
    elif arguments['set-temp']:
        set_temp_config(arguments["<id>"], arguments["<file>"])

