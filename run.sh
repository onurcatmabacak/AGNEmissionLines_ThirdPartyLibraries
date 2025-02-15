#!/bin/bash
sudo docker build --network=host -t my-python-app .
sudo docker run --rm -v "$(pwd)/output:/app/output" my-python-app
# sudo docker-compose down
# sudo docker-compose up --build -d
python3 log_parser_ultra.py
sed -i 's/_/-/g' table_output.tex
