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

def read_from_file(filename):
    lines = []
    with open(filename, "r") as config:
        lines = config.read().splitlines()

    for i in lines:
        l = str(i).split(":")
        weekday = l[0]
        for i in l[1:]:
            print(weekday, i)

def set_temp_config(id, template_file):
    config_from_file = read_from_file(template_file)

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

