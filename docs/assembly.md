# Prototype assembly plan

A0 is for engineering review. The step-by-step shop and bench sequence is [build.md](build.md). Complete [A1 gates](roadmap.md) before purchasing assembled PCBs or committing to a full case print.

1. Pick MX or Choc v1. The PCBs, plate thickness and switch-to-PCB spacing differ. Do not mix variants.
2. Obtain actual switch, socket, keycap and LCD samples. Every key on this grid is 1u, including Backspace, Enter, both Shifts, and the two Space keys. There is no stabilizer. The keycap envelopes do not include stems.
3. Print a small plate coupon in the intended material before a full plate. Test switch clip retention, stem travel, the south LED window, the LCD aperture and USB plug clearance.
4. Route and review the selected PCB. Require zero ERC errors, zero DRC errors, no unconnected nets, schematic/PCB pad-net parity and reviewed USB layout before generating Gerbers. Check the exact chosen four-layer fabricator stackup and assembly BOM.
5. Assemble a small PCB prototype quantity. Begin with a current-limited bench supply, inspect 3.3/1.1 V rails, verify no VBUS backfeed, and use SWD for initial firmware programming. Validate the J6/J7 center-port ROM override and restore RUN jumpers after flashing.
6. Populate switches and test every matrix position, diode orientation, USB input, LCD layer label, hot-swap socket and keycap clearance.
7. Follow [cnc.md](cnc.md) for the chassis, plate, palm rest, and split prints. The center tab is modeled. Print a coupon of that tab before a full half. Metal plates need a process that can hold square switch corners.
8. Use M2.5 screws after measuring the stack. The CAD uses 2.1 mm pilots for tapping aluminum, not insert pockets. Sole heights are already in the chassis: 3 mm at the front and 14 mm at the rear. Fit the display bezel and the palm rest with the two shelf screws.

Do not order directly from the illustrative BOM. Component lifecycle, price, stock, footprints and assembly orientation have not been supplier-verified for this project. No board has been fabricated or tested.

Exported parts retain assembly coordinates in STEP, STL and 3MF. Reorient the chosen part and place its bottom face on the build plate before slicing. The 3MF files contain geometry in millimeters, not printer-specific settings or a validated print profile.
