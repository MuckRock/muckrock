# MuckRock

[![Codeship Status for MuckRock/muckrock][codeship-img]][codeship]
[![codecov.io][codecov-img]][codecov]

MuckRock is a non-profit collaborative news site that gives you the tools to keep our government transparent and accountable.

## Install

### Software required

1. [docker][docker-install]
2. [docker-compose][docker-compose-install]
3. [python][python-install]
4. [invoke][invoke-install]

### Installation Steps

MuckRock depends on Squarelet for user authentication.  As the services need to communivate directly, the development environment for MuckRock depends on the development environment for Squarelet - the MuckRock docker containers will join Squarelet's docker network.  [Please install Squarelet and set up its development environment first][squarelet].

1. Check out the git repository - `git clone git@github.com:MuckRock/muckrock.git`
2. Enter the directory - `cd muckrock`
3. Run the dotenv initialization script - `python initialize_dotenvs.py`
This will create files with the environment variables needed to run the development environment.
4. Set up the javascript run `inv npm "install"` and `inv npm "run build"`
5. Start the docker images - `inv up`
This will build and start all of the docker images using docker-compose.  The invoke tasks specify the `local.yml` configuration file for docker-compose.  If you would like to run docker-compose commands directly, set the environment variable `export COMPSE_FILE=local.yml`.
6. Set `dev.muckrock.com` to point to localhost - `sudo echo "127.0.0.1   dev.muckrock.com" >> /etc/hosts`
7. Enter `dev.muckrock.com` into your browser - you should see the MuckRock home page.

## Docker info

The development environment is managed via [docker][docker] and [docker compose][docker-compose].  Please read up on them if you are unfmiliar with them.  The docker compose file is `local.yml`.  If you would like to run `docker-compose` commands directly, please run `export COMPOSE_FILE=local.yml` so you don't need to specify it in every command.

The containers which are run include the following:

* Django
This is the [Django][django] application

* PostgreSQL
[PostgreSQL][postgres] is the relational database used to store the data for the Django application

* Redis
[Redis][redis] is an in-memory datastore, used as a message broker for Celery as well as a cache backend for Django.

* Celery Worker
[Celery][celery] is a distrubuted task queue for Python, used to run background tasks from Django.  The worker is responsible for running the tasks.

* Celery Beat
The celery beat image is responsible for queueing up periodic celery tasks.

All systems can be brought up using `inv up`.  You can rebuild all images using `inv build`.  There are various other invoke commands for common tasks interacting with docker, which you can view in the `tasks.py` file.

### Squarelet Integration

If you have not yet created an RSA key on squarelet, please run: `manage.py creatersakey` from the squarelet command line.

Create the client on Squarelet by going to the Admin site - OpenID Connect Provider - Clients and adding a client.
* Name - set this to `MuckRock Dev`
* Owner - you may leave this blank or set it to your user account.
* Client Type - `Confidential`
* Response types - `code (Authorization Code Flow)`
* Redirect URIs - `http://dev.muckrock.com/accounts/complete/squarelet` (you may optionally add `http://dev.foiamachine.org/accounts/complete/squarelet` on a second line if you will be developing FOIAMachine)
* JWT Algorithm - `RS256`
* Require Consent? - Unchecked
* Reuse Consent? - Checked
* Client ID - This will be filled in automatically upon saving, and will be copied into the `.envs/.local/.django` file.
* Client SECRET - This will be filled in automatically upon saving, and will be copied into the `.envs/.local/.django` file.
* Scopes - `read_user write_user read_organization write_charge read_auth_token`
* Post Logout Redirect URIs - `http://dev.muckrock.com/` (you may optionally add `http://dev.foiamachine.org/` on a second line if you will be developing FOIAMachine)
* Add a client profile and set the Webhook URL - `http://dev.muckrock.com/squarelet/webhook/`

Click save and continue editing.  In `.envs/.local/.django` set the following environment variables:
* `SQUARELET_KEY` to the value of Client ID
* `SQUARELET_SECRET` to the value of Client SECRET

You should now be able to log in to MuckRock using your Squarelet account.

### Networking Setup

The MuckRock development environment will join Squarelet's environments docker network, so that the services can coexist.  Please see the README file from Squarelet for more information.

### Environment Variables

The application is configured with environment variables in order to make it easy to customize behavior in different environments (dev, testing, staging, production, etc).  Some of this environment variables may be sensitive information, such as passwords or API tokens to various services.  For this reason, they are not to be checked in to version control.  In order to assist with the setup of a new development environment, a script called `initialize_dotenvs.py` is provided which will create the files in the expected places, with the variables included.  Those which require external accounts will generally be left blank, and you may sign up for an account to use for development and add your own credentials in.  You may also add extra configuration here as necessary for your setup.

## Invoke info

Invoke is a task execution library.  It is used to allow easy access to common commands used during development.  You may look through the file to see the commands being run.  I will go through some of the more important ones here.

