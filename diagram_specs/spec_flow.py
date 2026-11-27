import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from vendor.jump2.uml_core import Diagram, C
from vendor.jump2.uml_drawml import to_drawingml
from vendor.jump2.uml_png import render_png
from vendor.jump2.uml_validate import validate, report_text_fit

def build_flow_m2c():
    # Portrait 15,6 x 20,5 cm
    d = Diagram("FlowM2C", 15.6, 20.5)
    steps = [
        "1. Publisher Kirim",
        "2. Broker Terima",
        "3. Conv Server Validasi",
        "4. CoAP POST /target",
        "5. CoAP Server Simpan",
        "6. CoAP GET Verifikasi"
    ]
    for i, step in enumerate(steps):
        d.rrect(f"s{i}", 2, 1 + i*3, 11, 2, text=step, fill=C["blue"], line=C["blue_d"])
    
    for i in range(len(steps)-1):
        d.edge([(7.5, 3 + i*3), (7.5, 1 + (i+1)*3)], color=C["blue_d"], arrow="arrow")
        
    return d

def build_flow_c2m():
    # Portrait 15,6 x 20,5 cm
    d = Diagram("FlowC2M", 15.6, 20.5)
    steps = [
        "1. POST Client",
        "2. CoAP Server /source",
        "3. Conv GET Polling 1s",
        "4. Deduplikasi LastID",
        "5. MQTT Publish",
        "6. Subscriber Verifikasi"
    ]
    for i, step in enumerate(steps):
        d.rrect(f"s{i}", 2, 1 + i*3, 11, 2, text=step, fill=C["green"], line=C["green_d"])
    
    for i in range(len(steps)-1):
        d.edge([(7.5, 3 + i*3), (7.5, 1 + (i+1)*3)], color=C["green_d"], arrow="arrow")
        
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
