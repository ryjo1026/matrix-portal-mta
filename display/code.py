import time

import adafruit_display_text.label
import adafruit_display_shapes.rect
import adafruit_display_shapes.circle
from adafruit_bitmap_font import bitmap_font
import board
import displayio
import framebufferio
import rgbmatrix
import terminalio

import busio
import neopixel
from digitalio import DigitalInOut
from adafruit_esp32spi import adafruit_esp32spi_wifimanager
from adafruit_esp32spi import adafruit_esp32spi

from secrets import secrets

import mta

esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(esp, secrets)

resp = wifi.get('https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm', headers={'x-api-key': secrets['mta-api-key']})
print(resp.content)

f = mta.Feed()

displayio.release_displays()
matrix = rgbmatrix.RGBMatrix(
    width=64, bit_depth=4,
    rgb_pins=[
        board.MTX_R1,
        board.MTX_G1,
        board.MTX_B1,
        board.MTX_R2,
        board.MTX_G2,
        board.MTX_B2
    ],
    addr_pins=[
        board.MTX_ADDRA,
        board.MTX_ADDRB,
        board.MTX_ADDRC,
        board.MTX_ADDRD
    ],
    clock_pin=board.MTX_CLK,
    latch_pin=board.MTX_LAT,
    output_enable_pin=board.MTX_OE
)
display = framebufferio.FramebufferDisplay(matrix)

SYMBOL_FONT = bitmap_font.load_font("/siji_mta.bdf")


TEXT_COLOR = 0x222222
TRAIN_COLOR_ORANGE_FM = 0xcc461b
ARROW_X = -2
TRAIN_SYMBOL_X = 7
RIGHT_ALIGN_X = 64

TOP_HALF_Y = 8
BOTTOM_HALF_Y = 24

# Top Half
top_half = displayio.Group()
# Up Arrow
top_half.append(adafruit_display_text.label.Label(
    SYMBOL_FONT,
    color=TEXT_COLOR,
    text="\uE12b",
    x=ARROW_X,
    y=TOP_HALF_Y - 1
))
# Train Symbol
top_half.append(adafruit_display_text.label.Label(
    SYMBOL_FONT,
    color=TRAIN_COLOR_ORANGE_FM,
    text="F",
    x=TRAIN_SYMBOL_X,
    y=TOP_HALF_Y
))
# top_half.append(make_train_symbol(TRAIN_SYMBOL_X, TOP_HALF_Y - 1, TRAIN_COLOR_ORANGE_FM))
# Train Text
top_half.append(adafruit_display_text.label.Label(
    terminalio.FONT,
    color=TEXT_COLOR,
    text="5 Min",
    anchor_point=(1.0, 0.5),
    anchored_position=(RIGHT_ALIGN_X, TOP_HALF_Y - 2)
))


# Bottom Half
bottom_half = displayio.Group()
# Down Arrow
bottom_half.append(adafruit_display_text.label.Label(
    SYMBOL_FONT,
    color=TEXT_COLOR,
    text="\uE12c",
    x=ARROW_X,
    y=BOTTOM_HALF_Y
))
# Train Symbol
bottom_half.append(adafruit_display_text.label.Label(
    SYMBOL_FONT,
    color=TRAIN_COLOR_ORANGE_FM,
    text="M",
    x=TRAIN_SYMBOL_X,
    y=BOTTOM_HALF_Y
))
bottom_half.append(adafruit_display_text.label.Label(
    terminalio.FONT,
    color=TEXT_COLOR,
    text="6 Min",
    anchor_point=(1.0, 0.5),
    anchored_position=(RIGHT_ALIGN_X, BOTTOM_HALF_Y - 2)
))

# Display the groups constructed above
g = displayio.Group()
g.append(top_half)
g.append(bottom_half)
display.show(g)


while True:
    display.refresh(minimum_frames_per_second=0)
    time.sleep(.03)
