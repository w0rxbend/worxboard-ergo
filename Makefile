SHELL := /bin/bash
.PHONY: generate cad native laser test pcb firmware manifest check-fabrication references

generate:
	uv run python -m tools.layout
	uv run python -m tools.firmware_layout
	uv run python -m tools.bom
cad:
	uv run python -m tools.cad
native:
	bash tools/native.sh
laser:
	uv run --with fonttools==4.55.0 python -m tools.signature
test:
	uv run pytest -q
pcb:
	bash tools/pcb.sh
firmware:
	bash tools/firmware.sh
manifest:
	uv run python -m tools.manifest
check-fabrication:
	uv run python -m tools.fabrication_gate

references:
	bash tools/references.sh
