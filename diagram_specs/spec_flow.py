import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from vendor.jump2.uml_core import Diagram, C, FILL
from vendor.jump2.uml_drawml import to_drawingml
from vendor.jump2.uml_png import render_png
from vendor.jump2.uml_validate import validate, report_text_fit

def build_flow_m2c():
    d = Diagram("FlowM2C", 16, 22)
    steps = [
        "1. Publisher sends JSON",
        "2. MQTT Broker receives",
        "3. Conv Server processes & signs",
        "4. POST /target to CoAP Server",
        "5. CoAP Server queues",
        "6. GET client verifies"
    ]
    for i, step in enumerate(steps):
        d.rrect(f"s{i}", 2, 1 + i*3.2, 12, 2.5, text=step, fill=FILL["blue"], line=C["blue_d"])
        d.circle(2, 2.25 + i*3.2, 0.4, fill=C["blue"], line=C["blue_d"])
    
    for i in range(len(steps)-1):
        d.edge([(8, 3.5 + i*3.2), (8, 1 + (i+1)*3.2)], color=C["blue_d"], arrow="arrow")
        
    return d

def build_flow_c2m():
    d = Diagram("FlowC2M", 16, 22)
    steps = [
        "1. POST client sends",
        "2. CoAP Server /source queues",
        "3. Conv Server GET polling (1s)",
        "4. Deduplication by ID",
        "5. MQTT Publish",
        "6. Subscriber verifies"
    ]
    for i, step in enumerate(steps):
        d.rrect(f"s{i}", 2, 1 + i*3.2, 12, 2.5, text=step, fill=FILL["green"], line=C["green_d"])
        d.circle(2, 2.25 + i*3.2, 0.4, fill=C["green"], line=C["green_d"])
    
    for i in range(len(steps)-1):
        d.edge([(8, 3.5 + i*3.2), (8, 1 + (i+1)*3.2)], color=C["green_d"], arrow="arrow")
        
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
    d1 = build_flow_m2c()
    save_diagram(d1, "flow_mqtt_to_coap", 302)
    
    d2 = build_flow_c2m()
    save_diagram(d2, "flow_coap_to_mqtt", 303)
