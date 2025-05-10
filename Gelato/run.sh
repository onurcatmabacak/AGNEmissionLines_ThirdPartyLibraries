#!/bin/bash
sudo docker build --network=host -t gelato .
sudo docker run -p 8888:8888 --rm -v "$(pwd)/output:/app/output" gelato
sudo chmod -R 777 output/
