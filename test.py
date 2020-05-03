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


    worker = casambi.Casambi(api_key=api_key, email=email, user_password=user_password, network_password=network_password)
    worker.create_user_session()
    worker.create_network_session()
    worker.ws_open()

    print("Turn unit on!")
    worker.turn_unit_on(unit_id=1)
    time.sleep(60)

    print("Turn unit off!")
    worker.turn_unit_off(unit_id=1)
    time.sleep(60)

    units = worker.get_unit_list()

    print("units: {}".format(units))

    scenes = worker.get_scenes_list()

    print("Scene on!")
    worker.turn_scene_on(scene_id=1)
    time.sleep(60)
    print("Scene off!")
    worker.turn_scene_off(scene_id=1)

    worker.ws_close()

if __name__ == "__main__":
    main()
