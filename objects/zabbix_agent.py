#!/usr/bin/env python
# Copyright 2016 Fiberhome Corp.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
# #      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.


import signal
import subprocess
import traceback

from oslo_config import cfg
from oslo_log import log as logging
from watchdog.objects import monitor_base

LOG = logging.getLogger(__name__)

zabbix_opts = [
    cfg.StrOpt('host', default='127.0.0.1',
               help='The zabbix-agent bind address'),
    cfg.IntOpt('port', default=10050,
               help='The zabbix-agent port where listen on'),
]

CONF = cfg.CONF
CONF.register_opts(zabbix_opts, group='zabbix_agent')


class ProcessTimeout(Exception):
    pass


class ZabbixAgent(monitor_base.MonitorBase):

    def __init__(self):
        super(ZabbixAgent, self).__init__()
        self.name = 'zabbix-agent'
        self.description = "Zabbix agent service"
        self.service_name = 'zabbix_agent'

        self.host = CONF.zabbix_agent.host
        self.port = CONF.zabbix_agent.port

    def is_alive(self):
        result = self.check_all()
        if result[0] == 0:
            return True

        return False

    def is_zombie(self):
        return False

    def check_all(self):
        cmd_list = [
            {'handler': 'socket_status',
             'success': ['zabbix_agent success',
                         'The socket checking is success'],
             'failure': ['zabbix_agent failure',
                         'The socket checking is failure']},
            {'handler': 'process_status',
             'success': ['zabbix_agent success',
                         'The process checking is success'],
             'failure': ['zabbix_agent failure',
                         'The process checking is failure']},
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

    def socket_status(self):
        cmd = "netstat -nlt | grep -q :%s" % self.port
        result, stdout, stderr = self.run_cmd(cmd)
        return result

    def process_status(self):
        cmd = "ps -ef | grep /usr/sbin/zabbix_agentd | grep -vq grep"
        result, stdout, stderr = self.run_cmd(cmd)
        return result
