import machine
import micropython
import pycom

if (not pycom.wdt_on_boot()) or (pycom.wdt_on_boot_timeout() != 60000):
    pycom.wdt_on_boot(True)
    pycom.wdt_on_boot_timeout(60000)

if machine.reset_cause() != machine.DEEPSLEEP_RESET:
    print('Resetting...')
    machine.deepsleep(1000)

micropython.alloc_emergency_exception_buf(100)

wdt = machine.WDT(timeout=30000)

pycom.heartbeat(False)
pycom.rgbled(0xff0000)

print('=== Exo Sense Py - LoRaWAN - v1.5.0 ===')
