import time
import adafruit_datetime

import adafruit_display_text.label
from adafruit_bitmap_font import bitmap_font
import board
import displayio
import framebufferio
import rgbmatrix
import terminalio

import busio
from digitalio import DigitalInOut
from adafruit_esp32spi import adafruit_esp32spi_wifimanager
from adafruit_esp32spi import adafruit_esp32spi

from secrets import secrets

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


# ------------------------------------------------------------------------------------------------------
# Logic
# ------------------------------------------------------------------------------------------------------

# CONSTANTS ----------------------------------------
# How many times to query the API (seconds)
API_REFRESH_DELAY = 30
# My station: 14th and 6
STOP_ID = 'D19'


# Get departure times from my API
def get_departure_times():
    resp = wifi.get(
        'https://bwpddnvln1.execute-api.us-east-1.amazonaws.com/dev/{}'.format(STOP_ID),
        headers={"x-api-key": secrets['ryan_personal_api_key']}
    )
    d = resp.json()
    resp.close()

    return d


class TimeBoard:
    # X-Positions
    TRAIN_SYMBOL_X_POS = 9
    RIGHT_ALIGN_X_POS = 64

    # Y-Positions
    TOP_HALF_Y_POS = 8
    BOTTOM_HALF_Y_POS = 24

    # Style
    SYMBOL_FONT = bitmap_font.load_font("/siji_mta.bdf")
    TEXT_COLOR = 0x222222
    TRAIN_COLOR_ORANGE_FM = 0xcc461b

    def __init__(self, departure_times):
        # 2D List to hold "slides" - A slide is a self-contained group of layers showing the departure time including icon, time, and arrow
        # The first item in the array is always displayed so to rotate the display, we roatate the array
        self.uptown_layers = []
        self.downtown_layers = []

        # Static layers don't rotate - Right now just the Uptown/Downtown arrows
        arrow_x_pos = -2
        self.static_layers = [
            adafruit_display_text.label.Label(
                self.SYMBOL_FONT,
                color=self.TEXT_COLOR,
                text='\uE12c',
                x=arrow_x_pos,
                y=self.BOTTOM_HALF_Y_POS
            ),
            adafruit_display_text.label.Label(
                self.SYMBOL_FONT,
                color=self.TEXT_COLOR,
                text='\uE12b',
                x=arrow_x_pos,
                y=self.TOP_HALF_Y_POS
            ),
        ]

        # The parent group for the actual displayio layers that make up the board
        self.time_board_group = displayio.Group()

        self.update_departure_times(departure_times)

    # Make an "empty slide" for use when there are no trains
    def make_empty_slide(self, y_val):
        return [
            adafruit_display_text.label.Label(
                terminalio.FONT,
                color=self.TEXT_COLOR,
                text="No trains",
                anchor_point=(1.0, 0.5),
                anchored_position=(self.RIGHT_ALIGN_X_POS, y_val - 1)
            )
        ]

    def make_uptown_slide(self, departure):
        return self.make_slide(departure, self.TOP_HALF_Y_POS)

    def make_downtown_slide(self, departure):
        return self.make_slide(departure, self.BOTTOM_HALF_Y_POS)

    # Make a "slide" - The icon and text associated with a departure time
    # Slide is list, not displayio.Group because displayio.Group has issues
    def make_slide(self, departure, y_val):
        slide = []
        # Train Symbol
        slide.append(adafruit_display_text.label.Label(
            self.SYMBOL_FONT,
            color=self.TRAIN_COLOR_ORANGE_FM,
            text=departure['route_id'],
            x=self.TRAIN_SYMBOL_X_POS,
            y=y_val
        ))

        if departure['departs_in'] == 0:
            slide.append(adafruit_display_text.label.Label(
                terminalio.FONT,
                color=0xaa0000,
                text="Now",
                anchor_point=(1.0, 0.5),
                anchored_position=(self.RIGHT_ALIGN_X_POS, y_val - 2)
            ))
        else:
            slide.append(adafruit_display_text.label.Label(
                terminalio.FONT,
                color=self.TEXT_COLOR,
                text="{} Min".format(departure['departs_in']),
                anchor_point=(1.0, 0.5),
                anchored_position=(self.RIGHT_ALIGN_X_POS, y_val - 2)
            ))

        return slide

    # Re-create layer arrays with the new departure time information
    def update_departure_times(self, departure_times):
        # Reset
        self.uptown_layers = []
        self.downtown_layers = []

        # Only create slides for the first 3 trains
        for departure in departure_times['uptown'][:3]:
            self.uptown_layers.append(self.make_uptown_slide(departure))
        for departure in departure_times['downtown'][:3]:
            self.downtown_layers.append(self.make_downtown_slide(departure))

        if len(self.uptown_layers) == 0:
            self.uptown_layers.append(self.make_empty_slide(self.TOP_HALF_Y_POS))
        if len(self.downtown_layers) == 0:
            self.downtown_layers.append(self.make_empty_slide(self.BOTTOM_HALF_Y_POS))

    # Since slides are stored in array with the first slide being the one displayed, slide advancement is just an array rotation
    def advance_slides(self):
        self.uptown_layers = self.uptown_layers[1:] + self.uptown_layers[: 1]
        self.downtown_layers = self.downtown_layers[1:] + self.downtown_layers[: 1]
        self.refresh_board()

    def refresh_board(self):
        # Clear board by deleting every item in the group
        # Incredibly hacky but CircuitPy throws a fit (ValueError: Layer already in a group) if this doesn't happen
        for _ in range(len(self.time_board_group)):
            del self.time_board_group[0]

        for layer in self.static_layers:
            self.time_board_group.append(layer)
        for layer in self.uptown_layers[0]:
            self.time_board_group.append(layer)
        for layer in self.downtown_layers[0]:
            self.time_board_group.append(layer)

    def get_board(self):
        return self.time_board_group


time_board = TimeBoard(get_departure_times())
last_refreshed = adafruit_datetime.datetime.now()
while True:
    # refresh the API every minute (or so)
    if adafruit_datetime.datetime.now() - last_refreshed > adafruit_datetime.timedelta(0, API_REFRESH_DELAY, 0):
        last_refreshed = adafruit_datetime.datetime.now()
        time_board.update_departure_times(get_departure_times())

    time_board.advance_slides()
    display.show(time_board.get_board())

    display.refresh(minimum_frames_per_second=0)
    time.sleep(10)
