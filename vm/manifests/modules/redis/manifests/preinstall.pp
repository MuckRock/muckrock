# = Class: redis::preinstall
#
# This class provides anything required by the install class.
# Such as package repositories.
#
class redis::preinstall {
  if $::redis::manage_repo {
    case $::operatingsystem {
      'RedHat', 'CentOS', 'Scientific', 'OEL': {
        $rpm_url = $::operatingsystemrelease ? {
          /^5/    => "http://download.powerstack.org/5/${::architecture}/",
          /^6/    => "http://download.powerstack.org/6/${::architecture}/",
          default => Fail['Operating system or release version not supported.'],
        }

        $rpm_gpgkey = $::operatingsystemrelease ? {
          /^5/    => 'https://raw.githubusercontent.com/santisaez/powerstack/master/RPM-GPG-KEY-powerstack',
          /^6/    => 'https://raw.githubusercontent.com/santisaez/powerstack/master/RPM-GPG-KEY-powerstack',
          default => Fail['Operating system or release version not supported.'],
        }

        yumrepo { 'powerstack':
          descr    => 'PowerStack for CentOS',
          baseurl  => $rpm_url,
          gpgkey   => $rpm_gpgkey,
          enabled  => 1,
          gpgcheck => 1;
        }
      }

      'Amazon': {
        $rpm_url = $::operatingsystemrelease ? {
          /^3/    => "http://download.powerstack.org/6/${::architecture}/",
          default => Fail['Operating system or release version not supported.'],
        }

        $rpm_gpgkey = $::operatingsystemrelease ? {
          /^3/    => 'https://raw.githubusercontent.com/santisaez/powerstack/master/RPM-GPG-KEY-powerstack',
          default => Fail['Operating system or release version not supported.'],
        }

        yumrepo { 'powerstack':
          descr    => 'PowerStack for CentOS',
          baseurl  => $rpm_url,
          gpgkey   => $rpm_gpgkey,
          enabled  => 1,
          gpgcheck => 1;
        }
      }

      'Debian': {
        include apt
        apt::key { 'dotdeb':
          key        => '89DF5277',
          key_source => 'http://www.dotdeb.org/dotdeb.gpg',
        }

        apt::source { 'dotdeb':
          location    => 'http://packages.dotdeb.org',
          release     => $::lsbdistcodename,
          repos       => 'all',
          include_src => true,
          require     => Apt::Key['dotdeb'],
        }
      }

      'Ubuntu': {
        include apt
        apt::ppa { $::redis::ppa_repo: }
      }

      default: {
      }
    }
  }
}

