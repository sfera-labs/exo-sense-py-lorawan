# Exo Sense Py LoRaWAN

This firmware lets you use [Exo Sense Py](https://www.sferalabs.cc/exo-sense-py/) equipped with a LoPy board as a LoRaWAN Class A/C end-device, sending environmental data encoded with the Cayenne LPP format.

This code includes this [CayenneLPP library](https://github.com/jojo-/py-cayenne-lpp) by Johan.

## Connecting to Exo Sense

Power up Exo Sense, it will start up with a WiFi access point enabled. If the module has never been configured, the WiFi name will be "lopy4-wlan-" followed by a number and the password will be "www.pycom.io". If this firmware was previously uploaded, the access point name and password are those specified in the uploaded configuration file (see below); the default WiFi name is "ExoSenseAP" and the default password is "exosense". This firmware will disable the access point after 5 minutes from power up (unless test mode is enabled, see configuration).

Join the access point network and use any FTP client to connect to `ftp://192.168.4.1`. Use plain FTP (no encryption) in passive mode, limiting the max number of connections to one. If using FileZilla, check [this page](https://docs.pycom.io/gettingstarted/programming/ftp.html#filezilla).

For non-configured modules use "micro" as username and "python" as password. For modules using this firmware use the previously configured credentials; the default ones are "exo" as username and "sense" as password.

To install this firmware, just upload the content of this repo into the `/flash` directory.

## Configuration

All configuration parameters are in the [config.py](config.py) file, together with their documentation.

To modify the configuration, restart Exo Sense, join its WiFi access point, download the file via FTP, edit it, re-upload it and restart Exo Sense.

## LED status table

|LED status|Description|
|:--------:|-----------|
|Red|Starting up|
|Red blink|Joining LoRaWAN network|
|Green|Sending initialization frames|
|Purple blink|Sending state uplink (if enabled in configuration)|
|Yellow|Configuration error: default access point and FTP credentials enabled|

## LoRaWAN Communication

When configured, Exo Sense will start sending unconfirmed state uplinks periodically, with the interval specified in the configuration. The packet payload is encoded using the [Cayenne LPP format](https://mydevices.com/cayenne/docs/lora/#lora-cayenne-low-power-payload).

Downlink commands, encoded in Cayenne LLP format, can be sent at any time to change the state of the digital output or to activate the buzzer.

### Cayenne channels

|Channels|Type|Uplink/Downlink|Description|
|:-------|:--:|---------------|-----------|
|10|Digital Input|U|DI1 state|
|11|Analog Input|U|DI1 counter, increased on every rising edge. Range: 0-327 (rolls back to 0 after 327)|
|20|Digital Input|U|DI2 state|
|30|Digital Output|U/D|DO1 state|
|50|Analog Output|D|Activate the buzzer for the specified time in 0.1sec (e.g. 3 = 300ms, 10 = 1s)|
|101|Temperature|U|Measured temperature|
|102|Relative Humidity|U|Measured relative humidity|
|103|Barometric Pressure|U|Measured atmospheric pressure|
|104|Analog Input|U|Air resistance (quality indication) in 10K&#8486; (e.g. 12 = 120K&#8486;)|
|111|Luminosity|U|Measured luminosity|
|121|Analog Input|U|Average of measured noise intensity since last uplink|
|122|Analog Input|U|Minimum measured noise intensity since last uplink|
|123|Analog Input|U|Maximum measured noise intensity since last uplink|
|99|Analog Input|U|Initialization frame sent 3 times at random interval at start up. The value is a progression from 1 to 3|
