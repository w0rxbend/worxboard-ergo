# System76 Launch reference and feature coverage

The full public [System76 Launch repository](https://github.com/system76/launch) is included as a pinned Git submodule at `references/system76-launch`. This includes its chassis models, PCB variants, common libraries, scripts, packaging, benchmark and regulatory source folders. Its nested QMK firmware submodule is retained; run `make references` to retrieve it. Those reference files describe Launch, not this RP2040 keyboard, and their regulatory results do not apply here.

| Launch capability | worxboard ergo A0 / target |
|---|---|
| Open source chassis/CAD/PCB/firmware | Original source and editable CAD/KiCad/ZMK starter included |
| Compact layout without numpad | 48-key split Planck; numbers and function keys on the Lower layer |
| Split spacebar | Two 1u spaces on the inner edge of the left Planck block |
| MX hot swap | Included in MX placement seed; physical fit pending |
| Per-switch matrix diodes / rollover | 48 diodes in the 6×15 scan matrix; host rollover not hardware tested |
| Per-key independent RGB | Target retained in roadmap; only expansion header exists in A0 |
| USB 3.2 Gen 2 integrated dock | Not included: user selected three alternative host-input sockets |
| QMK firmware | Replaced by user-requested ZMK on RP2040 |
| System76 Keyboard Configurator | Not compatible; ZMK Studio USB transport is the selected replacement |
| Runtime remapping/settings | Studio build configuration included; device/host testing pending |
| fwupd/LVFS updates | Not integrated; SWD then RP2040 UF2 after mux-override design |
| Milled aluminum chassis | Split Planck chassis and plate STEP, plus a prototype machining sheet; no first article |
| Adjustable incline | Fixed about 7° negative tilt from unequal feet; not adjustable, and the keywells are not roll-tented |
| Regulatory results | Upstream reference only; no product compliance claim |
| Low-profile version | Added Choc v1 option, not a Launch PCB transplant |
| Center layer LCD | Added SPI Sharp memory LCD with ZMK layer widget |

This repository does not promise binary compatibility with System76 software. Launch licenses and notices remain in its submodule. The local hardware is an independently generated RP2040 design with the sibling worxboard RP2040 circuit as a starting point.

`make references` intentionally retrieves Launch and its pinned QMK tree without fetching every legacy QMK build dependency. A recursive fetch attempted during A0 reached an HTTP 500 from Savannah for OpenOCD's nested `tools/git2cl` commit `8373c9f74993e218a08819cbcdbab3f3564bbeba`. That optional reference dependency is not needed for the local RP2040/ZMK build; its upstream gitlink and URL remain unchanged.
