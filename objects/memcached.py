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

memcached_opts = [
    cfg.StrOpt('host', default='127.0.0.1',
               help='The memcached bind address'),
    cfg.IntOpt('port', default=11211,
               help='The memcached port where listen on'),
]

CONF = cfg.CONF
CONF.register_opts(memcached_opts, group='memcached')


class ProcessTimeout(Exception):
    pass


class Memcached(monitor_base.MonitorBase):

    def __init__(self):
        super(Memcached, self).__init__()
        self.name = 'memcached'
        self.description = "Memcache service"
        self.service_name = 'memcached'

        self.host = CONF.memcached.host
        self.port = CONF.memcached.port

    def is_alive(self):
        result = self.check_all()
        if result[0] == 0:
            return True

        return False

    def is_zombie(self):
        if self.check_stats() == 0:
            return False

        return True

    def check_all(self):
        checks = [
            'check_listen_port',
            'check_service',
            'check_process',
            'check_stats'
        ]

        message = ()
        for chk in checks:
            chk_ret = getattr(self, chk)()
            if chk_ret == 1:
                message = (1,
                           '%s failure' % (self.service_name),
                           '%s failure' % (chk))
                break
            if chk_ret == -1:
                message = (-1,
                           '%s failure' % (self.service_name),
                           '%s script failure' % (chk))
                break
        if len(message) == 0:
            message = (0,
                       '%s success' % (self.service_name),
                       '%s checking success' % (self.service_name))
        return message

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

    def check_listen_port(self):
        cmd = "netstat -nlt | grep -q :%s" % self.port
        result, stdout, stderr = self.run_cmd(cmd)
        return result

    def check_process(self):
        cmd = "ps -ef | grep %s | grep -vq grep" % (self.service_name)
        result, stdout, stderr = self.run_cmd(cmd)
        return result

    def check_service(self):
        result = 1
        cmd = 'systemctl is-active %s.service' % (self.service_name)
        try:
            stdout = subprocess.check_output(cmd.split(' '))
            if stdout.strip() == 'active':
                result = 0
        except Exception:
            LOG.critical('check_service: got exception!')
            return -1
        if result == 0:
            LOG.info('check_service: success.')
        else:
            LOG.error('check_service: failure!')
        return result

    def check_stats(self):
        result = 1
        cmd1 = 'echo stats'
        cmd2 = 'nc %s %s' % (self.host, self.port)
        try:
            p1 = subprocess.Popen(cmd1.split(' '), stdout=subprocess.PIPE)
            p2 = subprocess.Popen(cmd2.split(' '),
                                  stdin=p1.stdout, stdout=subprocess.PIPE)
            p1.stdout.close()
            stdout = p2.communicate()[0]
            for i in stdout.split('\n'):
                if 'uptime' in i:
                    result = 0
                    break
        except Exception:
            LOG.critical('check_stats: got exception!')
            return -1
        if result == 0:
            LOG.info('check_stats: success.')
        else:
            LOG.error('check_stats: failure!')
        return result
