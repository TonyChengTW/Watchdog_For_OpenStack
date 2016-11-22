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
from oslo_log import log as logging
from oslo_service import periodic_task
from oslo_utils import importutils
import stevedore

from watchdog.controller import configuration as config
from watchdog.i18n import _LE
from watchdog import manager

LOG = logging.getLogger(__name__)

monitor_manager_opts = [
    cfg.ListOpt('monitor_servers',
                default=['nova-compute',
                         'nova-consoleauth',
                         'nova-api',
                         'nova-scheduler',
                         'nova-conductor',
                         'nova-novncproxy',
                         'ceilometer-api',
                         'ceilometer-collector',
                         'ceilometer-notification',
                         'ceilometer-compute',
                         'ceilometer-central',
                         'keystone',
                         'heat-api',
                         'heat-engine',
                         'cinder-api',
                         'cinder-volume',
                         'cinder-scheduler',
                         'cinder-backup',
                         'glance-api',
                         'glance-registry',
                         'neutron-server',
                         'neutron-openvswitch-agent',
                         'neutron-l3-agent',
                         'neutron-vpn-agent',
                         'neutron-dhcp-agent',
                         'neutron-metadata-agent',
                         'openvswitch',
                         'rabbitmq',
                         'keepalived',
                         'keepalived-drs',
                         'keepalived-vmha',
                         'haproxy',
                         'memcached',
                         'mongodb',
                         'mariadb',
                         'zabbix-agent'],
                help='Servers to be monitored'),
    cfg.ListOpt('disable_monitor_servers',
                default=[],
                help='Disable servers to be monitored'),
]

CONF = cfg.CONF
CONF.register_opts(monitor_manager_opts)
CONF.import_opt('monitor_task_period', 'watchdog.service', group='monitor')


class ControllerManager(manager.Manager):
    """This is controller to monitor all services."""

    def __init__(self, monitor_servers=None, binary='watchdog',
                 *args, **kwargs):
        super(ControllerManager, self).__init__(binary, *args, **kwargs)
        self.WATCHDOG_SERVICE_NAMESPACE = 'watchdog.monitor.servers'
        self.driver_path = 'watchdog.worker.driver.MonitorDriver'
        self.configuration = config.Configuration(monitor_manager_opts)
        self.monitor_objects = []

        if not monitor_servers:
            monitor_servers = self.configuration.monitor_servers

        disable_monitor_servers = self.configuration.disable_monitor_servers
        monitor_servers = [server for server in monitor_servers
                           if server not in disable_monitor_servers]

        self.monitor_objects = stevedore.NamedExtensionManager(
            namespace=self.WATCHDOG_SERVICE_NAMESPACE,
            names=monitor_servers,
            invoke_on_load=True,
            name_order=True)

        LOG.debug("Filtered monitored services are %s",
                  self.monitor_objects.names())

        self.monitor_driver = importutils.import_object(self.driver_path,
                                                        self.monitor_objects,
                                                        conf=CONF)

    @periodic_task.periodic_task(spacing=CONF.monitor.monitor_task_period)
    def _start_monitor_server(self, context=None):
        try:
            self.monitor_driver.monitor_server()
        except Exception as e:
            LOG.error(_LE("monitor server failed, %s."), e)

    def run_hang_periodic_tasks(self):
        try:
            self.monitor_driver.hang_detect()
        except Exception as e:
            LOG.error(_LE("Driver %s monitor server failed."), e)
