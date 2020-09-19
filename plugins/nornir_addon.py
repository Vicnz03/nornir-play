
import os
from datetime import date
import sys
import logging
import shutil
import psycopg2 as mdb
from nornir.core.exceptions import NornirSubTaskError

logger = logging.getLogger(__name__)
dates = date.today().strftime("%d_%m_%Y")

def validator(playbook, nr):
    vars_list = [item for item in dir(playbook) if not item.startswith("__")]
    vars_dict = {k: v for k, v in vars(playbook).items() if k in vars_list}
    core_type = ['ACX', 'SWC', 'RTR', 'QFX', 'CORE']  # support device type
    mode_type = ['collect', 'compare', 'commit', 'commit_only', 'jsnapy_pre', 'jsnapy_post']  # support mode type
    must_have = ['mode', 'device', 'custom_def', 'playbook_summary']
    optional = ['csv_report', 'email_report', 'commands', 'email_list',
                'config_dir', 'commit_comments', 'exclude_device', 'nornir_task','jsnapy_test']
    missing = [key for key in must_have if key not in vars_dict.keys()]
    no_command_needed = ['jsnapy_pre','jsnapy_post','commit_only']
    for key in optional:
        if key not in vars_dict.keys():
            vars_dict[key] = False

    if len(missing) != 0:
        logger.error('Vars check error: playbook missing ' + ' '.join(missing))
        sys.exit()

    try:
        mode = vars_dict['mode']
        assert (mode in mode_type)
        if 'commit' in mode and vars_dict['commit_comments'] == False:
            logger.error('Vars check error: Mode {} need {}'.format(
                mode, 'commit_comments'))
            sys.exit()

        if mode == 'commit_ony' and vars_dict['config_dir'] == False:
            logger.error('Vars check error: Mode {} need {}'.format(
                mode, 'config_dir'))
            sys.exit()

        if not vars_dict['custom_def'] and vars_dict['mode'] not in no_command_needed:
            if vars_dict['commands'] == False:
                logger.error(
                    'Vars check error: Not custom_def/commit_only need commands')
                sys.exit()

            elif isinstance(vars_dict['commands'], str):
                with open(vars_dict['commands'], 'r') as f:
                    vars_dict['commands'] = [
                        cmd.strip('\n') for cmd in f.readlines()]

            assert isinstance(vars_dict['commands'], list)

        if vars_dict['exclude_device'] != False:
            assert isinstance(vars_dict['exclude_device'], list)
            task_devices = nr.filter(
                filter_func=lambda h: h.name not in vars_dict['exclude_device'])
        else:
            task_devices = nr

        template_path = 'templates/jsnapy/{}.yml'
        if vars_dict['jsnapy_test']:
            assert isinstance(vars_dict['jsnapy_test'], list)
            for target in vars_dict['jsnapy_test']:
                if not os.path.isfile(template_path.format(target)):
                    logger.error('Target test yml file not exists:' + target)
                    vars_dict['jsnapy_test'].remove(target)
            if len(vars_dict['jsnapy_test']) == 0:
                sys.exit() 

        if vars_dict['email_report'] and vars_dict['email_list']:
            assert isinstance(vars_dict['email_list'], list)
        elif vars_dict['email_report'] and vars_dict['email_list'] == False:
            logger.error('Vars check error: Email report need email_list')
            sys.exit()

    except AssertionError as e:
        logging.error('Vars type incorrect')
        logging.error(e)
        sys.exit()

    except AttributeError as e:
        logging.error('Vars not defined')
        logging.error(e)
        sys.exit()

    except Exception as e:
        logging.error(e)
        sys.exit()

    return vars_dict, task_devices


def set_playbook(host, playbook_name):
    host.data['playbook_name'] = playbook_name

# create playbook_dir
def playbook_dir(playbook_name):
    output_dir = f'outputs/{playbook_name}/output-{dates}'
    if not os.path.isdir(output_dir):
        os.makedirs(output_dir)

    return output_dir

# check auth
def check_auth(task_devices):
    test_device_name = list(task_devices.inventory.hosts)[0]
    test_device= task_devices.inventory.hosts[test_device_name]
    try:
        test_device.open_connection("napalm", None)
        print('Login success')
    except NornirSubTaskError as e:
        print(e.result.exception)
        sys.exit()

