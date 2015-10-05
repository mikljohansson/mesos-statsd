FROM alpine:latest

RUN apk -U add python

COPY mesos-statsd.py /
COPY mesos-statsd.sh /

ENTRYPOINT ["/mesos-statsd.sh"]
