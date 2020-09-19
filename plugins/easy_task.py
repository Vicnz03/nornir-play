from plugins.nornir_addon import playbook_dir
from plugins.push_config import push_config
import logging
import re
from plugins.junos_get import junos_get
from nornir.core.task import Result, Task
logger = logging.getLogger(__name__)
output_template = '''
===============================================================================
Command:  {command}
===============================================================================
{result}

'''

# block commands shouldn't run via easy_task
def easy_task(task, mode, commands, commit_comments = ''):
    output_file = playbook_dir(task.host['playbook_name']) + '/{}_result.txt'

    if mode == 'collect':
        with open(output_file.format(task.host.name), 'w') as output:
            result = task.run(task = junos_get, commands = commands)
            report_prefix = [task.host.name, task.host.get('hostname'), task.host.get('description')]
            task.host['report_details'] = []
            for key, value in result[0].result.items():
                task.host['report_details'].append(report_prefix + [key, value])
                output.write(output_template.format(command=key,result=value))
    else:
        if mode == 'commit_only':
            commands = task.run(task=set_config_folder,folder=vars_dict['config_dir'])
        task.run(task=push_config, mode=mode, commands = commands, commit_comments=commit_comments)

def set_config_folder(task, folder):
    config_file = f'{folder}/{task.host.name}.conf'
    with open(config_file, 'r') as f:
        config = [output.strip('\n') for output in f.readlines()]

    return Result(host=task.host, result=config)
