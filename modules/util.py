#
# Copyright 2016 BMC Software, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import datetime
import json
import sys
import socket
import os

plugin_params = None
metrics = None
counters = None


def parse_params():
    '''
    Parses and returns the contents of the plugin's "param.json" file.
    '''
    global plugin_params
    param = os.getenv('TSP_PLUGIN_PARAMS')
    if param:
         plugin_params = json.loads(param)
    else:        
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


def unix_time(dt):
    epoch = datetime.datetime.utcfromtimestamp(0)
    delta = dt - epoch
    return delta.days * 86400 + delta.seconds + delta.microseconds // 1e6


def unix_time_millis(dt):
    return int(unix_time(dt) * 1000)


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
    tags = tags or ''
    event = {'data': '_bevent:{0}|m:{1}|t:{2}|tags:{3}'.format(title, message, type, tags)}

    payload = {
        "method": "event",
        "params": event,
        "jsonrpc": "2.0",
        "id": 1
    }
    netcat("localhost", 9192, json.dumps(payload))


def sendMeasurement(name, value, source, timestamp='', app_id=None, source_type=None, parent_source=None,
                    parent_type=None):
    data_str = '_bmetric:{0}|v:{1}|s:{2}'.format(name, value, source)

    if timestamp is not '':
        data_str = data_str + '|t:{0}'.format(timestamp)

    property_dict = {}
    if app_id is not None and app_id is not "":
        property_dict['app_id'] = app_id

    if source_type is not None:
        property_dict['source_type'] = source_type

    if parent_source is not None:
        property_dict['parent_source'] = parent_source

    if parent_type is not None:
        property_dict['parent_type'] = parent_type

    properties_str = ",".join(["=".join([key, str(val)]) for key, val in property_dict.items()])

    if properties_str is not "":
        data_str = data_str + '|properties:{0}'.format(properties_str)

    data = {'data': data_str}
    payload = {
        "method": "metric",
        "params": data,
        "jsonrpc": "2.0",
        "id": 1
    }
    netcat("localhost", 9192, json.dumps(payload))
