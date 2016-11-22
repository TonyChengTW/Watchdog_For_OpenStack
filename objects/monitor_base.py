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
from watchdog import utils

monitor_default_opts = [
    cfg.StrOpt('hang_detect_file_path', default='/etc/watchdog/zombie/',
               help='Zombie detecting file path'),
]

CONF = cfg.CONF
CONF.register_opts(monitor_default_opts)
LOG = logging.getLogger(__name__)


class MonitorBase(object):
    """This is the base class for all services.

    If you want to monitor a newservice, you must inherit this calss and
    override some methods.
    """

    def __init__(self):
        self.name = "monitorbase"
        self.description = ""
        self.conf = CONF
        self.monitor_count = 0
        self.hang_count = 0

    def is_alive(self):
        """check the status of the monitored service.

        :return: True if the service is alive, otherwise False
        """

        status, output = utils.execute('systemctl', 'status', self.name)
        if not status:
            # result is zero
            return True
        else:
            return False

    def restart(self):
        """restart the monitored service

        :return: None
        """
        pids = utils.get_pids(self.name)
        if pids:
            pid_str = ' '.join(pids)
            LOG.debug("Kill pids [%s]", pid_str)
            utils.execute('kill', '-9', pid_str)

        utils.execute('systemctl ', 'restart', self.name)
        LOG.debug("Execute restart %s finish", self.name)

    def is_zombie(self):
        """Detect if the process is zombie.

        If the monitored service is alived, but it does not worked well, we
        consider it a zombie.

        If the monitored service support zombie check,
        please override this method.

        :return: True if the service is zombie, otherwise False
        """
        return False

    def is_registered(self):
        """check the service is registered in os system.

        :return:
        """
        status, output = utils.execute('systemctl',
                                       'list-unit-files',
                                       '|',
                                       'grep',
                                       '%s.service' % self.name)

        if not status:
            # Only the service is enabled by systemctl, we should
            # monitor it.

            # Remove the empty strings
            service_enable_list = [x for x in output.split(' ') if x != '']
            if 'enabled' in service_enable_list:
                return True
            else:
                LOG.debug("service %s is in [%s] state, skip",
                          self.name, service_enable_list[-1])
                return False
        else:
            LOG.debug("service %s is not registered, skip",
                      self.name)
            return False

    def __repr__(self):
        return "Monitor[%s]" % self.name
