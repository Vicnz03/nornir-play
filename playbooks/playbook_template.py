# Must have
device = ['RTR02']
mode = 'collect' # collect, compare ,commit , commit_only, 'jsnapy_pre', 'jsnapy_post'
playbook_summary = 'Check interfaces'
custom_def = False

# conditional
# if mode = commit or commit_only
commit_comments = 'commit_comments'

# if mode not jsnapy_*,commit only
commands = ['show version | match junos','show configuration interfaces | display set']

# if mode = commit only
config_dir = 'path_to_config_folder'

# if custom_def = True
def nornir_task(task):
    pass

# options
csv_report = True
exclude_device = ['I-DONT-NEED']
jsnapy_test = ['test_bgp'] #if mode = jsnapy_pre, and no jsnapy_test, will run all test

# options come togother
email_report = True
email_list = ['xxx@xx.xx']

