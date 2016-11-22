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

CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class NovaCompute(monitor_base.MonitorBase):

    def __init__(self):
        super(NovaCompute, self).__init__()
        self.name = "nova-compute"
        self.description = "Nova compute service"

    def is_zombie(self):
        if not self.is_registered():
            return False

        config_dir = CONF.hang_detect_file_path
        hearbeat_file = config_dir + "/%s.heartbeat" % self.name
        if not os.path.isfile(hearbeat_file):
            LOG.debug("can't find heartbeat file for service %s", self.name)
            return True
        else:
            os.remove(hearbeat_file)
        return False


class NovaConsoleAuth(NovaCompute):

    def __init__(self):
        super(NovaCompute, self).__init__()
        self.name = "nova-consoleauth"
        self.description = "Nova consoleauth service"


class NovaApi(monitor_base.MonitorBase):

    def __init__(self):
        super(NovaApi, self).__init__()
        self.name = "nova-api"
        self.description = "Nova API service"


class NovaScheduler(monitor_base.MonitorBase):

    def __init__(self):
        super(NovaScheduler, self).__init__()
        self.name = "nova-scheduler"
        self.description = "Nova Scheduler service"


class NovaConductor(monitor_base.MonitorBase):

    def __init__(self):
        super(NovaConductor, self).__init__()
        self.name = "nova-conductor"
        self.description = "Nova Conductor service"


class NovaNovncproxy(monitor_base.MonitorBase):

    def __init__(self):
        super(NovaNovncproxy, self).__init__()
        self.name = "nova-novncproxy"
        self.description = "Nova nova-novncproxy service for vnc console"
