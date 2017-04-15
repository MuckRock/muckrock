# MuckRock

[![Codeship Status for MuckRock/muckrock][codeship-img]][codeship]
[![codecov.io][codecov-img]][codecov]

# Fedora Core 26 Notes

* sudo yum install postgresql-server.x86_64
* sudo yum install postgresql-devel
* sudo systemctl enable postgresql
* sudo postgresql-setup initdb (or sudo postgresql-setup --initdb --unit postgresql)
* service postgresql start
* sudo su -l postgres
```
createuser --no-superuser --no-createdb --no-createrole --pwprompt muckrockuser
createdb --owner muckrockuser muckrock
exit
```
* sudo vim /var/lib/pgsql/data/postgresql.conf
** uncomment and set ```listen_addresses``` to ```listen_addresses = '*'```
* sudo vim /var/lib/pgsql/data/pg_hba.conf and change the lines to trust incoming connections

```
# "local" is for Unix domain socket connections only
local   all             all                                     trust
# IPv4 local connections:
host    all             all             127.0.0.1/32            trust
# IPv6 local connections:
host    all             all             ::1/128                 trust
```
* service postgresql restart
* pip install -r requirements
* npm install
* npm run watch
* create a local file in muckrock/settings named mylocal.py and add the following:
```
from muckrock.settings.base import *

DEBUG = True
SITE_ID = 2

SECRET_KEY = "NONUNIQUEHIDDENKEY"

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': 'muckrock',
        'PORT': '5432', # PgBouncer port
        'HOST': 'localhost',
        'USER': 'muckrockuser',
        'PASSWORD': ''
    }
}

```
* python manage.py migrate --settings=muckrock.settings.mylocal
* psql -Umuckrockuser muckrock
```
insert into django_site values (2, 'foiamachine.org', 'foiamachine.org');
```
* add the following line to /etc/hosts
```
127.0.0.1   dev.foiamachine.org
```
* python manage.py runserver 0:8000 --settings=muckrock.settings.mylocal
* visit http://dev.foiamachine.org:8000/

### additional steps
* python manage.py loaddata muckrock/jurisdiction/fixtures/jurisdiction.json --settings=muckrock.settings.mylocal
* python manage.py loaddata muckrock/agency/fixtures/agency_types.json --settings=muckrock.settings.mylocal
* python manage.py loaddata muckrock/agency/fixtures/test_agencies.json --settings=muckrock.settings.mylocal
* python manage.py import_fm --settings=muckrock.settings.mylocal

## Install

1. Check out the git repository
  1. `git clone git@github.com:MuckRock/muckrock.git`

2. Set up your virtual machine
  1. Install [Vagrant][vagrant] and [VirtualBox][virtualbox]
  2. Run `vagrant up` (this will take a while)
  3. Run `vagrant ssh` to ssh into the virtual machine

3. Set the secrets
  1. `cd muckrock`
  2. `touch .settings.sh`
  3. The `.settings.sh` file should **never** be checked in to the repository.
  4. We will send you the (definitely) sensitive information in a (probably) secure manner.
  5. Inside your VM, run `source ~/.bashrc`.

4. Populate the database and sync the files from AWS inside the virtual machine (Run all commands inside the VM)
  1. Restart the database to pick up correct permissions, `sudo service postgresql`
  2. Login to heroku toolbelt, `heroku login`
  3. Pull the database, `fab populate-db`
  4. Pull files from S3, `fab sync-aws`

5. Build the search index
  1. Install watson with `fab manage:installwatson`
  2. Build the search index with `fab manage:buildwatson`
  3. After this, the index should stay updated. If a new model is registered with watson, then build the index (step 2). This command should be run on any staging or production servers when pushing code that updates the registration.

You should have a fully populated MuckRock site running locally now.
The code checked out from GitHub is synced between the virtual machine and your host machine, so you may edit the code using your favorite text editor locally while running the code from within the virtual machine.

## Develop

### Run

1. Run `npm run watch &` to start a background Webpack instance
1. Run `fab mail &` to start a background email server
2. Run `fab celery &` to start a background task queue
3. Run `fab runserver` to start a server instance
4. Navigate your web browser (from the host machine) to `localhost:8000`

### Add dependencies

To add a dependency, list it in one of the two `.in` files inside the `pip` folder.
The `dev-requirements.in` file is used for local libraries, like testing suites.
The `requirements.in` file is used for production libraries—stuff that should run on Heroku.

When entering a dependency, make sure to append a comment explaining its purpose.
This is hugely helpful when it comes to navigating dependency hell.

After entering your dependency in the `.in` file, run `fab pip-compile` to canonize your change.

### Test and lint

* Test your code in one of two ways:
    * Run `fab test` to run all the tests.
    * Run `fab test:muckrock.<app>` to test a particular application.
    * Run `fab test:muckrock,1` to reuse the database between tests, which saves a ton of time.
* Lint your Python by running `fab pylint`.
* Lint your Javascript by running `npm run lint`.

## Deploy

The `master` branch represents our product code. `master` should only ever be updated by merges from the `dev` branch, which tracks it. New features should be branched from `dev`, then merged back into `dev` once they are tested and linted. Any feature branch pushed to GitHub will be evaluated by Codeship. If the `staging` branch is pushed, the [staging server][staging] will be updated. If the `master` branch is pushed, the [production server][production] will be updated.

[codeship]: https://codeship.com/projects/52228
[codeship-img]: https://codeship.com/projects/c14392c0-630c-0132-1e4c-4ad47cf4b99f/status?branch=master
[staging]: http://muckrock-staging.herokuapp.com
[production]: https://www.muckrock.com
[vagrant]: https://www.vagrantup.com/downloads.html
[virtualbox]: https://www.virtualbox.org
[codecov-img]:https://codecov.io/github/MuckRock/muckrock/coverage.svg?token=SBg37XM3j1&branch=master
[codecov]: https://codecov.io/github/MuckRock/muckrock?branch=master
