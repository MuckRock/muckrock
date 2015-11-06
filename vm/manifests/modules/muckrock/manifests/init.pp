
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

	# postgresql

	class { 'postgresql::server':
		pg_hba_conf_defaults => false,
	}

	postgresql::server::db { 'muckrock':
		user     => 'muckrock',
		password => false,
	}

	postgresql::server::role { 'muckrock':
		createdb => true,
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

	# redis

	class { 'redis':; }
}
