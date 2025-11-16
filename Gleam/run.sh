#!/bin/bash
sudo docker build --network=host -t gleam .
sudo docker run -p 8888:8888 --rm -v "$(pwd)/output:/app/output" gleam
sudo chmod -R 777 output/
