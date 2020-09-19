device = ['ACX03']
mode = 'collect'
playbook_summary = 'Check interfaces'
custom_def = False
csv_report = True
commands = ['show version | match junos','show configuration interfaces | display set']

