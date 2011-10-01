'''
usage:
    $ fab dev_server uptime
    $ fab production_server host_info
'''
import os

from fabric.api import *

def prod():
    env.user = 'matt'
    env.hosts = ['kepler']
    env.virtualenv_dir = '/home/matt/virtualenvs/meduele-lib'
    env.project_dir = '/home/matt/meduele'
    env.supervisord_config = '/home/matt/conf/meduele/supervisord.conf'
    env.branch = 'master'


def deploy():
    # push changes of specific branch
    local('git push origin %s' % env.branch)

    # update the remote with these changes
    run('cd %s; git pull origin %s' % (env.project_dir, env.branch))
    
    # update the meduele module installation
    run('pip install -E %s -e %s' % (env.virtualenv_dir, env.project_dir))

    # restart the gunicorn processes
    gunicorn('restart')


''' gunicorn controls via supervisord
'''
def gunicorn(command):
    if command == 'start':
        run('supervisorctl -c %s start gunicorn' % env.supervisord_config)
    elif command == 'stop':
        run('supervisorctl -c %s stop gunicorn' % env.supervisord_config)
    elif command == 'restart':
        run('supervisorctl -c %s restart gunicorn' % env.supervisord_config)
    elif command == 'status':
        run('supervisorctl -c %s status gunicorn' % env.supervisord_config)
    elif command == 'logs':   # view the logs; supervisord redirects stderr and stdout to this path based on current config
        run('tail ~/log/meduele/gunicorn.log')
    else:
        print 'sorry, did not understand that gunicorn command'


''' nginx controls
'''
def nginx(command):
    if command == 'start':
        sudo('/etc/init.d/nginx start')
    elif command == 'stop':
        sudo('/etc/init.d/nginx stop')
    elif command == 'restart':
        nginx('stop')
        nginx('start')
    else:
        print 'hm, did not quite understand that nginx command'


''' misc
'''
def host_info():
    print 'checking lsb_release of host: '
    run('lsb_release -a')

def uptime():
    run('uptime')

def grep_python():
    run('ps aux | grep python')

