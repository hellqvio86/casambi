"""Comprehensive unit tests for the casambi package."""

import datetime
import json
import socket
import sys
import types
from unittest.mock import MagicMock, patch

import pytest
import yaml

# Provide websocket stub if websocket-client is not installed
if "websocket" not in sys.modules:
    ws_stub = types.ModuleType("websocket")
    ws_stub.create_connection = MagicMock()

    class WebSocketConnectionClosedException(Exception):
        pass

    class WebSocketTimeoutException(Exception):
        pass

    ws_stub.WebSocketConnectionClosedException = WebSocketConnectionClosedException
    ws_stub.WebSocketTimeoutException = WebSocketTimeoutException
    sys.modules["websocket"] = ws_stub

import websocket  # noqa: E402

import casambi  # noqa: E402
from casambi import consts  # noqa: E402
from casambi.exceptions import CasambiApiException, ConfigException  # noqa: E402
from casambi.private_casambi_api import Casambi as PrivateCasambi, Session  # noqa: E402
from casambi.public_casambi_api import Casambi as PublicCasambi  # noqa: E402


def _make_response(status_code=200, json_data=None, text="OK"):
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_data if json_data is not None else {}
    resp.text = text
    return resp


def test_consts_and_init():
    assert consts.DEVICE_NAME == "Casambi Python"
    assert casambi.Casambi is PublicCasambi


def test_private_session_expired():
    future = datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    past = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    s_valid = Session(session="s1", network="n1", manager=True, keyID=1, expires=future)
    s_expired = Session(session="s2", network="n1", manager=False, keyID=1, expires=past)
    assert not s_valid.expired()
    assert s_expired.expired()


def test_private_api_methods():
    api = PrivateCasambi(network_password="secret")
    assert not api.authenticated()

    # login failure
    with patch("casambi.private_casambi_api.requests.post", return_value=_make_response(401, text="unauth")):
        with pytest.raises(CasambiApiException):
            api.login(password="secret", network_id="net1")

    # login success
    future_ms = (datetime.datetime.utcnow() + datetime.timedelta(hours=2)).timestamp() * 1000
    session_payload = {
        "session": "sess-token",
        "network": "net1",
        "manager": True,
        "keyID": 2,
        "expires": future_ms,
        "role": 3,
    }
    with patch("casambi.private_casambi_api.requests.post", return_value=_make_response(200, session_payload)):
        res = api.login(password="secret", network_id="net1")
        assert res["session"] == "sess-token"
        assert api.authenticated()

    # get_network_information_from_uuid (MAC address format and plain UUID)
    with patch(
        "casambi.private_casambi_api.requests.get",
        return_value=_make_response(200, {"id": "net1", "uuid": "aabbccddeeff"}),
    ) as mock_get:
        net_id = api.get_network_id_from_uuid(uuid="AA:BB:CC:DD:EE:FF")
        assert net_id == "net1"
        assert mock_get.call_args[0][0].endswith("/AABBCCDDEEFF")

    with patch("casambi.private_casambi_api.requests.get", return_value=_make_response(200, {})):
        assert api.get_network_id_from_uuid(uuid="plain-uuid") is None

    with patch("casambi.private_casambi_api.requests.get", return_value=_make_response(500, text="err")):
        with pytest.raises(CasambiApiException):
            api.get_network_information_from_uuid(uuid="plain-uuid")

    # get_network_information success & failure
    with patch("casambi.private_casambi_api.requests.get", return_value=_make_response(200, {"name": "Home"})):
        assert api.get_network_information(network_id="net1") == {"name": "Home"}

    with patch("casambi.private_casambi_api.requests.get", return_value=_make_response(403, text="denied")):
        with pytest.raises(CasambiApiException):
            api.get_network_information(network_id="net1")


