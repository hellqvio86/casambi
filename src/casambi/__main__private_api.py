#!/usr/bin/python3
import yaml
import logging
import json

from pprint import pprint, pformat

from private_casambi_api import Casambi

logging.basicConfig(level=logging.DEBUG)

from casambi.exceptions import ConfigException


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

    if "network" not in config:
        raise ConfigException("network is not present in configuration")

    return config


def main():
    config = parse_config()

    network_password = config["network_password"]

    casambi_worker = Casambi(network_password=network_password)
    network_id = casambi_worker.get_network_id_from_uuid(uuid=config["network"])
    casambi_worker.login(password=network_password, network_id=network_id)

    data = casambi_worker.get_network_information(network_id=network_id)

    with open("network.json", "w", encoding="utf-8") as fdesc:
        json.dump(data, fdesc, indent=4)

    logging.debug(f"data: {pformat(data)}")


if __name__ == "__main__":
    main()
