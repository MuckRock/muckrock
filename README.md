# MuckRock

[![Codeship Status for MuckRock/muckrock][codeship-img]][codeship]
[![codecov.io][codecov-img]][codecov]

## Software Versions

The following instructions were tested to work with the following software versions:

1. Vagrant 1.9.3
2. VirtualBox 5.0.32

## Install

1. Check out the git repository - `git clone git@github.com:MuckRock/muckrock.git`
2. Set up your virtual machine
    1. Install [Vagrant][vagrant] and [VirtualBox][virtualbox]
    2. Run `vagrant up` (this will take a while)
    3. Run `vagrant ssh` to ssh into the virtual machine
3. You may edit the file `~/muckrock/.settings.sh` if you would like to set up accounts and passwords for any external providers - you should be able to develop without these unless you specifically need to use and test them

You should have a fully populated MuckRock site set up locally now.
The code checked out from GitHub is synced between the virtual machine and your host machine, so you may edit the code using your favorite text editor locally while running the code from within the virtual machine.

## Develop

### Run

1. The following commands should be run from the MuckRock directory inside the virtual machine: `cd muckrock`
2. Run `npm run build` to rebuild the javascript and css
3. Run `fab mail &` to start a background email server
4. Run `fab celery &` to start a background task queue
5. Run `fab runserver` to start a server instance
6. Navigate your web browser (from the host machine) to `localhost:8000`
7. You may log in as a super user with the username `super` and password `abc`

### Update search index

The index should stay updated. If a new model is registered with watson, then build the index (`fab manage:buildwatson`). This command should be run on any staging or production servers when pushing code that updates the registration.

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
