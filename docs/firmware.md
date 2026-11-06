# ZMK build and controls

The west manifest pins ZMK to `4dd95d7840eb3d5a3f59bb29fbf1ab054715ef85`, the same source revision already used by the sibling worxboard project. The module lives at repository root (`zephyr/module.yml`) and includes the RP2040 board and USB input selection code. It does not use Launch's QMK firmware.

`make firmware` initializes an isolated west workspace under `build/zmk-ws`, checks the pinned SHA, and builds `worxboard_ergo/rp2040` using the recorded ZMK container and Zephyr SDK 0.16.9. To reuse an existing **matching** workspace:

```sh
ERGO_ZMK_WORKSPACE=/absolute/path/to/workspace make firmware
```

Both variants share one electrical matrix, LCD and controller, so they use the same [UF2](../firmware/artifacts/worxboard-ergo.uf2). Generated keymaps and physical layouts come from `tools/firmware_layout.py`, not from duplicating key-order tables by hand. Bluetooth and deep sleep are disabled. The SPI memory LCD uses the built-in layer widget with labels BASE, FN and MAINT. No battery widget is enabled. USB Studio transport is included; its host connection and settings persistence need physical testing.

- BASE is the standard US ANSI-style keymap shown in the layout image.
- Hold Fn for media controls on F1–F6 and navigation on arrows.
- Hold Fn + F12 to reach MAINT. Esc requests bootloader; F1 requests reset.

Studio locking is disabled for the A0 development build. Before a user release, choose and test a physical unlock binding and re-enable locking. Bootloader entry requires the J6/J7 ROM setting described in [electrical.md](electrical.md); ROM USB will not choose a port by itself.

The three-port selector code runs as a Zephyr module. Its host-side tests cover all combinations of powered inputs, priority and selected-input retention. The firmware build validates compilation, linking, devicetree and Kconfig. None of those proves USB attach, display orientation, key scanning or switch debounce on real hardware.

Do not flash an unrelated RP2040 product with this image. A safe first bring-up is supply checks -> SWD flash -> single center USB input -> matrix scan -> LCD -> all input ports -> reconnect and simultaneous-cable isolation tests.
