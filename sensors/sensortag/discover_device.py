#!/usr/bin/python
# -*- mode: python; coding: utf-8 -*-

# Copyright (C) 2016, shima-nigoro
# This software is under the terms of Apache License v2 or later.

from __future__ import print_function
from gattlib import DiscoveryService

class DiscoverDevice():
    def GetDeviceList(self):
        service = DiscoveryService("hci0")
        device = service.discover(2)
        return device

if __name__ == '__main__':
    devList = DiscoverDevice().GetDeviceList()
    for address, name in devList.items():
        print("name: {}, address: {}".format(name, address))
