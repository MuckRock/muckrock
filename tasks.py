# Third Party
from invoke import task

DOCKER_COMPOSE_RUN_OPT = "docker-compose -f local.yml run {opt} --rm {service} {cmd}"
DOCKER_COMPOSE_RUN_OPT_USER = DOCKER_COMPOSE_RUN_OPT.format(
    opt="-u $(id -u):$(id -g) {opt}", service="{service}", cmd="{cmd}"
)
DOCKER_COMPOSE_RUN = DOCKER_COMPOSE_RUN_OPT.format(
    opt="", service="{service}", cmd="{cmd}"
)
DJANGO_RUN = DOCKER_COMPOSE_RUN.format(service="muckrock_django", cmd="{cmd}")
DJANGO_RUN_USER = DOCKER_COMPOSE_RUN_OPT_USER.format(
    opt="", service="muckrock_django", cmd="{cmd}"
)

# Release
# --------------------------------------------------------------------------------


@task(aliases=["prod", "p"])
def production(c):
    """Merge your dev branch into master and push to production"""
    c.run("git pull origin dev")
    c.run("git checkout master")
    c.run("git pull origin master")
    c.run("git merge dev")
    c.run("git push origin master")
    c.run("git checkout dev")


@task
def staging(c):
    """Push out staging"""
    c.run("git push origin staging")


# Test
# --------------------------------------------------------------------------------


@task
def test(c, test_path="", reuse="0", capture=False):
    """Run all tests, or a specific subset of tests"""
    cmd = DOCKER_COMPOSE_RUN_OPT_USER.format(
        opt="-e REUSE_DB={reuse}".format(reuse=reuse),
        service="muckrock_django",
        cmd="./manage.py test {test_path} {capture} --settings=muckrock.settings.test".format(
            test_path=test_path, capture="--nologcapture" if not capture else ""
        ),
    )
    c.run(cmd)


@task
def coverage(c, settings="test", reuse="0"):
    """Run the tests and generate a coverage report"""
    cmd = DOCKER_COMPOSE_RUN_OPT_USER.format(
        opt="-e REUSE_DB={reuse}".format(reuse=reuse),
        service="muckrock_django",
        cmd="sh -c 'coverage erase && "
        'coverage run --branch --source muckrock --omit="*/migrations/*" '
        "manage.py test --settings=muckrock.settings.{settings} && "
        "coverage html -i'".format(settings=settings),
    )
    c.run(cmd)


# Code Quality
# --------------------------------------------------------------------------------


@task
def pylint(c):
    """Run the linter"""
    c.run(
        DJANGO_RUN.format(
            cmd="pylint muckrock --rcfile=config/pylint.conf "
            "--jobs=$(expr $(nproc) / 2)"
        )
    )


@task
def format(c):
    """Format your code"""
    c.run(
        DJANGO_RUN_USER.format(
            cmd='yapf -i -r --style config/style.yapf -e "*/migrations/*" '
            "-p muckrock && isort -sp config -rc muckrock"
        )
    )


# Run
# --------------------------------------------------------------------------------


@task
def runserver(c):
    """Run the development server"""
    c.run(
        DOCKER_COMPOSE_RUN_OPT.format(
            opt="--service-ports --use-aliases", service="muckrock_django", cmd=""
        )
    )


@task
def celeryworker(c):
    """Run a celery worker"""
    c.run(
        DOCKER_COMPOSE_RUN_OPT.format(
            opt="--use-aliases", service="muckrock_celeryworker", cmd=""
        )
    )


@task
def celerybeat(c):
    """Run the celery scheduler"""
    c.run(
        DOCKER_COMPOSE_RUN_OPT.format(opt="--use-aliases", service="muckrock_celerybeat", cmd="")
    )


@task
def shell(c, opts=""):
    """Run an interactive python shell"""
    c.run(
        DJANGO_RUN.format(cmd="python manage.py shell_plus {opts}".format(opts=opts)),
        pty=True,
    )


