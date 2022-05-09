#!/bin/bash


if [ $MODE == 'api' ]; then
  source venv/bin/activate && python3 main.py -m API --ip $IP --port $PORT
else
  sleep 2 && source venv/bin/activate && python3 main.py -m CLI -i inventory.yaml -p playbook.yaml
fi