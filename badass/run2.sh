#!/bin/bash
sudo docker build -f dockerfile2 --network=host -t badass2 .
sudo docker run -p 8889:8889 --rm -v "$(pwd)/output2:/app/output2" badass2

