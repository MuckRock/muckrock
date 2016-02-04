# = Class: redis::config
#
# This class provides configuration for Redis.
#
class redis::config {
  if $::redis::notify_service {
    File {
      owner  => $::redis::config_owner,
      group  => $::redis::config_group,
      mode   => $::redis::config_file_mode,
      notify => Service[$::redis::service_name]
    }
  } else {
    File {
      owner => $::redis::config_owner,
      group => $::redis::config_group,
      mode  => $::redis::config_file_mode,
    }
  }

  file {
    $::redis::config_dir:
      ensure => directory,
      mode   => $::redis::config_dir_mode;

    $::redis::config_file:
      ensure  => present,
      content => template($::redis::conf_template);

    $::redis::log_dir:
      ensure => directory,
      group  => $::redis::service_group,
      mode   => $::redis::config_dir_mode,
      owner  => $::redis::service_user;
  }

  # Adjust /etc/default/redis-server on Debian systems
  case $::osfamily {
    'Debian': {
      file { '/etc/default/redis-server':
        ensure => present,
        group  => $::redis::config_group,
        mode   => $::redis::config_file_mode,
        owner  => $::redis::config_owner,
      }

      if $::redis::ulimit {
        augeas { 'redis ulimit' :
          context => '/files/etc/default/redis-server',
          changes => "set ULIMIT ${::redis::ulimit}",
        }
      }
    }

    default: {
    }
  }
}

