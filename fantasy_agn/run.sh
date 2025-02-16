#!/bin/bash
sudo docker build --network=host -t fantasy_agn .
sudo docker run --rm -v "$(pwd)/output:/app/output" fantasy_agn

