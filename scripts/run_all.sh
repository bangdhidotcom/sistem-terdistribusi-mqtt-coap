# Start all components
python src/mqtt_publisher.py --count 1 &
python src/mqtt_subscriber.py --duration 10 &
python experiments/payload_gen.py &
python scripts/healthcheck.py
