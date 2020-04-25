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

  user_session_id = casambi.create_user_session(email=email, api_key=api_key, user_password=user_password)
  network_ids = casambi.create_network_session(api_key=api_key, email=email, network_password=network_password)

  for network_id in network_ids:
      casambi.get_network_information(user_session_id=user_session_id, network_id=network_id, api_key=api_key)
      web_sock = casambi.ws_open_message(user_session_id=user_session_id, network_id=network_id, api_key=api_key)
      casambi.turn_unit_on(unit_id=1, web_sock=web_sock, wire_id=1)
      time.sleep(5)
      casambi.turn_unit_off(unit_id=1, web_sock=web_sock, wire_id=1)
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
```

## Authors

* **Olof Hellqvist** - *Initial work*

## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details
