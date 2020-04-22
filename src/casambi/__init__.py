#!/usr/bin/python3
import requests
import uuid
import websocket
import json
import logging
import datetime

# https://developer.casambi.com/

_LOGGER = logging.getLogger(__name__)


class CasambiApiException(Exception):
   """Custom exception"""
   pass

class ConfigException(Exception):
   """Custom exception"""
   pass


def create_user_session(*, api_key, email, user_password):
    url = 'https://door.casambi.com/v1/users/session/'
    headers = {'Content-type': 'application/json', 'X-Casambi-Key': api_key}

    payload = {"email": email, "password": user_password}


    r = requests.post(url, json=payload, headers=headers)
    if r.status_code != 200:
        reason = "create_user_session: headers: {},  payload: {}, message: \"Got a invalid status_code\", status_code: {}, response: {}".format(headers, payload, r.status_code, r.text)
        raise CasambiApiException(reason)

    data = r.json()

    return data['sessionId']


def create_network_session(*, api_key, email, network_password):
    url = 'https://door.casambi.com/v1/networks/session/'
    headers = {'X-Casambi-Key': api_key, 'Content-type': 'application/json', }

    payload = {"email": email, "password": network_password}

    r = requests.post(url, json=payload, headers=headers)

    if r.status_code != 200:
        reason = "create_network_session: failed with status_code: {}, response: {}".format(r.status_code, r.text)
        raise CasambiApiException(reason)

    data = r.json()

    return data.keys()


def get_network_information(*, user_session_id, network_id, api_key):
    # GET https://door.casambi.com/v1/networks/{id}

    url = "https://door.casambi.com/v1/networks/{}".format(network_id)

    headers = {'X-Casambi-Key': api_key, 'X-Casambi-Session': user_session_id,'Content-type': 'application/json', }

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        reason = "get_network_information: url: {} failed with status_code: {}, response: {}".format(url, r.status_code, r.text)
        raise CasambiApiException(reason)

    data = r.json()


def ws_open_message(*, user_session_id, network_id, api_key, wire_id=1):
    '''
    openWireSucceed         API key authentication failed. Either given key was invalid or WebSocket functionality is not enabled for it.
    keyAuthenticateFailed	API key authentication failed. Given key was invalid.
    keyAuthorizeFailed	    API key authorize failed. Given key has not been authorized or WebSocket functionality is not enabled for it.
    invalidSession	        Either access to given network is not authorized by session or given session is invalid.
    invalidValueType	    Received values are not in correct value type, for example when expecting a number but receiving string value instead.
    invalidData	            Received data is invalid and cannot be processed, for example expected list of items is in wrong data format.
    '''
    url = 'wss://door.casambi.com/v1/bridge/'

    reference = "{}".format(uuid.uuid1())

    message = {
        "method": "open",
        "id": network_id,
        "session": user_session_id,
        "ref": reference,
        "wire": wire_id, #wire id
        "type": 1 #Client type, use value 1 (FRONTEND)
    }

    web_sock = websocket.create_connection(url, subprotocols=[api_key])
    web_sock.send(json.dumps(message))

    result = web_sock.recv()

    data = json.loads(result)

    if data['wireStatus'] != 'openWireSucceed':
        reason = "ws_open_message: url: {} message: {} reason: \"failed with to open wire!\" response: {}".format(url, message, data)
        raise CasambiApiException(reason)

    return web_sock


def turn_unit_off(*, web_sock, unit_id, wire_id=1):
    target_controls = { 'Dimmer': {'value': 0 }}

    message = {
        "wire": wire_id,
        "method": 'controlUnit',
        "id": unit_id,
        "targetControls": target_controls
    }

    web_sock.send(json.dumps(message))

    result = web_sock.recv()

    data = json.loads(result)

    print("turn_unit_off: message: {}, response:{}".format(message, data))


def turn_unit_on(*, web_sock, unit_id, wire_id=1):
    '''
    Response on ok:
    {'wire': 1, 'method': 'peerChanged', 'online': True}
    '''
    target_controls = { 'Dimmer': {'value': 1 }}

    message = {
        "wire": wire_id,
        "method": 'controlUnit',
        "id": unit_id,
        "targetControls": target_controls
    }

    web_sock.send(json.dumps(message))

    result = web_sock.recv()

    data = json.loads(result)


