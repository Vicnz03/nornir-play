# nornir-play
## Usage
```
python nornir_play.py <playbook_name.py>
```
## Example
```
python nornir_play.py playbooks/easy_task.py
```

## Project layout
```
├─ nornir_play
   ├─ nornir_play_lab.py
   ├─ nornir_play.py
   ├─ standalone_script.py
   |
   ├─ inventory
   |  └─ HF inventory
   |  └─ lab inventory   
   |
   ├─ output
   |  └─ playbook_name
   |
   ├─ playbooks
   |  └─ playbook.py
   |
   ├─ plugins
   |  └─ plugins can use
   |
   └─  logs
```
## Install
Nornir requires python 3.6+.

## nornir_play
Main Script

- Init logging 
- Init nornir
- Run playbook
- Check playbook vars
- Check auth


## plugins
- nornir_addon: args validator, playbook_dir, check_auth
- push_config: when needs commit/compare config
- easy_task: when custom_def = False
- jsnapy_check: use jsnapy to pre/post check
- jsnapy_get: use rpc.cli to get facts
- junos_rpc: run rpc calls
- Report: Generate CSV report and send email

## playbook
Custom playbook called by nornir_play

Must has vars:

- device: # Device to run script
    - deivce name # 
- mode
    - 'collect' # Collect info from devices
    - 'compare' # push config to devices and show | compare then rollback, won't commit 
    - 'commit' # commit config to devices
    - 'commit_only' #commit existing config
    - 'jsnapy_*' # use jsnapy to pre/post check
- playbook_summary = 'Check version' # summary of playbook
- custom_def = False # use custom_def or easy_task

Option vars:

- csv_report: bool # Generate CSV report or not
- email_report: bool # email output and playbook
- email_list: list # When email_report is true, list of recipients
- commands: list # When custom_def is False, list of commands to run
- nornir_task: def # When custom_def is true, def will called by nornir_play
- exclude_device: list # exclude devices
- commit_comments: string # When mode is commit, need commit comments
- config_dir: string #when mode is commit_only, config folder
- jsnapy_test: list # list of jsnpay test file , run all test when it's not included

