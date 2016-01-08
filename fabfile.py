from fabric.api import cd, env, lcd, local, run, settings, task, prompt
import os

env.run = local
env.cd = lcd
env.base_path = os.path.dirname(env.real_fabfile)

@task(alias='prod')
def production():
    """Merge the dev branch into master and push into production"""
    status = env.run('git s --porcelain', capture=True)
    if '??' in status:
        print 'Untracked files, exiting'
        exit()
    env.run('git pull origin dev', capture=False)
    env.run('git co master', capture=False)
    env.run('git pull origin master', capture=False)
    env.run('git merge dev --no-ff', capture=False)
    env.run('git push origin master', capture=False)
    env.run('git push origin dev', capture=False)
    env.run('git co dev', capture=False)

@task
def staging():
    """Push the staging branch to the staging server"""
    env.run('git push origin staging', capture=False)

@task
def test(test_path='', reuse='0', capture=False):
    """Run all tests, or a specific subset of tests"""
    cmd = 'REUSE_DB=%(reuse)s ./manage.py test %(test_path)s %(capture)s' % {
        'reuse': reuse,
        'test_path': test_path,
        'capture': '--nologcapture' if not capture else ''
    }
    with env.cd(env.base_path):
        env.run(cmd)

@task
def coverage():
    """Run the tests and generate a coverage report"""
    with env.cd(env.base_path):
        env.run('coverage erase')
        env.run('coverage run --branch --source muckrock manage.py test')
        env.run('coverage html')

@task
def pylint():
    """Run pylint"""
    with env.cd(env.base_path):
        excludes = ['migrations', '__init__.py', 'manage.py', 'formwizard',
                    'vendor', 'fabfile', 'static', 'nested_inlines']
        stmt = ('find . -name "*.py"' +
                ''.join(' | grep -v %s' % e for e in excludes) +
                ' | xargs pylint --load-plugins=pylint_django '
                '--rcfile=config/pylint.conf -r n')
        env.run(stmt)

@task
def mail():
    """Run the test mail server"""
    env.run('python -m smtpd -n -c DebuggingServer localhost:1025')

@task(alias='rs')
def runserver():
    """Run the test server"""
    with env.cd(env.base_path):
        env.run('./manage.py runserver 0.0.0.0:8000')

@task
def celery():
    """Run the celery worker"""
    with env.cd(env.base_path):
        env.run('./manage.py celery worker')

@task(alias='m')
def manage(cmd):
    """Run a python manage.py command"""
    with env.cd(env.base_path):
        env.run('./manage.py %s' % cmd)

@task
def pip():
    """Update installed python packages with pip"""
    with env.cd(env.base_path):
        env.run('pip install -r requirements.txt')

@task(name='populate-db')
def populate_db():
    """Populate the local DB with the data from the latest heroku backup"""
    # https://devcenter.heroku.com/articles/heroku-postgres-import-export

    confirm = prompt('This will over write your local database.  '
                     'Are you sure you want to continue? [y/N]')
    if confirm.lower() not in ['y', 'yes']:
        return
    
    with env.cd(env.base_path):
        env.run('PGUSER=postgres dropdb muckrock')
        env.run('PGUSER=postgres heroku pg:pull DATABASE muckrock')

@task(name='sync-aws')
def sync_aws():
    """Sync images from AWS to match the production database"""

    folders = [
            'account_images',
            'agency_images',
            'jurisdiction_images', 
            'news_images', 
            'news_photos', 
            'project_images', 
            ]
    with env.cd(env.base_path):
        for folder in folders:
            env.run('aws s3 sync s3://muckrock/{folder} '
                    './muckrock/static/media/{folder}'
                    .format(folder=folder))

@task
def hello():
    """'Hello world' for testing purposes"""
    env.run('echo hello world')

@task(alias='v')
def vagrant(cmd=None):
    """Run a vagrant command or a task on the vagrant VM"""
    # run as `fab vagrant:up`
    if cmd:
        with lcd(os.path.join(env.base_path, 'vm')):
            local('vagrant %s' % cmd)

    # run as `fab vagrant runserver`
    else:
        # change from the default user to 'vagrant'
        env.user = 'vagrant'
        # connect to the port-forwarded ssh
        env.hosts = ['127.0.0.1:2222']

        # use vagrant ssh key
        with lcd(os.path.join(env.base_path, 'vm')):
            result = local('vagrant ssh-config | grep IdentityFile',
                    capture=True)
        env.key_filename = result.split()[1]

        env.run = run
        env.cd = cd
        env.base_path = '/home/vagrant/muckrock'

@task
def setup():
    """Run to initialize your VM"""
    # XXX this doesnt work yet
    vagrant('up')
    with lcd(os.path.join(env.base_path, 'vm')):
        result = local('vagrant ssh-config | grep IdentityFile',
                capture=True)
    with settings(user='vagrant', host_string='127.0.0.1:2222', key_filename=result.split()[1]):
        manage('migrate')