@task
def sh(c):
    """Run an interactive shell"""
    c.run(
        DOCKER_COMPOSE_RUN_OPT.format(
            opt="--use-aliases", service="muckrock_django", cmd="sh"
        ),
        pty=True,
    )


@task
def dbshell(c, opts=""):
    """Run an interactive db shell"""
    c.run(
        DJANGO_RUN.format(cmd="python manage.py dbshell {opts}".format(opts=opts)),
        pty=True,
    )


@task(aliases=["m"])
def manage(c, cmd):
    """Run a Django management command"""
    c.run(DJANGO_RUN_USER.format(cmd="python manage.py {cmd}".format(cmd=cmd)))


@task
def run(c, cmd):
    """Run a command directly on the docker instance"""
    c.run(DJANGO_RUN_USER.format(cmd=cmd))


@task
def npm(c, cmd):
    """Run an NPM command"""
    c.run(DJANGO_RUN.format(cmd="npm {cmd}".format(cmd=cmd)), pty=True)


@task
def heroku(c, staging=False):
    """Run commands on heroku"""
    if staging:
        app = "muckrock-staging"
    else:
        app = "muckrock"
    c.run("heroku run --app {app} python manage.py shell_plus".format(app=app))


# Dependency Management
# --------------------------------------------------------------------------------


@task(name="pip-compile")
def pip_compile(c, upgrade=False, package=None):
    """Run pip compile"""
    if package:
        upgrade_flag = "--upgrade-package {package}".format(package=package)
    elif upgrade:
        upgrade_flag = "--upgrade"
    else:
        upgrade_flag = ""
    c.run(
        DJANGO_RUN.format(
            cmd="pip-compile {upgrade_flag} pip/requirements.in &&"
            "pip-compile {upgrade_flag} pip/requirements-dev.in".format(
                upgrade_flag=upgrade_flag
            )
        )
    )


@task
def build(c):
    """Build the docker images"""
    c.run("docker-compose build")


# Database populating
# --------------------------------------------------------------------------------


@task(name="populate-db")
def populate_db(c, db_name="muckrock"):
    """Populate the local DB with the data from heroku"""
    # https://devcenter.heroku.com/articles/heroku-postgres-import-export

    confirm = raw_input(
        "This will over write your local database ({db_name}).  "
        "Are you sure you want to continue? [y/N] ".format(db_name=db_name)
    )
    if confirm.lower() not in ["y", "yes"]:
        return

    c.run(
        DJANGO_RUN.format(
            cmd='sh -c "dropdb {db_name} && '
            "heroku pg:pull DATABASE {db_name} --app muckrock "
            '--exclude-table-data=\\"public.reversion_version;public.foia_rawemail\\""'.format(
                db_name=db_name
            ),
        ),
    )


@task(name="update-staging-db")
def update_staging_db(c):
    """Update the staging database"""
    c.run("heroku maintenance:on --app muckrock-staging")
    c.run("heroku pg:copy muckrock::DATABASE_URL DATABASE_URL --app muckrock-staging")
    c.run("heroku maintenance:off --app muckrock-staging")


# Static file populating
# --------------------------------------------------------------------------------


@task(name="sync-aws")
def sync_aws(c):
    """Sync images from AWS to match the production database"""

    folders = [
        "account_images",
        "agency_images",
        "jurisdiction_images",
        "news_images",
        "news_photos/2019",
        "project_images",
    ]
    for folder in folders:
        c.run(
            "aws s3 sync s3://muckrock/{folder} ./muckrock/static/media/{folder}"
            .format(folder=folder)
        )


@task(name="sync-aws-staging")
def sync_aws_staging(c):
    """Sync images from AWS to match the production database"""

    folders = [
        "account_images",
        "agency_images",
        "jurisdiction_images",
        "news_images",
        "news_photos",
        "project_images",
    ]
    for folder in folders:
        c.run(
            "aws s3 sync s3://muckrock/{folder} "
            "s3://muckrock-staging//{folder} --acl public-read".format(folder=folder)
        )
