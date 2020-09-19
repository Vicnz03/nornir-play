from lxml import etree
def junos_rpc(task_host,rpc_cmd, to_str = 1):
    if 'napalm' not in task_host.connections:
        task_host.open_connection("napalm", None)
    #result = task_host.get_connection("napalm", None).device.rpc['get_system_information']()
    method_to_call = getattr(task_host.get_connection("napalm", None).device.rpc, rpc_cmd)
    result = method_to_call()
    if to_str:
        result = etree.tostring(result, encoding="unicode")
    return result