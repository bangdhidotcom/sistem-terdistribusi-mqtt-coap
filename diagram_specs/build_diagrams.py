import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from vendor.jump2.uml_core import Diagram, C
from vendor.jump2.uml_drawml import to_drawingml
from vendor.jump2.uml_png import render_png
from vendor.jump2.uml_validate import validate, report_text_fit

def build_architecture():
    # 25,7 x 16,3 cm landscape
    d = Diagram("Architecture", 25.7, 16.3)
    # Define roles
    d.rrect("mqtt_pub", 1, 5, 4, 2, text="MQTT Publisher", fill=C["blue"], line=C["blue_d"])
    d.rrect("mqtt_brk", 6, 2, 4, 2, text="MQTT Broker\n127.0.0.1:1883", fill=C["green"], line=C["green_d"])
    d.rrect("conv_srv", 11, 5, 4, 3, text="Conversion Server", fill=C["purple"], line=C["purple_d"])
    d.rrect("coap_srv", 17, 2, 4, 2, text="CoAP Server\n127.0.0.1:5683", fill=C["orange"], line=C["orange_d"])
    d.rrect("coap_cli", 22, 5, 3, 2, text="CoAP Client", fill=C["red"], line=C["red_d"])
    d.rrect("mqtt_sub", 1, 9, 4, 2, text="MQTT Subscriber", fill=C["blue"], line=C["blue_d"])

    # Edges
    d.edge([(5, 5.5), (6, 3)], color=C["blue_d"], arrow="arrow", label="iot/mqtt_to_coap")
    d.edge([(10, 3), (11, 6)], color=C["blue_d"], arrow="arrow")
    d.edge([(15, 6.5), (17, 3)], color=C["blue_d"], arrow="arrow", label="/target")
    
    # CoAP to MQTT
    d.edge([(22, 5.5), (21, 4)], color=C["green_d"], arrow="arrow", label="/source")
    d.edge([(17, 3), (15, 7.5)], color=C["green_d"], arrow="arrow")
    d.edge([(11, 7.5), (10, 10)], color=C["green_d"], arrow="arrow", label="iot/coap_to_mqtt")

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
