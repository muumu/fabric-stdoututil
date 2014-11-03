# -*- coding:utf-8 -*-

from stdoututil import *

def print_dict(d):
    for k, v in d.items():
        print('{} =>'.format(k))
        if isinstance(v, list):
            print '\n'.join(v)
        else:
            print v

# put your own host list here to execute sample task
_hosts = ['localhost', 'ap01.example.com', 'ap02.example.com']

src1 = '''
    process1: running
    process2: running
    process3: running
    '''
src2 = '''
    process1: running
    process2: running
    process3: stopped
    '''
src3 = '''
    thread: enable
    status: OK
    '''

@task
def sample():
    execute(run, 'echo test', hosts='localhost')
    sample_get_stdout()
    sample_contains()
    sample_get_values()
    sample_get_dict()
    sample_validate_values()
    sample_validate_keyvalues()

def sample_get_stdout():
    '''works only on Debian platforms that support "apt list"'''
    command = 'apt list | ' + cmd_egrep_startswith('glibc')
    print_dict(get_stdouts(command, hosts=_hosts))
    command = 'apt list | ' + cmd_egrep_startswith('libxml2', 'nss', excludes='python')
    print_dict(get_stdouts(command, hosts=_hosts, user='root'))

def sample_contains():
    print_dict(contains('echo "{}"'.format(src2), ['running', 'stopped', 'unknown'], hosts=_hosts))

def sample_get_values():
    print_dict(get_values('echo "{}"'.format(src2), 'process', ':', hosts=_hosts))

def sample_get_dict():
    print_dict(get_dict('echo "{}"'.format(src2), ':', hosts=_hosts))

def sample_validate_values():
    cmd1 = 'echo "{}"'.format(src1)
    print_dict(validate_values(cmd1, 'process', 'running', hosts=_hosts))
    cmd2 = 'echo "{}"'.format(src2)
    print_dict(validate_values(cmd2, 'process', 'running', hosts=_hosts))
    
def sample_validate_keyvalues():
    cmd = 'echo "{}"'.format(src3)
    r = validate_keyvalues(cmd, {'thread': 'enable', 'status': 'OK'}, hosts=_hosts)
    print r
    for host in _hosts:
        print all(r[host].values())
    r = validate_keyvalues(cmd, {'thread': 'disable', 'status': 'OK'}, hosts=_hosts)
    print r
    for host in _hosts:
        print all(r[host].values())

