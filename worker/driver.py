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

import eventlet
from oslo_log import log as logging

from watchdog.i18n import _LE, _LI

LOG = logging.getLogger(__name__)


class MonitorDriver(object):
    """MonitorDriver.

    This driver will invoke every monitor object in conf to monitor
    if the server is alive and zombie.
    """

    def __init__(self, monitor_objects=None, conf=None):
        self.monitor_objects = monitor_objects
        self.conf = conf
        self.monitor_times = self.conf.monitor.monitor_retry_times
        self.hang_times = self.conf.hang_detect.detect_retry_times

    # Monitor server to see if it's alive now.
    def monitor_server(self):
        for monitor in self.monitor_objects:
            monitor_object = monitor.obj
            LOG.info(_LI("Begin to monitor %s"), monitor_object.name)
            try:
                is_reg = monitor_object.is_registered()
                if is_reg and (not monitor_object.is_alive()):
                    LOG.debug("process %(name)s is not alive, count=%(c)s",
                              {"name": monitor_object.name,
                               'c': monitor_object.monitor_count})
                    if (monitor_object.monitor_count >=
                            self.monitor_times):
                        LOG.info(_LI("%(object)s is not alive, restart it."),
                                 {'object': monitor_object.name})
                        monitor_object.restart()
                        monitor_object.monitor_count = 0
                    else:
                        monitor_object.monitor_count += 1
                else:
                    monitor_object.monitor_count = 0
            except Exception as e:
                LOG.error(_LE("monitor obj %(object)s has exception: %(e)s"),
                          {'object': monitor_object.name, 'e': e})

    def ensure_zombie_folder(self):
        config_dir = self.conf.hang_detect_file_path
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)

    # Monitor server to see if it's zombie now.
    def hang_detect(self):
        self.ensure_zombie_folder()
        for monitor in self.monitor_objects:
            monitor_object = monitor.obj
            LOG.info(_LI("Begin to hang detect %s"), monitor_object.name)
            try:
                if (monitor_object.is_registered() and
                        monitor_object.is_zombie()):
                    LOG.debug("zombie detected: %(name)s, count=%(c)s",
                              {"name": monitor_object.name,
                               'c': monitor_object.hang_count})
                    if monitor_object.hang_count >= self.hang_times:
                        LOG.info(_LI("%(object)s is zombie now, restart it."),
                                 {'object': monitor_object.name})
                        monitor_object.restart()
                        monitor_object.hang_count = 0
                    else:
                        monitor_object.hang_count += 1
                else:
                    monitor_object.hang_count = 0
                eventlet.sleep(0)
            except Exception as e:
                LOG.error(_LE("hang object %(object)s has exception: %(e)s"),
                          {'object': monitor_object.name, 'e': e})

    # Call api by sending request to see if it's alive or zombie now.
    def api_detect(self):
        pass
