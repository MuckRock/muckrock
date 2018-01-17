
class muckrock {

	file { '/home/vagrant/.bashrc':
		ensure => present,
		source => "puppet:///modules/muckrock/bashrc",
		owner  => "vagrant",
		group  => "vagrant",
	}
	file { '/home/vagrant/.git-prompt.sh':
		ensure => present,
		source => "puppet:///modules/muckrock/git-prompt.sh",
		owner  => "vagrant",
		group  => "vagrant",
	}
	file { '/home/vagrant/.dir_colors':
		ensure => present,
		source => "puppet:///modules/muckrock/dir_colors",
		owner  => "vagrant",
		group  => "vagrant",
	}
	file { '/home/vagrant/ve':
		ensure => directory,
		owner  => "vagrant",
		group  => "vagrant",
	}
	file { '/home/vagrant/muckrock/.settings.sh':
		ensure => present,
		source => "puppet:///modules/muckrock/settings.sh",
		owner  => "vagrant",
		group  => "vagrant",
	}

	exec { "generate secret key":
		user    => 'vagrant',
		command => "/usr/bin/python -c 'import random; print \"export SECRET_KEY=\\x27%s\\x27\" % \"\".join([random.SystemRandom().choice(\"abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)\") for i in range(50)])' > .secret_key.sh",
		cwd     => '/home/vagrant/muckrock',
		creates => '/home/vagrant/muckrock/.secret_key.sh',
	}


    class { 'apt':
        update => {
            frequency => 'always',
        },
    }

    apt::ppa { 'ppa:ubuntugis/ppa': }

	package { 'gdal-bin':
		ensure => installed,
	}

	package { 'ruby-dev':
		ensure => installed,
	} ->
	package { 'sass':
		ensure   => installed,
		provider => 'gem',
	}
	package { 'git':
		ensure => installed,
	} ->
	package { 'libmemcached-dev':
		ensure => installed,
	} ->
	package { 'libxml2-dev':
		ensure => installed,
	} ->
	package { 'libxslt1-dev':
		ensure => installed,
	} ->
	package { 'libevent-dev':
		ensure => installed,
	} ->
	package { 'libpq-dev':
		ensure => installed,
	} ->
	package { 'zlib1g-dev':
		ensure => installed,
	} ->
	package { 'liblapack-dev':
		ensure => installed,
	} ->
	package { 'libblas-dev':
		ensure => installed,
	} ->
	package { 'gfortran':
		ensure => installed,
	}

	package { 'awscli':
		ensure => installed,
	}

	package { 'graphviz':
		ensure => installed,
	}

	package { 'fabric':
		ensure => installed,
	}

	# python

	class { 'python':
		version    => "system",
		pip        => true,
		dev        => true,
		virtualenv => true,
	}

	package { 'libjpeg-dev':
		ensure => installed,
	} ->
	python::virtualenv { '/home/vagrant/ve/muckrock' :
		ensure       => present,
		owner        => 'vagrant',
		group        => 'vagrant',
		requirements => '/home/vagrant/muckrock/requirements.txt',
		require      => [File['/home/vagrant/ve'],
						Package['zlib1g-dev'],],
	} ->
	python::requirements {'/home/vagrant/muckrock/pip/dev-requirements.txt' :
		virtualenv  => '/home/vagrant/ve/muckrock',
		owner       => 'vagrant',
		group       => 'vagrant',
		forceupdate => true,
		before      => Exec['migrate'],
	}

	# nodejs

	class { 'nvm':
		user                => 'vagrant',
		install_node        => '5.6.0',
		manage_dependencies => false,
		profile_path        => '/home/vagrant/.nvm.sh',
		require             => Package['sass'],
	} ->
	exec { 'install node requirements':
		user    => 'vagrant',
        path    => '/home/vagrant/.nvm/versions/node/v5.6.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
		command => '/home/vagrant/.nvm/versions/node/v5.6.0/bin/npm install',
		cwd     => '/home/vagrant/muckrock',
		creates => '/home/vagrant/muckrock/node_modules',
	} ->
	exec { 'npm build':
		user    => 'vagrant',
        path    => '/home/vagrant/.nvm/versions/node/v5.6.0/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin',
		command => '/home/vagrant/.nvm/versions/node/v5.6.0/bin/npm run build',
		cwd     => '/home/vagrant/muckrock',
		creates => '/home/vagrant/muckrock/muckrock/assets/bundles/main.js',
	}

	# postgresql

	class { 'postgresql::globals':
		version => '9.5',
	} ->
	class { 'postgresql::server':
		pg_hba_conf_defaults => false,
	}

	postgresql::server::role { 'vagrant':
		createdb => true,
	} ->
	postgresql::server::db { 'muckrock':
		user     => 'vagrant',
		owner    => 'vagrant',
		password => false,
	}

	postgresql::server::pg_hba_rule { 'trust local access':
		type        => 'local',
		database    => 'all',
		user        => 'all',
		auth_method => 'trust',
	}

	postgresql::server::pg_hba_rule { 'trust localhost access':
		type        => 'host',
		database    => 'all',
		user        => 'all',
		address     => '127.0.0.1/32',
		auth_method => 'trust',
	}

	postgresql::server::pg_hba_rule { 'trust localhost access ipv6':
		type        => 'host',
		database    => 'all',
		user        => 'all',
		address     => '::1/128',
		auth_method => 'trust',
		before      => Exec['migrate'],
	}

	postgresql::server::config_entry { 'synchronous_commit':
		value => 'off',
	}
	# these speed up the database, but are not safe to data corruption
	# can turn them on if you do not care about your dev database
	#postgresql::server::config_entry { 'fsync':
	#	value => 'off',
	#}
	#postgresql::server::config_entry { 'full_page_writes':
	#	value => 'off',
	#}

	# redis

	class { 'redis':; }

	# heroku

	#class { 'heroku':; }
	include 'heroku'

	exec { "migrate":
		user => 'vagrant',
		command => "/bin/bash -c 'source ~/.bashrc; /home/vagrant/ve/muckrock/bin/python /home/vagrant/muckrock/manage.py migrate --noinput'",
	} ->
	exec { "load data":
		user => 'vagrant',
		command => "/bin/bash -c 'source ~/.bashrc; /home/vagrant/ve/muckrock/bin/python /home/vagrant/muckrock/manage.py loaddata test_users test_profiles test_statistics jurisdictions agency_types test_agencies holidays test_foiarequests test_foiacommunications test_foiafiles test_news test_task tagged_item_base taggit tags sites'",
	} ->
	exec { "install watson":
		user => 'vagrant',
		command => "/bin/bash -c 'source ~/.bashrc; /home/vagrant/ve/muckrock/bin/python /home/vagrant/muckrock/manage.py installwatson'",
	} ->
	exec { "build watson":
		user => 'vagrant',
		command => "/bin/bash -c 'source ~/.bashrc; /home/vagrant/ve/muckrock/bin/python /home/vagrant/muckrock/manage.py buildwatson'",
	}
}
