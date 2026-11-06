/* SPDX-License-Identifier: GPL-3.0-or-later */
#pragma once
/* Bit 0 left, bit 1 center, bit 2 right. Keep an active port until its VBUS disappears. */
static inline int ergo_usb_choose(unsigned present, int current) {
    if (current >= 0 && current < 3 && (present & (1u << current))) { return current; }
    if (present & 2u) { return 1; }
    if (present & 1u) { return 0; }
    if (present & 4u) { return 2; }
    return -1;
}
