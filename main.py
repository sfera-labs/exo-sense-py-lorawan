last_send = None
buzzer_start = 0
buzzer_ms = 0

def _set_config(attr, def_val):
    val = getattr(config, attr, def_val)
    setattr(config, attr, val)

try:
    import config
except Exception:
    class Config(object):
        pass
    config = Config()

try:
    import sys
    import time
    import socket
    import micropython
    import pycom
    import ubinascii
    import struct
    import crypto
    from network import WLAN
    from network import LoRa
    from exosense import ExoSense
    from exosense import thpa_const
    import cayenneLPP

    _set_config('TEMP_OFFSET', 0)
    _set_config('ELEVATION', 0)
    _set_config('LORA_SEND_INTERVAL', 60)
    _set_config('LORA_LED', True)
    _set_config('MODE_TEST', False)

    if config.FTP_USER and config.FTP_PASSWORD:
        if config.AP_SSID and config.AP_PASSWORD:
            wlan.init(mode=WLAN.AP, ssid=config.AP_SSID, auth=(WLAN.WPA2, config.AP_PASSWORD))
            print('AP enabled', config.AP_SSID)
        ftp.init(login=(config.FTP_USER, config.FTP_PASSWORD))
        print('FTP enabled')

    exo = ExoSense()
    exo.light.init()
    exo.thpa.init(temp_offset=(config.TEMP_OFFSET - 5), elevation=config.ELEVATION)

    lora = LoRa(mode=LoRa.LORAWAN, region=getattr(LoRa, config.LORA_REGION), device_class=LoRa.CLASS_C)

    wdt.init(timeout=300000)
    wdt.feed()

    try:
        dev_addr = struct.unpack(">l", ubinascii.unhexlify(config.ABP_DEV_ADDR))[0]
        nwk_swkey = ubinascii.unhexlify(config.ABP_NWK_SWKEY)
        app_swkey = ubinascii.unhexlify(config.ABP_APP_SWKEY)
        lora.join(activation=LoRa.ABP, auth=(dev_addr, nwk_swkey, app_swkey))
        print("Using ABP")
    except Exception:
        app_eui = ubinascii.unhexlify(config.OTAA_APP_EUI)
        app_key = ubinascii.unhexlify(config.OTAA_APP_KEY)
        lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=0)
        print("Using OTAA")

    blink = True
    while not lora.has_joined():
        blink = not blink
        pycom.rgbled(0xff0000 if blink else 0x000000)
        time.sleep(0.5)

    pycom.rgbled(0xff0000)

    wdt.init(timeout=30000)
    wdt.feed()

    s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
    s.setsockopt(socket.SOL_LORA, socket.SO_DR, config.LORA_DR)
    s.setblocking(False)

    lpp = cayenneLPP.CayenneLPP(size=100, sock=s)

    config.LORA_SEND_INTERVAL *= 1000

    print("Waiting...")
    # Sleep random time up to 7 seconds
    time.sleep_ms(((crypto.getrandbits(32)[0] << 8) | crypto.getrandbits(32)[0]) % 7000)

    thpa_read_ok = exo.thpa.read()
    start_time = time.ticks_ms();
    last_thpa_read = start_time

    print("Starting loop")
    pycom.rgbled(0x000000)

    while True:
        now = time.ticks_ms()

        if (not config.MODE_TEST) and ftp.isrunning() and time.ticks_diff(start_time, now) >= 300000:
            ftp.deinit()
            wlan.deinit()
            print('AP and FTP disabled')

        if (not thpa_read_ok) or time.ticks_diff(last_thpa_read, now) >= 5000:
            print('Reading THPA')
            thpa_read_ok = exo.thpa.read()
            if thpa_read_ok:
                wdt.feed()
                last_thpa_read = now

        if exo.buzzer() and time.ticks_diff(buzzer_start, now) >= buzzer_ms:
            exo.buzzer(0)

        if thpa_read_ok and (last_send == None or time.ticks_diff(last_send, now) >= config.LORA_SEND_INTERVAL):
            # Sleep random time up to 255 ms
            time.sleep_ms(crypto.getrandbits(32)[0])

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

            if config.LORA_LED:
                pycom.rgbled(0x000050)

            try:
                print("Sending")
                lpp.send(reset_payload=True)
                last_send = time.ticks_ms()
            except OSError:
                print("Send error:", e)

            if config.LORA_LED:
                time.sleep_ms(200)
                pycom.rgbled(0x000000)

        try:
            rx, port = s.recvfrom(16)
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
            print("Receive error:", e)

except Exception as e:
    sys.print_exception(e)
    if last_send == None:
        wdt.init(timeout=300000)
        wdt.feed()
        pycom.rgbled(0xffff00)
        wlan.deinit()
        ftp.deinit()
        time.sleep(1)
        wlan.init(mode=WLAN.AP, ssid='ExoSenseAP', auth=(WLAN.WPA2, 'exosense'))
        ftp.init(login=('exo', 'sense'))
        print('AP and FTP default enabled')
