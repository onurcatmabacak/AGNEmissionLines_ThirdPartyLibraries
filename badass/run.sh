#!/bin/bash
sudo docker build --network=host -t badass .
sudo docker run -p 8888:8888 --rm -v "$(pwd)/output:/app/output" badass

