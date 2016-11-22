#!/usr/bin/env python
# Copyright 206 Fiberhome Corp.
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

LOG = logging.getLogger(__name__)
CONF = cfg.CONF


class NeutronAgentBase(monitor_base.MonitorBase):

    def __init__(self):
        super(NeutronAgentBase, self).__init__()
        self.alias = self.name = 'neutron agent base'

    def is_zombie(self):
        if not self.is_registered():
            return False

        config_dir = self.conf.hang_detect_file_path
        hearbeat_file = config_dir + "%s.heartbeat" % self.alias
        if not os.path.isfile(hearbeat_file):
            return True
        else:
            os.remove(hearbeat_file)
        return False


class NeutronVPNAgent(NeutronAgentBase):
    '''Monitor neutron-vpn-agent'''

    def __init__(self):
        super(NeutronVPNAgent, self).__init__()
        self.name = 'neutron-vpn-agent'
        self.alias = 'neutron-l3-agent'


class NeutronOpenvswitchAgent(NeutronAgentBase):
    '''Monitor neutron-openvswitch-agent'''

    def __init__(self):
        super(NeutronOpenvswitchAgent, self).__init__()
        self.alias = self.name = 'neutron-openvswitch-agent'


class NeutronDhcpAgent(NeutronAgentBase):
    '''Monitor neutron-dhcp-agent'''

    def __init__(self):
        super(NeutronDhcpAgent, self).__init__()
        self.alias = self.name = 'neutron-dhcp-agent'


class NeutronL3Agent(NeutronAgentBase):
    '''Monitor neutron-l3-agent'''

    def __init__(self):
        super(NeutronL3Agent, self).__init__()
        self.alias = self.name = 'neutron-l3-agent'


class NeutronMetadataAgent(monitor_base.MonitorBase):
    '''Monitor neutron-metadata-agent'''

    def __init__(self):
        super(NeutronMetadataAgent, self).__init__()
        self.alias = self.name = "neutron-metadata-agent"


class NeutronServer(monitor_base.MonitorBase):
    '''Monitor neutron-server'''

    def __init__(self):
        super(NeutronServer, self).__init__()
        self.alias = self.name = "neutron-server"


class NeutronOpenvswitch(monitor_base.MonitorBase):
    '''Monitor openvswitch daemon'''

    def __init__(self):
        super(NeutronOpenvswitch, self).__init__()
        self.alias = self.name = "openvswitch"
