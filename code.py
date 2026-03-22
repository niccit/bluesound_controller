# SPDX-License-Identifier: MIT
import os
import adafruit_connection_manager
import adafruit_minimqtt.adafruit_minimqtt
from adafruit_minimqtt.adafruit_minimqtt import MMQTTException
import board
import socketpool
import wifi
import time
import neopixel
from adafruit_neokey.neokey1x4 import NeoKey1x4
import adafruit_logging
import adafruit_requests
from adafruit_requests import OutOfRetries
from adafruit_seesaw import digitalio, rotaryio, seesaw
from neopixel import NeoPixel

from ElementTree import fromstring
import adafruit_led_animation.color
from adafruit_max1704x import MAX17048

# Use to test that properly formatted objects will be passed and to turn on debug logging
testing = False

# ---- Set up Logging ---- #
logger = adafruit_logging.getLogger("bluesound_logger")
if testing:
    logger.setLevel(adafruit_logging.DEBUG)
    logger.debug("we are testing")
else:
    logger.setLevel(adafruit_logging.INFO)

# ---- Set up Socketpool ---- #
pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool)

# --- Battery Monitor --- #
batMon = MAX17048(i2c_bus=board.I2C())

# --- I2C Setup --- #
i2c = board.STEMMA_I2C()

# ---- Volume Control setup ---- #
seesaw = seesaw.Seesaw(i2c, 0x37)
seesaw.pin_mode(24, seesaw.INPUT_PULLUP)
button = digitalio.DigitalIO(seesaw, 24)
button_held = False
encoder = rotaryio.IncrementalEncoder(seesaw)
last_position = None
volume_increment = os.getenv("volume_inc")  # Android app increments by 2

# ----- NeoPixel setup ----- #
# Colors
hdmi_source = adafruit_led_animation.color.CYAN
optical_source = adafruit_led_animation.color.JADE
aloha_joe = adafruit_led_animation.color.RED

# 4 key NeoKey
keypad = NeoKey1x4(i2c, addr=0x30)
keypad.pixels[0] = optical_source
keypad.pixels[1] = hdmi_source
keypad.pixels[3] = aloha_joe

# ---- Bluesound Node ---- #
baseURL = os.getenv("bluesound_baseUrl")
logger.debug(f"base url is {baseURL}")
opticalInput = "Play?url=Capture%3Ahw%3Aimxspdif%2C0%2F1%2F25%2F2%3Fid%3Dinput1&preset_id&image=/images/capture/ic_opticalinput.png"
hdmiInput = "Play?url=Capture%3Ahw%3Aimxspdif%2C0%2F1%2F25%2F2%3Fid%3Dinput2&preset_id&image=/images/capture/ic_hdmi.png"
volumeQuery = "Volume"
volumeChange = "Volume?level="
aloha_joe_play = "Play?url=TuneIn%3As49372&preset_id&image=http://cdn-radiotime-logos.tunein.com/s49372g.png"
aloha_joe_pause = "Pause?url=TuneIn%3As49372&preset_id&image=http://cdn-radiotime-logos.tunein.com/s49372g.png"

# ---- MQTT ---- #
# Config
radio = wifi.radio
pool = adafruit_connection_manager.get_radio_socketpool(radio)
ssl_context = adafruit_connection_manager.get_radio_ssl_context(radio)

# MQTT specific helpers
def on_connect(mqtt_client, userdata, flags, rc):
    # This function will be called when the mqtt_client is connected
    # successfully to the broker.
    logger.info("Connected to MQTT Broker!")
    logger.debug(f"Flags: {flags}\n RC: {rc}")

def on_disconnect(mqtt_client, userdata, rc):
    # This method is called when the mqtt_client disconnects
    # from the broker.
    logger.error(f"Disconnected from MQTT Broker!")
    counter = 0
    while counter <= 10:
        try:
            my_mqtt.reconnect()
            counter = 11
        except MMQTTException:
            counter += 1
            time.sleep(1)
            pass

def on_subscribe(mqtt_client, userdata, topic, granted_qos):
    # This method is called when the mqtt_client subscribes to a new feed.
    logger.debug(f"Subscribed to {topic} with QOS level {granted_qos}")

def on_unsubscribe(mqtt_client, userdata, topic, pid):
    # This method is called when the mqtt_client unsubscribes from a feed.
    logger.debug(f"Unsubscribed from {topic} with PID {pid}")

def on_publish(mqtt_client, userdata, topic, pid):
    # This method is called when the mqtt_client publishes data to a feed.
    logger.debug(f"Published to {topic} with PID {pid}")

def on_message(client, topic, message):
    logger.debug(f"New message on topic {topic}: {message}")

# MQTT set up
local_mqtt_broker = os.getenv("mqtt_local_server")
local_mqtt_port = os.getenv("mqtt_local_port")
local_mqtt_username = os.getenv("mqtt_local_username")
local_mqtt_password = os.getenv("mqtt_local_key")

my_mqtt = adafruit_minimqtt.adafruit_minimqtt.MQTT(
    broker=local_mqtt_broker
    , port=local_mqtt_port
    , username=local_mqtt_username
    , password=local_mqtt_password
    , ssl_context = ssl_context
    , socket_pool=pool
    , is_ssl=False
)

# Connect callback handlers to mqtt_client
my_mqtt.on_connect = on_connect
my_mqtt.on_disconnect = on_disconnect
my_mqtt.on_subscribe = on_subscribe
my_mqtt.on_unsubscribe = on_unsubscribe
my_mqtt.on_publish = on_publish
my_mqtt.on_message = on_message

