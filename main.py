from network import WLAN
from network import Server
from machine import WDT
from exosense import ExoSense
from exosense import thpa_const
from network import LoRa
import time
import socket
import sys
import config
import micropython
import pycom
import cayenneLPP
import ubinascii
import struct

wdt = WDT(timeout=30000)

if hasattr(config, 'MODE_TEST'):
    config_MODE_TEST = config.MODE_TEST
else:
    config_MODE_TEST = False

if config.FTP_USER and config.FTP_PASSWORD:
    if config.AP_SSID and config.AP_PASSWORD:
        wlan.init(mode=WLAN.AP, ssid=config.AP_SSID, auth=(WLAN.WPA2, config.AP_PASSWORD))
        print('AP enabled')
    ftp.init(login=(config.FTP_USER, config.FTP_PASSWORD))
    print('FTP enabled')

exo = ExoSense()
exo.light.init()
exo.thpa.init(temp_offset=(config.TEMP_OFFSET - 5), elevation=config.ELEVATION)

wdt.feed()

lora = LoRa(mode=LoRa.LORAWAN, region=getattr(LoRa, config.LORA_REGION))

dev_addr = struct.unpack(">l", ubinascii.unhexlify(config.LORA_DEV_ADDR))[0]
nwk_swkey = ubinascii.unhexlify(config.LORA_NWK_SWKEY)
app_swkey = ubinascii.unhexlify(config.LORA_APP_SWKEY)

lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey))

wdt.feed()

s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
s.setsockopt(socket.SOL_LORA, socket.SO_DR, config.LORA_DR)

s.setblocking(True)
s.settimeout(5)

lpp = cayenneLPP.CayenneLPP(size=100, sock=s)

thpa_read_ok = exo.thpa.read()
start_time = time.ticks_ms();
last_thpa_read = start_time
last_send = None

buzzer_start = 0
buzzer_ms = 0

print("Starting loop")
pycom.rgbled(0x000000)

while True:
    now = time.ticks_ms()

    if (not config_MODE_TEST) and ftp.isrunning() and time.ticks_diff(start_time, now) >= 300000:
        print('AP and FTP disabled')
        ftp.deinit()
        wlan.deinit()

    if (not thpa_read_ok) or time.ticks_diff(last_thpa_read, now) >= 2000:
        thpa_read_ok = exo.thpa.read()
        if thpa_read_ok:
            wdt.feed()
            last_thpa_read = now

    if exo.buzzer() and time.ticks_diff(buzzer_start, now) >= buzzer_ms:
        exo.buzzer(0)

    if thpa_read_ok and (last_send == None or time.ticks_diff(last_send, now) >= config.LORA_SEND_INTERVAL * 1000):
        lpp.add_digital_input(exo.DI1(), channel=101)
        lpp.add_digital_input(exo.DI2(), channel=102)
        lpp.add_digital_output(exo.DO1(), channel=111)
        lpp.add_temperature(exo.thpa.temperature(), channel=121)
        lpp.add_relative_humidity(exo.thpa.humidity(), channel=122)
        lpp.add_barometric_pressure(exo.thpa.pressure(), channel=123)
        gas = exo.thpa.gas_resistance()
        if gas:
            if gas > 327670: # 327670 = 0x7FFF = max positive val
                gas = 327670
            lpp.add_analog_input(gas / 1000, channel=124)
        lpp.add_luminosity(exo.light.lux(), channel=131)

        print("----------------------")
        print("Sending...")
        lpp.send(reset_payload=True)
        print("Sent")
        last_send = time.ticks_ms()

        print('Receiving...')
        try:
            rx, port = s.recvfrom(256)
            if rx:
                print('Received: {}, on port: {}'.format(rx, port))
                if len(rx) == 4 and rx[3] == 0xff:
                    if rx[0] == 141:
                        buzzer_ms = int(((rx[1] & 0xff) << 8) + rx[2])
                        print('Beep:', buzzer_ms)
                        if buzzer_ms > 0:
                            buzzer_start = time.ticks_ms()
                            exo.buzzer(1)
        except TimeoutError:
            pass
        except Exception as e:
            print("Error:", e)
        print('Done')
