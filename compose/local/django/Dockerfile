# # syntax = docker/dockerfile:experimental
FROM python:3.9.19

ENV PYTHONUNBUFFERED 1

RUN apt-get update && apt-get install -y --no-install-recommends \
  # psycopg2 dependencies
  #&& apt-get install build-deps gcc python2-dev musl-dev \
  #&& apt-get install postgresql-dev \
  # Pillow dependencies
  #&& apt-get install jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev \
  # CFFI dependencies
  #&& apt-get install libffi-dev py-cffi \
  # Translations dependencies
  #&& apt-get install gettext \
  # https://docs.djangoproject.com/en/dev/ref/django-admin/#dbshell
  postgresql-client \
  # for downloading dependencies from git
  #&& apt-get install git \
  # xml parser
  #&& apt-get install libxml2-dev libxslt-dev \
  # for numpy / scipy
  #&& apt-get install openblas-dev gfortran g++ \
  # memcahced
  libmemcached-dev \
  # for imagediet
  #&& apt-get install libmagic
  ghostscript

# set up makecert root CA
RUN curl http://localhost/rootCA.pem > /usr/local/share/ca-certificates/rootCA.crt && update-ca-certificates


RUN apt-get update && apt-get install -y libsodium-dev
ENV SODIUM_INSTALL=system

# install NVM
ENV NVM_DIR /usr/local/nvm
ENV NODE_VERSION 18.16.0

RUN mkdir $NVM_DIR
RUN curl https://raw.githubusercontent.com/nvm-sh/nvm/v0.39.3/install.sh | bash \
    && . $NVM_DIR/nvm.sh \
    && nvm install $NODE_VERSION \
    && nvm alias default $NODE_VERSION \
    && nvm use default

ENV NODE_PATH $NVM_DIR/v$NODE_VERSION/lib/node_modules
ENV PATH      $NVM_DIR/versions/node/v$NODE_VERSION/bin:$PATH

# heroku cli
RUN curl https://cli-assets.heroku.com/install.sh | sh

# Requirements are installed here to ensure they will be cached.
COPY ./pip /pip
#RUN --mount=type=cache,target=/root/.cache/pip pip install -r /pip/requirements.txt
#RUN --mount=type=cache,target=/root/.cache/pip pip install -r /pip/dev-requirements.txt
# Update setuptools
RUN pip install --upgrade setuptools>=61.0.0
# Use pre-built wheel
RUN pip install wheel
# Install requirements
RUN pip install -r /pip/requirements.txt
RUN pip install -r /pip/dev-requirements.txt

COPY ./compose/production/django/entrypoint /entrypoint
RUN sed -i 's/\r//' /entrypoint
RUN chmod +x /entrypoint

COPY ./compose/local/django/start /start
RUN sed -i 's/\r//' /start
RUN chmod +x /start

COPY ./compose/local/django/celery/worker/start /start-celeryworker
RUN sed -i 's/\r//' /start-celeryworker
RUN chmod +x /start-celeryworker

COPY ./compose/local/django/celery/beat/start /start-celerybeat
RUN sed -i 's/\r//' /start-celerybeat
RUN chmod +x /start-celerybeat

WORKDIR /app

ENTRYPOINT ["/entrypoint"]
