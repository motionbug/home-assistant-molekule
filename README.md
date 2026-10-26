![logo](https://github.com/user-attachments/assets/65b8b825-56c5-41db-8d95-6bdddef1ddf2)

# README

Home Assistant Molekule Integration

Version: 0.1.17

Requires Home Assistant Core 2026.10 or newer. Regression tests run against
Home Assistant 2026.10.4 on Python 3.14; real-device testing is still required.

### Description

This integration provides support for Molekule devices directly integrated into Home Assistant.  (Currently only Molekule Air Pro & Molekule Air).

[Note: Molekule Air less tested!]

This relies on the cloud, it talks directly to Molekule's web api.

This will show sensors for: 

* Air Quality
* VOC
* Humidity
* PM2.5
* PM10
* CO2
* Air Filter life.

This will add a fan entity that will allow you to: 

* Control Mode (Automatic / Manual)
* Control Fan Speed 

There is configuration for:

* How often to poll Molekule's api
* Whether or not for enable "Quiet" (aka Silent) mode when the unit is set to Automatic

### Installation

This integration requires [HACS](https://hacs.xyz/).
1. In HACS, open the menu and choose **Custom repositories**.
2. Add `https://github.com/motionbug/home-assistant-molekule` with type **Integration**.
3. Download **Molekule**. This fork permits default-branch downloads without a GitHub release.
4. Restart Home Assistant, then go to **Settings → Devices & services → Add integration → Molekule**.
5. Enter your Molekule account email and password. Polling and quiet automatic mode
   can be changed using **Configure** after setup.

Only one Molekule integration can be installed at a time. If switching from the
original repository, back up your configuration and replace its HACS repository
with this fork; retain your existing Molekule config entry to preserve entity IDs.

For manual development installation, copy `custom_components/molekule/` into
`<config>/custom_components/molekule/` and restart Home Assistant.

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=molekule)

### Notes

* Pull Requests and Issues are welcome.
* This is only tested with `Molekule Air Pro`, other models are not supported.
* This was inspired by: https://github.com/csirikak/homebridge-molekule  (Thanks!)

### Compatibility update (0.1.17)

Replaces the obsolete `warrant` authentication wrapper with `pycognito`, retaining
Cognito SRP, the existing Molekule API URLs and command payloads. Updates setup,
options, reauthentication and sensor unit APIs, fixes connection recovery, and adds
English UI translations. Existing account data, entity unique IDs and polling
options are retained, including the legacy `sync_interval` option.

### Troubleshooting

If HACS cannot download the integration, check that this fork is registered as an
Integration and that the default branch or a release is available. After updating,
restart Home Assistant before adding or configuring Molekule.

For **Unable to install**, **Failed to set up**, or **Config flow could not be
loaded**, check **Settings → System → Logs**. Include the Home Assistant Core
version, integration version, failure stage (HACS download or Add Integration),
and traceback in an issue. Redact passwords, tokens, emails, serial numbers and
device responses. Cloud outages are retried; rejected credentials prompt
reauthentication. Accounts requiring password changes or MFA need attention in
Molekule's own app first.

### Development and tests

Use Python 3.14.2 or newer in the 3.14 series in a virtual environment:

```sh
python3.14 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements_test.txt
python -m pytest -q
python -m compileall -q custom_components/molekule
git diff --check
```

Tests use real Home Assistant flow/coordinator/entity classes with mocked cloud
responses; no Molekule credentials are needed. CI also runs hassfest and HACS
validation. Before releasing, test HACS installation, authentication, sensors,
fan controls, options and reload/unload on a real Home Assistant instance and
record the device model and Core version.


