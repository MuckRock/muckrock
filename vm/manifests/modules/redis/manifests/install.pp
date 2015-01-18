# = Class: redis::install
#
# This class installs the application.
#
class redis::install {
  package { $::redis::package_name:
    ensure => $::redis::package_ensure,
  }
}

