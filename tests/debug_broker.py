import os, subprocess, sys, time
from pathlib import Path
import paho.mqtt.client as mqtt
ROOT = Path(__file__).resolve().parents[1]
PORT = 1885
env = os.environ.copy(); env['MQTT_PORT'] = str(PORT)
broker = subprocess.Popen([sys.executable, str(ROOT/'src'/'mqtt_broker.py'), '--log', 'data/raw/debug'], cwd=str(ROOT), env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
time.sleep(1)
events = []
def on_connect(c,u,f,rc,p=None):
    events.append('connected rc=%r' % (rc,)); c.subscribe('iot/test')
def on_message(c,u,m):
    events.append('got %s %r' % (m.topic, m.payload))
sub = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id='dbg_sub')
sub.on_connect = on_connect; sub.on_message = on_message
sub.connect('127.0.0.1', PORT, keepalive=60); sub.loop_start()
time.sleep(1)
pub = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2, client_id='dbg_pub')
pub.connect('127.0.0.1', PORT, keepalive=60); pub.loop_start()
time.sleep(0.3); pub.publish('iot/test', b'hello'); time.sleep(3)
sub.loop_stop(); pub.loop_stop(); broker.terminate()
out,_ = broker.communicate(timeout=5)
print('EVENTS:', events)
print('BROKER OUT:', out[-2000:])
