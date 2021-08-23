# This example implements a simple two line scroller using
# Adafruit_CircuitPython_Display_Text. Each line has its own color
# and it is possible to modify the example to use other fonts and non-standard
# characters.

import adafruit_display_text.label
import adafruit_display_shapes.rect
import adafruit_display_shapes.circle
from adafruit_bitmap_font import bitmap_font
import board
import displayio
import framebufferio
import rgbmatrix
import terminalio
import time

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


# Return a train symbol group with the text and shape
def make_train_symbol(x, y, color):
    train_symbol = displayio.Group()
    #  Circle bg
    # train_symbol.append(adafruit_display_shapes.circle.Circle(
    #     x, y, 5, outline=color, stroke=1))
    train_symbol.append(adafruit_display_text.label.Label(
        SYMBOL_FONT,
        color=color,
        text="F",
        x=x-5,
        y=y+1,
        scale=1
    ))

    return train_symbol


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


# You can add more effects in this loop. For instance, maybe you want to set the
# color of each label to a different value.
while True:
    display.refresh(minimum_frames_per_second=0)
    time.sleep(.03)
