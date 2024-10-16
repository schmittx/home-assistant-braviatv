"""Sony Bravia Client"""
from .const import VALID_TV_SCHEMES


class SonyBraviaDevice(object):

    def __init__(self, client, data):
        self.client = client
        self.data = data

    @property
    def power_status(self):
        return self.data.get("power_status")

    @power_status.setter
    def power_status(self, status):
        self.client.send_json(
            endpoint="system",
            method="setPowerStatus",
            id=55,
            params=[dict(status=bool(status))],
            version="1.0",
        )

    @property
    def is_on(self):
        return bool(self.power_status == "active")

    @property
    def available(self):
        return bool(self.power_status is not None)

    @property
    def product_category(self):
        return self.data.get("interface_info", {}).get("productCategory")

    @property
    def product_name(self):
        return self.data.get("interface_info", {}).get("productName")

    @property
    def model_name(self):
        return self.data.get("interface_info", {}).get("modelName")

    @property
    def interface_version(self):
        return self.data.get("interface_info", {}).get("interfaceVersion")

    @property
    def model(self):
        return self.data.get("system_info", {}).get("model")

    @property
    def name(self):
        return self.data.get("system_info", {}).get("name")

    @property
    def serial(self):
        return self.data.get("system_info", {}).get("serial")

    @property
    def mac_address(self):
        return self.data.get("system_info", {}).get("macAddr")

    @property
    def generation(self):
        return self.data.get("system_info", {}).get("generation")

    @property
    def cid(self):
        return self.data.get("system_info", {}).get("cid")

    @property
    def apps(self):
        return self.data.get("apps", {})

    @property
    def commands(self):
        return self.data.get("commands", {})

    @property
    def sources(self):
        return self.data.get("sources", {})

    @property
    def volume(self):
        return self.data.get("volume_info", {}).get("volume")

    @volume.setter
    def volume(self, volume):
        self.client.send_json(
            endpoint="audio",
            method="setAudioVolume",
            id=98,
            params=[dict(target="speaker", volume=volume, ui="on")],
            version="1.2",
        )

    @property
    def mute(self):
        return bool(self.data.get("volume_info", {}).get("mute"))

    @mute.setter
    def mute(self, mute):
        self.client.send_json(
            endpoint="audio",
            method="setAudioMute",
            id=601,
            params=[dict(status=bool(mute))],
            version="1.0",
        )

    @property
    def source(self):
        return self.data.get("playing_info", {}).get("source")

    @property
    def tv_input_active(self):
        return bool(self.source in VALID_TV_SCHEMES)

    @property
    def title(self):
        return self.data.get("playing_info", {}).get("title")

    @property
    def display_number(self):
        return self.data.get("playing_info", {}).get("dispNum")

    @property
    def program_title(self):
        return self.data.get("playing_info", {}).get("programTitle")

    @property
    def start_time(self):
        return self.data.get("playing_time", {}).get("start_time")

    @property
    def end_time(self):
        return self.data.get("playing_time", {}).get("end_time")

    def set_active_app(self, uri):
        self.client.send_json(
            endpoint="appControl",
            method="setActiveApp",
            id=601,
            params=[dict(uri=uri)],
            version="1.0",
        )

    def set_play_content(self, uri):
        self.client.send_json(
            endpoint="avContent",
            method="setPlayContent",
            id=101,
            params=[dict(uri=uri)],
            version="1.0",
        )

    def send_command(self, command):
        self.client.send_ircc(command)

    def wake_on_lan(self):
        self.client.wake_on_lan(self.mac_address)