def test_public_sessions_and_getters():
    worker = PublicCasambi(
        api_key="key",
        email="user@example.com",
        user_password="upw",
        network_password="npw",
    )

    # Unauthenticated calls should raise
    with pytest.raises(CasambiApiException):
        worker.get_network_information()
    with pytest.raises(CasambiApiException):
        worker.get_unit_state(unit_id=1)
    with pytest.raises(CasambiApiException):
        worker.ws_open()
    with pytest.raises(CasambiApiException):
        worker.get_unit_list()
    with pytest.raises(CasambiApiException):
        worker.get_scenes_list()
    with pytest.raises(CasambiApiException):
        worker.get_fixture_information(unit_id=1)
    with pytest.raises(CasambiApiException):
        worker.get_network_state()
    with pytest.raises(CasambiApiException):
        worker.get_network_datapoints()

    # create_user_session failure and success
    with patch("casambi.public_casambi_api.requests.post", return_value=_make_response(401, text="bad")):
        with pytest.raises(CasambiApiException):
            worker.create_user_session()

    user_sess_data = {"sessionId": "usess-1", "networks": {"net-1": {"id": "net-1"}}}
    with patch("casambi.public_casambi_api.requests.post", return_value=_make_response(200, user_sess_data)):
        assert worker.create_user_session() == "usess-1"
        assert worker.network_id == "net-1"

    # ws_open when network_id is missing
    worker.network_id = None
    with pytest.raises(CasambiApiException):
        worker.ws_open()

    # create_network_session failure and success
    with patch("casambi.public_casambi_api.requests.post", return_value=_make_response(401, text="bad")):
        with pytest.raises(CasambiApiException):
            worker.create_network_session()

    net_sess_data = {"net-1": {"sessionId": "nsess-1"}}
    with patch("casambi.public_casambi_api.requests.post", return_value=_make_response(200, net_sess_data)):
        keys = worker.create_network_session()
        assert "net-1" in keys
        assert worker.network_id == "net-1"

    # get_network_information
    with patch("casambi.public_casambi_api.requests.get", return_value=_make_response(500)):
        with pytest.raises(CasambiApiException):
            worker.get_network_information()
    with patch("casambi.public_casambi_api.requests.get", return_value=_make_response(200, {"id": "net-1"})):
        assert worker.get_network_information() == {"id": "net-1"}

    # get_unit_state
    with patch("casambi.public_casambi_api.requests.get", return_value=_make_response(500)):
        with pytest.raises(CasambiApiException):
            worker.get_unit_state(unit_id=1)
    with patch("casambi.public_casambi_api.requests.get", return_value=_make_response(200, {"id": 1})):
        assert worker.get_unit_state(unit_id=1) == {"id": 1}

    # get_unit_list, get_scenes_list, get_fixture_information, get_network_state
    for method, kwargs in [
        (worker.get_unit_list, {}),
        (worker.get_scenes_list, {}),
        (worker.get_fixture_information, {"unit_id": 10}),
        (worker.get_network_state, {}),
    ]:
        with patch("casambi.public_casambi_api.requests.get", return_value=_make_response(500)):
            with pytest.raises(CasambiApiException):
                method(**kwargs)
        with patch("casambi.public_casambi_api.requests.get", return_value=_make_response(200, {"ok": True})):
            assert method(**kwargs) == {"ok": True}

    # get_network_datapoints
    with pytest.raises(CasambiApiException):
        worker.get_network_datapoints(sensor_type=99)
    with patch("casambi.public_casambi_api.requests.get", return_value=_make_response(500)):
        with pytest.raises(CasambiApiException):
            worker.get_network_datapoints(sensor_type=0)
    with patch("casambi.public_casambi_api.requests.get", return_value=_make_response(200, {"dp": []})):
        assert worker.get_network_datapoints(sensor_type=1) == {"dp": []}


