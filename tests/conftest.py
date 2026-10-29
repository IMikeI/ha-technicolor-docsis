"""Load the real Home Assistant test fixtures for integration tests."""

from copy import deepcopy

import pytest

pytest_plugins = ("pytest_homeassistant_custom_component",)


@pytest.fixture(autouse=True)
def enable_integration(enable_custom_integrations, request):
    """Permit the custom component and loopback HTTP tests after HA's setup hook."""
    if request.node.path.name == "test_api.py":
        request.getfixturevalue("socket_enabled")


@pytest.fixture
def router_data():
    channel = {
        "__id": "1",
        "ChannelID": "1",
        "LockStatus": "Locked",
        "PowerLevel": "1.9 dBmV",
        "SNRLevel": "41.9 dB",
        "Frequency": "274 MHz",
        "Modulation": "256-QAM",
        "Octets": "424511439",
        "Correcteds": "0",
        "Uncorrectables": "0",
        "ChannelType": "SC-QAM",
    }
    return deepcopy(
        {
            "system": {
                "ModelName": "CGA4233-EU",
                "Manufacturer": "Technicolor",
                "SerialNumber": "TEST123",
                "CMMACAddress": "02:00:00:00:00:01",
                "CMStatus": "OPERATIONAL",
                "UpTime": "12535",
                "CPUUsage": "2",
                "SoftwareVersion": "test-firmware",
                "HardwareVersion": "3.1.5\n",
                "MemTotal": "350216",
                "MemFree": "135924",
            },
            "modem": {
                "DSTbl": [channel],
                "USTbl": [],
                "exUSTbl": [],
                "exDSTbl": [
                    {
                        "__id": "1",
                        "ChannelID": "159",
                        "PowerLevel": "2.9 dBmV",
                        "SNRLevel": "42.67 dB",
                        "PLCFrequency": "122 MHz",
                        "LockStatus": "Locked",
                        "ChannelType": "OFDM",
                        "FFT": "256-qam/4096-qam",
                        "Profile": "2",
                    }
                ],
                "ErrTbl": [
                    {
                        "__id": "1",
                        "Octets": "761663734",
                        "Correcteds": "18607766",
                        "Uncorrectables": "0",
                    }
                ],
            },
        }
    )
