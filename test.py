#!/usr/bin/python3

import casambi
import yaml
import logging
import json
import time

logging.basicConfig(level=logging.DEBUG)


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

    api_key = config['api_key']
    email = config['email']
    network_password = config['network_password']
    user_password = config['user_password']

    if verbose:
        print("main: config: {}".format(config))

    user_session_id = casambi.create_user_session(email=email, api_key=api_key, user_password=user_password)
    network_ids = casambi.create_network_session(api_key=api_key, email=email, network_password=network_password)

    for network_id in network_ids:
        network_information = casambi.get_network_information(user_session_id=user_session_id, network_id=network_id, api_key=api_key)
        print("network_information: {}".format(network_information))

        web_sock = casambi.ws_open_message(user_session_id=user_session_id, network_id=network_id, api_key=api_key)
        print("Turn unit on!")
        casambi.turn_unit_on(unit_id=12, web_sock=web_sock, wire_id=1)
        time.sleep(60)

        network_information = casambi.get_network_information(user_session_id=user_session_id, network_id=network_id, api_key=api_key)
        print("network_information: {}".format(network_information))

        casambi.turn_unit_off(unit_id=12, web_sock=web_sock, wire_id=1)
        units = casambi.get_unit_list(api_key=api_key, network_id=network_id, user_session_id=user_session_id)

        print("units: {}".format(units))

        scenes = casambi.get_scenes_list(api_key=api_key, network_id=network_id, user_session_id=user_session_id)

        print("scenes: {}".format(units))

        print("Scene on!")
        casambi.turn_scene_on(scene_id=1, web_sock=web_sock, wire_id=1)
        time.sleep(60)
        print("Scene off!")
        casambi.turn_scene_off(scene_id=1, web_sock=web_sock, wire_id=1)

        casambi.ws_close_message(web_sock=web_sock)


if __name__ == "__main__":
    main()
