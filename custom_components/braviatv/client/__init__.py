"""Sony Bravia Client"""
import datetime
import json
import os
import requests
import socket
import struct
import time

from .const import (
    IRCC_DATA,
    IRCC_HEADERS,
    MINIMUM_UPDATE_INTERVAL,
    TIMEOUT,
    VALID_EXT_INPUT_SCHEMES,
    VALID_TV_SCHEMES,
)
from .device import SonyBraviaDevice


class SonyBraviaException(Exception):
    """Raised when an update has failed."""


class SonyBraviaClient(object):

    def __init__(self, host, psk, save_location=None):
        self.host = host
        self.psk = psk
        self.data = {}
        self.last_update_timestamp = time.time()
        self.save_location = save_location

    @property
    def auth_header(self):
        return {"X-Auth-PSK": self.psk}

    def send_ircc(self, code):
        if code is None:
            return
        try:
            response = requests.post(
                url=f"http://{self.host}/sony/IRCC",
                data=IRCC_DATA.format(code).encode("UTF-8"),
                headers={**self.auth_header, **IRCC_HEADERS},
                timeout=TIMEOUT,
            )
        except (requests.exceptions.HTTPError, requests.exceptions.Timeout, Exception) as exception_instance:
            raise SonyBraviaException(f"HTTPError: {str(exception_instance)}")
        else:
            content = response.content
            return content

    def send_json(self, endpoint, method, id, params, version):
        data = dict(method=method, id=id, params=params, version=version)
        try:
            response = requests.post(
                url=f"http://{self.host}/sony/{endpoint}",
                data=json.dumps(data).encode("UTF-8"),
                headers=self.auth_header,
                timeout=TIMEOUT,
            )
        except (requests.exceptions.HTTPError, requests.exceptions.Timeout, Exception) as exception_instance:
            raise SonyBraviaException(f"HTTPError: {str(exception_instance)}")
        else:
            response = json.loads(response.content.decode("utf-8"))
            if "error" in response:
                raise SonyBraviaException(f"Invalid response: {response},\nendpoint: {endpoint},\nmethod: {method},\nparams: {params},\ndata: {data}")
            self.save_response(response=response, name=method)
            return response

    def define_end_time(self, tm, secs):
        fulldate = datetime.datetime(100, 1, 1, tm.hour, tm.minute, tm.second)
        fulldate = fulldate + datetime.timedelta(seconds=secs)
        return fulldate.time()

    def save_response(self, response, name="response"):
        if self.save_location and response:
            if not os.path.isdir(self.save_location):
                os.mkdir(self.save_location)
            name = name.replace("/", "_").replace(".", "_")
            with open(f"{self.save_location}/{name}.json", "w") as file:
                json.dump(response, file, default=lambda o: "not-serializable", indent=4, sort_keys=True)
            file.close()

    def update(self):
        try:
            if time.time() - self.last_update_timestamp <= MINIMUM_UPDATE_INTERVAL:
                return self.data

            self.data["power_status"] = self.get_power_status()

            if not self.data.get("interface_info"):
                self.data["interface_info"] = self.get_interface_info()

            if not self.data.get("system_info"):
                self.data["system_info"] = self.get_system_info()

            if self.data["power_status"] != "active":
                self.last_update_timestamp = time.time()
                return SonyBraviaDevice(self, self.data)

            self.data["apps"] = self.get_apps()
            self.data["commands"] = self.get_commands()
            self.data["sources"] = self.get_sources()
            self.data["volume_info"] = self.get_volume_info()
            self.data["playing_info"] = self.get_playing_info()
            self.data["playing_time"] = self.get_playing_time(self.data["playing_info"])
            self.save_response(response=self.data, name="update")

            self.last_update_timestamp = time.time()
        except SonyBraviaException:
            return SonyBraviaDevice(self, self.data)
        return SonyBraviaDevice(self, self.data)

    def get_apps(self):
        _apps = []
        response = self.send_json(
            endpoint="appControl",
            method="getApplicationList",
            id=60,
            params=[],
            version="1.0",
        )
        if not response.get("error"):
            _apps.extend(response.get("result")[0])

        apps = {}
        for app in _apps:
            title = app["title"].replace("&amp;", "&")
            apps[title] = {
                "uri": app["uri"],
            }
            icon = app["icon"]
            if icon:
                apps[title]["icon"] = icon
        return apps

    def get_commands(self):
        _commands = []
        response = self.send_json(
            endpoint="system",
            method="getRemoteControllerInfo",
            id=54,
            params=[],
            version="1.0",
        )
        if not response.get("error"):
            _commands.extend(response.get("result")[1])

        commands = {}
        for command in _commands:
            commands[command["name"]] = command["value"]
        return commands

    def get_interface_info(self):
        interface_info = {}
        response = self.send_json(
            endpoint="system",
            method="getInterfaceInformation",
            id=33,
            params=[],
            version="1.0",
        )
        if not response.get("error"):
            interface_info = response.get("result")[0]
        return interface_info

    def get_playing_info(self):
        playing_info = {}
        response = self.send_json(
            endpoint="avContent",
            method="getPlayingContentInfo",
            id=103,
            params=[],
            version="1.0",
        )
        if not response.get("error"):
            playing_info = response.get("result")[0]
        return playing_info

    def get_playing_time(self, playing_info):
        # startdatetime format 2017-03-24T00:00:00+0100
        playing_time = {}
        start_date_time = playing_info.get("startDateTime")
        duration = playing_info.get("durationSec")
        if start_date_time and duration:
            start_date_time = start_date_time[:19]

            start = datetime.datetime.strptime(
                start_date_time, "%Y-%m-%dT%H:%M:%S"
            ).time()
            end = self.define_end_time(start, duration)
            start_time = start.strftime("%H:%M")
            end_time = end.strftime("%H:%M")
            playing_time = dict(start_time=start_time, end_time=end_time)
        return playing_time

    def get_power_status(self):
        power_status = None
        response = self.send_json(
            endpoint="system",
            method="getPowerStatus",
            id=50,
            params=[],
            version="1.0",
        )
        if not response.get("error"):
            power_status = response.get("result")[0].get("status")
        return power_status

    def get_sources(self):
        _sources = []
        response = self.send_json(
            endpoint="avContent",
            method="getSourceList",
            id=1,
            params=[dict(scheme="tv")],
            version="1.0",
        )
        if not response.get("error"):
            results = response.get("result")[0]
            for result in results:
                if result["source"] in VALID_TV_SCHEMES:
                    response = self.send_json(
                        endpoint="avContent",
                        method="getContentList",
                        id=88,
                        params=[result],
                        version="1.0",
                    )
                    if not response.get("error"):
                        _sources.extend(response.get("result")[0])

        response = self.send_json(
            endpoint="avContent",
            method="getSourceList",
            id=1,
            params=[dict(scheme="extInput")],
            version="1.0",
        )
        if not response.get("error"):
            results = response.get("result")[0]
            for result in results:
                if result["source"] in VALID_EXT_INPUT_SCHEMES:
                    response = self.send_json(
                        endpoint="avContent",
                        method="getContentList",
                        id=88,
                        params=[result],
                        version="1.0",
                    )
                    if not response.get("error"):
                        _sources.extend(response.get("result")[0])

        _input_labels = []
        response = self.send_json(
            endpoint="avContent",
            method="getCurrentExternalInputsStatus",
            id=105,
            params=[],
            version="1.1",
        )
        if not response.get("error"):
            _input_labels.extend(response.get("result")[0])

        input_labels = {}
        for input in _input_labels:
            if input["label"]:
                input_labels[input["title"]] = input["label"]

        sources = {}
        for source in _sources:
            label = input_labels.get(source["title"], source["title"])
            if label:
                sources[label] = source["uri"]
        return sources

    def get_system_info(self):
        system_info = {}
        response = self.send_json(
            endpoint="system",
            method="getSystemInformation",
            id=33,
            params=[],
            version="1.0",
        )
        if not response.get("error"):
            system_info = response.get("result")[0]
        return system_info

    def get_volume_info(self):
        volume_info = {}
        response = self.send_json(
            endpoint="audio",
            method="getVolumeInformation",
            id=33,
            params=[],
            version="1.0",
        )
        if not response.get("error"):
            results = response.get("result")[0]
            for result in results:
                if result["target"] == "speaker":
                    volume_info = result
        return volume_info

    def wake_on_lan(self, mac_address):
        if mac_address:
            addr_byte = mac_address.split(":")
            hw_addr = struct.pack(
                "BBBBBB",
                int(addr_byte[0], 16),
                int(addr_byte[1], 16),
                int(addr_byte[2], 16),
                int(addr_byte[3], 16),
                int(addr_byte[4], 16),
                int(addr_byte[5], 16),
            )
            msg = b"\xff" * 6 + hw_addr * 16
            socket_instance = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            socket_instance.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            socket_instance.sendto(msg, ("<broadcast>", 9))
            socket_instance.close()
