#!/usr/bin/env python
import os, sys, optparse, logging, time, urllib2, json, urlparse, socket

parser = optparse.OptionParser(
    usage='docker run meltwater/mesos-statsd:latest [options]...',
    description='StatsD forwarder for Mesos master and slave metrics')

def parsebool(value):
    truevals = set(['true', '1'])
    falsevals = set(['false', '0'])
    stripped = str(value).lower().strip()
    if stripped in truevals:
        return True
    if stripped in falsevals:
        return False
    
    logging.error("Invalid boolean value '%s'", value)
    sys.exit(1)

def parseint(value):
    try:
        return int(value)
    except:
        logging.error("Invalid integer value '%s'", value)
        sys.exit(1)

def parselist(value):
    return filter(bool, value.split(','))

parser.add_option('-m', '--mesos-url', dest='mesosurl', help='Mesos master or slave HTTP endpoint to check, e.g. "http://localhost:5050/"',
    default=os.environ.get('MESOS_URL', ''))
parser.add_option('-d', '--statsd-url', dest='statsdurl', help='StatsD url to forward metrics to, e.g. "statsd://localhost:8125"',
    default=os.environ.get('STATSD_URL', ''))

parser.add_option('-p', '--metrics-prefix', dest='prefix', help='Key prefix for metrics [default: %default]',
    default=os.environ.get('METRICS_PREFIX', 'mesos'))

parser.add_option('-i', '--refresh-interval', dest='interval', help='Metrics update interval [default: %default]',
    type="int", default=parseint(os.environ.get('REFRESH_INTERVAL', '60')))

parser.add_option('-v', '--verbose', dest='verbose', help='Increase logging verbosity',
    action="store_true", default=parsebool(os.environ.get('VERBOSE', False)))

(options, args) = parser.parse_args()

if options.verbose:
    logging.getLogger().setLevel(logging.DEBUG)
else:
    logging.getLogger().setLevel(logging.INFO)

if not options.mesosurl:
    parser.print_help()
    sys.exit(1)

class StatsD(object):
    def __init__(self, url):
        parsedurl = urlparse.urlparse(url)
        self._dest = (parsedurl.hostname or 'localhost', parsedurl.port or 8125)
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def gauge(self, key, value):
        self._send(key, value, 'g')

    def _send(self, key, value, mtype):
        self._socket.sendto('%s:%s|%s' % (key.replace('/', '.'), value, mtype), self._dest)

def forward(backend, key, value):
    if isinstance(value, dict):
        for key2, value2 in value.iteritems():
            forward(backend, key + '.' + key2, value2)
    else:
        backend.gauge(key, value)

url = options.mesosurl + '/metrics/snapshot'
mesos = urllib2.Request(url)
backend = StatsD(options.statsdurl)

while True:
    try:
        response = urllib2.urlopen(mesos)
        data = response.read()
        metrics = json.loads(data)
        forward(backend, options.prefix, metrics)
    except (urllib2.URLError, urllib2.HTTPError), e:
        logging.exception("Failed to fetch metrics from '%s': %s", url, e.message)

    time.sleep(options.interval)
