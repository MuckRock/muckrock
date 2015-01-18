
1. Check out the repository from github:
	1. Create a github account and have us give you access to the muckrock repository
	2. Check out the repository: `git clone git@github.com:MuckRock/muckrock.git`
    See more: https://help.github.com/articles/set-up-git#platform-all
    http://git-scm.com/documentation

2. Set the secrets
	1. Create a file muckrock/local_settings.py (settings.py should already be in this directory), which contains sensitive information that will not be checked into the repository
	2. We will send you the sensitive information in a secure manner

3. Set up vagrant
	1. Install vagrant https://www.vagrantup.com/downloads.html
	2. cd to the `vm` directory and type: `vagrant up` (this will take a few minutes)
	3. Type `vagrant ssh` to ssh into the virtual machine

4. Sync the database
	1. From within the virtual machine, `cd muckrock`
	2. Run `./manage.py syncdb` and create a superuser when asked to do so
	3. Run `./manage.py migrate`

5. Run the test server
	1. Run `./manage.py runserver 0.0.0.0:8000`
	2. Navigate your web browser (from the hostt machine) to http://127.0.0.1:8000
	3. Run `./manage.py celeryd` to start a celery process to run delayed tasks

6. Install the heroku toolbelt
	1. https://toolbelt.heroku.com/
	2. Set up a heroku remote branch so you can deploy your code: https://devcenter.heroku.com/articles/git#creating-a-heroku-remote

----

You should have a very bare MuckRock site running locally now.  Putting some documents into the database will help flesh out the site.  The code checked out from github is synced between the virtual machine and your host machine, so you may edit the code using your favorite text editor locally while running the code from within the virtual machine.

