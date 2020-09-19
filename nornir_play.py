""" Run Nornir playbook

Usage:
    nornir_play.py (<playbook_name>)

Arguments:
  playbook_name       Playbook needs to run

Examples:
  nornir_play.py playbook_name.py 

Options:
    -h --help   This message
"""

from nornir import InitNornir
from nornir.core.filter import F
from nornir.core.exceptions import NornirSubTaskError
import os
from datetime import date
import getpass
from plugins.n import NagiosInventory
from docopt import docopt
import re
import sys
import logging
import shutil
import importlib
import glob
from plugins.nornir_addon import *
from plugins.jsnapy_check import *
from plugins.report import *
from plugins.easy_task import *
from plugins.push_config import push_config
from tqdm import tqdm

# init logging
dates = date.today().strftime("%d_%m_%Y")
log_file = 'logs/nornir_play-{}.log'.format(dates)

# create log file if no exists
if not os.path.isfile(log_file):
    open(log_file, 'w').close()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)12s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)

logging.getLogger("paramiko").setLevel(logging.WARNING)
logging.getLogger("ncclient").setLevel(logging.WARNING)


if __name__ == '__main__':
    arguments = docopt(__doc__)

    playbook_path = arguments['<playbook_name>'].split(
        '.')[0]  # get path/playbook from path/playbook.py
    # get playbook from path/playbook
    playbook_name = playbook_path.split('/')[-1]
    # check if playbook exists
    if os.path.isfile(arguments['<playbook_name>']):
        playbook = importlib.import_module(playbook_path.replace('/', '.'))
    else:
        logging.error('Playbook {} not exists'.format(
            arguments['<playbook_name>']))
        sys.exit()

    # Init nornir
    nr = InitNornir(
        inventory={
            "plugin": "nornir.plugins.inventory.simple.SimpleInventory",
            "options": {
                "host_file": "inventory/hosts.yaml",
                "group_file": "inventory/groups.yaml"
            },
            "transform_function": set_playbook,
            "transform_function_options": {'playbook_name': playbook_name},

        },
        logging={
            "enabled": False
        },
        core={
            "num_workers": 30
        }
    )

    # Get&Check vars from playbook
    vars_dict, task_devices = validator(playbook, nr)
    task_devices = nr.filter(filter_func=lambda h: h.name in vars_dict['device'])
    playbook_summary = vars_dict['playbook_summary']
    device = vars_dict['device']
    mode = vars_dict['mode']

    # set username&password
    username = 'admin'
    password = 'xxxxxx'
    nr.inventory.defaults.username = username
    nr.inventory.defaults.password = password
    user = 'vic.chen'

    # check auth and create playbook folder
    if len(task_devices.inventory.hosts) == 0:
        logging.error('no valid devices, please check')
        sys.exit()
    else:
        task_summary = '{} using nornir_play run {}\nPlaybook_summary:{}\nMode:{}\nDevice list:\n{}'.format(
            user, playbook_name, playbook_summary, mode, '\n'.join(list(task_devices.inventory.hosts)))

    logging.info(task_summary)
    check_auth(task_devices)
    playbook_dir(playbook_name)

    # call nornir_task in playbook if not custom_def
    if vars_dict['custom_def']:
        task_devices.run(task=vars_dict['nornir_task'])
    elif mode == 'jsnapy_pre':
        task_devices.run(task=jsnapy_pre)
    elif mode == 'jsnapy_post':
        task_devices.run(task=jsnapy_post)
    elif mode == 'rpc':
        task_devices.run(task=junos_rpc)
    else:
        # run easy_task
        task_devices.run(task=easy_task, mode=mode, commands=vars_dict['commands'],commit_comments=vars_dict['commit_comments'])

    if vars_dict['csv_report']:
        generate_report(task_devices, playbook_name)

    if vars_dict['email_report']:
        send_report(user, vars_dict['email_list'], playbook_path,
                    playbook_summary, task_summary)
