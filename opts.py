# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy
# of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import itertools
import watchdog.controller.manager
import watchdog.objects.monitor_base
import watchdog.service


def list_opts():
    return [
        ('DEFAULT',
         itertools.chain(
             watchdog.controller.manager.monitor_manager_opts,
             watchdog.objects.monitor_base.monitor_default_opts,
         )),
        ('monitor',
         itertools.chain(
             watchdog.service.monitor_task_opts,
         )),
        ('hang_detect',
         itertools.chain(
             watchdog.service.hang_task_opts,
         )),
    ]
