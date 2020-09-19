from nornir.plugins.tasks.networking import netmiko_send_command, netmiko_send_config, netmiko_commit, napalm_cli
from jnpr.jsnapy import SnapAdmin
from pprint import pprint
from jnpr.junos import Device
from plugins.junos_rpc import junos_rpc
from lxml import etree
from nornir.plugins.tasks.text import template_file
import json
from datetime import date
import os
import logging

logger = logging.getLogger(__name__)
dates = date.today().strftime("%d_%m_%Y")
output_dir = 'outputs/jsnapy/'
template_path = 'templates/jsnapy/{}.yml'
if not os.path.isdir(output_dir):
    os.makedirs(output_dir)

test_yml = """  - {}
"""

config_data = """
hosts:
  - device: {}
    username : {}
    passwd: {}
tests:
{}
sqlite:
  - store_in_sqlite: yes
    check_from_sqlite: yes
    database_name: jsnapy.db  
"""


def gather_data(task):
    task.host['gather_data'] = {}
    task.host['gather_data']['module'] = junos_rpc(
        task.host, 'get_system_information', to_str=0)[0].text
    task.host['gather_data']['ospf_existance_results'] = junos_rpc(
        task.host, 'get-ospf-neighbor-information')
    task.host['gather_data']['bgp_existance_results'] = junos_rpc(
        task.host, 'get-bgp-summary-information')
    task.host['gather_data']['vpls_existance_results'] = junos_rpc(
        task.host, 'get-vpls-connection-information')
    task.host['gather_data']['l2vpn_existance_results'] = junos_rpc(
        task.host, 'get-l2vpn-connection-information')
    task.host['gather_data']['ccc_existance_results'] = junos_rpc(
        task.host, 'get-ccc-information')
    task.host['gather_data']['subscriber_count'] = junos_rpc(
        task.host, 'get-subscribers')
    task.host['gather_data']['bfd_sessions'] = junos_rpc(
        task.host, 'get-bfd-session-information')
    task.host['gather_data']['ldp_sessions'] = junos_rpc(
        task.host, 'get-ldp-session-information')
    task.host['gather_data']['rsvp_sessions'] = junos_rpc(
        task.host, 'get-rsvp-session-information')
    task.host['gather_data']['mpls_sessions'] = junos_rpc(
        task.host, 'get-mpls-lsp-information')


def get_host_check(task):
    test_common = ['test_chassis','test_interfaces','test_isis','test_route','test_bgp']
    host_data = task.host.data['gather_data']
    host_checks = test_common
    if host_data['module'] == 'mx480':
        host_checks.append('test_re_dual')
    else:
        host_checks.append('test_re_single')
    if '<sessions>0</sessions>' not in host_data['bfd_sessions']:
        host_checks.append('test_bfd')
    if 'instance' in host_data['l2vpn_existance_results']:
        host_checks.append('test_l2vpn')
    if 'ospf-neighbor-information-all' in host_data['ospf_existance_results']:
        host_checks.append('test_ospf')
    #if 'bgp-information' in gather_data['bgp_existance_results']:
    if 'instance' in host_data['vpls_existance_results']:
        host_checks.append('test_vpls')
    if 'ccc-connection' in host_data['ccc_existance_results']:
        host_checks.append('test_ccc')
    if '<number-of-active-subscribers>\n0\n' not in host_data['subscriber_count']:
        host_checks.append('test_subscribers')
    if 'not running' not in host_data['ldp_sessions']:
        host_checks.append('test_ldp')
    if 'not configured' not in host_data['rsvp_sessions']:
        host_checks.append('test_rsvp')
    if 'not configured' not in host_data['mpls_sessions']:
        host_checks.append('test_mpls')
    # output result to dir
    
    task.host['host_checks'] = host_checks


def jsnapy_pre(task,jsnapy_test):
    if jsnapy_test:
        task.host['host_checks'] = jsnapy_test
    else:
        task.run(task=gather_data)
        task.run(task=get_host_check)

    
    host_check_result = ''
    for check in task.host['host_checks']:
        host_check_result += test_yml.format(template_path.format(check))
    
    host_check_yml = output_dir+task.host.name+'_check.yml'
    with open(host_check_yml, 'w') as f:
        f.write(host_check_result)

    js = SnapAdmin()
    config_host = config_data.format(
        task.host.hostname, task.host.username, task.host.password, host_check_result)
    js.snap(config_host, "pre")


def jsnapy_post(task):
    host_check_yml = output_dir+task.host.name+'_check.yml'
    with open(host_check_yml,'r') as f:
        host_check_resutl = f.read()
    js = SnapAdmin()
    config_host = config_data.format(
        task.host.hostname, task.host.username, task.host.password, host_check_resutl)
    js.snap(config_host, "post")
    snapchk = js.check(config_host, "pre", "post")
    result_output = '{}{}_{}_result.txt'
    for val in snapchk:
        with open(result_output.format(output_dir, task.host.name,dates), 'w') as f:
            f.write(json.dumps(dict(val.test_details), indent=4))
