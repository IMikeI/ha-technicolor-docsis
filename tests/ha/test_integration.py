"""Exercise GUI flows, entity lifecycle and diagnostics against Home Assistant."""

from copy import deepcopy
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.technicolor_docsis.api import AuthenticationError, RouterError
from custom_components.technicolor_docsis.const import DOMAIN
from custom_components.technicolor_docsis.diagnostics import async_get_config_entry_diagnostics
from custom_components.technicolor_docsis.number import PollingIntervalNumber
from homeassistant.config_entries import SOURCE_REAUTH, SOURCE_RECONFIGURE, SOURCE_USER
from homeassistant.const import EVENT_HOMEASSISTANT_STOP, STATE_UNAVAILABLE
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er

INPUT = {"host": "http://192.0.2.1", "username": "test-user", "password": "test-password"}
FETCH = "custom_components.technicolor_docsis.api.RouterClient.async_get_data"


def add_entry(hass):
    entry = MockConfigEntry(domain=DOMAIN, unique_id="test123", data=INPUT)
    entry.add_to_hass(hass)
    return entry


async def test_user_flow(hass, router_data):
    with (
        patch(FETCH, return_value=router_data),
        patch("custom_components.technicolor_docsis.async_setup_entry", return_value=True),
    ):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        assert result["type"] is FlowResultType.FORM
        result = await hass.config_entries.flow.async_configure(result["flow_id"], INPUT)
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == "test123"
    assert result["data"] == INPUT


@pytest.mark.parametrize(
    "error, expected", [(AuthenticationError(), "invalid_auth"), (RouterError(), "cannot_connect")]
)
async def test_flow_errors(hass, error, expected):
    with patch(FETCH, side_effect=error):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], INPUT)
    assert result["errors"] == {"base": expected}


async def test_invalid_host(hass):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {**INPUT, "host": "http://router/#/login"}
    )
    assert result["errors"] == {"host": "invalid_host"}


async def test_duplicate_router(hass, router_data):
    add_entry(hass)
    with patch(FETCH, return_value=router_data):
        result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": SOURCE_USER})
        result = await hass.config_entries.flow.async_configure(result["flow_id"], INPUT)
    assert result["reason"] == "already_configured"


@pytest.mark.parametrize(
    "source, step, reason",
    [
        (SOURCE_RECONFIGURE, "reconfigure", "reconfigure_successful"),
        (SOURCE_REAUTH, "reauth_confirm", "reauth_successful"),
    ],
)
async def test_reconfigure_and_reauth(hass, router_data, source, step, reason):
    entry = add_entry(hass)
    with (
        patch(FETCH, return_value=router_data),
        patch.object(hass.config_entries, "async_reload", return_value=True),
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": source, "entry_id": entry.entry_id},
            data=entry.data if source == SOURCE_REAUTH else None,
        )
        assert result["step_id"] == step
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {**INPUT, "password": "new-test-password"}
        )
        await hass.async_block_till_done()
    assert result["reason"] == reason
    assert entry.data["password"] == "new-test-password"


async def test_reconfigure_wrong_router(hass, router_data):
    entry = add_entry(hass)
    router_data["system"]["SerialNumber"] = "OTHER-ROUTER"
    with patch(FETCH, return_value=router_data):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_RECONFIGURE, "entry_id": entry.entry_id}
        )
        result = await hass.config_entries.flow.async_configure(result["flow_id"], INPUT)
    assert result["reason"] == "wrong_device"


async def test_options(hass):
    entry = add_entry(hass)
    with patch.object(hass.config_entries, "async_reload", return_value=True):
        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"update_interval": 180}
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert entry.options["update_interval"] == 180


async def test_device_sensors_discovery_missing_channels_and_unload(hass, router_data):
    entry = add_entry(hass)
    with patch(FETCH, return_value=router_data):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    registry = er.async_get(hass)
    power_id = registry.async_get_entity_id("sensor", DOMAIN, "test123_DSTbl_1_PowerLevel")
    error_id = registry.async_get_entity_id("sensor", DOMAIN, "test123_ErrTbl_1_Correcteds")
    assert hass.states.get(power_id).state == "1.9"
    assert hass.states.get(error_id).state == "18607766"
    assert dr.async_get(hass).async_get_device(identifiers={(DOMAIN, "test123")}) is not None
    assert len(dr.async_get(hass).devices) == 1
    newer = deepcopy(router_data)
    newer["modem"]["DSTbl"].append({**newer["modem"]["DSTbl"][0], "ChannelID": "2"})
    entry.runtime_data.async_set_updated_data(newer)
    await hass.async_block_till_done()
    assert registry.async_get_entity_id("sensor", DOMAIN, "test123_DSTbl_2_PowerLevel") is not None
    newer = deepcopy(newer)
    newer["modem"]["DSTbl"] = []
    entry.runtime_data.async_set_updated_data(newer)
    await hass.async_block_till_done()
    assert hass.states.get(power_id).state == STATE_UNAVAILABLE
    session = entry.runtime_data.client._session
    assert await hass.config_entries.async_unload(entry.entry_id)
    assert session.closed


