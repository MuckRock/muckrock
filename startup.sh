source ~/.virtualenvs/muckrock/bin/activate
postgres -D /usr/local/var/postgres &
python manage.py runserver
