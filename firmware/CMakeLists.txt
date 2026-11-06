# SPDX-License-Identifier: GPL-3.0-or-later
if(CONFIG_BOARD_WORXBOARD_ERGO)
  zephyr_library()
  zephyr_library_sources(src/usb_selector.c)
endif()
