# ABP activation parameters (remove to use OTAA)
ABP_DEV_ADDR = '00000005'
ABP_NWK_SWKEY = '2B7E151628AED2A6ABF7158809CF4FAB'
ABP_APP_SWKEY = '2B7E151628AED2A6ABF7158809CF4FCD'

# OTAA activation parameters
OTAA_APP_EUI = 'ADA4DAE3AC12676B'
OTAA_APP_KEY = '11B0282A189B75B0B4D2D8C7FA38548B'

LORA_REGION = 'EU868' # 'AS923', 'AU915', 'EU868', or 'US915'
LORA_DR = 5 # Data rate: 0 to 5

LORA_SEND_INTERVAL = 60 # Inteval in seconds between state uplinks

LORA_STATE_PERSIST = True # Set to True to persist the LoRaWAN state (joined status, frame counters, etc) in non-volatile memory in order to retain it across power cycles.

LORA_LED = True # Set to True to have the LED light flash when state uplinks are transmitted. False to disable it.

TEMP_OFFSET = 0 # Temperature offset (°C)
ELEVATION = 90 # Elevation from sea level in meters, for atmospheric pressure calculation

DI_DEBOUNCE_MS = 50 # Debounce time (ms) applied to digital inputs

# FTP server credentials
FTP_USER = 'exo' # set to '' to disable, you won't be able to access via FTP anymore
FTP_PASSWORD = 'sense'

# Access point WiFi
AP_SSID = 'ExoSenseAP'
AP_PASSWORD = 'exosense'

MODE_TEST = False # Test mode
