#!/usr/bin/python
# -*- mode: python; coding: utf-8 -*-

# Copyright (C) 2016, shima-nigoro
# This software is under the terms of Apache License v2 or later.

from __future__ import print_function

import sys
import ctypes
import time
import struct
import boto3
import datetime
from gattlib import GATTRequester, DiscoveryService

class SensorTag(object):
    def __init__(self, address):
        self.requester = GATTRequester(address, False)
        self.humidity = float(0.0)
        self.temperature = float(0.0)
        self.object_temperature = float(0.0)
        self.barometer = float(0.0)
        self.gyrometer = {"x":float(0.0), "y":float(0.0), "z":float(0.0)}
        self.acceleration = {"x":float(0.0), "y":float(0.0), "z":float(0.0)}
        self.geomagnetism = {"x":float(0.0), "y":float(0.0), "z":float(0.0)}
        self.lux = float(0.0)

    def connect(self):
        print("Connecting...")
        self.requester.connect(True)
        print("Succeed.")

    def check_status(self):
        status = "connected" if self.requester.is_connected() else "not connected"
        print("Checking current status: {}".format(status))

    def disconnect(self):
        print(str("Disconnecting..."))
        self.requester.disconnect()
        print("Succeed.")

    def enable_humidity(self, enable):
        status = '\x01' if enable else '\x00'
        self.requester.write_by_handle(0x2f, status)

    def check_humidity(self):
        time.sleep(3)
        raw_data = self.requester.read_by_handle(0x2c)[0]
        raw_temp = (ord(raw_data[1]) << 8) + ord(raw_data[0])
        raw_humi = (ord(raw_data[3]) << 8) + ord(raw_data[2])
        self.temperature = round((float(raw_temp) / float(65536)) * 165 - 40, 1)
        self.humidity = round((float(raw_humi) / float(65536)) * 100, 1)

    def enable_IRtemperature(self, enable):
        status = '\x01' if enable else '\x00'
        self.requester.write_by_handle(0x27, status)

    def check_IRtemperature(self):
        time.sleep(3)
        raw_data = self.requester.read_by_handle(0x24)[0]
        raw_obj = (ord(raw_data[1]) << 8) + ord(raw_data[0])
        raw_amb = (ord(raw_data[3]) << 8) + ord(raw_data[2])
        self.object_temperature = round((float(raw_obj) / 4.0 ) * 0.03125, 1)
        self.temperature = round((float(raw_amb) / 4.0 ) * 0.03125, 1)

    def enable_Barometer(self, enable):
        status = '\x01' if enable else '\x00'
        self.requester.write_by_handle(0x37, status)

    def check_Barometer(self):
        time.sleep(3)
        raw_data = self.requester.read_by_handle(0x34)[0]
        raw_temp = (ord(raw_data[2]) << 16) + (ord(raw_data[1]) << 8) + ord(raw_data[0])
        raw_baro = (ord(raw_data[5]) << 16) + (ord(raw_data[4]) << 8) + ord(raw_data[3])
        self.temperature = round(float(raw_temp) / 100.0, 1)
        self.barometer = round(float(raw_baro) / 100.0, 1)

    def enable_9AxisSensor(self, enable):
        status = '\x7f\x00' if enable else '\x00\x00'
        self.requester.write_by_handle(0x3f, status)

    def check_9AxisSensor(self):
        time.sleep(3)
        raw_data = self.requester.read_by_handle(0x3c)[0]
        raw_gyro_x = struct.unpack('h',raw_data[0] + raw_data[1])[0]
        raw_gyro_y = struct.unpack('h',raw_data[2] + raw_data[3])[0]
        raw_gyro_z = struct.unpack('h',raw_data[4] + raw_data[5])[0]
        raw_acce_x = struct.unpack('h',raw_data[8] + raw_data[7])[0]
        raw_acce_y = struct.unpack('h',raw_data[10] + raw_data[9])[0]
        raw_acce_z = struct.unpack('h',raw_data[10] + raw_data[11])[0]
        raw_geom_x = struct.unpack('h',raw_data[12] + raw_data[13])[0]
        raw_geom_y = struct.unpack('h',raw_data[14] + raw_data[15])[0]
        raw_geom_z = struct.unpack('h',raw_data[16] + raw_data[17])[0]
        self.gyrometer["x"] = round(float(raw_gyro_x) / (65536 / 500),2)
        self.gyrometer["y"] = round(float(raw_gyro_y) / (65536 / 500),2)
        self.gyrometer["z"] = round(float(raw_gyro_z) / (65536 / 500),2)
        #/2.0 ? /8.0 ?
        self.acceleration["x"] = float(raw_acce_x) / (32768.0/8.0)
        self.acceleration["y"] = float(raw_acce_y) / (32768.0/8.0)
        self.acceleration["z"] = float(raw_acce_z) / (32768.0/8.0)
        self.geomagnetism["x"] = float(raw_geom_x)
        self.geomagnetism["y"] = float(raw_geom_y)
        self.geomagnetism["z"] = float(raw_geom_z)

    def enable_Optical(self, enable):
        status = '\x01' if enable else '\x00'
        self.requester.write_by_handle(0x47, status)

    def check_Optical(self):
        raw_data = self.requester.read_by_handle(0x44)[0]
        raw_lux = (ord(raw_data[1]) << 8) + ord(raw_data[0])
        raw_lux_m = raw_lux & 0b0000111111111111
        raw_lux_e = (raw_lux & 0b1111000000000000) >> 12
        self.lux = raw_lux_m * (0.01 * pow(2.0,raw_lux_e))

