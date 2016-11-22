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


"""
    This script is for check the status of watchdog and ensure the high
    availability
"""

import os

from watchdog import utils

if __name__ == "__main__":
    config_dir = '/var/log/watchdog/'
    if not os.path.exists(config_dir):
        os.makedirs(config_dir)
    status, output = utils.execute(
        "ps -ef | grep -w 'python /usr/bin/watchdog' | grep -v grep")
    if status:
        utils.execute('python',
                      '/usr/bin/watchdog',
                      '--config-file',
                      '/etc/watchdog/watchdog.conf &', system=True)
