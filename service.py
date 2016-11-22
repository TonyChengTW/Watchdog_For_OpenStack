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

import inspect
import os
import random

from oslo_config import cfg
from oslo_log import log as logging
from oslo_service import loopingcall
from oslo_service import service
from oslo_utils import importutils

from watchdog.i18n import _, _LI
from watchdog import version

LOG = logging.getLogger(__name__)

monitor_task_opts = [
    cfg.BoolOpt('is_monitor', default=True, help='If opening monitor task'),
    cfg.StrOpt('watchdog_manager',
               default='watchdog.controller.manager.ControllerManager',
               help='watchdog controller manager class.'),
    cfg.IntOpt('monitor_task_period', default=10,
               help='Interval, in seconds, between running monitor tasks.'),
    cfg.IntOpt('periodic_fuzzy_delay',
               default=30,
               help='Range, in seconds, to randomly delay when starting the'
                    ' periodic task scheduler to reduce stampeding.'
                    ' (Disable by setting to 0)'),
    cfg.IntOpt('monitor_retry_times', default=3,
               help='Monitor retry times.'),
]

hang_task_opts = [
    cfg.BoolOpt('is_detect', default=True, help='If opening hang task'),
    cfg.IntOpt('hang_task_period', default=60,
               help='Interval, in seconds, between running monitor tasks.'),
    cfg.IntOpt('hang_periodic_fuzzy_delay',
               default=30,
               help='Range, in seconds, to randomly delay when starting the'
                    ' periodic task scheduler to reduce stampeding.'
                    ' (Disable by setting to 0)'),
    cfg.IntOpt('detect_retry_times', default=3,
               help='Hang detect retry times.'),

]

CONF = cfg.CONF
CONF.register_opts(monitor_task_opts, group='monitor')
CONF.register_opts(hang_task_opts, group='hang_detect')


