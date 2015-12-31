__author__ = 'goutham'

import datetime
import time
import json
import sys
import socket

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
    time.sleep(float(params['items'][0].get("pollInterval", 1000) / 1000))


def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.days * 86400 + delta.seconds + delta.microseconds / 1e6


def unix_time_millis(dt):
    return unix_time(dt) * 1000.0


def netcat(hostname, port, content):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((hostname, port))
    if sys.version_info >= (3, 0, 0):
        s.sendall(bytes(content, 'UTF-8'))
    else:
        s.sendall(content)
    s.shutdown(socket.SHUT_WR)
    # print "Connection closed."
    s.close()


def sendEvent(title, message, type, tags=None):
    # sys.stdout.write('_bevent:{0}|m:{1}|t:{2}\n'.format(title,message,type,timestamp))
    # sys.stdout.flush()
    tags = tags or ''
    event = {'data': '_bevent:{0}|m:{1}|t:{2}|tags:{3}'.format(title,message,type,tags)}
    #event = {'data':'_bevent:%s|m:%s|t:%s|tags:%s' % title, message, type, tags)}
 
    payload = {
        "method": "event",
        "params": event,
	"jsonrpc":"2.0",
	"id":1
    }
    netcat("localhost",9192,json.dumps(payload))


def sendMeasurement(name, value, source, timestamp='', parent_source=None, parent_type=None):
    """ Sends measurements to standard out to be read by plugin manager"""
    data_str = '_bmetric:{0}|v:{1}|s:{2}'.format(name,value,source)
    timestamp = '' 
    if timestamp is not '':
	data_str = data_str + '|t:{0}'.format(timestamp)
    
    if parent_source is not '':
	data_str = data_str + '|properties:parent_source={0},parent_type={1}'.format(parent_source, parent_type)

    data = {'data': data_str} 
    payload = {
        "method": "metric",
        "params": data,
	"jsonrpc":"2.0",
	"id":1
    }
    netcat("localhost",9192,json.dumps(payload))