### Release
`inv prod` will merge your dev branch into master, and push to GitHub, which will trigger [CodeShip][codeship] to release it to Heroku, as long as all code checks pass.  The production site is currently hosted at [https://www.muckrock.com/](https://www.muckrock.com/).
`inv staging` will push the staging branch to GitHub, which will trigger CodeShip to release it to Heroku, as long as all code checks pass.  The staging site is currently hosted at [https://muckrock-staging.herokuapp.com/](https://muckrock-staging.herokuapp.com/).

### Test
`inv test` will run the test suite.  To reuse the database, pass it the `-r=1` option.
`inv coverage` will run the test suite and generate a coverage report at `htmlcov/index.html`.

The test suite will be run on CodeShip prior to releasing new code.  Please ensure your code passes all tests before trying to release it.  Also please add new tests if you develop new code.

### Code Quality
`inv pylint` will run [pylint][pylint].  It is possible to silence checks, but should only be done in instances where pylint is misinterpreting the code.
`inv format` will format the code using the [yapf][yapf] code formatter.

Both linting and formatting are checked on CodeShip.  Please ensure your code is linted and formatted correctly before attempting to release changes.

### Run
`inv up` will start all containers in the background.
`inv runserver` will run the Django server in the foreground.  Be careful to not have multiple Django servers running at once.  Running the server in the foreground is mainly useful for situations where you would like to use an interactive debugger within your application code.
`inv shell` will run an interactive python shell within the Django environment.
`inv sh` will run a bash shell within the Django docker comtainer.
`inv dbshell` will run a postgresql shell.
`inv manage` will allow you to easily run Django manage.py commands.
`inv npm` will allow you to run NPM commands.  `inv npm "run build"` should be run to rebuild assets if any javascript or CSS is changed. If you will be editing a lot of javascript or CSS, you can run `inv npm "run watch"`.
`inv heroku` will open a python shell on Heroku.

## Pip Tools

Python dependencies are managed via [pip-tools][pip-tools].  This allows us to keep all of the python dependencies (including underling dependencies) pinned, to allow for consistent execution across development and production environments.

The corresponding files are kept in the `pip` folder.  There are `requirements` and `dev-requirements` files.  `requirements` will be installed in all environments, while `dev-requirements` will only be installed for local development environments.  It can be used for code only needed during develpoment, such as testing.  For each environment there is an `.in` file and a `.txt` file.  The `.in` file is the input file - you list your direct dependencies here.  You may specify version constraints here, but do not have to.

Running `inv pip-compile` will compile the `.in` files to the corresponding `.txt` files.  This will pin all of the dependencies, and their dependencies, to the latest versions that meet any constraints that have been put on them.  You should run this command if you need to add any new dependencies to an `.in` files.  Please keep the `.in` files sorted.  After running `inv pip-compile`, you will need to run `inv build` to rebuild the docker images with the new dependencies included.

## FOIAMachine

FOIAMachine is our free FOIA filing tool, that allows you to track your requests while requiring you to manually handle all of the message sending and receiving.  It is run off of the same code base as MuckRock.  To access it, set `dev.foiamachine.org` to point to localhost - `sudo echo "127.0.0.1   dev.foiamachine.org" >> /etc/hosts`.  Then pointing your browser to `dev.foiamachine.org` will take you to FOIAMachine - the correst page is shown depending on the domain host.

## Update search index

MuckRock uses [watson][watson] for search.  The index should stay updated. If a new model is registered with watson, then build the index (`fab manage:buildwatson`). This command should be run on any staging or production servers when pushing code that updates the registration.


[docker]: https://docs.docker.com/
[docker-compose]: https://docs.docker.com/compose/
[django]: https://www.djangoproject.com/
[postgres]: https://www.postgresql.org/
[redis]: https://redis.io/
[celery]: https://docs.celeryproject.org/en/latest/
[invoke]: http://www.pyinvoke.org/
[docker-install]: https://docs.docker.com/install/
[docker-compose-install]: https://docs.docker.com/compose/install/
[invoke-install]: http://www.pyinvoke.org/installing.html
[python-install]: https://www.python.org/downloads/
[codeship]: https://app.codeship.com/projects/296009
[pylint]:  https://www.pylint.org/
[pip-tools]: https://github.com/jazzband/pip-tools
[codeship]: https://codeship.com/projects/52228
[codeship-img]: https://codeship.com/projects/c14392c0-630c-0132-1e4c-4ad47cf4b99f/status?branch=master
[codecov]: https://codecov.io/github/MuckRock/muckrock?branch=master
[codecov-img]:https://codecov.io/github/MuckRock/muckrock/coverage.svg?token=SBg37XM3j1&branch=master
[squarelet]: https://github.com/muckrock/squarelet/
[yapf]: https://github.com/google/yapf
[watson]: https://github.com/etianen/django-watson
