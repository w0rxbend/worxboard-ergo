# Prototype assembly plan

A0 is for engineering review. Complete [A1 gates](roadmap.md) before purchasing assembled PCBs or committing to a full case print.

1. Pick MX or Choc v1. The PCBs, plate thickness and switch-to-PCB spacing differ. Do not mix variants.
2. Obtain actual switch, socket, stabilizer, keycap and LCD samples. Wide Choc v1 keycaps in this familiar staggered layout may require custom keycaps or a layout revision. The current keycap envelopes do not include stems. Confirm these parts before freezing the layout.
3. Print small plate/cutout coupons in the intended material; test switch clip retention, stem travel, stabilizer alignment, LCD aperture and USB plug clearance. The two plate profiles include provisional stabilizer openings that are not yet approved for either family.
4. Route and review the selected PCB. Require zero ERC errors, zero DRC errors, no unconnected nets, schematic/PCB pad-net parity and reviewed USB layout before generating Gerbers. Check the exact chosen four-layer fabricator stackup and assembly BOM.
5. Assemble a small PCB prototype quantity. Begin with a current-limited bench supply, inspect 3.3/1.1 V rails, verify no VBUS backfeed, and use SWD for initial firmware programming. Validate the J6/J7 center-port ROM override and restore RUN jumpers after flashing.
6. Populate switches and test every matrix position, diode orientation, USB input, LCD layer label, hot-swap socket and keycap clearance.
7. Print the whole tray and plate on a suitable bed, or finish the split-part registration and joining design. The exported split files are fit models, not a mechanically complete tiled enclosure. Start with PETG/ASA coupons; material shrinkage and plate flexibility are untested. Metal plates need a manufacturer review of internal corners and clip retention.
8. Use appropriate M2.5 screws after measuring the final stack. The CAD uses 2.1 mm pilot bores, not insert pockets. Select screw length to avoid bottoming or cutting through the floor. Fit the removable display bezel and add non-slip feet and a palm-rest surface/attachment chosen during fit review.

Do not order directly from the illustrative BOM. Component lifecycle, price, stock, footprints and assembly orientation have not been supplier-verified for this project. No board has been fabricated or tested.

Exported parts retain assembly coordinates in STEP, STL and 3MF. Reorient the chosen part and place its bottom face on the build plate before slicing. The 3MF files contain geometry in millimeters, not printer-specific settings or a validated print profile.