def turn_scene_off(*, scene_id, web_sock, wire_id=1):
    '''
    Response on ok:
    {'wire': 1, 'method': 'peerChanged', 'online': True}
    '''
    value = 0

    message = {
        "wire": wire_id,
        "method": 'controlScene',
        "id": scene_id,
        "level": value
    }

    web_sock.send(json.dumps(message))

    result = web_sock.recv()

    data = json.loads(result)


def turn_scene_on(*, scene_id, web_sock, wire_id=1):
    '''
    Response on ok:
    {'wire': 1, 'method': 'peerChanged', 'online': True}
    '''
    value = 1

    message = {
        "wire": wire_id,
        "method": 'controlScene',
        "id": scene_id,
        "level": value
    }

    web_sock.send(json.dumps(message))

    result = web_sock.recv()

    data = json.loads(result)


def get_unit_list(*, api_key, network_id, user_session_id):
    url = "https://door.casambi.com/v1/networks/{}/units".format(network_id)

    headers = {'X-Casambi-Key': api_key, 'X-Casambi-Session': user_session_id,'Content-type': 'application/json', }

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        reason = "get_network_unit_list: headers: {}, message: \"Got a invalid status_code\", status_code: {}, response: {}".format(headers, r.status_code, r.text)
        raise CasambiApiException(reason)

    data = r.json()

    _LOGGER.debug("get_network_unit_list: headers: {} response: {}".format(headers, data))

    return data


def get_scenes_list(*, api_key, network_id, user_session_id):
    url = "https://door.casambi.com/v1/networks/{}/scenes".format(network_id)

    headers = {'X-Casambi-Key': api_key, 'X-Casambi-Session': user_session_id,'Content-type': 'application/json', }

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        reason = "get_network_unit_list: headers: {}, message: \"Got a invalid status_code\", status_code: {}, response: {}".format(headers, r.status_code, r.text)
        raise CasambiApiException(reason)

    data = r.json()

    _LOGGER.debug("get_scenes_list: headers: {} response: {}".format(headers, data))

    return data


def get_fixture_information(*, api_key, session_id, unit_id):
    '''
    GET https://door.casambi.com/v1/fixtures/{id}
    '''

    url = "https://door.casambi.com/v1/fixtures/{}".format(unit_id)

    headers = {'X-Casambi-Key': api_key, 'X-Casambi-Session': user_session_id,'Content-type': 'application/json', }

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        reason = "get_fixture_information: headers: {},  payload: {}, message: \"Got a invalid status_code\", status_code: {}, response: {}".format(headers, r.status_code, r.text)
        raise CasambiApiException(reason)

    data = r.json()

    _LOGGER.debug("get_fixture_information: headers: {} response: {}".format(headers, data))

    return data


def get_network_datapoints(*, from_time=None, to_time=None, sensor_type=0):
    '''
    sensorType: [0 = Casambi | 1 = Vendor]
    from: yyyyMMdd[hh[mm[ss]]]
    to: yyyyMMdd[hh[mm[ss]]]
    '''
    headers = {'X-Casambi-Key': api_key, 'X-Casambi-Session': user_session_id,'Content-type': 'application/json', }

    if not (sensor_type == 0 or sensor_type==1):
        raise CasambiApiException('invalid sentor_type')

    now = datetime.now()

    if not to_time:
        to_time = now.strftime("%Y%m%d%H%M")

    if not from_time:
        from_time = (now - timedelta(days=7)).strftime("%Y%m%d%H%M")

    print("from_time: {}".format(from_time))
    print("to_time: {}".format(to_time))
    print("sensor_type: {}".format(sensor_type))

    #url = "https://door.casambi.com/v1/networks/{}/datapoints?sensorType={}&from={}&to={}" % (self.network_id, sensor_type, from_time, to_time)
    url = 'https://door.casambi.com/v1/networks/' + str(self.network_id) + '/datapoints?sensorType=' + str(sensor_type) + '&from=' + from_time + '&to=' + to_time

    print("url: {}".format(url))

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        reason = "get_network_datapoints: headers: {}, message: \"Got a invalid status_code\", status_code: {}, response: {}".format(headers, r.status_code, r.text)
        raise CasambiApiException(reason)

    data = r.json()

    _LOGGER.debug("get_network_datapoints\nheaders: {}\nresponse: {}".format(headers, data))

    return data


def ws_close_message(*, web_sock, wire_id=1):
    '''
    Response on success?
    {'wire': 1, 'method': 'peerChanged', 'online': True}
    '''

    message = {
        "method": "close",
        "wire": wire_id
    }

    web_sock.send(json.dumps(message))

    result = web_sock.recv()

    data = json.loads(result)

    return
