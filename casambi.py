#!/usr/bin/python3
import pprint
import requests
import uuid
import websocket
import json
import yaml

# https://developer.casambi.com/


class ApiException(Exception):
   """Custom exception"""
   pass

class ConfigException(Exception):
   """Custom exception"""
   pass


def create_user_session(api_key, email, user_password):
    url = 'https://door.casambi.com/v1/users/session/'
    headers = {'Content-type': 'application/json', 'X-Casambi-Key': api_key}

    payload = {"email": email, "password": user_password}
    

    r = requests.post(url, json=payload, headers=headers)
    if r.status_code != 200:
        reason = "create_user_session: headers: {},  payload: {}, message: \"Got a invalid status_code\", status_code: {}, response: {}".format(headers, payload, r.status_code, r.text)
        raise ApiException(reason)

    data = r.json()
    str_response = pprint.pformat(data, indent=2)

    print("create_user_session: url: {}, payload: {}, headers: {}, response:\n{}".format(url, payload, headers, str_response))

    return data['sessionId']


def create_network_session(api_key, email, network_password):
    url = 'https://door.casambi.com/v1/networks/session/'
    headers = {'X-Casambi-Key': api_key, 'Content-type': 'application/json', }

    payload = {"email": email, "password": network_password}
    
    r = requests.post(url, json=payload, headers=headers)

    if r.status_code != 200:
        reason = "create_network_session: failed with status_code: {}, response: {}".format(r.status_code, r.text)
        raise ApiException(reason)

    data = r.json()
    str_response = pprint.pformat(data, indent=2)

    print("create_network_session: url: {}, payload: {}, headers: {}, response:\n{}".format(url, payload, headers, str_response))

    return data.keys()


def get_network_information(user_session_id, network_id, api_key):
    # GET https://door.casambi.com/v1/networks/{id}

    url = "https://door.casambi.com/v1/networks/{}".format(network_id)

    headers = {'X-Casambi-Key': api_key, 'X-Casambi-Session': user_session_id,'Content-type': 'application/json', }

    r = requests.get(url, headers=headers)

    if r.status_code != 200:
        reason = "get_network_information: url: {} failed with status_code: {}, response: {}".format(url, r.status_code, r.text)
        raise ApiException(reason)

    data = r.json()
    str_response = pprint.pformat(data, indent=2)

    print("get_network_information: url: {}, headers: {}, response:\n{}".format(url, headers, str_response))


def ws_open_message(user_session_id, network_id, api_key, wire_id=1):
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

    websock = websocket.create_connection(url, subprotocols=[api_key])
    websock.send(json.dumps(message))

    result =  websock.recv()

    data = json.loads(result)

    if data['wireStatus'] != 'openWireSucceed':
        reason = "ws_open_message: url: {} message: {} reason: \"failed with to open wire!\" response: {}".format(url, message, data)
        raise ApiException(reason)

    return websock


def turn_unit_off(websock, unit_id, wire_id=1):
    target_controls = { 'Dimmer': {'value': 0 }}
    
    message = {
        "wire": wire_id,
        "method": 'controlUnit',
        "id": unit_id,
        "targetControls": target_controls
    }

    websock.send(json.dumps(message))

    result =  websock.recv()

    data = json.loads(result)

    print("turn_unit_off: message: {}, response:{}".format(message, data))


def turn_unit_on(websock, unit_id, wire_id=1):
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

    websock.send(json.dumps(message))

    result =  websock.recv()

    data = json.loads(result)

    print("turn_unit_on: message: {}, response:{}".format(message, data))


def ws_close_message(websock, wire_id=1):
    '''
    Response on success?
    {'wire': 1, 'method': 'peerChanged', 'online': True}
    '''

    message = {
        "method": "close",
        "wire": wire_id
    }

    websock.send(json.dumps(message))

    result =  websock.recv()

    data = json.loads(result)

    print("ws_close_message: data: {}".format(data))

    return


def parse_config(config_file='casambi.yaml'):
    config = None

    with open(config_file, 'r') as stream:
        config = yaml.safe_load(stream)
    
    if 'api_key' not in config:
        raise ConfigException('api_key is not present in configuration')

    if 'email' not in config:
        raise ConfigException('email is not present in configuration')

    if 'network_password' not in config:
        raise ConfigException('api_key is not present in configuration')

    if 'user_password' not in config:
        raise ConfigException('api_key is not present in configuration')

    return config


def main():
    verbose = True
    config = parse_config()


    api_key             = config['api_key']
    email               = config['email']
    network_password    = config['network_password']
    user_password       = config['user_password']

    if verbose:
        print("main: config: {}".format(config))

    user_session_id = create_user_session(api_key, email, user_password)
    network_ids = create_network_session(api_key, email, network_password)

    for network_id in network_ids:
        get_network_information(user_session_id, network_id, api_key)
        websock = ws_open_message(user_session_id, network_id, api_key)
        turn_unit_on(websock, 1)
        ws_close_message(websock)

    # 
    

if __name__ == "__main__":
    main()