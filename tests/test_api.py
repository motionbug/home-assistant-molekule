"""Exercise the client with network responses replaced at the HTTP boundary."""

import asyncio
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock

import aiohttp
import pytest
from botocore.exceptions import ClientError, EndpointConnectionError
from pycognito.exceptions import MFAChallengeException

from custom_components.molekule.api import ApiConnectionError, AuthenticationError, MolekuleApi


class Response:
    def __init__(self, status=200, data=None):
        self.status = status
        self.data = data

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    async def json(self):
        return self.data

    async def text(self):
        return "response body"


class Session:
    """Capture outbound requests without reaching Molekule."""

    def __init__(self, responses, calls):
        self.responses = iter(responses)
        self.calls = calls
        self.closed = False
        self.headers = {"x-api-version": "1.0", "Content-Type": "application/json"}

    def request(self, method, url, **kwargs):
        self.calls.append((method, url, kwargs))
        response = next(self.responses)
        if isinstance(response, Exception):
            raise response
        return response

    async def close(self):
        self.closed = True


@pytest.fixture
async def api():
    client = MolekuleApi("test@example.com", "test-password")
    client.token = "id-token"
    client.token_expiration = datetime.now() + timedelta(hours=1)
    yield client
    await client.close()


async def test_refresh_failure_reauthenticates_without_deadlock(api, monkeypatch):
    def failed_refresh():
        raise RuntimeError("refresh token expired")

    api.cognito = SimpleNamespace(renew_access_token=failed_refresh)
    monkeypatch.setattr(
        api, "_create_and_authenticate_cognito", lambda: SimpleNamespace(id_token="new-token")
    )
    await asyncio.wait_for(api.refresh_token(), timeout=1)
    assert api.token == "new-token"


async def test_request_retry_keeps_authentication_executor_alive(api, monkeypatch):
    calls = []
    first = Session([aiohttp.ClientConnectionError("connection reset")], calls)
    second = Session([Response(401), Response(data={"content": []})], calls)
    api._session = first
    api._retry_delay = 0
    monkeypatch.setattr(aiohttp, "ClientSession", lambda **kwargs: second)
    monkeypatch.setattr(
        api, "_create_and_authenticate_cognito", lambda: SimpleNamespace(id_token="renewed")
    )
    result = await api.get_devices()
    assert result == {"content": []}
    assert first.closed
    assert calls[-1][2]["headers"]["Authorization"] == "renewed"


@pytest.mark.parametrize(
    ("method", "args", "path", "payload"),
    [
        ("set_power_status", ("serial", True), "set-power-status", {"status": "on"}),
        ("set_power_status", ("serial", False), "set-power-status", {"status": "off"}),
        ("set_fan_speed", ("serial", 4), "set-fan-speed", {"fanSpeed": 4}),
        ("set_auto_mode", ("serial", True, True), "enable-smart-mode", {"silent": "1"}),
        ("set_auto_mode", ("serial", True, False), "enable-smart-mode", {"silent": "0"}),
        ("set_auto_mode", ("serial", False), "set-fan-speed", {"fanSpeed": 1}),
    ],
)
async def test_commands_preserve_wire_contract(api, method, args, path, payload):
    calls = []
    api._session = Session([Response(204)], calls)
    assert await getattr(api, method)(*args) is True
    assert calls == [
        (
            "POST",
            f"https://api.molekule.com/users/me/devices/serial/actions/{path}",
            {
                "headers": {
                    "Authorization": "id-token",
                    "x-api-version": "1.0",
                    "Content-Type": "application/json",
                },
                "json": payload,
            },
        )
    ]


async def test_sensor_endpoint_and_latest_valid_reading(api, monkeypatch):
    calls = []
    monkeypatch.setattr("custom_components.molekule.api.time.time", lambda: 4000)
    api._session = Session(
        [Response(data={"sensorData": [
            {"type": "PM2_5", "sensorDataValue": [{"v": 2}, {"v": 7}, {"v": -1}]},
            {"type": "RH", "sensorDataValue": [{"v": 45}]},
        ]})], calls,
    )
    assert await api.get_sensor_data("serial") == {
        "PM2_5": 7, "PM10": None, "RH": 45, "TVOC": None, "CO2": None,
    }
    assert calls[0][0:2] == (
        "GET",
        "https://api.molekule.com/users/me/devices/serial/sensordata"
        "?aggregation=false&fromDate=400000&resolution=5&toDate=4000000",
    )


async def test_cognito_keeps_srp_configuration(api, monkeypatch):
    cognito = Mock()
    cognito.return_value.id_token = "authenticated"
    monkeypatch.setattr("custom_components.molekule.api.Cognito", cognito)
    await api.authenticate()
    assert api.token == "authenticated"
    cognito.assert_called_once_with(
        "us-west-2_KqrEZKC6r", "1ec4fa3oriciupg94ugoi84kkk",
        username="test@example.com", user_pool_region="us-west-2",
    )
    cognito.return_value.authenticate.assert_called_once_with(password="test-password")


@pytest.mark.parametrize("error", [
    EndpointConnectionError(endpoint_url="https://cognito-idp.us-west-2.amazonaws.com"),
    ClientError({"Error": {"Code": "TooManyRequestsException"}}, "InitiateAuth"),
])
async def test_auth_service_failures_are_retryable(api, monkeypatch, error):
    def authenticate():
        raise error
    monkeypatch.setattr(api, "_create_and_authenticate_cognito", authenticate)
    with pytest.raises(ApiConnectionError):
        await api.authenticate()


async def test_rejected_credentials_remain_authentication_errors(api, monkeypatch):
    def authenticate():
        raise ClientError({"Error": {"Code": "NotAuthorizedException"}}, "InitiateAuth")
    monkeypatch.setattr(api, "_create_and_authenticate_cognito", authenticate)
    with pytest.raises(AuthenticationError):
        await api.authenticate()


async def test_device_poll_does_not_hide_rejected_credentials(api, monkeypatch):
    api.token = None
    def authenticate():
        raise ClientError({"Error": {"Code": "NotAuthorizedException"}}, "InitiateAuth")
    monkeypatch.setattr(api, "_create_and_authenticate_cognito", authenticate)
    with pytest.raises(AuthenticationError):
        await api.get_devices()


async def test_auth_challenge_does_not_log_tokens(api, monkeypatch, caplog):
    cognito = Mock()
    cognito.return_value.authenticate.side_effect = MFAChallengeException(
        "MFA required", {"IdToken": "private-challenge-token"}
    )
    monkeypatch.setattr("custom_components.molekule.api.Cognito", cognito)
    with pytest.raises(AuthenticationError):
        await api.authenticate()
    assert "private-challenge-token" not in caplog.text
