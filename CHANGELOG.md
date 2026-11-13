# Changelog

All releases are engineering previews of hardware revision A0. None is a fabrication release. No keyboard has been built.

## [0.2.0-a0] - 2026-11-13

### Added
- A curved, Sculpt-style shell around the unchanged 48-key layout: a tangent-arc outline, an open slot between the wells, and a 67 mm palm rest.
- A flush top cover that frames both wells and holds the display window.
- An optional magnetic riser for 6.7° of negative tilt.
- A [3D print guide](docs/printing.md) and a [documentation index](docs/README.md).
- A product page, published with GitHub Pages, with renders of the CAD model.
- Fit checks for USB plugs and receptacles, switch housings, keycap travel, and the display pocket.

### Changed
- All screws now enter from the underside: eight into the top cover and six into the palm rest.
- The one-piece chassis is 303 × 223 mm and needs a 350 mm class bed. The split halves need about 235 mm.

### Fixed
- Exported parts were mirror images of the PCB. They now match it, and tests check the shared holes against the board placement.

### Removed
- The separate `display_bezel` part. The top cover replaces it.

### Known problems
- Both PCBs are unrouted: zero tracks and 329 unconnected items each. Do not order them.
- The PCB places the three USB jacks facing the typist. The case assumes they face the rear wall.
- The PCB keeps parts on the top side, under the plate, with no height check.
- Nothing has been printed, measured, or assembled.

## [0.1.0] - unreleased

- First 48-key split Planck layout, replacing the earlier TKL.
- Launch-style tray case, KiCad placement seeds, and the ZMK board.

[0.2.0-a0]: https://github.com/w0rxbend/worxboard-ergo/releases/tag/v0.2.0-a0
