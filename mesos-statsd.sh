#!/bin/sh

# Run Python script in subprocess to make sure that [defunct] processes are reaped 
# properly by bash. Google "docker PID 1 zombie reaping problem" for more info.
python /bin/mesos-statsd.py $@ & wait
