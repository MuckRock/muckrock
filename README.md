# MuckRock

[![Codeship Status for MuckRock/muckrock][codeship-img]][codeship]
[![codecov.io](codecov-img)](codecov)

## Install

1. Set up your virtual machine
  1. Install [Vagrant][vagrant] and [VirtualBox][virtualbox]
  2. Run `vagrant up` (this will take a while)
  3. Run `vagrant ssh` to ssh into the virtual machine

2. Set the secrets
  1. `cd muckrock`
  2. `touch local_settings.py` (`settings.py` should already be in this directory).
  2. The `local_settings.py` file should never be checked in to the repository.
  3. We will send you the (definitely) sensitive information in a (probably) secure manner.

3. Sync and populate the database inside the virtual machine
  1. From within the virtual machine, `cd muckrock`
  2. Run `./manage.py syncdb` and create a superuser when asked to do so
  3. Run `./manage.py migrate`
  4. ~~Run `fab populate-db` to populate the DB~~ (Broken)

4. Run the test server inside the virtual machine
  1. Run `fab mail &` to start a background email server
  2. Run `fab celery &` to start a background task queue
  3. Run `fab runserver` to start a server instance
  4. Navigate your web browser (from the host machine) to `localhost:8000`

You should have a very bare MuckRock site running locally now.
The code checked out from GitHub is synced between the virtual machine and your host machine, so you may edit the code using your favorite text editor locally while running the code from within the virtual machine. To run the server again, just follow step 4.

## Test and lint

* Test your code in one of two ways:
    * Run `fab test` to run all the tests.
    * Run `fab test:muckrock.<app>` to test a particular application.
    * Run `fab test:muckrock,1` to reuse the database between tests, which saves a ton of time.
* Lint your code by running `fab pylint`.

## Push and deploy

The `master` branch represents our product code. `master` should only ever be updated by merges from the `dev` branch, which tracks it. New features should be branched from `dev`, then merged back into `dev` once they are tested and linted. Any feature branch pushed to GitHub will be evaluated by Codeship. If the `staging` branch is pushed, the [staging server][staging] will be updated. If the `master` branch is pushed, the [production server][production] will be updated.

[codeship]: https://codeship.com/projects/52228
[codeship-img]: https://codeship.com/projects/c14392c0-630c-0132-1e4c-4ad47cf4b99f/status?branch=master
[staging]: http://muckrock-staging.herokuapp.com
[production]: https://www.muckrock.com
[vagrant]: https://www.vagrantup.com/downloads.html
[virtualbox]: https://www.virtualbox.org
[codecov-img]:https://codecov.io/github/MuckRock/muckrock/coverage.svg?token=SBg37XM3j1&branch=master
[codecov]: https://codecov.io/github/MuckRock/muckrock?branch=master
