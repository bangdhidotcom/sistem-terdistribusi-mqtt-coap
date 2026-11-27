import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from vendor.jump2.uml_core import Diagram, C, FILL
from vendor.jump2.uml_drawml import to_drawingml
from vendor.jump2.uml_png import render_png
from vendor.jump2.uml_validate import validate, report_text_fit

def build_architecture():
    # Setup canvas
    d = Diagram("Architecture", 26, 16)
    d.label_at(13, 0.55, "Arsitektur Replikasi MQTT <-> CoAP pada IP Konvensional",
               pt=10.5, bold=True, color=C["ink"], fill=C["paper"])

    # Legend
    d.rrect("leg_bg", 0.2, 11.8, 8.2, 3.3, fill=C["paper"], line=C["gray"])
    d.label_at(4.3, 12.25, "Legenda", pt=9.5, bold=True)
    d.label_at(2.6, 12.85, "Biru: MQTT -> CoAP", pt=8, bold=False, color=C["blue_d"])
    d.label_at(2.9, 13.35, "Hijau: CoAP -> MQTT", pt=8, bold=False, color=C["green_d"])
    d.label_at(3.1, 13.85, "Ungu: Conversion Server", pt=8, bold=False, color=C["purple_d"])
    d.label_at(4.1, 14.35, "Kotak = proses / peran", pt=7.5, bold=False, color=C["muted"])

    # Components
    d.rrect("mqtt_pub", 2, 2, 4, 1.5, text="MQTT Publisher", fill=FILL["blue"], line=C["blue_d"])
    d.rrect("mqtt_brk", 8, 2, 4, 1.5, text="MQTT Broker\n1883 / 1884", fill=FILL["green"], line=C["green_d"])
    d.rrect("conv_srv", 14, 5, 4, 4, text="Conversion\nServer", fill=FILL["purple"], line=C["purple_d"])
    d.rrect("coap_srv", 20, 2, 4, 1.5, text="CoAP Server\n5683 / 5684", fill=FILL["orange"], line=C["orange_d"])
    d.rrect("coap_cli", 22, 5, 3, 1.5, text="CoAP Client", fill=FILL["red"], line=C["red_d"])
    d.rrect("mqtt_sub", 2, 8, 4, 1.5, text="MQTT Subscriber", fill=FILL["blue"], line=C["blue_d"])

    # Edges (label chip sengaja diletakkan di luar kotak agar tidak menimpa)
    d.edge([(6, 2.75), (8, 2.75)], color=C["blue_d"], arrow="arrow")
    d.label_at(7, 1.45, "iot/mqtt_to_coap", pt=7.5, bold=True, color=C["blue_d"], fill=C["paper"])
    d.edge([(12, 2.75), (14, 6)], color=C["blue_d"], arrow="arrow")
    d.edge([(18, 6), (20, 2.75)], color=C["blue_d"], arrow="arrow")
    d.label_at(19.1, 4.75, "/target", pt=8, bold=True, color=C["blue_d"], fill=C["paper"])

    d.edge([(22, 5.75), (20, 3.5)], color=C["green_d"], arrow="arrow")
    d.label_at(22.6, 4.55, "/source", pt=8, bold=True, color=C["green_d"], fill=C["paper"])
    d.edge([(18, 7), (14, 8.75)], color=C["green_d"], arrow="arrow")
    d.edge([(8, 8.75), (6, 8.75)], color=C["green_d"], arrow="arrow")
    d.label_at(7, 10.1, "iot/coap_to_mqtt", pt=7.5, bold=True, color=C["green_d"], fill=C["paper"])

    return d

def save_diagram(d, name, doc_id):
    xml_path = f"output-xml/{name}.xml"
    png_path = f"output/{name}.png"
    
    with open(xml_path, "w", encoding="utf-8") as f:
        f.write(to_drawingml(d, doc_id=doc_id, name=name))
    
    render_png(d, png_path, dpi=200)
    
    print(f"--- Validating {name} ---")
    validate(d)
    report_text_fit(d)

if __name__ == "__main__":
    d = build_architecture()
    save_diagram(d, "mqtt_coap_architecture", 301)
