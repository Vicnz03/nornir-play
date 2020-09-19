from plugins.nornir_addon import playbook_dir
from lxml import etree
from jnpr.junos.utils.config import Config
from nornir.core.exceptions import NornirSubTaskError
from ncclient.operations.rpc import RPCError
import logging
from time import sleep

logger = logging.getLogger(__name__)

def push_config(task, mode, commands = [],commit_comments=''):
    output_file = playbook_dir(task.host['playbook_name']) + '/{}.conf'
    result_file = playbook_dir(task.host['playbook_name']) + '/{}_result.txt'
    task.host['compare'] = 'Compare: Failed'
    task.host['commit'] = 'Commit: N/A'
    if 'napalm' not in task.host.connections:
        task.host.open_connection("napalm", None)
    dev = task.host.get_connection("napalm", None).device

    # if there's config to run and mode not collect
    if commands != 0 and mode != 'collect':
        with open(output_file.format(task.host.name), 'w') as f:
            config_set = '\n'.join(commands)
            f.write(config_set)
        
        with open(result_file.format(task.host.name), 'w') as f:
            try:
                with Config(dev, mode='exclusive') as cu:
                    cu.rollback()
                    cu.load(config_set, format="set", merge=True)
                    cu.commit_check()
                    logger.info(task.host.name + ' :configuration check succeeds')
                    task.host['compare'] = cu.diff(0)
                    f.write(task.host['compare'])
                    if mode == 'compare':
                        cu.rollback()
                    elif 'commit' in mode:
                        logger.info(task.host.name + ' :committing')
                        cu.commit(confirm=1, comment=commit_comments)
                        sleep(5)
                        cu.commit_check()
                        task.host['commit'] = 'commit: succeeds'
                        logger.info(task.host.name + ' :commit: succeeds')
                        f.write(task.host['commit'])

            except RPCError as e:
                logger.error(task.host.name + ' : ' + str(e))
                print(e)
                cu.rollback()
                cu.unlock()

            except NornirSubTaskError as e:
                print(e)
                logger.error(task.host.name + ' : ' + str(e.result.exception))
            
            except Exception as e:
                print(e)
                logger.error(task.host.name + ' : ' + str(e))

        # add output into report_details
        report_prefix = [task.host.name, task.host.get(
            'hostname'), task.host.get('description')]
        task.host['report_details'] = []
        task.host['report_details'].append(
            report_prefix + ['config', config_set])
        task.host['report_details'].append(
            report_prefix + ['compare', task.host['compare']])
        task.host['report_details'].append(
            report_prefix + ['commit', task.host['commit']])
