# Homewizard Climate integration for Homeassistant

## installation
you can add this repo to your homeassistant by installing HACS and choosing integrations, install a custom repository and paste this url.

![image](https://user-images.githubusercontent.com/15904064/216421839-c1feff4c-36c4-4e8c-9df4-9b4eb7c52a5d.png)

after that you can add the integration to Homeassistant and input your username and password.

## supported devices
This custom_component is in an early stage of development and works for the following device types returned from the Homewizard Climate API:
- `heaterfan`
- `infraredheater`
- `heater`
- `dehumidifier`
- `fan`
- `aircooler`

It has been tested on the following devices (even though it might work on others too):
- [Princess Smart Heating and Cooling Tower (01.347000.01.001)](https://www.princesshome.eu/en-gb/princess-01-347000-01-001-smart-heating-and-01.347000.01.001)
- [Princess Smart Infrared Panel Heater 350 (01.343350.02.001)](https://www.princesshome.eu/en-gb/princess-01-343350-02-001-smart-infrared-panel-01.343350.02.001)
- [Princess Smart Glass Panel Heater (01.342001.09.001)](https://www.princesshome.eu/en-gb/princess-01-342001-09-001-smart-glass-panel-heater-01.342001.09.001)
- [Princess 353130 Smart Dehumidifier 30](https://www.princesshome.eu/en-gb/princess-products/dehumidifiers/princess-353130-smart-dehumidifier-30-01.353130.01.001) ✓ tested
- [Princess 350000 Smart Tower Fan](https://www.princesshome.eu/en-gb/princess-products/fans/princess-350000-smart-tower-fan-01.350000.01.001) ✓ tested
- [Princess 357250 Smart Air Cooler](https://www.princesshome.eu/en-gb/princess-357250-smart-air-cooler-01.357250.01.001) ✓ tested

Note: The original heater/infraredheater/heaterfan devices are listed as supported but have not been tested by the current maintainer.

## my device isn't supported
If your device is supported in the Homewizard climate app but not yet in this integration please create an issue.
