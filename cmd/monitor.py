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

"""Starter script for Watch Dog."""

import eventlet
import logging as python_logging
import os
from oslo_config import cfg
from oslo_log import log as logging
import sys
from watchdog import service
from watchdog import version

if os.name == 'nt':
    # eventlet monkey patching the os module causes subprocess.Popen to fail
    # on Windows when using pipes due to missing non-blocking IO support.
    eventlet.monkey_patch(os=False)
else:
    eventlet.monkey_patch()

monitor_default_opts = [
    cfg.StrOpt('log_config_append',
               default='/etc/watchdog/logging.conf',
               help='Watchdog logging conf file.'),
]

CONF = cfg.CONF
CONF.register_opts(monitor_default_opts)
LOG = logging.getLogger(__name__)


def main():
    CONF(sys.argv[1:], project='watchdog',
         version=version.version_string())
    logging.setup(CONF, "watchdog")
    python_logging.captureWarnings(True)
    server = service.Service.create(binary='watchdog')
    service.serve(server)
    LOG.info("WatchDog start successfully.")
    service.wait()
