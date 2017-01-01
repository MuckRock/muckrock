
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

	exec { "apt-update":
		command => "/usr/bin/apt-get update"
	}

	Exec["apt-update"] -> Package <| |>

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
	}

	# nodejs

    class { 'nodejs': 
		repo_url_suffix => '5.x',
	}

    # symlink the nodejs folder to node, since Ubuntu
    # has a weird legacy issue when installing NodeJS
    file { '/usr/bin/node':
        ensure => 'link',
        target => '/usr/bin/nodejs'
    }


	# postgresql

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

	postgresql::server::config_entry { 'fsync':
		value => 'off',
	}
	postgresql::server::config_entry { 'synchronous_commit':
		value => 'off',
	}
	postgresql::server::config_entry { 'full_page_writes':
		value => 'off',
	}

	# redis

	class { 'redis':; }

	# heroku

	#class { 'heroku':; }
	include 'heroku'

}
