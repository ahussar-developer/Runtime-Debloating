#!/bin/bash

pushd /home/user/
# Simple WGET test
wget http://127.0.0.1:8181/index.html
rm index.html

# AB Testing
### Connections
ab -n 10000 http://127.0.0.1:8181/index.html
### Connections & Concurrency
ab -n 10000 -c 500 http://127.0.0.1:8181/index.html

# Simulate user interaction
python3 /home/user/passes/py_scripts/webdriver.py

popd
