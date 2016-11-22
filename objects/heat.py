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


from oslo_config import cfg
from watchdog.objects import monitor_base

CONF = cfg.CONF


class HeatApi(monitor_base.MonitorBase):

    def __init__(self):
        super(HeatApi, self).__init__()
        self.name = "heat-api"
        self.description = "Heat API service"


class HeatEngine(monitor_base.MonitorBase):

    def __init__(self):
        super(HeatEngine, self).__init__()
        self.name = "heat-engine"
        self.description = "Heat engine service"