def test_public_websocket_and_unit_controls():
    worker = PublicCasambi(
        api_key="key",
        email="user@example.com",
        user_password="upw",
        network_password="npw",
    )
    worker._session_id = "sess-1"
    worker.network_id = "net-1"

    # Without websocket open, control methods should fail
    with pytest.raises(CasambiApiException):
        worker.turn_unit_off(unit_id=1)
    with pytest.raises(CasambiApiException):
        worker.turn_unit_on(unit_id=1)
    with pytest.raises(CasambiApiException):
        worker.set_unit_vertical(unit_id=1, value=0.5)
    with pytest.raises(CasambiApiException):
        worker.set_unit_target_controls(unit_id=1, target_controls={})
    with pytest.raises(CasambiApiException):
        worker.set_unit_value(unit_id=1, value=0.5)
    with pytest.raises(CasambiApiException):
        worker.set_unit_rgbw_color(unit_id=1, color_value=(10, 20, 30, 40))
    with pytest.raises(CasambiApiException):
        worker.set_unit_rgb_color(unit_id=1, color_value=(10, 20, 30))
    with pytest.raises(CasambiApiException):
        worker.turn_scene_off(scene_id=1)
    with pytest.raises(CasambiApiException):
        worker.turn_scene_on(scene_id=1)
    with pytest.raises(CasambiApiException):
        worker.ws_recieve_message()
    with pytest.raises(CasambiApiException):
        worker.ws_recieve_messages()
    with pytest.raises(CasambiApiException):
        worker.ws_close()

    mock_ws = MagicMock()
    with patch("casambi.public_casambi_api.websocket.create_connection", return_value=mock_ws):
        mock_ws.recv.return_value = json.dumps({"wireStatus": "openWireSucceed"})
        assert worker.ws_open() is True

        mock_ws.recv.return_value = json.dumps({"method": "peerChanged", "wire": 1, "online": True})
        assert worker.ws_open() is True

        mock_ws.recv.return_value = json.dumps({"wireStatus": "invalidSession"})
        assert worker.ws_open() is False

    # Test unit_id type conversions (int, str, float, invalid)
    for method, extra in [
        (worker.turn_unit_off, {}),
        (worker.turn_unit_on, {}),
        (worker.set_unit_vertical, {"value": 0.5}),
        (worker.set_unit_target_controls, {"target_controls": {"Dimmer": {"value": 1}}}),
        (worker.set_unit_value, {"value": 0.5}),
        (worker.set_unit_rgbw_color, {"color_value": (255, 0, 0, 128)}),
        (worker.set_unit_rgb_color, {"color_value": (255, 0, 0), "send_rgb_format": False}),
        (worker.set_unit_rgb_color, {"color_value": (255, 0, 0), "send_rgb_format": True}),
    ]:
        for uid in (1, "2", 3.0):
            method(unit_id=uid, **extra)
        with pytest.raises(CasambiApiException):
            method(unit_id=[1], **extra)

    # Vertical and value bounds
    with pytest.raises(CasambiApiException):
        worker.set_unit_vertical(unit_id=1, value=-0.1)
    with pytest.raises(CasambiApiException):
        worker.set_unit_vertical(unit_id=1, value=1.5)
    with pytest.raises(CasambiApiException):
        worker.set_unit_value(unit_id=1, value=2.0)

    # Scene controls
    for scene_method in (worker.turn_scene_off, worker.turn_scene_on):
        for sid in (1, "2", 3.0):
            scene_method(scene_id=sid)
        with pytest.raises(CasambiApiException):
            scene_method(scene_id=[1])

    # ws_recieve_message, ws_recieve_messages, ws_close
    mock_ws.recv.return_value = json.dumps({"hello": "world"})
    assert worker.ws_recieve_message() == {"hello": "world"}

    for exc in (
        websocket.WebSocketConnectionClosedException(),
        socket.timeout(),
        websocket.WebSocketTimeoutException(),
    ):
        mock_ws.recv.side_effect = [json.dumps({"msg": 1}), exc]
        assert worker.ws_recieve_messages() == [{"msg": 1}]

    worker.ws_close()


