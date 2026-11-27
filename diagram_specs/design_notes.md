# Design Notes: MQTT-CoAP Diagrams

## Color Palette Strategy
- **Blue (MQTT → CoAP Path)**: Fill `E3ECFF`, Line `2A5FD4`
- **Green (CoAP → MQTT Path)**: Fill `D8F5E4`, Line `27AE60`
- **Purple (Conversion Server)**: Fill `EBDEF0`, Line `7D3C98`
- **Nodes/Entities**:
    - MQTT components: Blue accents
    - CoAP components: Orange/Green accents
    - Storage/Queues: Standardized as cylinders

## Diagram Layout Improvements
1. **Architecture Diagram**:
    - Use a clearer horizontal flow with dedicated lanes.
    - Add color-coded arrows and a clear legend in the bottom-right corner.
    - Conversion Server as the central hub.
2. **Flow Diagrams**:
    - Use sequence-style layout for steps 1-6.
    - Each step marked by a colored circle corresponding to its flow.
    - Use `activation` and `lifeline` primitives for process flow where appropriate.
3. **Visual Quality**:
    - Ensure all labels are legible (9pt min).
    - Use `label_chip` for step numbers.
    - Strict `validate()` pass to ensure no overlaps.
