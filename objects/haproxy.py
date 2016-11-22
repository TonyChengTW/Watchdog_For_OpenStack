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

from oslo_log import log as logging
from watchdog.objects import monitor_base

LOG = logging.getLogger(__name__)


class ProcessTimeout(Exception):
    pass


class Haproxy(monitor_base.MonitorBase):

    def __init__(self):
        super(Haproxy, self).__init__()
        self.name = 'haproxy'
        self.description = "Haproxy service"
        self.service_name = 'haproxy'

    def is_alive(self):
        result = self.check_all()
        if result[0] == 0:
            return True

        return False

    def is_zombie(self):
        return False

    def check_all(self):
        checks = [
            'check_service',
            'check_process'
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

    def check_service(self):
        cmd = "systemctl is-active %s.service" % (self.service_name)
        result, stdout, stderr = self.run_cmd(cmd)
        if stdout.strip() != 'active':
            result = 1
        return result

    def check_process(self):
        cmd = "ps -ef | grep %s | grep -vq grep" % (self.service_name)
        result, stdout, stderr = self.run_cmd(cmd)
        return result
