import time
import adafruit_datetime

import json

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

# My station: 14th and 6
STOP_ID = 'D19'

# ------------------------------------------------------------------------------------------------------
# SETUP
# ------------------------------------------------------------------------------------------------------
# ESP wifi setup
esp32_cs = DigitalInOut(board.ESP_CS)
esp32_ready = DigitalInOut(board.ESP_BUSY)
esp32_reset = DigitalInOut(board.ESP_RESET)
spi = busio.SPI(board.SCK, board.MOSI, board.MISO)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)
wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(esp, secrets)

# Display setup
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


def get_departure_times():
    resp = wifi.get(
        'https://bwpddnvln1.execute-api.us-east-1.amazonaws.com/dev/{}'.format(STOP_ID),
        headers={"x-api-key": secrets['ryan_personal_api_key']}
    )
    d = resp.json()
    resp.close()

    return d


# How many times to query the API (seconds)
API_REFRESH_DELAY = 30


ARROW_X = -2
TRAIN_SYMBOL_X = 9
RIGHT_ALIGN_X = 64

TOP_HALF_Y = 8
BOTTOM_HALF_Y = 24


class TimeBoard:
    # X-Values (Where each slide-piece is placed horizontally)
    ARROW_X = -2

    # Style
    SYMBOL_FONT = bitmap_font.load_font("/siji_mta.bdf")
    TEXT_COLOR = 0x222222
    TRAIN_COLOR_ORANGE_FM = 0xcc461b

    UP_ARROW = '\uE12b'
    DOWN_ARROW = '\uE12c'

    def __init__(self, departure_times):
        # Arrays to hold "slides" - A slide is a self-contained group showing the departure time including icon, time, and arrow
        # The first item in the array is always displayed so to rotate the display, we roatate the array
        self.uptown_slides = []
        self.downtown_slides = []

        # The parent group for the actual displayio layers that make up the board
        self.time_board_group = displayio.Group()

        self.update_board(departure_times)

    # Make an "empty slide" for use when there are no trains
    def make_empty_slide(self, arrow, y_val):
        # Slide is list, not displayio.Group because displayio.Group has issues
        slide = []

        slide.append(adafruit_display_text.label.Label(
            self.SYMBOL_FONT,
            color=self.TEXT_COLOR,
            text=arrow,
            x=ARROW_X,
            y=y_val
        ))
        slide.append(adafruit_display_text.label.Label(
            terminalio.FONT,
            color=self.TEXT_COLOR,
            text="No trains",
            anchor_point=(1.0, 0.5),
            anchored_position=(RIGHT_ALIGN_X, y_val - 1)
        ))

        return slide

    def make_uptown_slide(self, departure):
        return self.make_slide(departure, self.UP_ARROW, TOP_HALF_Y)

    def make_downtown_slide(self, departure):
        return self.make_slide(departure, self.DOWN_ARROW, BOTTOM_HALF_Y)

    def make_slide(self, departure, arrow, y_val):
        slide = []

        slide.append(adafruit_display_text.label.Label(
            self.SYMBOL_FONT,
            color=self.TEXT_COLOR,
            text=arrow,
            x=ARROW_X,
            y=y_val
        ))
        # Train Symbol
        slide.append(adafruit_display_text.label.Label(
            self.SYMBOL_FONT,
            color=self.TRAIN_COLOR_ORANGE_FM,
            text=departure['route_id'],
            x=TRAIN_SYMBOL_X,
            y=y_val
        ))

        if departure['departs_in'] == 0:
            slide.append(adafruit_display_text.label.Label(
                terminalio.FONT,
                color=0xaa0000,
                text="Now",
                anchor_point=(1.0, 0.5),
                anchored_position=(RIGHT_ALIGN_X, y_val - 2)
            ))
        else:
            slide.append(adafruit_display_text.label.Label(
                terminalio.FONT,
                color=self.TEXT_COLOR,
                text="{} Min".format(departure['departs_in']),
                anchor_point=(1.0, 0.5),
                anchored_position=(RIGHT_ALIGN_X, y_val - 2)
            ))

        return slide

    # Re-create arrays with the new departure time information
    def update_board(self, departure_times):
        # Reset
        self.uptown_slides = []
        self.downtown_slides = []

        # Only cycle the first 3 trains
        for departure in departure_times['uptown'][:3]:
            self.uptown_slides.append(self.make_uptown_slide(departure))
        for departure in departure_times['downtown'][:3]:
            self.downtown_slides.append(self.make_downtown_slide(departure))

        if len(self.uptown_slides) == 0:
            self.uptown_slides.append(self.make_empty_slide('\uE12b', TOP_HALF_Y))
        if len(self.downtown_slides) == 0:
            self.downtown_slides.append(self.make_empty_slide('\uE12c', BOTTOM_HALF_Y))

    # Since slides are stored in array with the first slide being the one displayed, slide advancement is just an array rotation
    def advance_slides(self):
        # Clear board by deleting every item in the group
        # Incredibly hacky but CircuitPy throws a fit (ValueError: Layer already in a group) if this doesn't happen
        for _ in range(len(self.time_board_group)):
            del self.time_board_group[0]

        self.uptown_slides = self.uptown_slides[1:] + self.uptown_slides[: 1]
        self.downtown_slides = self.downtown_slides[1:] + self.downtown_slides[: 1]

        for slide in self.uptown_slides[0]:
            self.time_board_group.append(slide)
        for slide in self.downtown_slides[0]:
            self.time_board_group.append(slide)

    def get_board(self):
        return self.time_board_group


time_board = TimeBoard(get_departure_times())
last_refreshed = adafruit_datetime.datetime.now()
while True:
    # refresh the API every minute (or so)
    if adafruit_datetime.datetime.now() - last_refreshed > adafruit_datetime.timedelta(0, API_REFRESH_DELAY, 0):
        last_refreshed = adafruit_datetime.datetime.now()
        time_board.update_board(get_departure_times())

    time_board.advance_slides()
    display.show(time_board.get_board())

    display.refresh(minimum_frames_per_second=0)
    time.sleep(10)
