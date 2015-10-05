# Mesos StatsD forwarder
Forwards Mesos master and slave metrics to a StatsD instance.

## Environment Variables

 * **MESOS_URL** - Mesos metrics endpoint, e.g. "http://localhost:5050/"
 * **STATSD_URL** - StatsD URL to forward metrics to, e.g. "statsd://localhost:8125"
 * **METRICS_PREFIX=mesos** - Key prefix for metrics. Defaults to 'mesos'.
 * **REFRESH_INTERVAL=60** - Metrics update interval. Defaults to 60 seconds.

## Command Line Usage

```
Usage: docker run meltwater/mesos-statsd:latest [options]...

StatsD forwarder for Mesos metrics

Options:
  -h, --help            show this help message and exit
  -m MESOSURL, --mesos-url=MESOSURL
                        Mesos master or slave HTTP endpoint to check, e.g.
                        "http://localhost:5050/"
  -d STATSDURL, --statsd-url=STATSDURL
                        StatsD url to forward metrics to, e.g.
                        "statsd://localhost:8125"
  -p PREFIX, --metrics-prefix=PREFIX
                        Key prefix for metrics [default: mesos]
  -i INTERVAL, --refresh-interval=INTERVAL
                        Metrics update interval [default: 60]
  -v, --verbose         Increase logging verbosity
```

## Deployment
Both the Mesos master and slave supports the */metrics/snapshot* API. The master usually runs 
on port 5050 while the slave is available on port 5051.

### Systemd and CoreOS/Fleet
Create a [Systemd unit](http://www.freedesktop.org/software/systemd/man/systemd.unit.html) file 
in **/etc/systemd/system/mesos-statsd.service** with contents like below. Using CoreOS and
[Fleet](https://coreos.com/docs/launching-containers/launching/fleet-unit-files/) then
add the X-Fleet section to schedule the unit on all cluster nodes.


#### Mesos master
```
[Unit]
Description=StatsD forwarder for Mesos master
After=docker.service
Requires=docker.service

[Install]
WantedBy=multi-user.target

[Service]
Environment=IMAGE=meltwater/mesos-statsd:latest NAME=mesos-statsd

# Allow docker pull to take some time
TimeoutStartSec=600

# Restart on failures
KillMode=none
Restart=always
RestartSec=15

ExecStartPre=-/usr/bin/docker kill $NAME
ExecStartPre=-/usr/bin/docker rm $NAME
ExecStartPre=-/usr/bin/docker pull "${IMAGE}"
ExecStart=/usr/bin/docker run --net=host \
    --name=${NAME} \
    -e MESOS_URL=http://localhost:5050/ \
    -e STATSD_URL=statsd://localhost:8125 \
    -e METRICS_PREFIX=mesos.master.%H
    $IMAGE

ExecStop=/usr/bin/docker stop $NAME

# Schedule on Mesos master machines
[X-Fleet]
Global=true
MachineMetadata=mesos-master=true

```

##### Mesos slave
```
ExecStart=/usr/bin/docker run --net=host \
    --name=${NAME} \
    -e MESOS_URL=http://localhost:5051/ \
    -e STATSD_URL=statsd://localhost:8125 \
    -e METRICS_PREFIX=mesos.slave.%H
    $IMAGE

# Schedule on Mesos slave machines
[X-Fleet]
Global=true
MachineMetadata=mesos-slave=true

```

### Puppet Hiera
Using the [garethr-docker](https://github.com/garethr/garethr-docker) module

```
classes:
  - docker::run_instance

docker::run_instance:
  'mesos-statsd':
    image: 'meltwater/mesos-statsd:latest'
    net: 'host'
    env:
      - "MESOS_URL=http://localhost:5050/"
      - "STATSD_URL=statsd://localhost:8125"
      - "METRICS_PREFIX=mesos.master.%{::hostname}"
```
