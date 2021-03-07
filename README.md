![PyPI - Python Version](https://img.shields.io/pypi/pyversions/casambi) ![PyPI](https://img.shields.io/pypi/v/casambi) ![GitHub](https://img.shields.io/github/license/hellqvio86/casambi) ![GitHub issues](https://img.shields.io/github/issues-raw/hellqvio86/casambi) ![GitHub last commit](https://img.shields.io/github/last-commit/hellqvio86/casambi) ![PyPI - Downloads](https://img.shields.io/pypi/dm/casambi)

# Python library for controlling Casambi lights

Python library for controlling Casambi via Cloud API

## Getting Started
1. Request developer api key from Casambi: https://developer.casambi.com/
2. Setup a site in Casambi app: http://support.casambi.com/support/solutions/articles/12000041325-how-to-create-a-site

## Installating
Install this library through pip: 
```
pip install casambi
```

## Example Code block 1
```python

  import casambi
  import time

  api_key = 'REPLACEME'
  email = 'replaceme@replace.com'
  network_password = 'REPLACEME'
  user_password = 'REPLACEME'

  worker = casambi.Casambi(api_key=api_key, email=email, \
    user_password=user_password, network_password=network_password)
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
```
## Other Casambi projects
* https://github.com/hellqvio86/aiocasambi - Asynchronous I/O version of this library
* https://github.com/hellqvio86/home_assistant_casambi - Home Assistant Plugin for Casambi
* https://github.com/awahlig/homebridge-casambi Homebridge plugin for Casambi

## Authors

* **Olof Hellqvist** - *Initial work*

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

## Disclaimer
This library is neither affiliated with nor endorsed by Casambi.
