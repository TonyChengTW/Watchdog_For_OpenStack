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


import signal
import subprocess
import traceback

from oslo_config import cfg
from oslo_log import log as logging
from watchdog.objects import monitor_base

LOG = logging.getLogger(__name__)

mariadb_opts = [
    cfg.StrOpt('host', default='127.0.0.1',
               help='The mariadb bind address'),
    cfg.IntOpt('port', default=3306,
               help='The mariadb port where listen on'),
    cfg.StrOpt('user', default='root',
               help='The mariadb user of login'),
    cfg.StrOpt('password', default='root',
               help='The mariadb password of login'),
]

CONF = cfg.CONF
CONF.register_opts(mariadb_opts, group='mariadb')


class ProcessTimeout(Exception):
    pass


class Mariadb(monitor_base.MonitorBase):

    def __init__(self):
        super(Mariadb, self).__init__()
        self.name = 'mariadb'
        self.description = "Mariadb service"
        self.service_name = 'mariadb'

        self.host = CONF.mariadb.host
        self.port = CONF.mariadb.port
        self.user = CONF.mariadb.user
        self.password = CONF.mariadb.password

    def is_alive(self):
        result = self.check_all()
        if result[0] == 0:
            return True

        return False

    def is_zombie(self):
        if self.check_node_ready() == 1:
            return True
        return False

    def check_all(self):
        cmd_list = [
            {'handler': 'socket_status',
             'success': ['mariadb success',
                         'The mariadb socket checking is success'],
             'failure': ['mariadb failure',
                         'The mariadb socket checking is failure']},
            {'handler': 'process_status',
             'success': ['mariadb success',
                         'The mariadb process checking is success'],
             'failure': ['mariadb failure',
                         'The mariadb process checking is failure']},
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

    def check_health(self):
        cmd_list = ['check_cluster_status',
                    'check_cluster_size',
                    'check_node_state',
                    'check_node_ready']

        for cmd in cmd_list:
            func = cmd['handler']
            result = getattr(self, func).__call__()
            if result == 1:
                return 1
        return 0

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
        cmd = "ps -ef | grep '/usr/libexec/mysqld' | grep -vq grep"
        result, stdout, stderr = self.run_cmd(cmd)
        return result

    def sql_status(self, status_name):
        cmd = "mysql -u%s -p%s -e \"SHOW STATUS LIKE '%s';\"" \
              % (self.user, self.password, status_name)
        cmd += "| grep '%s' | awk '{print $NF}'" % (status_name)
        result, stdout, stderr = self.run_cmd(cmd)
        if result == 0:
            return stdout
        return ''

    def check_cluster_status(self):
        output = self.sql_status('wsrep_cluster_status')
        if 'Primary' in output:
            return 0
        return 1

    def check_cluster_size(self):
        output = self.sql_status('wsrep_cluster_size')
        if '3' in output:
            return 0
        return 1

    def check_node_state(self):
        output = self.sql_status('wsrep_local_state_comment')
        if 'Synced' in output:
            return 0
        return 1

    def check_node_ready(self):
        output = self.sql_status('wsrep_ready')
        if 'ON' in output:
            return 0
        return 1
