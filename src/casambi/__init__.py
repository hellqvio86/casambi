#!/usr/bin/python3
'''
Library for Casambi Cloud api.
Request api_key at: https://developer.casambi.com/
'''
import requests
import uuid
import websocket
import json
import logging
import datetime
import re
import socket

_LOGGER = logging.getLogger(__name__)


class CasambiApiException(Exception):
    """Custom exception"""


class ConfigException(Exception):
    """Custom exception"""


class Casambi(object):
    def __init__(self, *, api_key, email, user_password, network_password, wire_id=1):
        self.sock = None

        self.connected = False
        self.network_id = None
        self.user_session_id = None

        self.wire_id = wire_id
        self.api_key = api_key
        self.email = email
        self.user_password = user_password
        self.network_password = network_password

    def create_user_session(self):
        url = 'https://door.casambi.com/v1/users/session/'
        headers = {'Content-type': 'application/json',
                   'X-Casambi-Key': self.api_key}

        payload = {"email": self.email, "password": self.user_password}

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            reason = "create_user_session: headers: {},".format(headers)
            reason += " payload: {},".format(payload)
            reason += 'message: "Got a invalid status_code",'
            reason += "status_code: {},".format(response.status_code)
            reason += "#response: {}".format(response.text)
            raise CasambiApiException(reason)

        data = response.json()

        self.user_session_id = data['sessionId']

        return data['sessionId']

    def create_network_session(self):
        url = 'https://door.casambi.com/v1/networks/session/'
        headers = {'X-Casambi-Key': self.api_key,
                   'Content-type': 'application/json', }

        payload = {"email": self.email, "password": self.network_password}

        response = requests.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            reason = "create_network_session: failed with status_code: {}, response: {}".format(
                response.status_code, response.text)
            raise CasambiApiException(reason)

        data = response.json()

        self.network_id = list(data.keys())[0]

        return data.keys()

    def get_network_information(self):
        # GET https://door.casambi.com/v1/networks/{id}

        url = "https://door.casambi.com/v1/networks/{}".format(self.network_id)

        headers = {'X-Casambi-Key': self.api_key, 'X-Casambi-Session':
                   self.user_session_id, 'Content-type': 'application/json', }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            reason = "get_network_information: url: {}".format(url)
            reason += "failed with status_code: {},".format(response.status_code)
            reason += "response: {}".format(response.text)
            raise CasambiApiException(reason)

        data = response.json()

        _LOGGER.debug(
            "get_network_information: headers: {} response: {}".format(headers, data))

        return data

    def get_unit_state(self, unit_id):
        # GET https://door.casambi.com/v1/networks/{id}

        url = "https://door.casambi.com/v1/networks/{}/units/{}/state".format(self.network_id, unit_id)

        headers = {'X-Casambi-Key': self.api_key, 'X-Casambi-Session':
                   self.user_session_id, 'Content-type': 'application/json', }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            reason = "get_unit_state: url: {}".format(url)
            reason += "failed with status_code: {},".format(response.status_code)
            reason += "response: {}".format(response.text)
            raise CasambiApiException(reason)

        data = response.json()

        _LOGGER.debug(
            "get_unit_state: headers: {} response: {}".format(headers, data))

        return data

    def ws_open(self):
        '''
        openWireSucceed         API key authentication failed. Either given key was
        invalid or WebSocket functionality is not enabled for it.

        keyAuthenticateFailed	API key authentication failed. Given key was invalid.

        keyAuthorizeFailed	    API key authorize failed. Given key has not been
        authorized or WebSocket functionality is not enabled for it.

        invalidSession	        Either access to given network is not authorized by
        session or given session is invalid.

        invalidValueType	    Received values are not in correct value type,
        for example when expecting a number but receiving string value instead.

        invalidData	            Received data is invalid and cannot be processed,
        for example expected list of items is in wrong data format.
        '''
        url = 'wss://door.casambi.com/v1/bridge/'

        reference = "{}".format(uuid.uuid1())

        message = {
            "method": "open",
            "id": self.network_id,
            "session": self.user_session_id,
            "ref": reference,
            "wire": self.wire_id,  # wire id
            "type": 1  # Client type, use value 1 (FRONTEND)
        }

        self.web_sock = websocket.create_connection(
            url, subprotocols=[self.api_key])
        self.web_sock.send(json.dumps(message))

        result = self.web_sock.recv()

        data = json.loads(result)

        if data['wireStatus'] != 'openWireSucceed':
            reason = "ws_open_message: url: {},".format(url)
            reason += "message: {},".format(message)
            reason += 'reason: "failed with to open wire!"'
            reason += "response: {}".format(data)
            raise CasambiApiException(reason)

        return

    def turn_unit_off(self, *, unit_id):
        # Unit_id needs to be an integer
        if isinstance(unit_id, int):
            pass
        elif isinstance(unit_id, str):
            unit_id = int(unit_id)
        elif isinstance(unit_id, float):
            unit_id = int(unit_id)
        else:
            raise CasambiApiException(
                "expected unit_id to be an integer, got: {}".format(unit_id))

        if not self.web_sock:
            raise CasambiApiException('No websocket connection!')

        target_controls = {'Dimmer': {'value': 0}}

        message = {
            "wire": self.wire_id,
            "method": 'controlUnit',
            "id": unit_id,
            "targetControls": target_controls
        }

        self.web_sock.send(json.dumps(message))

    def turn_unit_on(self, *, unit_id):
        '''
        Response on ok:
        {'wire': 1, 'method': 'peerChanged', 'online': True}
        '''
        # Unit_id needs to be an integer
        if isinstance(unit_id, int):
            pass
        elif isinstance(unit_id, str):
            unit_id = int(unit_id)
        elif isinstance(unit_id, float):
            unit_id = int(unit_id)
        else:
            reason = 'expected unit_id to be an integer,'
            reason += "got: {}".format(unit_id)
            raise CasambiApiException(reason)
        
        if not self.web_sock:
            raise CasambiApiException('No websocket connection!')

        target_controls = {'Dimmer': {'value': 1}}

        message = {
            "wire": self.wire_id,
            "method": 'controlUnit',
            "id": unit_id,
            "targetControls": target_controls
        }

        self.web_sock.send(json.dumps(message))

    def set_unit_targetControls(self, *, unit_id, targetControls):
        '''
        Response on ok:
        {'wire': 1, 'method': 'peerChanged', 'online': True}
        '''
        # Unit_id needs to be an integer
        if isinstance(unit_id, int):
            pass
        elif isinstance(unit_id, str):
            unit_id = int(unit_id)
        elif isinstance(unit_id, float):
            unit_id = int(unit_id)
        else:
            raise CasambiApiException(
                "expected unit_id to be an integer, got: {}".format(unit_id))

        if not self.web_sock:
            raise CasambiApiException('No websocket connection!')

        message = {
            "wire": self.wire_id,
            "method": 'controlUnit',
            "id": unit_id,
            "targetControls": targetControls
        }

        self.web_sock.send(json.dumps(message))

    def set_unit_value(self, *, unit_id, value):
        '''
        Response on ok:
        {'wire': 1, 'method': 'peerChanged', 'online': True}
        '''
        # Unit_id needs to be an integer
        if isinstance(unit_id, int):
            pass
        elif isinstance(unit_id, str):
            unit_id = int(unit_id)
        elif isinstance(unit_id, float):
            unit_id = int(unit_id)
        else:
            raise CasambiApiException(
                "expected unit_id to be an integer, got: {}".format(unit_id))

        if not(value >= 0 and value <= 1):
            raise CasambiApiException('value needs to be between 0 and 1')

        if not self.web_sock:
            raise CasambiApiException('No websocket connection!')


        target_controls = {'Dimmer': {'value': value}}

        message = {
            "wire": self.wire_id,
            "method": 'controlUnit',
            "id": unit_id,
            "targetControls": target_controls
        }

        self.web_sock.send(json.dumps(message))

    def turn_scene_off(self, *, scene_id):
        '''
        Response on ok:
        {'wire': 1, 'method': 'peerChanged', 'online': True}
        '''
        # Unit_id needs to be an integer
        if isinstance(scene_id, int):
            pass
        elif isinstance(scene_id, str):
            scene_id = int(scene_id)
        elif isinstance(scene_id, float):
            scene_id = int(scene_id)
        else:
            raise CasambiApiException(
                "expected scene_id to be an integer, got: {}".format(scene_id))

        if not self.web_sock:
            raise CasambiApiException('No websocket connection!')

        value = 0

        message = {
            "wire": self.wire_id,
            "method": 'controlScene',
            "id": scene_id,
            "level": value
        }

        self.web_sock.send(json.dumps(message))

    def turn_scene_on(self, *, scene_id):
        '''
        Response on ok:
        {'wire': 1, 'method': 'peerChanged', 'online': True}
        '''
        # Unit_id needs to be an integer
        if isinstance(scene_id, int):
            pass
        elif isinstance(scene_id, str):
            scene_id = int(scene_id)
        elif isinstance(scene_id, float):
            scene_id = int(scene_id)
        else:
            raise CasambiApiException(
                "expected scene_id to be an integer, got: {}".format(scene_id))

        if not self.web_sock:
            raise CasambiApiException('No websocket connection!')

        value = 1

        message = {
            "wire": self.wire_id,
            "method": 'controlScene',
            "id": scene_id,
            "level": value
        }

        self.web_sock.send(json.dumps(message))

    def get_unit_list(self):
        url = "https://door.casambi.com/v1/networks/{}/units".format(
            self.network_id)

        headers = {'X-Casambi-Key': self.api_key, 'X-Casambi-Session':
                   self.user_session_id, 'Content-type': 'application/json', }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            reason = "get_network_unit_list: headers: {}, message: \"Got a invalid status_code\", status_code: {}, response: {}".format(
                headers, response.status_code, response.text)
            raise CasambiApiException(reason)

        data = response.json()

        _LOGGER.debug(
            "get_network_unit_list: headers: {} response: {}".format(headers, data))

        return data

    def get_scenes_list(self):
        url = "https://door.casambi.com/v1/networks/{}/scenes".format(
            self.network_id)

        headers = {'X-Casambi-Key': self.api_key, 'X-Casambi-Session':
                   self.user_session_id, 'Content-type': 'application/json', }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            reason = "get_network_unit_list: headers: {}, message: \"Got a invalid status_code\", status_code: {}, response: {}".format(
                headers, response.status_code, response.text)
            raise CasambiApiException(reason)

        data = response.json()

        _LOGGER.debug(
            "get_scenes_list: headers: {} response: {}".format(headers, data))

        return data

    def get_fixture_information(self, *, unit_id):
        '''
        GET https://door.casambi.com/v1/fixtures/{id}
        '''

        url = "https://door.casambi.com/v1/fixtures/{}".format(unit_id)

        headers = {'X-Casambi-Key': self.api_key, 'X-Casambi-Session':
                   self.user_session_id, 'Content-type': 'application/json', }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            reason = "get_fixture_information: headers: {},  payload: {}, message: \"Got a invalid status_code\", status_code: {}, response: {}".format(
                headers, response.status_code, response.text)
            raise CasambiApiException(reason)

        data = response.json()

        _LOGGER.debug(
            "get_fixture_information: headers: {} response: {}".format(headers, data))

        return data
    
    def get_unit_state(self, *, unit_id):
        url = f"{self.rest_url}/networks/{self.network_id}/units/{unit_id}/state"

        headers = {'X-Casambi-Key': self.api_key, 'X-Casambi-Session':
                   self.user_session_id, 'Content-type': 'application/json', }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            reason = "get_unit_state: headers: {},  payload: {}, message: \"Got a invalid status_code\", status_code: {}, response: {}".format(
                headers, response.status_code, response.text)
            raise CasambiApiException(reason)

        data = response.json()

        _LOGGER.debug(
            "get_unit_state: headers: {} response: {}".format(headers, data))

        return data

    def get_network_state(self):
        url = f"{self.rest_url}/networks/{self.network_id}/state"

        headers = {'X-Casambi-Key': self.api_key, 'X-Casambi-Session':
                   self.user_session_id, 'Content-type': 'application/json', }

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            reason = "get_network_state: headers: {},  payload: {}, message: \"Got a invalid status_code\", status_code: {}, response: {}".format(
                headers, response.status_code, response.text)
            raise CasambiApiException(reason)

        data = response.json()

        _LOGGER.debug(
            "get_network_state: headers: {} response: {}".format(headers, data))

        return data

    def get_network_datapoints(self, *, from_time=None, to_time=None, sensor_type=0):
        '''
        sensorType: [0 = Casambi | 1 = Vendor]
        from: yyyyMMdd[hh[mm[ss]]]
        to: yyyyMMdd[hh[mm[ss]]]
        '''
        headers = {'X-Casambi-Key': self.api_key, 'X-Casambi-Session':
                   self.user_session_id, 'Content-type': 'application/json', }

        if not (sensor_type == 0 or sensor_type == 1):
            raise CasambiApiException('invalid sentor_type')

        now = datetime.datetime.now()

        if not to_time:
            to_time = now.strftime("%Y%m%d%H%M")

        if not from_time:
            from_time = (now - datetime.timedelta(days=7)
                         ).strftime("%Y%m%d%H%M")

        url = 'https://door.casambi.com/v1/networks/' + \
            str(self.network_id) + '/datapoints?sensorType=' + \
            str(sensor_type) + '&from=' + from_time + '&to=' + to_time

        response = requests.get(url, headers=headers)

        if response.status_code != 200:
            reason = "get_network_datapoints: headers: {}, message: \"Got a invalid status_code\", status_code: {}, response: {}".format(
                headers, response.status_code, response.text)
            raise CasambiApiException(reason)

        data = response.json()

        _LOGGER.debug(
            "get_network_datapoints\nheaders: {}\nresponse: {}".format(headers, data))

        return data

    def ws_recieve_message(self):
        '''
        Response on success?
        {'wire': 1, 'method': 'peerChanged', 'online': True}
        '''
        if not self.web_sock:
            raise CasambiApiException('No websocket connection!')

        result = self.web_sock.recv()

        data = json.loads(result)

        return data

    def ws_recieve_messages(self):
        '''
        Response on success?
        {'wire': 1, 'method': 'peerChanged', 'online': True}
        '''
        messages = []

        if not self.web_sock:
            raise CasambiApiException('No websocket connection!')

        self.web_sock.settimeout(0.1)

        while True:
            try:
                casambi_msg = self.web_sock.recv()
                data = json.loads(casambi_msg)

                messages.append(data)
            except websocket._exceptions.WebSocketConnectionClosedException:
                break
            except socket.timeout:
                break
            except websocket._exceptions.WebSocketTimeoutException:
                break
        return messages

    def ws_close(self):
        '''
        Response on success?
        {'wire': 1, 'method': 'peerChanged', 'online': True}
        '''

        if not self.web_sock:
            raise CasambiApiException('No websocket connection!')

        message = {
            "method": "close",
            "wire": self.wire_id
        }

        self.web_sock.send(json.dumps(message))
