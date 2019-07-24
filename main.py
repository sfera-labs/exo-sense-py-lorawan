last_send = None
buzzer_start = 0
buzzer_ms = 0
buzzer_flip = 0
DI1_deb_val = -1
DI1_deb_ts = 0
DI1_deb_count = 0
DI2_deb_val = -1
DI2_deb_ts = 0
DI2_deb_count = 0

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
    from cayenneLPP import cayenneLPP

    _set_config('TEMP_OFFSET', 0)
    _set_config('ELEVATION', 0)
    _set_config('LORA_SEND_INTERVAL', 60)
    _set_config('LORA_LED', True)
    _set_config('MODE_TEST', False)
    _set_config('DI_DEBOUNCE_MS', 50)

    if config.FTP_USER and config.FTP_PASSWORD:
        if config.AP_SSID and config.AP_PASSWORD:
            wlan.init(mode=WLAN.AP, ssid=config.AP_SSID, auth=(WLAN.WPA2, config.AP_PASSWORD))
            print('AP enabled', config.AP_SSID)
        ftp.init(login=(config.FTP_USER, config.FTP_PASSWORD))
        print('FTP enabled')

    exo = ExoSense()
    exo.light.init()
    exo.thpa.init(temp_offset=(config.TEMP_OFFSET - 5), elevation=config.ELEVATION)
    exo.sound.init(avg_samples=0, peak_samples=0, peak_return_time=0)

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
        f = open('deveui.txt', 'w')
        f.write(ubinascii.hexlify(lora.mac()).decode('ascii'))
        f.close()
        lora.join(activation=LoRa.OTAA, auth=(app_eui, app_key), timeout=0)
        print("Using OTAA")

    blink = True
    while not lora.has_joined():
        blink = not blink
        pycom.rgbled(0xff0000 if blink else 0x000000)
        time.sleep(0.5)

    pycom.rgbled(0x00ff00)

    wdt.init(timeout=30000)
    wdt.feed()

    s = socket.socket(socket.AF_LORA, socket.SOCK_RAW)
    s.setsockopt(socket.SOL_LORA, socket.SO_DR, config.LORA_DR)
    s.setblocking(False)

    lpp = cayenneLPP.CayenneLPP(size=100, sock=s)

    config.LORA_SEND_INTERVAL *= 1000

    print("Waiting...")
    for i in range(3):
        time.sleep_ms(1000)
        time.sleep_ms(((crypto.getrandbits(32)[0] << 8) | crypto.getrandbits(32)[0]) % 3000)
        wdt.feed()
        try:
            print("Sending", i)
            lpp.reset_payload()
            lpp.add_analog_input(i, channel=99)
            lpp.send()
        except OSError as e:
            print("Send error:", e)

    time.sleep_ms(1000)

    thpa_read_ok = exo.thpa.read()
    sound_val = sound_min = sound_max = sound_avg = exo.sound.read()
    sound_samples = 1
    start_time = time.ticks_ms()
    last_thpa_read = start_time
    last_sound_sample = start_time

    print("Starting loop")
    pycom.rgbled(0x000000)

    while True:
        now = time.ticks_ms()

        DI1_val = exo.DI1()
        DI2_val = exo.DI2()

        if DI1_deb_val != DI1_val:
            if time.ticks_diff(DI1_deb_ts, now) >= config.DI_DEBOUNCE_MS:
                DI1_deb_val = DI1_val
                DI1_deb_ts = now
                if DI1_val == 1:
                    if DI1_deb_count < 327:
                        DI1_deb_count += 1
                    else:
                        DI1_deb_count = 0
        else:
            DI1_deb_ts = now

        if DI2_deb_val != DI2_val:
            if time.ticks_diff(DI2_deb_ts, now) >= config.DI_DEBOUNCE_MS:
                DI2_deb_val = DI2_val
                DI2_deb_ts = now
                if DI2_val == 1:
                    if DI2_deb_count < 327:
                        DI2_deb_count += 1
                    else:
                        DI2_deb_count = 0
        else:
            DI2_deb_ts = now

        sound_val = (sound_val * 299 + exo.sound.read()) // 300

        sound_do_sample = False

        if sound_val < sound_min:
            sound_min = sound_val
            sound_do_sample = True

        if sound_val > sound_max:
            sound_max = sound_val
            sound_do_sample = True

        if sound_do_sample or time.ticks_diff(last_sound_sample, now) >= 300:
            if sound_samples < 10000:
                sound_samples += 1
            sound_avg = (sound_avg * (sound_samples - 1) + sound_val) // sound_samples
            last_sound_sample = now

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

            lpp.reset_payload()
            lpp.add_digital_input(DI1_deb_val, channel=10)
            lpp.add_analog_input(DI1_deb_count, channel=11)
            lpp.add_digital_input(DI2_deb_val, channel=20)
            lpp.add_analog_input(DI2_deb_count, channel=21)
            lpp.add_digital_output(exo.DO1(), channel=30)
            lpp.add_digital_input(buzzer_flip, channel=51)
            lpp.add_temperature(exo.thpa.temperature(), channel=101)
            lpp.add_relative_humidity(exo.thpa.humidity(), channel=102)
            lpp.add_barometric_pressure(exo.thpa.pressure(), channel=103)
            gas = exo.thpa.gas_resistance()
            if gas:
                lpp.add_analog_input(gas / 10000, channel=104)
            lpp.add_luminosity(exo.light.lux(), channel=111)
            lpp.add_analog_input(sound_avg / 100, channel=121)
            lpp.add_analog_input(sound_min / 100, channel=122)
            lpp.add_analog_input(sound_max / 100, channel=123)

            if config.LORA_LED:
                pycom.rgbled(0x500030)

            try:
                print("Sending")
                lpp.send()
                last_send = time.ticks_ms()
                sound_min = sound_max = sound_avg = sound_val
                sound_samples = 1
            except OSError as e:
                print("Send error:", e)

            if config.LORA_LED:
                time.sleep_ms(200)
                pycom.rgbled(0x000000)

        try:
            rx, port = s.recvfrom(16)
            if rx:
                print('Received: {}, on port: {}'.format(rx, port))
                if len(rx) == 4 and rx[3] == 0xff:
                    if rx[0] == 50:
                        buzzer_ms = int(((rx[1] & 0xff) << 8) + rx[2])
                        print('Beep:', buzzer_ms)
                        if buzzer_ms > 0:
                            buzzer_start = time.ticks_ms()
                            exo.buzzer(1)
                            buzzer_flip = not buzzer_flip
                    elif rx[0] == 30:
                        do1_val = 0 if (rx[1] == 0 and rx[2] == 0) else 1
                        print('DO1:', do1_val)
                        exo.DO1(do1_val)
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
