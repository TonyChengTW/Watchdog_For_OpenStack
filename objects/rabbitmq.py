#!/usr/bin/env python
# Copyright 2016 Fiberhome Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import base64
import json
import signal
import subprocess
import traceback
import urllib2

from oslo_config import cfg
from oslo_log import log as logging
from watchdog.objects import monitor_base

LOG = logging.getLogger(__name__)

rabbitmq_opts = [
    cfg.StrOpt('host', default='127.0.0.1',
               help='The rabbitmq bind address'),
    cfg.IntOpt('port', default=5672,
               help='The rabbitmq broker port where listen on'),
    cfg.IntOpt('mgr_port', default=15672,
               help='The rabbitmq management port where listen on'),
    cfg.IntOpt('cluster_port', default=25672,
               help='The rabbitmq cluster port where listen on'),
    cfg.StrOpt('user', default='guest',
               help='The rabbitmq user of login'),
    cfg.StrOpt('password', default='guest',
               help='The rabbitmq password of login'),
]

CONF = cfg.CONF
CONF.register_opts(rabbitmq_opts, group='rabbitmq')


class ProcessTimeout(Exception):
    pass


class Rabbitmq(monitor_base.MonitorBase):

    def __init__(self):
        super(Rabbitmq, self).__init__()
        self.name = 'rabbitmq-server'
        self.description = "Rabbitmq service"
        self.service_name = 'rabbitmq'

        self.host = CONF.rabbitmq.host
        self.port = CONF.rabbitmq.port
        self.mgr_port = CONF.rabbitmq.mgr_port
        self.cluster_port = CONF.rabbitmq.cluster_port
        self.epmd_port = '4369'
        self.user = CONF.rabbitmq.user
        self.password = CONF.rabbitmq.password

    def is_alive(self):
        result = self.check_all()
        if result[0] == 0:
            return True

        return False

    def is_zombie(self):
        url = 'http://%s:%s/api/overview' % (self.host, self.mgr_port)

        try:
            self.run_url(url)
        except Exception:
            LOG.error(traceback.format_exc())
            return True

        return False

    def check_all(self):
        cmd_list = [
            {'handler': 'epmd_socket_status',
             'success': ['rabbitmq_cluster success',
                         'The epmd socket checking is success'],
             'failure': ['rabbitmq_cluster failure',
                         'The epmd socket checking is failure']},
            {'handler': 'beam_socket_status',
             'success': ['rabbitmq_cluster success',
                         'The beam socket checking is success'],
             'failure': ['rabbitmq_cluster failure',
                         'The beam socket checking is failure']},
            {'handler': 'epmd_process_status',
             'success': ['rabbitmq_cluster success',
                         'The epmd process checking is success'],
             'failure': ['rabbitmq_cluster failure',
                         'The epmd process checking is failure']},
            {'handler': 'beam_process_status',
             'success': ['rabbitmq_cluster success',
                         'The beam process checking is success'],
             'failure': ['rabbitmq_cluster failure',
                         'The beam process checking is failure']},
        ]

        status_info = ()
        for cmd in cmd_list:
            func = cmd['handler']
            result = getattr(self, func).__call__()
            if result == 0:
                LOG.info('Checking - %s:success', func)
                status_info = (result, cmd['success'][0], cmd['success'][1])
            else:
                LOG.info('Checking - %s:failure', func)
                status_info = (result, cmd['failure'][0], cmd['failure'][1])
                break
        return status_info

    def run_cmd(self, cmd, timeout=90):
        LOG.info('run_cmd start - cmd:[%s] t:%s', cmd, timeout)

        def timeout_handler(signum, frame):
            raise ProcessTimeout

        stdout = ''
        stderr = ''
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(timeout)
        proc = subprocess.Popen(cmd, shell=True,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            stdout, stderr = proc.communicate()
            signal.alarm(0)
        except ProcessTimeout:
            LOG.error(traceback.format_exc())
            proc.kill()
        returncode = proc.wait()
        LOG.info('run_cmd end - code:%s out:%s err:%s',
                 returncode, stdout, stderr)
        return (returncode, stdout, stderr)

    def run_url(self, url, data=[], username=None, password=None):
        if username is None:
            username = self.user

        if password is None:
            password = self.password

        header = {"Content-Type": "application/json"}
        data = json.dumps(data)
        request = urllib2.Request(url, data)
        request = urllib2.Request(url)
        for key in header:
            request.add_header(key, header[key])

        base64string = base64.b64encode('%s:%s' % (username, password))
        request.add_header("Authorization", "Basic %s" % base64string)

        res = urllib2.urlopen(request, timeout=10)
        if res.code != 200:
            raise Exception("ERROR: HTTP-status:%s" % (res.code))

        return json.loads(res.read())

    def epmd_socket_status(self):
        cmd = "netstat -nlt | grep -q :%s" % self.epmd_port
        result, stdout, stderr = self.run_cmd(cmd)
        return result

    def beam_socket_status(self):
        cmd = "netstat -nlt | grep -q :%s" % self.port
        result, stdout, stderr = self.run_cmd(cmd)
        return result

    def epmd_process_status(self):
        cmd = "ps -ef | grep '/bin/epmd -daemon' | grep -vq grep"
        result, stdout, stderr = self.run_cmd(cmd)
        return result

    def beam_process_status(self):
        cmd = "ps -ef | grep '/bin/beam.smp' | grep -vq grep"
        result, stdout, stderr = self.run_cmd(cmd)
        return result

    def node_status(self):
        url = 'http://%s:%s/api/overview' % (self.host, self.mgr_port)
        url_result = []

        try:
            url_result = self.run_url(url)
        except Exception:
            LOG.error(traceback.format_exc())

        node_name = url_result['node']
        enable_ports = []
        for listen in url_result['listeners']:
            if listen['node'] == node_name:
                enable_ports.append(str(listen['port']))

        if self.port not in enable_ports:
            return 1
        if self.cluster_port not in enable_ports:
            return 1
        return 0

    def cluster_status(self):
        url = 'http://%s:%s/api/nodes' % (self.host, self.mgr_port)
        url_result = []
        try:
            url_result = self.run_url(url)
        except Exception:
            LOG.error(traceback.format_exc())
        node_num = len(url_result)
        running_num = 0
        for node in url_result:
            if node['running']:
                running_num += 1

        LOG.info('/api/nodes nodes:%d running:%d', node_num, running_num)
        if node_num != running_num:
            return 1
        return 0
