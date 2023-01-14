#!/usr/bin/python3
"""
Inofficial api
"""
import logging
import re

from dataclasses import dataclass
from datetime import datetime

import requests

from exceptions import CasambiApiException
from consts import DEVICE_NAME

_LOGGER = logging.getLogger(__name__)


@dataclass()
class Session:
    session: str
    network: str
    manager: bool
    keyID: int
    expires: datetime

    role: int = 3

    def expired(self) -> bool:
        return datetime.utcnow() > self.expires


class Casambi:
    """
    Casambi api object
    """

    def __init__(self, *, network_password):
        self.network_password = network_password
        self.url = "https://api.casambi.com"

        self.session = None

    def login(self, *, password: str, network_id: str) -> bool:
        """ """
        url = f"https://api.casambi.com/network/{network_id}/session"

        headers = {
            "Content-type": "application/json",
        }

        payload = {"password": password, "deviceName": DEVICE_NAME}

        response = requests.post(url, headers=headers, json=payload)

        if response.status_code != 200:
            reason = "login: failed with "
            reason += f"status_code: {response.status_code} "
            reason += f"response: {response.text} "
            reason += f"url: {url}"

            raise CasambiApiException(reason)

        data = response.json()

        data["expires"] = datetime.utcfromtimestamp(data["expires"] / 1000)
        self.session = Session(**data)

        return data

    def authenticated(self) -> bool:
        if not self.session:
            return False
        return not self.session.expired()

    def get_network_id_from_uuid(self, *, uuid: str) -> str:
        """
        Get network id from uuid
        """
        data = self.get_network_information_from_uuid(uuid=uuid)

        if "id" in data:
            return data["id"]
        return None

    def get_network_information(self, *, network_id) -> dict:
        """
        Get network information
        """

        if not self.authenticated:
            raise CasambiApiException("Need to be authenticated!")

        url = f"{self.url}/network/{network_id}/"

        payload = {"formatVersion": 1, "deviceName": DEVICE_NAME}
        headers = {"X-Casambi-Session": self.session.session}

        response = requests.get(url, headers=headers, json=payload)

        if response.status_code != 200:
            reason = "get_network_information_from_uuid: failed with"
            reason += f"status_code: {response.status_code} "
            reason += f"response: {response.text} "
            reason += f"url {url}"

            raise CasambiApiException(reason)

        data = response.json()

        return data

    def get_network_information_from_uuid(self, *, uuid: str) -> dict:
        """
        https://api.casambi.com/network/uuid/

        Response

        '{"id":"<ID>","uuid":"<UUID>","name":"<Name>","type":2,"grade":0}'

        """
        mac_regexp = re.compile("^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
        clean_name = None

        if mac_regexp.match(uuid):
            clean_name = uuid.replace(":", "")
            clean_name = clean_name.replace("-", "")
        else:
            clean_name = uuid

        url = f"{self.url}/network/uuid/{clean_name}"

        headers = {
            "Content-type": "application/json",
        }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            reason = "get_network_information_from_uuid: failed with"
            reason += f"status_code: {response.status_code} "
            reason += f"response: {response.text} "
            reason += f"url {url}"

            raise CasambiApiException(reason)

        data = response.json()

        return data
