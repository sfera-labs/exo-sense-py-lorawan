from network import WLAN
from network import Server
import pycom
import micropython

micropython.alloc_emergency_exception_buf(100)
pycom.heartbeat(False)
pycom.rgbled(0xff0000)
print('=== Exo Sense Py - LoRaWAN - v1.0.1 ===')

wlan = WLAN()
wlan.deinit()

ftp = Server()
ftp.deinit()
