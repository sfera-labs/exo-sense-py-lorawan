from network import WLAN
from network import Server
from machine import WDT
import pycom
import micropython
import time

micropython.alloc_emergency_exception_buf(100)
pycom.heartbeat(False)
pycom.rgbled(0xff0000)
print('=== Exo Sense Py - LoRaWAN - v1.4.0 ===')

wdt = WDT(timeout=30000)

wlan = WLAN()
wlan.deinit()

ftp = Server()
ftp.deinit()

time.sleep(1)