class Server():
    def up(self, json):
        service = DiscoveryService("hci0")
        device = service.discover(2)
        return device


class DiscoverDevice():
    def GetDeviceList(self):
        service = DiscoveryService("hci0")
        device = service.discover(2)
        return device

if __name__ == '__main__':
    dynamodb = boto3.resource('dynamodb', region_name='us-west-1')
    date = datetime.datetime.now().strftime('%Y%m%d%H%M%S.%f')
    table = dynamodb.Table('botMansion')
    table.put_item(
        Item={
            'eventName': 'pythonTest',
            'date': date,
            'data': {'val': 10}
            }
        )

    #if len(sys.argv) < 2:
    #    print("Usage: {} <addr>".format(sys.argv[0]))
    #    sys.exit(1)
    #tag = SensorTag(sys.argv[1])
    #tag.connect()
    #tag.enable_Optical(True)
    #time.sleep(3)
    #while True:
    #    tag.check_Optical()
    #    print(tag.lux, ' lux')
    #    time.sleep(1)

    tag.enable_9AxisSensor(True)
    time.sleep(3)

    #state = False # True if gt 0.4 else Flase
    #count = 0
    #while True:
    #    tag.check_9AxisSensor()
    #    print(tag.acceleration["x"],"G ",tag.acceleration["y"],"G ",tag.acceleration["z"],"G")
    #
    #    if state == False and tag.acceleration["z"] > 0.0:
    #        state = True
    #        print('push to the server')
    #        # push to server
    #    else:
    #        state = False
    #        dynamodb = boto3.resource('dynamodb')
    #        date = datetime.datetime.now().strftime('%Y%m%d%H%M%S.%f')
    #        table = dynamodb.Table('botMansion')
    #        table.put_item(
    #
    #
    #    time.sleep(1)



    #tag.enable_humidity(True)
    #tag.check_humidity()
    #print(tag.humidity,"% ", tag.temperature, "C")
    #
    #tag.enable_IRtemperature(True)
    #tag.check_IRtemperature()
    #print(tag.object_temperature,"C ", tag.temperature, "C")
    #
    #tag.enable_Barometer(True)
    #tag.check_Barometer()
    #print(tag.barometer,"hPa ", tag.temperature, "C")
    #
    #tag.enable_9AxisSensor(True)
    #tag.check_9AxisSensor()
    #print(tag.gyrometer["x"],"deg/sec ",tag.gyrometer["y"],"deg/sec ",tag.gyrometer["z"],"deg/sec")
    #print(tag.acceleration["x"],"G ",tag.acceleration["y"],"G ",tag.acceleration["z"],"G")
    #print(tag.geomagnetism["x"],"uT ",tag.geomagnetism["y"],"uT ",tag.geomagnetism["z"],"uT")
    #
    #tag.enable_Optical(True)
    #tag.check_Optical()
    #print(tag.lux,"lx")

    tag.disconnect()
