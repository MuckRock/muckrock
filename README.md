[ ![Codeship Status for MuckRock/muckrock](https://codeship.com/projects/c14392c0-630c-0132-1e4c-4ad47cf4b99f/status?branch=master)](https://codeship.com/projects/52228)

#. Check out the repository from github:
	#. Create a github account and have us give you access to the muckrock repository
	#. Check out the repository: `git clone git@github.com:MuckRock/muckrock.git`
    See more: https://help.github.com/articles/set-up-git#platform-all
    http://git-scm.com/documentation

#. Set the secrets
	#. Create a file `muckrock/local_settings.py` (`settings.py` should already be in this directory), which contains sensitive information that will not be checked into the repository
	#. We will send you the sensitive information in a secure manner.

#. Set up vagrant
	#. Install vagrant https://www.vagrantup.com/downloads.html
	#. cd to the `vm` directory and type: `vagrant up` (this will take a few minutes)
	#. Type `vagrant ssh` to ssh into the virtual machine

#. Sync and populate the database
	#. From within the virtual machine, `cd muckrock`
	#. Run `./manage.py syncdb` and create a superuser when asked to do so
	#. Run `./manage.py migrate`
	#. Run `./manage.py shell < myscript.py`

#. Run the test server
	#. Run `./manage.py runserver 0.0.0.0:8000`
	#. Navigate your web browser (from the hostt machine) to http://127.0.0.1:8000
	#. Run `./manage.py celeryd` to start a celery process to run delayed tasks
    	#. Run `python -m smtpd -n -c DebuggingServer localhost:1025` to start a dummy email server

#. Install the heroku toolbelt
	#. https://toolbelt.heroku.com/
	#. Set up a heroku remote branch so you can deploy your code: https://devcenter.heroku.com/articles/git#creating-a-heroku-remote

----

You should have a very bare MuckRock site running locally now.
The code checked out from github is synced between the virtual machine and your host machine, so you may edit the code using your favorite text editor locally while running the code from within the virtual machine.