# Feeds
battery_feed = os.getenv("battery_feed")

# ---- Helpers ---- #
# Return the last volume level
def get_volume():
    volumeResponse = requests.get(baseURL + volumeQuery)
    stringToParse = f"""{volumeResponse.text}"""
    volumeBuffer = fromstring(stringToParse)
    currentVolume = volumeBuffer.text
    return currentVolume

# Monitor the battery
batteryCheckWait = 60
batteryCheck = None
batteryWarn = False
def monitor_battery():
    batVoltage = round(batMon.cell_voltage, 1)
    batPercentage = round(batMon.cell_percent, 2)
    return batVoltage, batPercentage

# Handle all MQTT publish requests
def do_publish(feed, msg):
    if testing:
        logger.debug(f"Testing: would publish {msg} to {feed}")
    else:
        try:
            my_mqtt.publish(feed, msg)
        except MMQTTException:
            logger.error("unable to connect to remote MQTT broker, message not sent")
            my_mqtt.disconnect()
            pass

# Handle all API requests
def send_request(url):
    if testing:
        logger.debug(f"Would send {url}")
    else:
        try:
            requests.post(url)
        except OutOfRetries as e:
            logger.error(f"unable to send message: {e}")
            pass

# ---- Startup ---- #
my_mqtt.connect()
increment = int(volume_increment)  # mirror the Android app, increase volume by 2 with each turn
is_playing = False
logger.info("Bluesound companion starting up!")
onboardLED = neopixel.NeoPixel(board.NEOPIXEL, 1, brightness=1)

while True:
    position = -encoder.position    # turn clockwise to increase, counter-clockwise to decrease

    # Setting the volume on the bluesound node does not directly relate to the position of the
    # rotary encoder. We set this to determine if volume should be increased or decreased
    if last_position is None:
        last_position = position
        logger.debug(f"position is {position} and last_position is {last_position}")

    if last_position != position:
        logger.debug(f"last position {last_position} does not equal position {position}")
        volumeLevel = get_volume()  # get current volume level
        volume = int(volumeLevel)  # convert to an int for maths
        logger.debug(f"volume is {volume}")
        if position < last_position:    # lower the volume
            logger.debug(f"{position} < {last_position}")
            last_position = position
            logger.debug(f"last position is {last_position}")
            new_volume = volume - int(volume_increment)
            logger.debug(f"new_volume is {new_volume}")
            if new_volume >= 0:
                volume_url = f"{baseURL}{volumeChange}{new_volume}"
                send_request(volume_url)
        elif position > last_position:  # increase the volume
            logger.debug(f"{position} > {last_position}")
            last_position = position
            logger.debug(f"last position is {last_position}")
            new_volume = volume + int(volume_increment)
            logger.debug(f"new_volume is {new_volume}")
            if new_volume <= 100:
                logger.debug(f"new_volume is less than or equal to 100")
                volume_url = f"{baseURL}{volumeChange}{new_volume}"
                send_request(volume_url)

    # If the rotary encoder is pressed, if volume is not 0 set it to zero/mute
    # Store the volume prior to change
    # If the volume is zero, restore volume to last saved level
    if not button.value:
        logger.debug(f"button pushed volume is {volume}")
        if volume != 0:
            last_volume = volume
            mute_url = f"{baseURL}{volumeChange}0"
            logger.debug(f"url to send is mute_url: {mute_url}")
            send_request(mute_url)
            volume = 0
        else:
            unmute_url = f"{baseURL}{volumeChange}{last_volume}"
            logger.debug(f"url to send is unmute_url: {unmute_url}")
            send_request(unmute_url)
            volume = last_volume

    # Keypad
    # The third key is intentionally not programmed
    if keypad[0]:       # Change input to Optical
        logger.debug("switching to optical")
        keypad_url = baseURL + opticalInput
        send_request(keypad_url)
    if keypad[1]:       # Change input to HDMI Arc
        logger.debug("switching to HDMI")
        keypad_url = baseURL + hdmiInput
        send_request(keypad_url)
    if keypad[3]:       # Play TuneIn favorite Aloha Joe Radio
        logger.debug("tuning in to Aloha Joe Radio")
        if not is_playing:
            keypad_url = baseURL + aloha_joe_play
            send_request(keypad_url)
            is_playing = True
        else:
            keypad_url = baseURL + aloha_joe_pause
            send_request(keypad_url)
            is_playing = False

    # Check the voltage of the battery, send a message to MQTT if it's below 3.7V
    if batteryCheck is None or time.monotonic() > batteryCheck + batteryCheckWait:
        logger.debug("battery check hello")
        batteryVoltage, batteryPercentage = monitor_battery()
        if batteryVoltage < 3.7 and not batteryWarn:
            logger.debug("We need to warn")
            batteryWarn = True
            onboardLED.fill((255, 128, 0))
            do_publish(battery_feed, batteryVoltage)
        elif batteryVoltage >= 4.0 and batteryWarn:
            logger.debug("We need to reset the warn flag")
            do_publish(battery_feed, batteryVoltage)
            onboardLED.fill((0, 255, 0))
            batteryWarn = False
        elif 3.9 > batteryVoltage >= 3.7:
            onboardLED.fill((255, 255, 0))

        logger.debug(f"battery warning {batteryVoltage:.2f} Volts, and battery warn is {batteryWarn}")
        batteryCheck = time.monotonic()

    time.sleep(0.25)

