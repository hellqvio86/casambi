#!/usr/bin/python3
import yaml
import logging
import time
import sys
import os
import random

from pprint import pprint, pformat

sys.path.append(os.path.split(os.path.dirname(sys.argv[0]))[0])

try:
    import casambi
except ModuleNotFoundError as err:
    pprint(sys.path)
    raise err

from casambi.exceptions import ConfigException

logging.basicConfig(level=logging.DEBUG)


def parse_config(config_file="casambi.yaml"):
    config = None

    with open(config_file, "r") as stream:
        config = yaml.safe_load(stream)

    if "api_key" not in config:
        raise ConfigException("api_key is not present in configuration")

    if "email" not in config:
        raise ConfigException("email is not present in configuration")

    if "network_password" not in config:
        raise ConfigException("api_key is not present in configuration")

    if "user_password" not in config:
        raise ConfigException("api_key is not present in configuration")

    return config


def print_unit_information(*, worker: casambi.Casambi, unit_id: int):
    data = worker.get_fixture_information(unit_id=unit_id)
    msg = f"Unit fixture information for unit: {unit_id}"
    msg += f"\n{pformat(data)}\n"
    print(msg)

    data = worker.get_unit_state(unit_id=unit_id)
    msg = f"Unit state for unit_id: {unit_id}"
    msg += f"\n{pformat(data)}\n"
    print(msg)

    supports_color_temperature = worker.unit_supports_color_temperature(unit_id=unit_id)
    print(f"Does unit support color temperature: {supports_color_temperature}")

    supports_rgb = worker.unit_supports_rgb(unit_id=unit_id)
    print(f"Does unit support rgb: {supports_rgb}")


def main():
    verbose = True
    config = parse_config()

    api_key = config["api_key"]
    email = config["email"]
    network_password = config["network_password"]
    user_password = config["user_password"]
    units = []
    scene_id = 1
    unit_id = 1

    if "unit_id" in config:
        unit_id = config["unit_id"]

    if "scene_id" in config:
        scene_id = config["scene_id"]

    if "units" in config:
        units = config["units"]

    if verbose:
        print("main: config: {}".format(config))

    worker = casambi.Casambi(
        api_key=api_key,
        email=email,
        user_password=user_password,
        network_password=network_password,
    )

    worker.create_user_session()
    worker.create_network_session()
    worker.ws_open()

    if len(units) == 0:
        units.append(unit_id)

    for unit_id in units:
        print_unit_information(worker=worker, unit_id=unit_id)
        time.sleep(60)

    worker.ws_close()


if __name__ == "__main__":
    main()