async def test_diagnostics_redacted(hass, router_data):
    entry = add_entry(hass)
    with patch(FETCH, return_value=router_data):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    diagnostics = str(await async_get_config_entry_diagnostics(hass, entry))
    for secret in (
        "TEST123",
        "02:00:00:00:00:01",
        INPUT["password"],
        INPUT["host"],
        INPUT["username"],
    ):
        assert secret not in diagnostics
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_polling_auth_failure(hass, router_data):
    entry = add_entry(hass)
    with patch(FETCH, return_value=router_data):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    with patch(FETCH, new=AsyncMock(side_effect=AuthenticationError())):
        await entry.runtime_data.async_refresh()
        await hass.async_block_till_done()
    assert not entry.runtime_data.last_update_success
    assert any(
        flow["context"]["source"] == SOURCE_REAUTH
        for flow in hass.config_entries.flow.async_progress()
    )
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_shutdown_closes_router_session(hass, router_data):
    entry = add_entry(hass)
    with patch(FETCH, return_value=router_data):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    session = entry.runtime_data.client._session
    hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
    await hass.async_block_till_done()
    assert session.closed
    assert await hass.config_entries.async_unload(entry.entry_id)


@pytest.mark.parametrize("seconds", [60, 180, 3600])
async def test_interval_entity_persists_without_reload(hass, router_data, seconds):
    entry = add_entry(hass)
    hass.config_entries.async_update_entry(entry, options={"retained_option": True})
    with (
        patch(FETCH, return_value=router_data) as fetch,
        patch.object(hass.config_entries, "async_reload", return_value=True) as reload_entry,
    ):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        coordinator = entry.runtime_data
        entity_id = er.async_get(hass).async_get_entity_id(
            "number", DOMAIN, "test123_update_interval"
        )
        state = hass.states.get(entity_id)
        assert float(state.state) == 120
        assert state.attributes["min"] == 60
        assert state.attributes["max"] == 3600
        assert state.attributes["step"] == 1
        previous_timer = coordinator._unsub_refresh
        assert previous_timer is not None
        await hass.services.async_call(
            "number", "set_value", {"entity_id": entity_id, "value": seconds}, blocking=True
        )
        await hass.async_block_till_done()
        assert float(hass.states.get(entity_id).state) == seconds
        assert entry.options == {"retained_option": True, "update_interval": seconds}
        assert coordinator.update_interval == timedelta(seconds=seconds)
        assert coordinator._unsub_refresh is not previous_timer
        assert entry.runtime_data is coordinator
        reload_entry.assert_not_called()
        assert fetch.call_count == 1
        assert await hass.config_entries.async_unload(entry.entry_id)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        assert float(hass.states.get(entity_id).state) == seconds
        assert entry.runtime_data.update_interval == timedelta(seconds=seconds)
        assert await hass.config_entries.async_unload(entry.entry_id)


@pytest.mark.parametrize("value", [59, 3601, 120.5, float("nan"), float("inf")])
async def test_interval_entity_rejects_invalid_values(hass, router_data, value):
    entry = add_entry(hass)
    with patch(FETCH, return_value=router_data):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    control = PollingIntervalNumber(entry.runtime_data)
    with pytest.raises(ServiceValidationError):
        await control.async_set_native_value(value)
    assert entry.options == {}
    assert entry.runtime_data.update_interval == timedelta(seconds=120)
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_interval_control_remains_available_during_router_failure(hass, router_data):
    entry = add_entry(hass)
    with patch(FETCH, return_value=router_data):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
    coordinator = entry.runtime_data
    coordinator.last_update_success = False
    coordinator.async_update_listeners()
    entity_id = er.async_get(hass).async_get_entity_id("number", DOMAIN, "test123_update_interval")
    assert float(hass.states.get(entity_id).state) == 120
    await hass.services.async_call(
        "number", "set_value", {"entity_id": entity_id, "value": 300}, blocking=True
    )
    assert float(hass.states.get(entity_id).state) == 300
    assert not coordinator.last_update_success
    assert entry.options["update_interval"] == 300
    assert await hass.config_entries.async_unload(entry.entry_id)


async def test_options_and_interval_entity_share_the_same_setting(hass, router_data):
    entry = add_entry(hass)
    with patch(FETCH, return_value=router_data):
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()
        result = await hass.config_entries.options.async_init(entry.entry_id)
        result = await hass.config_entries.options.async_configure(
            result["flow_id"], {"update_interval": 240}
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY
    entity_id = er.async_get(hass).async_get_entity_id("number", DOMAIN, "test123_update_interval")
    assert float(hass.states.get(entity_id).state) == 240
    assert entry.runtime_data.update_interval == timedelta(seconds=240)
    assert await hass.config_entries.async_unload(entry.entry_id)
