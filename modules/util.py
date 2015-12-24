__author__ = 'goutham'

import datetime
import time
import json
import sys

plugin_params = None
metrics = None
counters = None


def parse_params():
    '''
    Parses and returns the contents of the plugin's "param.json" file.
    '''
    global plugin_params
    if not plugin_params:
        with open('param.json') as f:
            plugin_params = json.loads(f.read())
    return plugin_params


def parse_metrics():
    '''
    Parses and returns the contents of the plugin's "metrics.json" file.
    '''
    global metrics
    if not metrics:
        with open('metrics.json') as f:
            metrics = json.loads(f.read())
    return metrics


def parse_counters():
    '''
    Parses and returns the contents of the plugin's "metrics.json" file.
    '''
    global counters
    if not counters:
        with open('modules/counters.json') as f:
            counters = json.loads(f.read())
    return counters


def get_counter(metric_name=None):
    counter_name = None
    if metric_name:
        counters = parse_counters().get("counters")
        for counter in counters:
            if counter.get("metric", None) == metric_name:
                counter_name = counter.get("name")
                break
    return counter_name


def get_metric(counter_name=None):
    if counter_name:
        counters = parse_counters().get("counters")
        for counter in counters:
            if counter.get("name", None) == counter_name:
                counter_name = counter.get("metric")
                break
    return counter_name


def sleep_interval():
    '''
    Sleeps for the plugin's poll interval, as configured in the plugin's parameters.
    '''
    params = parse_params()
    time.sleep(float(params[0].get("pollInterval", 1000) / 1000))


def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.days * 86400 + delta.seconds + delta.microseconds / 1e6


def unix_time_millis(dt):
    return unix_time(dt) * 1000.0


def report_metric(name, value, source=None, timestamp=None):
    '''
    Reports a metric to the Pulse Meter.
    @param name Metric name, as defined in the plugin's plugin.json file.
    @param value Metric value, should be a number.
    @param source Metric source.  Defaults to the machine's hostname.
    @param timestamp Timestamp of the metric as a Python datetime object.  Defaults to none
        (Pulse uses the current time in that case).
    '''
    source = source
    #if timestamp:
    #    timestamp = unix_time_millis(timestamp)
    out = "%s %s %s%s" % (name, value, source, (' %s' % timestamp) if timestamp else '')
    print(out)


def report_event(type, message, tags):
    tags = tags or ''
    print('_bevent:%s|t:%s|tags:%s' % message, type, tags)

def sendEvent(self,title,message,type,timestamp):
    sys.stdout.write('_bevent:{0}|m:{1}|t:{2}\n'.format(title,message,type,timestamp).decode('utf-8'))
    sys.stdout.flush()


def sendMeasurement(self,metric,value,source,timestamp):
    """ Sends measurements to standard out to be read by plugin manager"""
    sys.stdout.write('{0} {1} {2} {3}\n'.format(metric,value,source,timestamp).decode('utf-8'))
    sys.stdout.flush()
