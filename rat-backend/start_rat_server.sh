#!/bin/sh
source /home/rat-backend/rat/bin/activate
nohup python backend_controller_start.py >backend_log.out &
