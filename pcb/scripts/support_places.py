# SPDX-License-Identifier: GPL-3.0-or-later
"""Seats for everything that is not a key or a mounting hole.

Component side follows measured height. The Choc plate underside is 1.0 mm
above the PCB and the chassis floor is 4.0 mm below it, so every SMD part
sits on B.Cu, the J6/J7 slide switches and the J5 connector included. Only the
receptacles (the case mouths are on the top side) and the J4 display position are
on F.Cu. place.py is the only consumer.

ANCHORS are absolute layout millimetres. SATELLITES are seated by place.py
as close as possible to one pad of their host, in table order.
"""
from layout.model import DISPLAY, USB_RECEPTACLE_L, mouths

TOP_SIDE = frozenset({"J1", "J2", "J3", "J4"})
MOUTH_FACES_REAR = 180.0          # the stock footprint opens toward +y; the case mouths are at the rear
HEADER_PITCH = 2.54
LCD_HEADER_INSET = 1.5            # nice!view pin row inside the module's short edge; check against a real module
DIODE_NORTH = 8.2                 # matrix diode centre behind its switch, clear of both socket types
BOSS_CLEAR = {"B": 4.0, "F": 2.9}   # chassis boss R3.6 below, cover boss R2.5 above, plus 0.4
DECOUPLING_RING = 5.0             # RP2040 capacitor centres stay this far from their pin: the band between holds
                                  # the escape vias of the 30 GPIO pins. Each pin and capacitor reach the planes by via

def anchors():
    """ref -> (x, y, angle). Receptacle bodies end flush with the board edge at each case mouth."""
    left, center, right = (mouths()[name] for name in ("left", "center", "right"))
    jack_y = USB_RECEPTACLE_L / 2
    lcd_x = DISPLAY["x"] + DISPLAY["module_width"] / 2 - LCD_HEADER_INSET
    return {
        "J1": (left[0], left[1] + jack_y, MOUTH_FACES_REAR),
        "J2": (center[0], center[1] + jack_y, MOUTH_FACES_REAR),
        "J3": (right[0], right[1] + jack_y, MOUTH_FACES_REAR),
        "J4": (lcd_x, DISPLAY["y"] - 2 * HEADER_PITCH, 0.0),
        # Pins 43-56 (USB, QSPI, regulator) face the rear, toward the mux and the centre receptacle.
        "U1": (-14.0, -34.0, 180.0),
        # USB leaves pins 46/47 straight to the rear: series resistors, then the mux with its common side facing them.
        # The resistors sit a little left of the pins, so the 3V3 pins 48-49 beside them can escape.
        "R4": (-16.2, -39.9, 270.0), "R3": (-15.0, -39.9, 270.0), "U7": (-15.2, -42.9, 0.0),
        # Flash to the rear and one side of the QSPI pins, pin 1 away from the MCU: the bus wraps both pin rows.
        # It stands far enough east that the right receptacle pair can end beside the mux inputs.
        "U2": (-5.5, -43.5, 180.0),
        "U3": (30.0, -46.0, 0.0),
        "SW1": (-34.0, -22.0, 0.0), "SW2": (-44.0, -22.0, 0.0),
        "J5": (44.0, -36.0, 90.0), "J6": (34.0, -24.0, 0.0), "J7": (34.0, -30.0, 0.0),   # J6/J7: 6.7 mm slide switches side by side
        "TP10": (-24.0, -22.0, 0.0),
    }

# The box around these pads of the first part and all of the second stays empty: the QSPI bus runs there.
CORRIDORS = (("U1", ("51", "52", "53", "54", "55", "56"), "U2"),)
# Boxes kept empty around a part, as (x0, y0, x1, y1) from its centre: the mux inputs to the rear and the right,
# its common pair to the front. Its own passives go to the select side.
KEEP_CLEAR = (("U7", (-5.0, -7.0, 6.0, 2.5), "B"),)

# (part, host, host pad, least distance between part centre and host pad)
SATELLITES = (
    ("Y1", "U1", "20", 4.6), ("R7", "U1", "21", 0.0), ("C6", "Y1", "1", 0.0), ("C7", "Y1", "3", 0.0),
    ("C19", "U1", "45", DECOUPLING_RING), ("C18", "U1", "44", DECOUPLING_RING), ("C17", "U1", "50", DECOUPLING_RING),
    ("C16", "U1", "23", DECOUPLING_RING), ("C14", "U1", "48", DECOUPLING_RING), ("C13", "U1", "49", DECOUPLING_RING),
    ("C15", "U1", "43", DECOUPLING_RING), ("C8", "U1", "1", DECOUPLING_RING), ("C9", "U1", "10", DECOUPLING_RING),
    ("C10", "U1", "22", DECOUPLING_RING), ("C11", "U1", "33", DECOUPLING_RING), ("C12", "U1", "42", DECOUPLING_RING),
    ("C5", "U2", "8", 0.0), ("R8", "U2", "1", 0.0), ("R9", "U2", "1", 0.0),
    ("C20", "U7", "12", 0.0), ("R40", "U7", "1", 0.0), ("R41", "U7", "2", 0.0),
    ("C1", "U3", "1", 0.0), ("C3", "U3", "5", 0.0), ("C4", "U3", "5", 0.0), ("C2", "U3", "1", 0.0),
    ("R42", "J6", "1", 0.0), ("R43", "J7", "1", 0.0), ("R10", "SW2", "1", 0.0),
    ("TP8", "U1", "24", 4.0), ("TP9", "U1", "25", 4.0),
) + tuple(row for i in (1, 2, 3) for row in (
    (f"U{3 + i}", f"J{i}", "A6", 0.0),
    (f"R{20 + 5 * i}", f"J{i}", "A5", 0.0), (f"R{21 + 5 * i}", f"J{i}", "B5", 0.0),
    (f"D{i}", f"J{i}", "A4", 0.0),
    (f"R{22 + 5 * i}", f"D{i}", "2", 0.0), (f"R{23 + 5 * i}", f"R{22 + 5 * i}", "2", 0.0),
))
