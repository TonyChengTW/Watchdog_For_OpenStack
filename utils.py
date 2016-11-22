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


import commands
import os
import psutil
import re


def execute(*cmd, **kwargs):
    """Convenience wrapper around oslo's execute() method.

    :param cmd: the string of executed command
    :return: status is return code, and output is oriented-text result.
    """

    cmd = list(cmd)
    cmd = [str(c) for c in cmd]
    cmd = ' '.join(cmd)
    output = None
    os_cmd = kwargs.pop('system', False)
    if os_cmd:
        status = os.system(cmd)
    else:
        status, output = commands.getstatusoutput(cmd)

    return status, output


def get_pids(name):
    """Get the pid from process name

    :param name:
    :return: the pid list
    """
    pids = []
    if len(name) > 15:
        # only match the first 15 characters
        name = name[:15]

    pid_list = psutil.get_process_list()
    for pid in pid_list:
        pid = str(pid)
        f = re.compile(name, re.I)
        if f.search(pid):
            pids.append(pid.split('pid=')[1].split(',')[0])

    return pids
