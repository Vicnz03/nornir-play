from lxml import etree
import re
import logging
from collections import OrderedDict
from nornir.plugins.tasks.networking import netmiko_send_command
from nornir.core.task import Result, Task
invaild_cmd = re.compile('^(request|clear|start|restart).*')
get_config = re.compile('^show configuration .*')

logger = logging.getLogger(__name__)
def _count(txt, none):  # Second arg for consistency only. noqa
    """
    Return the exact output, as Junos displays
    e.g.:
    > show system processes extensive | match root | count
    Count: 113 lines
    """
    count = len(txt.splitlines())
    return "Count: {count} lines".format(count=count)

def _trim(txt, length):
    """
    Trim specified number of columns from start of line.
    """
    try:
        newlines = []
        for line in txt.splitlines():
            newlines.append(line[int(length) :])
        return "\n".join(newlines)
    except ValueError:
        return txt

def _except(txt, pattern):
    """
    Show only text that does not match a pattern.
    """
    rgx = "^.*({pattern}).*$".format(pattern=pattern)
    unmatched = [
        line for line in txt.splitlines() if not re.search(rgx, line, re.I)
    ]
    return "\n".join(unmatched)

def _last(txt, length):
    """
    Display end of output only.
    """
    try:
        return "\n".join(txt.splitlines()[(-1) * int(length) :])
    except ValueError:
        return txt

def _match(txt, pattern):
    """
    Show only text that matches a pattern.
    """
    rgx = "^.*({pattern}).*$".format(pattern=pattern)
    matched = [line for line in txt.splitlines() if re.search(rgx, line, re.I)]
    return "\n".join(matched)

def _find(txt, pattern):
    """
    Search for first occurrence of pattern.
    """
    rgx = "^.*({pattern})(.*)$".format(pattern=pattern)
    match = re.search(rgx, txt, re.I | re.M | re.DOTALL)
    if match:
        return "{pattern}{rest}".format(pattern=pattern, rest=match.group(2))
    else:
        return "\nPattern not found"

def _process_pipe(cmd, txt):
    """
    Process CLI output from Juniper device that
    doesn't allow piping the output.
    """
    if txt is None:
        return txt
    _OF_MAP = OrderedDict()
    _OF_MAP["except"] = _except
    _OF_MAP["match"] = _match
    _OF_MAP["last"] = _last
    _OF_MAP["trim"] = _trim
    _OF_MAP["count"] = _count
    _OF_MAP["find"] = _find
    # the operations order matter in this case!
    exploded_cmd = cmd.split("|")
    pipe_oper_args = {}
    for pipe in exploded_cmd[1:]:
        exploded_pipe = pipe.split()
        pipe_oper = exploded_pipe[0]  # always there
        pipe_args = "".join(exploded_pipe[1:2])
        # will not throw error when there's no arg
        pipe_oper_args[pipe_oper] = pipe_args
    for oper in _OF_MAP.keys():
        # to make sure the operation sequence is correct
        if oper not in pipe_oper_args.keys():
            continue
        txt = _OF_MAP[oper](txt, pipe_oper_args[oper])
    return txt


def junos_get(task, commands):
    if 'napalm' not in task.host.connections:
        task.host.open_connection("napalm", None)
    dev = task.host.get_connection("napalm", None).device
    result = {}
    for command in commands:
        if not invaild_cmd.match(command):
            #(cmd, _, _) = command.partition("|")
            cmds = command.split('|')
            display = ''
            for item in cmds:
                if 'display' in item:
                    display = '|' + item
            cmd_result = dev.rpc.cli(command=cmds[0]+display, format='text')
            cmd_result = etree.tostring(cmd_result, encoding='unicode')
            cmd_result = _process_pipe(command,cmd_result)
            result[command] = cmd_result

        else:
            logger.info('Invaild command: ' + command)
    return Result(host=task.host, result=result)

                
            


            

