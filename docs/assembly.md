# Prototype assembly plan

A0 is for engineering review. The step-by-step shop and bench sequence is [build.md](build.md). Complete [A1 gates](roadmap.md) before purchasing assembled PCBs or committing to a full case print.

1. Pick MX or Choc v1. The PCBs, plate thickness and switch-to-PCB spacing differ. Do not mix variants.
2. Obtain actual switch, socket, keycap and LCD samples. Every key on this grid is 1u, including Backspace, Enter, both Shifts, and the two Space keys. There is no stabilizer. The keycap envelopes do not include stems.
3. Print a small plate coupon in the intended material before a full plate. Test switch clip retention, stem travel, the south LED window, the LCD aperture and USB plug clearance.
4. Review the routed PCB and its order package, `pcb/fab/<variant>/` (see `ORDER.md` there). The design files pass ERC, DRC, unconnected-item, schematic-parity and pad-net checks; that is not a review. AGENTS.md still requires a person to review the USB pairs, ground planes and return paths, and every Gerber layer, before any money is spent. The assembler fits every SMD part on the bottom side, the three USB-C receptacles on top, and the hot-swap sockets. It does not fit switches, J4, J5, J6 or J7.
5. Do not fit standard pin headers at J5, J6 or J7, or the 5 mm socket at J4, on the top side: each is taller than the room under the plate (1.0 mm on Choc v1, 3.5 mm on MX). For the J6/J7 RUN setting, bridge pins 1–2 of each with a short wire link on the bottom side; see [electrical.md](electrical.md) for the ROM setting. The LCD mounting is open: the case expects the module 1.2 mm (Choc v1) or 4.0 mm (MX) above the PCB.
6. Assemble a small PCB prototype quantity. Begin with a current-limited bench supply, inspect 3.3/1.1 V rails, verify no VBUS backfeed, and use SWD for initial firmware programming. Validate the J6/J7 center-port ROM override and restore RUN jumpers after flashing.
7. Populate switches and test every matrix position, diode orientation, USB input, LCD layer label, hot-swap socket and keycap clearance.
8. Follow [cnc.md](cnc.md) for the chassis, plate, top cover, palm rest, and split prints. The center tab is modeled. Print a coupon of that tab before a full half. Metal plates need a process that can hold square switch corners.
9. Use M2.5 screws after measuring the stack. All screws enter from the underside: eight into the top-cover bosses and six into the palm rest. The pilots are 2.1 mm, not insert pockets. The chassis has no feet; it sits flat on four pads, or on the magnetic riser.

The BOM lines marked `MPN_READ_2026-11-13_STOCK_AND_PRICE_UNKNOWN` in `docs/bom.csv` had their part numbers read on a maker or distributor page; stock, price, lifecycle and assembly rotation are not checked. Lines marked `UNVERIFIED_NOT_FOR_ORDER` are not chosen. No board has been fabricated or tested.

Exported parts retain assembly coordinates in STEP, STL and 3MF. Reorient the chosen part and place its bottom face on the build plate before slicing. The 3MF files contain geometry in millimeters, not printer-specific settings or a validated print profile.
