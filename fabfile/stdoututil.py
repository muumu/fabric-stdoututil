# -*- coding:utf-8 -*-

from getpass import getpass
import re
import multiprocessing
from functools import partial
from fabric.api import env, local, run, sudo, execute, hide, settings
from fabric.decorators import task, parallel


lk_passwd = multiprocessing.Lock()
def confirm_passwd():
    """prompt user with password if env.password is not set"""
    lk_passwd.acquire()
    if not env.password:
        env.password = getpass('Input sudo password: ')
    lk_passwd.release()

def handy_parallel(task):
    """decorator for executing parallel task conveniently"""
    def inner(*args, **kwargs):
        hosts = kwargs.pop('hosts', None)
        user = kwargs.pop('user', None)
        quiet = kwargs.pop('quiet', True)
        if user != None:
            confirm_passwd()
        with settings(parallel=True):
            return task(*args, user=user, quiet=quiet, hosts=hosts, **kwargs)
    return inner

def cmd_egrep(*args, **kwargs):
    """get string of egrep command"""
    ex = kwargs.get('excludes', [])
    if isinstance(ex, str):
        ex = [ex]
    if len(args) > 0 and len(ex) > 0:
        return 'egrep ' + '"' + '|'.join(args)+ '"' + '| egrep -v "' + '|'.join(ex) + '"'
    if len(args) > 0:
        return 'egrep ' + '"' + '|'.join(args)+ '"'
    if len(ex) > 0:
        return 'egrep -v ' + '"' + '|'.join(ex)+ '"'
    raise Exception('Empty args for egrep')

def cmd_egrep_startswith(*args, **kwargs):
    """get string of egrep command with adding line head regex to each keyword"""
    f = lambda s: '^(' + s + ')'
    ex = kwargs.get('excludes', [])
    if isinstance(ex, str):
        kwargs['excludes'] = f(ex)
    else:
        kwargs['excludes'] = map(f, ex)
    return cmd_egrep(*map(f, args), **kwargs)

def task_get_stdouts(command, user=None, quiet=True):
    """returns list of stdouts produced by shell command"""
    f = run
    if user != None:
        f = partial(sudo, user=user)
        confirm_passwd()
    r = f(command, quiet=quiet, pty=False, combine_stderr=False).stdout
    return map(lambda l: l.strip(), filter(lambda l: len(l) > 0, r.split('\n')))

def task_contains(command, values, user=None, quiet=True):
    """returns dict whether or not each value is found in stdout of command"""
    result = '\n'.join(task_get_stdouts(command, user, quiet))
    return dict(map(lambda v: (v, v in result), values))

def task_get_values(command, key, delim=':', user=None, quiet=True):
    """find line that startswith key and returns right side of it separated by delim"""
    f = lambda l: l.startswith(key) or l.find(delim) >= 0
    r = filter(f, task_get_stdouts(command, user, quiet))
    return map(lambda l: l.split(delim)[1].strip(), r)

def task_get_dict(command, delim=':', user=None, quiet=True):
    """create dict by splitting stdout of command"""
    results = filter(lambda l: l.find(delim) > 0, task_get_stdouts(command, user, quiet))
    return dict(map(lambda l: (l.split(delim)[0].strip(), l.split(delim)[1].strip()), results))

def task_validate_values(command, key, value, user=None, quiet=True):
    """returns whether or not each line where key is found contains value"""
    r = filter(lambda l: re.match('.*({}).*'.format(key), l), task_get_stdouts(command, user, quiet))
    return all(map(lambda l: re.match('.*({}).*'.format(value), l), r))

def find_key(s, keys):
    """
    return key found in a string
    string containing more than one key is not supported
    """
    key = filter(lambda k: k in s, keys)
    if len(key) > 1:
        raise Exception('More than one keys found. {} are in {}'.format(key, s))
    if len(key) == 0:
        return None
    return key[0]

def task_validate_keyvalues(command, keyvalues, user=None, quiet=True):
    """returns whether or not each line where key is found contains value for each key"""
    lines = task_get_stdouts(command, user, quiet)
    d = {}
    for l in lines:
        key = find_key(l, keyvalues.keys())
        if key != None:
            d[key] = keyvalues[key] in l
    return d

@handy_parallel
def get_stdouts(command, **kwargs):
    """returns list of stdouts produced by shell command (for each host)"""
    return execute(task_get_stdouts, command,
        kwargs['user'], kwargs['quiet'], hosts=kwargs['hosts'])

@handy_parallel
def contains(command, values, **kwargs):
    """returns dict whether or not each value is found in stdout of command (for each host)"""
    return execute(task_contains, command, values,
        kwargs['user'], kwargs['quiet'], hosts=kwargs['hosts'])

@handy_parallel
def get_values(command, key, delim=':', **kwargs):
    """find line containing key and returns right side of it separated by delim (for each host)"""
    return execute(task_get_values, command, key, delim,
        kwargs['user'], kwargs['quiet'], hosts=kwargs['hosts'])

@handy_parallel
def get_dict(command, delim=':', **kwargs):
    """create dict by splitting stdout of command (for each host)"""
    return execute(task_get_dict, command, delim,
        kwargs['user'], kwargs['quiet'], hosts=kwargs['hosts'])

@handy_parallel
def validate_values(command, key, value, **kwargs):
    """returns whether or not each line where key is found contains value (for each host)"""
    return execute(task_validate_values, command, key, value,
        kwargs['user'], kwargs['quiet'], hosts=kwargs['hosts'])

@handy_parallel
def validate_keyvalues(command, keyvalues, **kwargs):
    """returns whether or not each line where key is found contains value for each key (for each host)"""
    return execute(task_validate_keyvalues, command, keyvalues,
        kwargs['user'], kwargs['quiet'], hosts=kwargs['hosts'])
