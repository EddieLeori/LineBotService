#!/bin/bash
mkdir -p log
nohup python3 main.py >> log.txt 2>&1 &

