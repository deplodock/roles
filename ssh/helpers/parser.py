#!/usr/bin/env python
# Copyright 2017 deplodock.ru
# Licensed under GPLv3 or later. See https://www.gnu.org/licenses/gpl-3.0.en.html

import requests
import argparse
import os
import sys
import json


def parse_command_line():
    """Parse command line"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--inventory", help="Inventory to populate")
    parser.add_argument("-g", "--group", help="Group to populate")
    parser.add_argument("-t", "--token", help="Token")
    parser.add_argument("-c", "--config", help="Config to parse", default="/etc/ssh/sshd_config")
    parser.add_argument("-p", "--prefix", help="Variable prefix", default="ssh_")
    return parser.parse_args()


class Populator():

    API = "https://api.deplodock.ru/v1"

    def __init__(self):
        self.args = parse_command_line()
        self.group = self.args.group
        self.config = self.args.config
        self.prefix = ""
        self.token = ""
        self.inventory = ""
        if self.args.prefix is not None:
            self.prefix = self.args.prefix

        # get token and inventory name
        self.get_environ()

        self.api_url = "/".join([self.API, "inventory", self.inventory,
                                 "groups", self.group, "vars"])
        self.prepared = {}

    def get_environ(self):
        """Get DK_TOKEN and DK_INVENTORY from os environment"""
        token = os.environ.get("DK_TOKEN")
        inventory = os.environ.get("DK_INVENTORY")
        if token is None:
            if self.args.token is not None:
                self.token = self.args.token
            else:
                sys.stderr.write("Token not provided and DK_TOKEN is empty\n")
                sys.exit(1)
        else:
            self.token = token

        if inventory is None:
            if self.args.inventory is not None:
                self.inventory = self.args.inventory
            else:
                sys.stderr.write("Inventory name not provided and DK_INVENTORY is empty\n")
                sys.exit(1)
        else:
            self.inventory = inventory

    def parse_config(self):
        """Parse config file and return dict{"string": "string"}"""
        with open(self.config, "r") as f:
            for line in f.readlines():
                if line.startswith("#") or line == "\n":
                    continue
                line = line.strip()
                conf_line = line.split()
                variable = "".join([self.prefix, conf_line[0]])
                del(conf_line[0])
                value = " ".join(conf_line)
                self.prepared[variable] = value

    def populate(self):
        """Populate group variables"""
        for k in self.prepared.keys():
            var_url = "/".join([self.api_url, k])
            header = {"X-Auth-Token": self.token}
            resp = requests.put(var_url, headers=header, data=self.prepared[k])
            if json.loads(resp.content)["status"] == "already exixts":
                resp = requests.post(var_url, headers=header, data=self.prepared[k])
            print(resp.content)
        # finally provide path to config file
        variable = "".join([self.prefix, "config_file"])
        var_url = "/".join([self.api_url, variable])
        resp = requests.put(var_url, headers=header, data=self.prepared[k])
        if json.loads(resp.content)["status"] == "already exixts":
            resp = requests.post(var_url, headers=header, data=self.prepared[k])
        print(resp.content)


if __name__ == "__main__":
    populator = Populator()

    # Parse configuration file
    populator.parse_config()
    populator.populate()
