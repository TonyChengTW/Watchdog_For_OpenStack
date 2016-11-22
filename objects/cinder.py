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

import os

from oslo_config import cfg
from oslo_log import log as logging

from watchdog.objects import monitor_base
from watchdog import utils

LOG = logging.getLogger(__name__)

cinder_monitor_opts = [
    cfg.StrOpt('cinder_conf_path', default='/etc/cinder/cinder.conf',
               help='Cinder configuration file path.'),
]

CONF = cfg.CONF
CONF.register_opts(cinder_monitor_opts, group='cinder')


class CinderApi(monitor_base.MonitorBase):
    """Monitor cinder-api service"""

    def __init__(self):
        super(CinderApi, self).__init__()
        self.name = 'cinder-api'


class CinderVolume(monitor_base.MonitorBase):
    """Monitor cinder-volume server"""

    def __init__(self):
        super(CinderVolume, self).__init__()
        self.name = 'cinder-volume'

    def is_alive(self):
        """check the status of the monitored service.

        :return: True if the service is alive, otherwise False
        """
        if not self.is_registered():
            return True

        cmd = ('cat ' + CONF.cinder.cinder_conf_path +
               ' | grep ^enabled_backends')
        status, output = utils.execute(cmd)
        backends_num = len(output.split('=')[1].split(','))
        cmd = ('ps -e | grep ' + self.name + ' | wc -l')
        status, output = utils.execute(cmd)
        result = int(output.replace('\n', ''))
        LOG.debug('compare result %(result)s and backend_num %(backend)s',
                  {'result': result, 'backend': backends_num})
        if result != (backends_num + 1):
            return False
        return True

    def is_zombie(self):
        config_dir = self.conf.hang_detect_file_path

        cmd = ('cat ' + CONF.cinder.cinder_conf_path +
               ' | grep ^enabled_backends')
        status, output = utils.execute(cmd)
        backends = output.split('=')[1].split(',')

        is_zombie = False
        for backend in backends:
            hearbeat_file = config_dir + "%s.%s.heartbeat" \
                % (self.name, backend.replace(' ', ''))
            if not os.path.isfile(hearbeat_file):
                LOG.warning('Watchdog cannot find "%s".' % hearbeat_file)
                is_zombie = True
            else:
                LOG.info('Watchdog finds "%s", start to remove it.'
                         % hearbeat_file)
                os.remove(hearbeat_file)
        return is_zombie


class CinderScheduler(monitor_base.MonitorBase):
    """Monitor cinder-scheduler service"""

    def __init__(self):
        super(CinderScheduler, self).__init__()
        self.name = 'cinder-scheduler'

    def is_zombie(self):
        config_dir = self.conf.hang_detect_file_path
        hearbeat_file = config_dir + "%s.heartbeat" % self.name
        if not os.path.isfile(hearbeat_file):
            LOG.warning('Watchdog cannot find "%s".' % hearbeat_file)
            return True
        else:
            LOG.info('Watchdog finds "%s", start to remove it.'
                     % hearbeat_file)
            os.remove(hearbeat_file)
        return False


class CinderBackup(monitor_base.MonitorBase):
    """Monitor cinder-backup service"""

    def __init__(self):
        super(CinderBackup, self).__init__()
        self.name = 'cinder-backup'

    def is_zombie(self):
        config_dir = self.conf.hang_detect_file_path
        hearbeat_file = config_dir + "%s.heartbeat" % self.name
        if not os.path.isfile(hearbeat_file):
            LOG.warning('Watchdog cannot find "%s".' % hearbeat_file)
            return True
        else:
            LOG.info('Watchdog finds "%s", start to remove it.'
                     % hearbeat_file)
            os.remove(hearbeat_file)
        return False
