#!/usr/bin/env python3
import datetime
import os
import time
import uuid

import requests
import serial

POST_URL = "http://192.168.0.2:8000"


class Gps:
    def __init__(self, serial_connection):
        self.serial = serial_connection
        self.serial.reset_input_buffer()
        self.serial.write(b"ATE0\n")
        self.serial.flush()
        resp = self.serial.read(100).decode('utf-8')  # just read a shit ton of stuff meh
        if resp.strip("\r\n") == "ERROR":
            print("Board seems broken. Try to fix?")
        else:
            print("Board ready.")
        if os.path.isfile("uuid.txt"):
            f = open("uuid.txt")
            self.uuid = f.read()
            print("Device UUID: {}".format(self.uuid))
        else:
            f = open("uuid.txt", mode="w")
            self.uuid = str(uuid.uuid4())
            print("No UUID found. Generated a new one: {}".format(self.uuid))
            f.write(self.uuid)
        f.close()

    def check_ok(self):
        """
        Checks to see if the board is running correctly.
        :return: bool
        """
        self.serial.reset_input_buffer()
        self.serial.write(b"AT\n")
        self.serial.flush()
        resp = self.serial.read(100).decode("utf-8")
        if "ERROR" in resp:
            print("Board seems broken. Try to fix?")
            print(resp)
            return False
        else:
            print("Board ok.")
            return True

    def location(self):
        """
        Get the location from the GPS device and encode it into a dict with the uuid
        :return: dict
        """
        self.serial.reset_input_buffer()
        self.serial.write(b"AT+CGNSINF\n")
        self.serial.flush()
        time.sleep(1)  # sometimes it's a little slow to respond
        resp = self.serial.read(1000).decode('utf-8').strip("OKCGNSINF+:\r\n ")  # strip out all the garbage boilerplate
        if resp == "ERROR":
            # assume temporary error, and retry the next cycle
            print("Board is a little overwhelmed. Waiting for next cycle.")
            return {"error": "Wait a bit", "uuid": self.uuid}
        resp_split = resp.split(",")
        if resp_split[0] == "0":
            print("GPS is off")
            return {"error": "GPS chip disabled", "uuid": self.uuid}
        elif resp_split[1] == "0":
            print("No lock. Searching...")
            return {"error": "No lock", "uuid": self.uuid}
        else:
            print("Sending location to server")
            return {
                "date_time": datetime.datetime(
                    int(resp_split[2][:4]),
                    int(resp_split[2][4:6]),
                    int(resp_split[2][6:8]),
                    int(resp_split[2][8:10]),
                    int(resp_split[2][10:12]),
                    tzinfo=datetime.timezone.utc
                ).isoformat(),  # YYYY-MM-DDTHH:MM:SS
                "latitude": resp_split[3],  # in decimal degrees
                "longitude": resp_split[4],  # in decimal degrees
                "altitude": resp_split[5],  # in metres
                "speed": resp_split[6],  # in kilometres/hour
                "direction": resp_split[7],  # in degrees
                "uuid": self.uuid,  # the uuid
            }

    def power(self, setting=None):
        """
        Set the GPS receiver power "on" or "off", or determine the power (no arg)
        :param setting: str
        :return: bool
        """
        if setting is None:
            self.serial.write(b"AT+CGNSPWR?\n")
            self.serial.flush()
            self.serial.reset_input_buffer()
            resp = self.serial.read(100).decode('utf-8').strip("\r\n+CGNSPWROK: ")
            return resp == "1"
        elif setting == "on":
            self.serial.write(b"AT+CGNSPWR=1")
            self.serial.flush()
            self.serial.reset_input_buffer()
        elif setting == "off":
            self.serial.write(b"AT+CGNSPWR=0")
            self.serial.flush()
            self.serial.reset_input_buffer()
        else:
            print("Improper argument: {}".format(setting))
            return False


class Gprs:
    def __init__(self, serial_connection):
        self.serial = serial_connection

    def online(self, setting=None):
        """
        Set the GPRS receiver power "on" or "off", or determine the power (no arg)
        :param setting: str
        :return: bool
        """
        return True  # use WiFi for Proof-of-concept

    def send(self, data):
        """
        Transmit the location data to the system
        :param data: dictionary returned by self.location()
        :return: bool: success
        """
        pass


class EmbeddedSystem:
    def __init__(self, serial_file):
        if os.geteuid() != 0:
            print("This must be run as root")
            exit(1)
        self.serial = serial.Serial(serial_file, baudrate=115200, timeout=0)
        self.gps = Gps(self.serial)
        self.gprs = Gprs(self.serial)

    def run_forever(self, interval):
        time.sleep(10)
        if not self.gps.power():
            self.gps.power("on")
        while True:
            time.sleep(interval)
            locat = self.gps.location()
            try:
                r = requests.post(POST_URL, json=locat)
                if r.status_code != 200:
                    print("Server rejected our data: {} {}".format(r.status_code, r.reason))
                else:
                    print("Sent data to server. Sleeping.")
            except requests.exceptions.ConnectionError:
                print("Connection Failure")
            except requests.exceptions.RequestException:
                print("Server failure")


if __name__ == "__main__":
    ems = EmbeddedSystem("/dev/ttyUSB0")
    ems.run_forever(5)
