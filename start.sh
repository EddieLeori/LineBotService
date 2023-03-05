#!/bin/bash
mkdir -p log
mkdir -p ssl
nohup python3 main.py >> log.txt 2>&1 &

