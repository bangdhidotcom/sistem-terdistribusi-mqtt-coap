# DIAGRAM QA REPORT

## Overview
- Architecture Diagram: `mqtt_coap_architecture`
- MQTT→CoAP Flow: `flow_mqtt_to_coap`
- CoAP→MQTT Flow: `flow_coap_to_mqtt`

## Metadata Summary

| Diagram | XML Size (bytes) | PNG Size (bytes) | Validated |
| :--- | :--- | :--- | :--- |
| `mqtt_coap_architecture` | ~47 KB | ~102 KB | Yes (0 issues) |
| `flow_mqtt_to_coap` | ~30 KB | ~55 KB | Yes (0 issues) |
| `flow_coap_to_mqtt` | ~30 KB | ~54 KB | Yes (0 issues) |

Catatan alur: Gambar 1 menampilkan `POST /source` dari CoAP client ke CoAP server dan
`GET /source (1 dtk)` dari conversion server ke CoAP server, sesuai implementasi
`src/conversion_server.py`. Validasi `validate()`/`report_text_fit()` hanya memeriksa
struktur dan tumpang tindih, bukan kesesuaian semantik alur.

## Implementation Details
- Used `uml_core`, `uml_drawml`, `uml_png`, `uml_validate` from `vendor/jump2/`.
- No `r:embed` or `<pic:pic>` found in XML (verified via structure check).
- All diagrams use `wps:wsp` and `wpg:wgp` structure.
- PNGs rendered at 200 DPI.

## Contrast Check (Manual)
All text colors (22304C) against pastel backgrounds meet the >4.5:1 contrast requirement for accessibility standards, as the backgrounds are light (e.g., E3ECFF, D5F5EC).

## Final Checks
- All diagrams have passed `validate()` and `report_text_fit()`.
- No structural overlaps or edge collisions reported.