def test_color_temperature_and_capability_detection():
    worker = PublicCasambi(
        api_key="key",
        email="user@example.com",
        user_password="upw",
        network_password="npw",
    )
    worker._session_id = "sess-1"
    worker.network_id = "net-1"
    worker.web_sock = MagicMock()

    # Empty state (no controls)
    with patch.object(worker, "get_unit_state", return_value={}):
        assert worker.get_supported_color_temperature(unit_id=1) == (0, 0, 0)
        assert worker.unit_supports_rgbw(unit_id=1) is False
        assert worker.unit_supports_rgb(unit_id=1) is False
        assert worker.unit_supports_color_temperature(unit_id=1) is False

    # Nested list controls and flat dict controls
    nested_state = {
        "controls": [
            [
                {"type": "CCT", "min": 2200, "max": 6000, "value": 4000},
                {"type": "Color"},
                {"type": "White"},
            ]
        ]
    }
    flat_state = {
        "controls": [
            {"type": "CCT", "min": 2700, "max": 5000, "value": 3000},
            {"type": "Color"},
            {"type": "White"},
        ]
    }
    for state in (nested_state, flat_state):
        with patch.object(worker, "get_unit_state", return_value=state):
            cct_min, cct_max, current = worker.get_supported_color_temperature(unit_id=1)
            assert cct_min > 0 and cct_max > cct_min and current > 0
            assert worker.unit_supports_rgbw(unit_id=1) is True
            assert worker.unit_supports_rgb(unit_id=1) is True
            assert worker.unit_supports_color_temperature(unit_id=1) is True

    # set_unit_color_temperature with mired, rounding to 50K, clamping to min/max, and unit_id types
    with patch.object(worker, "get_supported_color_temperature", return_value=(2200, 6000, 4000)):
        worker.set_unit_color_temperature(unit_id=1, value=333, source="mired")
        worker.set_unit_color_temperature(unit_id="2", value=1500)  # clamped to min
        worker.set_unit_color_temperature(unit_id=3.0, value=7000)  # clamped to max
        with pytest.raises(CasambiApiException):
            worker.set_unit_color_temperature(unit_id=[1], value=3000)

        worker.web_sock = None
        with pytest.raises(CasambiApiException):
            worker.set_unit_color_temperature(unit_id=1, value=3000)


def test_cli_entrypoints(tmp_path):
    from casambi import __main__official_api_login as main_official
    from casambi import __main__private_api as main_private
    from casambi import __main__public_api as main_public

    cfg_file = tmp_path / "casambi.yaml"
    cfg_data = {
        "api_key": "k",
        "email": "user@example.com",
        "network_password": "np",
        "user_password": "up",
        "network": "aa:bb:cc:dd:ee:ff",
        "unit_id": 1,
        "scene_id": 2,
        "units": [1],
    }
    cfg_file.write_text(yaml.dump(cfg_data), encoding="utf-8")

    assert main_official.parse_config(str(cfg_file))["api_key"] == "k"
    assert main_private.parse_config(str(cfg_file))["network"] == "aa:bb:cc:dd:ee:ff"
    assert main_public.parse_config(str(cfg_file))["api_key"] == "k"

    for key in ("api_key", "email", "network_password", "user_password"):
        bad = dict(cfg_data)
        del bad[key]
        bad_file = tmp_path / f"bad_{key}.yaml"
        bad_file.write_text(yaml.dump(bad), encoding="utf-8")
        with pytest.raises(ConfigException):
            main_official.parse_config(str(bad_file))
        with pytest.raises(ConfigException):
            main_private.parse_config(str(bad_file))
        with pytest.raises(ConfigException):
            main_public.parse_config(str(bad_file))

    bad_net = dict(cfg_data)
    del bad_net["network"]
    bad_net_file = tmp_path / "bad_net.yaml"
    bad_net_file.write_text(yaml.dump(bad_net), encoding="utf-8")
    with pytest.raises(ConfigException):
        main_private.parse_config(str(bad_net_file))

    mock_worker = MagicMock()
    mock_worker.unit_supports_color_temperature.return_value = True
    mock_worker.get_supported_color_temperature.return_value = (2200, 6000, 4000)
    mock_worker.unit_supports_rgb.return_value = True

    with (
        patch.object(main_official, "parse_config", return_value=cfg_data),
        patch.object(main_official.casambi, "Casambi", return_value=mock_worker),
        patch.object(main_official.time, "sleep"),
    ):
        main_official.main()

    with (
        patch.object(main_public, "parse_config", return_value=cfg_data),
        patch.object(main_public.casambi, "Casambi", return_value=mock_worker),
        patch.object(main_public.time, "sleep"),
    ):
        main_public.main()

    mock_priv_worker = MagicMock()
    mock_priv_worker.get_network_id_from_uuid.return_value = "net-1"
    mock_priv_worker.get_network_information.return_value = {"id": "net-1"}
    with (
        patch.object(main_private, "parse_config", return_value=cfg_data),
        patch.object(main_private, "Casambi", return_value=mock_priv_worker),
        patch("builtins.open", MagicMock()),
    ):
        main_private.main()
