# puppet-python [![Build Status](https://travis-ci.org/stankevich/puppet-python.svg?branch=master)](https://travis-ci.org/stankevich/puppet-python)

Puppet module for installing and managing python, pip, virtualenvs and Gunicorn virtual hosts.

**Version 1.1.x Notes**

Version `1.1.x` makes several fundamental changes to the core of this module, adding some additional features, improving performance and making operations more robust in general.

Please note that several changes have been made in `v1.1.x` which make manifests incompatible with the previous version.  However, modifying your manifests to suit is trivial.  Please see the notes below.

Currently, the changes you need to make are as follows:

* All pip definitions MUST include the owner field which specifies which user owns the virtualenv that packages will be installed in.  Adding this greatly improves performance and efficiency of this module.
* You must explicitly specify pip => true in the python class if you want pip installed.  As such, the pip package is now independent of the dev package and so one can exist without the other.

## Installation

```shell
git submodule add https://github.com/stankevich/puppet-python.git /path/to/python
```
**OR**

``` shell
puppet module install stankevich-python
```

## Usage

### python

Installs and manages python, python-pip, python-dev, python-virtualenv and Gunicorn.

**version** - Python version to install. Default: system default

**pip** - Install python-pip. Default: true

**dev** - Install python-dev. Default: false

**virtualenv** - Install python-virtualenv. Default: false

**gunicorn** - Install Gunicorn. Default: false

**manage_gunicorn** - Allow Installation / Removal of Gunicorn. Default: true

```puppet
  class { 'python' :
    version    => 'system',
    pip        => true,
    dev        => true,
    virtualenv => true,
    gunicorn   => true,
  }
```

### python::pip

Installs and manages packages from pip.

**pkgname** - the name of the package to install. Required.

**ensure** - present/latest/absent. You can also specify the version. Default: present

**virtualenv** - virtualenv to run pip in. Default: system (no virtualenv)

**url** - URL to install from. Default: none

**owner** - The owner of the virtualenv to ensure that packages are installed with the correct permissions (must be specified). Default: root

**proxy** - Proxy server to use for outbound connections. Default: none

**environment** - Additional environment variables required to install the packages. Default: none

**egg** - The egg name to use. Default: `$name` of the class, e.g. cx_Oracle

**install_args** - Array of additional flags to pass to pip during installaton. Default: none

**uninstall_args** - Array of additional flags to pass to pip during uninstall. Default: none

**timeout** - Timeout for the pip install command. Defaults to 1800.
```puppet
  python::pip { 'cx_Oracle' :
    pkgname       => 'cx_Oracle',
    ensure        => '5.1.2',
    virtualenv    => '/var/www/project1',
    owner         => 'appuser',
    proxy         => 'http://proxy.domain.com:3128',
    environment   => 'ORACLE_HOME=/usr/lib/oracle/11.2/client64',
    install_args  => ['-e'],
    timeout       => 1800,
   }
```

### python::requirements

Installs and manages Python packages from requirements file.

**virtualenv** - virtualenv to run pip in. Default: system-wide

**proxy** - Proxy server to use for outbound connections. Default: none

**owner** - The owner of the virtualenv to ensure that packages are installed with the correct permissions (must be specified). Default: root

**src** - The `--src` parameter to `pip`, used to specify where to install `--editable` resources; by default no `--src` parameter is passed to `pip`.

**group** - The group that was used to create the virtualenv.  This is used to create the requirements file with correct permissions if it's not present already.

```puppet
  python::requirements { '/var/www/project1/requirements.txt' :
    virtualenv => '/var/www/project1',
    proxy      => 'http://proxy.domain.com:3128',
    owner      => 'appuser',
    group      => 'apps',
  }
```

### python::virtualenv

Creates Python virtualenv.

**ensure** - present/absent. Default: present

**version** - Python version to use. Default: system default

**requirements** - Path to pip requirements.txt file. Default: none

**proxy** - Proxy server to use for outbound connections. Default: none

**systempkgs** - Copy system site-packages into virtualenv. Default: don't

**distribute** - Include distribute in the virtualenv. Default: true

**venv_dir** - The location of the virtualenv if resource path not specified. Must be absolute path. Default: resource name

**owner** - Specify the owner of this virtualenv

**group** - Specify the group for this virtualenv

**index** - Base URL of Python package index. Default: none

**cwd** - The directory from which to run the "pip install" command. Default: undef

**timeout** - The maximum time in seconds the "pip install" command should take. Default: 1800

```puppet
  python::virtualenv { '/var/www/project1' :
    ensure       => present,
    version      => 'system',
    requirements => '/var/www/project1/requirements.txt',
    proxy        => 'http://proxy.domain.com:3128',
    systempkgs   => true,
    distribute   => false,
    venv_dir     => '/home/appuser/virtualenvs',
    owner        => 'appuser',
    group        => 'apps',
    cwd          => '/var/www/project1',
    timeout      => 0,
  }
```

### python::gunicorn

Manages Gunicorn virtual hosts.

**ensure** - present/absent. Default: present

**virtualenv** - Run in virtualenv, specify directory. Default: disabled

**mode** - Gunicorn mode. wsgi/django. Default: wsgi

**dir** - Application directory.

**bind** - Bind on: 'HOST', 'HOST:PORT', 'unix:PATH'. Default: `unix:/tmp/gunicorn-$name.socket` or `unix:${virtualenv}/${name}.socket`

**environment** - Set ENVIRONMENT variable. Default: none

**appmodule** - Set the application module name for gunicorn to load when not using Django. Default: `app:app`

**osenv** - Allows setting environment variables for the gunicorn service. Accepts a hash of 'key': 'value' pairs. Default: false

**timeout** - Allows setting the gunicorn idle worker process time before being killed. The unit of time is seconds. Default: 30

**template** - Which ERB template to use. Default: python/gunicorn.erb

```puppet
  python::gunicorn { 'vhost' :
    ensure      => present,
    virtualenv  => '/var/www/project1',
    mode        => 'wsgi',
    dir         => '/var/www/project1/current',
    bind        => 'unix:/tmp/gunicorn.socket',
    environment => 'prod',
    appmodule   => 'app:app',
    osenv       => { 'DBHOST' => 'dbserver.example.com' },
    timeout     => 30,
    template    => 'python/gunicorn.erb',
  }
```

## Authors

[Sergey Stankevich](https://github.com/stankevich)
[Shiva Poudel](https://github.com/shivapoudel)
[Ashley Penney](https://github.com/apenney)
[Marc Fournier](https://github.com/mfournier)
[Fotis Gimian](https://github.com/fgimian)
