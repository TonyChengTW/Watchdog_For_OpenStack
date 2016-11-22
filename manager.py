# Copyright 2016 Fiberhome Corp
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""Base Manager class.

This module provides Manager, a base class for managers.

"""


from oslo_config import cfg
from oslo_log import log as logging
from oslo_service import periodic_task

from watchdog import version

from eventlet import greenpool


CONF = cfg.CONF
LOG = logging.getLogger(__name__)


class PeriodicTasks(periodic_task.PeriodicTasks):
    def __init__(self):
        super(PeriodicTasks, self).__init__(CONF)


class Manager(PeriodicTasks):

    def __init__(self, binary='undefined'):
        self.binary = binary
        self._tp = greenpool.GreenPool()
        super(Manager, self).__init__()

    def periodic_tasks(self, context=None, raise_on_error=False):
        """Tasks to be run at a periodic interval."""
        return self.run_periodic_tasks(context, raise_on_error=raise_on_error)

    def hang_periodic_tasks(self, raise_on_error=False):
        """Tasks to be run at a periodic interval."""
        return self.run_hang_periodic_tasks()

    def init_host(self):
        """Handle initialization if this is a standalone service.

        A hook point for services to execute tasks before the services are made
        available (i.e. showing up on RPC and starting to accept RPC calls) to
        other components.  Child classes should override this method.

        """
        pass

    def service_version(self):
        return version.version_string()

    def service_config(self):
        config = {}
        for key in CONF:
            config[key] = CONF.get(key, None)
        return config

    def is_working(self):
        """Method indicating if service is working correctly.

        This method is supposed to be overriden by subclasses and return if
        manager is working correctly.
        """
        return True

    def _add_to_threadpool(self, func, *args, **kwargs):
        self._tp.spawn_n(func, *args, **kwargs)