class Service(service.Service):
    """Service objects for binaries running on hosts.

    A service takes a manager and enables rpc by listening to queues based
    on topic. It also periodically runs tasks on the manager and reports
    it state to the database services table.
    """

    def __init__(self, binary, manager=None, periodic_interval=None,
                 periodic_fuzzy_delay=None, hang_periodic_interval=None,
                 hang_periodic_fuzzy_delay=None, is_monitor=True,
                 is_detect=True, *args, **kwargs):
        super(Service, self).__init__()

        self.binary = binary
        self.manager_class_name = manager
        manager_class = importutils.import_class(self.manager_class_name)
        self.manager = manager_class(binary=self.binary,
                                     *args, **kwargs)
        self.is_monitor = is_monitor
        self.is_detect = is_detect
        self.periodic_interval = periodic_interval
        self.periodic_fuzzy_delay = periodic_fuzzy_delay
        self.hang_periodic_interval = hang_periodic_interval
        self.hang_periodic_fuzzy_delay = hang_periodic_fuzzy_delay
        self.saved_args, self.saved_kwargs = args, kwargs
        self.timers = []

    def start(self):
        version_string = version.version_string()
        LOG.info(_LI('Starting watchdog (version %(version_string)s)'),
                 {'version_string': version_string})
        self.manager.init_host()

        if self.periodic_interval and self.is_monitor:
            if self.periodic_fuzzy_delay:
                initial_delay = random.randint(0, self.periodic_fuzzy_delay)
            else:
                initial_delay = None

            periodic = loopingcall.FixedIntervalLoopingCall(
                self.periodic_tasks)
            periodic.start(interval=self.periodic_interval,
                           initial_delay=initial_delay)
            self.timers.append(periodic)

        if self.hang_periodic_interval and self.is_detect:
            if self.hang_periodic_fuzzy_delay:
                initial_delay = random.randint(0,
                                               self.hang_periodic_fuzzy_delay)
            else:
                initial_delay = None

            periodic = loopingcall.FixedIntervalLoopingCall(
                self.hang_periodic_tasks)
            periodic.start(interval=self.hang_periodic_interval,
                           initial_delay=initial_delay)
            self.timers.append(periodic)

    def __getattr__(self, key):
        manager = self.__dict__.get('manager', None)
        return getattr(manager, key)

    @classmethod
    def create(cls, binary=None, manager=None, periodic_interval=None,
               periodic_fuzzy_delay=None, hang_periodic_interval=None,
               hang_periodic_fuzzy_delay=None):
        """Instantiates class and passes back application objects.

        :param binary: defaults to basename of executable
        :param manager: defaults to CONF.<topic>_manager
        :param periodic_interval: defaults to
                CONF.monitor.monitor_task_period
        :param periodic_fuzzy_delay: defaults to
                CONF.monitor.periodic_fuzzy_delay
        :param hang_periodic_interval: defaults to
                CONF.hang_detect.hang_task_period
        :param hang_periodic_fuzzy_delay: defaults to
                CONF.hang_periodic_fuzzy_delay

        """
        if not binary:
            binary = os.path.basename(inspect.stack()[-1][1])
        if not manager:
            manager = CONF.monitor.watchdog_manager
        if periodic_interval is None:
            periodic_interval = CONF.monitor.monitor_task_period
        if periodic_fuzzy_delay is None:
            periodic_fuzzy_delay = CONF.monitor.periodic_fuzzy_delay

        if hang_periodic_interval is None:
            hang_periodic_interval = CONF.hang_detect.hang_task_period
        if hang_periodic_fuzzy_delay is None:
            temp = CONF.hang_detect.hang_periodic_fuzzy_delay
            hang_periodic_fuzzy_delay = temp

        is_monitor = CONF.monitor.is_monitor
        is_detect = CONF.hang_detect.is_detect
        service_obj = cls(binary, manager,
                          periodic_interval=periodic_interval,
                          periodic_fuzzy_delay=periodic_fuzzy_delay,
                          hang_periodic_interval=hang_periodic_interval,
                          hang_periodic_fuzzy_delay=hang_periodic_fuzzy_delay,
                          is_monitor=is_monitor,
                          is_detect=is_detect)

        return service_obj

    def stop(self):

        self.timers_skip = []
        for x in self.timers:
            try:
                x.stop()
            except Exception:
                self.timers_skip.append(x)
        super(Service, self).stop(graceful=True)

    def wait(self):
        skip = getattr(self, 'timers_skip', [])
        for x in self.timers:
            if x not in skip:
                try:
                    x.wait()
                except Exception:
                    pass
        super(Service, self).wait()

    def periodic_tasks(self, raise_on_error=False):
        """Tasks to be run at a periodic interval."""
        self.manager.periodic_tasks(raise_on_error=raise_on_error)

    def hang_periodic_tasks(self, raise_on_error=False):
        """Tasks to be run at a periodic interval."""
        self.manager.hang_periodic_tasks(raise_on_error=raise_on_error)

    def reset(self):
        super(Service, self).reset()


def process_launcher():
    return service.ProcessLauncher(CONF)


# NOTE(vish): the global launcher is to maintain the existing
#             functionality of calling service.serve +
#             service.wait
_launcher = None


def serve(server, workers=None):
    global _launcher
    if _launcher:
        raise RuntimeError(_('serve() can only be called once'))

    _launcher = service.launch(CONF, server, workers=workers)


def wait():
    LOG.debug('Full set of CONF:')
    for flag in CONF:
        flag_get = CONF.get(flag, None)
        LOG.debug('%(flag)s : %(flag_get)s',
                  {'flag': flag, 'flag_get': flag_get})
    try:
        _launcher.wait()
    except KeyboardInterrupt:
        _launcher.stop()


class Launcher(object):
    def __init__(self):
        self.launch_service = serve
        self.wait = wait


def get_launcher():
    # Note(lpetrut): ProcessLauncher uses green pipes which fail on Windows
    # due to missing support of non-blocking I/O pipes. For this reason, the
    # service must be spawned differently on Windows, using the ServiceLauncher
    # class instead.
    if os.name == 'nt':
        return Launcher()
    else:
        return process_launcher()
