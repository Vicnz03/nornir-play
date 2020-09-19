from nornir.plugins.tasks.networking import netmiko_send_command
from plugins.nornir_addon import easy_task
device = ['SWC01','SWC02', 'RTR01']
mode = 'collect'
playbook_summary = 'Decommission'
custom_def = True
vlan_list  = [
    '554',
    '600',
    '1127',
    '1154',
    '3007',
    '3232',]
def nornir_task(task):
    show_vlan = 'show vlans {}'
    show_l3_intf = 'show configuration | display set | match "ae0(.| unit ){}"'
    if task.host.name == 'RTR01':
        commands = [ show_l3_intf.format(vlan) for vlan in vlan_list]
    else:
        commands = [ show_vlan.format(vlan) for vlan in vlan_list]
        
    task.run(task=easy_task, mode=mode, commands=commands)