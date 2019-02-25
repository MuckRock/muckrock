# Standard Library
import os

# Third Party
from fabric.api import (
    cd,
    env,
    lcd,
    local,
    prompt,
    run,
    settings,
    task,
    warn_only,
)

env.run = local
env.cd = lcd
env.base_path = os.path.dirname(env.real_fabfile)


@task(alias='prod')
def production(force=False):
    """Merge the dev branch into master and push into production"""
    status = env.run('git s --porcelain', capture=True)
    if '??' in status and not force:
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
    cmd = DOCKER_COMPOSE_RUN_OPT.format(
        opt='-e REUSE_DB={reuse}'.format(reuse=reuse),
        service='django',
        cmd=
        './manage.py test {test_path} {capture} --settings=muckrock.settings.test'.
        format(
            test_path=test_path,
            capture='--nologcapture' if not capture else '',
        )
    )
    with env.cd(env.base_path):
        env.run(cmd)


@task
def coverage(settings='test', reuse='0'):
    """Run the tests and generate a coverage report"""
    with env.cd(env.base_path):
        env.run('coverage erase')
        env.run(
            'REUSE_DB=%s coverage run --branch --source muckrock --omit="*/migrations/*" manage.py test --settings=muckrock.settings.%s'
            % (reuse, settings)
        )
        env.run('coverage html')


@task
def pylint():
    """Run pylint"""
    with env.cd(env.base_path):
        excludes = [
            'migrations', '__init__.py', 'manage.py', 'vendor', 'fabfile',
            'static', 'node_modules'
        ]
        stmt = (
            'find ./muckrock -name "*.py"' +
            ''.join(' | grep -v %s' % e for e in excludes) +
            ' | xargs pylint --load-plugins=pylint_django '
            '--rcfile=config/pylint.conf -r n'
        )
        env.run(stmt)


@task
def format():
    """Format all the code"""
    with env.cd(env.base_path):
        env.run(
            'yapf -i -r --style config/style.yapf -e "*/migrations/*" -p muckrock'
        )
        env.run('isort -sp config -rc muckrock')


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
        env.run('./manage.py celery worker -Q celery,phaxio -l DEBUG')


@task(alias='m')
def manage(cmd):
    """Run python manage command"""
    with env.cd(env.base_path):
        env.run(DJANGO_RUN_USER.format(cmd='python manage.py {}'.format(cmd)))


@task
def pip():
    """Update installed python packages with pip"""
    with env.cd(env.base_path):
        env.run('pip install -r requirements.txt')


@task(name='populate-db')
def populate_db():
    """Populate the local DB with the data from the latest heroku backup"""
    # https://devcenter.heroku.com/articles/heroku-postgres-import-export

    confirm = prompt(
        'This will over write your local database.  '
        'Are you sure you want to continue? [y/N]'
    )
    if confirm.lower() not in ['y', 'yes']:
        return

    with env.cd(env.base_path):
        env.run('dropdb muckrock')
        env.run('heroku pg:pull DATABASE muckrock --app muckrock')


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
    with env.cd(env.base_path), warn_only():
        for folder in folders:
            env.run(
                'aws s3 sync s3://muckrock/{folder} '
                './muckrock/static/media/{folder}'.format(folder=folder)
            )


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
            result = local(
                'vagrant ssh-config | grep IdentityFile', capture=True
            )
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
        result = local('vagrant ssh-config | grep IdentityFile', capture=True)
    with settings(
        user='vagrant',
        host_string='127.0.0.1:2222',
        key_filename=result.split()[1]
    ):
        manage('migrate')


@task(name='update-staging-db')
def update_staging_db():
    """Update the staging database"""
    env.run('heroku maintenance:on --app muckrock-staging')
    env.run(
        'heroku pg:copy muckrock::DATABASE_URL DATABASE_URL --app muckrock-staging'
    )
    env.run('heroku maintenance:off --app muckrock-staging')


@task(name='pip-compile')
def pip_compile():
    """Update requirements"""
    with env.cd(os.path.join(env.base_path, 'pip')):
        env.run('pip-compile requirements.in')
        env.run('pip-compile dev-requirements.in')


@task(name='pip-upgrade')
def pip_upgrade():
    """Update and upgrade requirements"""
    with env.cd(os.path.join(env.base_path, 'pip')):
        env.run('pip-compile --upgrade requirements.in')
        env.run('pip-compile --upgrade dev-requirements.in')


@task(name='pip-sync')
def pip_sync():
    """sync requirements"""
    with env.cd(os.path.join(env.base_path, 'pip')):
        env.run('pip-sync requirements.txt dev-requirements.txt')


@task(name='npm-build')
def npm_build():
    """Build assets"""
    with env.cd(env.base_path):
        env.run(DJANGO_RUN.format(cmd='npm run build'))


@task(name='npm-watch')
def npm_watch():
    """Continuously build assets"""
    with env.cd(env.base_path):
        env.run(DJANGO_RUN.format(cmd='npm run watch'))


@task(name='npm-lint')
def npm_lint():
    """ESLint"""
    with env.cd(env.base_path):
        env.run(DJANGO_RUN.format(cmd='npm run lint'))
