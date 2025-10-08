# Standard Library
import os

# Third Party
from invoke import task


DOCKER_COMPOSE_RUN_OPT = f"docker compose -f local.yml run {{opt}} --rm {{service}} {{cmd}}"

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
    c.run("git push origin dev")


@task
def staging(c):
    """Push out staging"""
    c.run("git push origin staging")


# Test
# --------------------------------------------------------------------------------


@task
def test(c, path="muckrock", create_db=False, ipdb=False, warnings=False):
    """Run the test suite"""
    create_switch = "--create-db" if create_db else ""
    ipdb_switch = "--pdb --pdbcls=IPython.terminal.debugger:Pdb" if ipdb else ""
    warnings = "-e PYTHONWARNINGS=always" if warnings else ""

    c.run(
        DOCKER_COMPOSE_RUN_OPT_USER.format(
            opt=f"-e DJANGO_SETTINGS_MODULE=muckrock.settings.test {warnings}",
            service="muckrock_django",
            cmd=f"pytest {create_switch} {ipdb_switch} {path}",
        ),
        pty=True,
    )


@task
def test_codeship(c, v=1):
    c.run("pytest --create-db --ds=muckrock.settings.codeship muckrock")


@task
def coverage(c, settings="test", reuse="0", codeship=False):
    """Run the tests and generate a coverage report"""
    if codeship:
        settings = "codeship"
    cmds = [
        "coverage erase",
        'coverage run --branch --source muckrock --omit="*/migrations/*" '
        f"manage.py test --settings=muckrock.settings.{settings}",
        # "coverage html -i",
    ]
    if codeship:
        for cmd in cmds:
            c.run(cmd)
    else:
        sh_cmd = " && ".join(cmds)
        cmd = DOCKER_COMPOSE_RUN_OPT_USER.format(
            opt="-e REUSE_DB={reuse}".format(reuse=reuse),
            service="muckrock_django",
            cmd=f"sh -c '{sh_cmd}'",
        )
        c.run(cmd)


# Code Quality
# --------------------------------------------------------------------------------


@task
def pylint(c, codeship=False):
    """Run the linter"""
    cmd = "pylint muckrock"
    if codeship:
        c.run(cmd)
    else:
        c.run(
            DOCKER_COMPOSE_RUN_OPT.format(
                opt="-e DJANGO_SETTINGS_MODULE=muckrock.settings.local",
                service="muckrock_django",
                cmd=cmd,
            )
        )


@task
def format(c):
    """Format your code"""
    c.run(
        DJANGO_RUN_USER.format(
            cmd="black muckrock --exclude migrations\\|vendor\\|gloo && "
            "isort --recursive muckrock --skip ./muckrock/gloo"
        )
    )


@task(name="format-check")
def format_check(c):
    """Check your code format"""
    c.run(
        DJANGO_RUN_USER.format(
            cmd="black --check muckrock --exclude migrations\\|vendor\\|gloo && "
            "isort --check-only --recursive muckrock --skip ./muckrock/gloo"
        )
    )


# Run
# --------------------------------------------------------------------------------


@task
def up(c):
    """Start the docker images"""
    c.run(f"docker compose up -d ")


@task
def down(c):
    """Shut down the docker images"""
    c.run(f"docker compose down")


@task
def runserver(c):
    """Run the development server"""
    c.run(
        DOCKER_COMPOSE_RUN_OPT.format(
            opt="--service-ports --use-aliases", service="muckrock_django", cmd=""
        ),
        pty=True,
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
        DOCKER_COMPOSE_RUN_OPT.format(
            opt="--use-aliases", service="muckrock_celerybeat", cmd=""
        )
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
    c.run(
        "heroku run --app {app} python manage.py shell_plus".format(app=app), pty=True
    )


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
            "pip-compile {upgrade_flag} pip/dev-requirements.in".format(
                upgrade_flag=upgrade_flag
            )
        )
    )


@task
def build(c):
    """Build the docker images"""
    c.run("docker compose build")


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
            "aws s3 sync s3://muckrock/{folder} ./muckrock/static/media/{folder}".format(
                folder=folder
            )
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
