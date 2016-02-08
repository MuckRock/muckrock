# == Define: python::virtualenv
#
# Creates Python virtualenv.
#
# === Parameters
#
# [*ensure*]
#  present|absent. Default: present
#
# [*version*]
#  Python version to use. Default: system default
#
# [*requirements*]
#  Path to pip requirements.txt file. Default: none
#
# [*systempkgs*]
#  Copy system site-packages into virtualenv. Default: don't
#  If virtualenv version < 1.7 this flag has no effect since
# [*venv_dir*]
#  Directory to install virtualenv to. Default: $name
#
# [*distribute*]
#  Include distribute in the virtualenv. Default: true
#
# [*index*]
#  Base URL of Python package index. Default: none (http://pypi.python.org/simple/)
#
# [*owner*]
#  The owner of the virtualenv being manipulated. Default: root
#
# [*group*]
#  The group relating to the virtualenv being manipulated. Default: root
#
# [*proxy*]
#  Proxy server to use for outbound connections. Default: none
#
# [*environment*]
#  Additional environment variables required to install the packages. Default: none
#
# [*path*]
#  Specifies the PATH variable. Default: [ '/bin', '/usr/bin', '/usr/sbin' ]
#
# [*cwd*]
#  The directory from which to run the "pip install" command. Default: undef
#
# [*timeout*]
#  The maximum time in seconds the "pip install" command should take. Default: 1800
#
# [*extra_pip_args*]
#  Extra arguments to pass to pip after requirements file.  Default: blank
#
# === Examples
#
# python::virtualenv { '/var/www/project1':
#   ensure       => present,
#   version      => 'system',
#   requirements => '/var/www/project1/requirements.txt',
#   proxy        => 'http://proxy.domain.com:3128',
#   systempkgs   => true,
#   index        => 'http://www.example.com/simple/'
# }
#
# === Authors
#
# Sergey Stankevich
# Ashley Penney
# Marc Fournier
# Fotis Gimian
#
define python::virtualenv (
  $ensure           = present,
  $version          = 'system',
  $requirements     = false,
  $systempkgs       = false,
  $venv_dir         = $name,
  $distribute       = true,
  $index            = false,
  $owner            = 'root',
  $group            = 'root',
  $proxy            = false,
  $environment      = [],
  $path             = [ '/bin', '/usr/bin', '/usr/sbin' ],
  $cwd              = undef,
  $timeout          = 1800,
  $extra_pip_args   = ''
) {

  if $ensure == 'present' {

    $python = $version ? {
      'system' => 'python',
      'pypy'   => 'pypy',
      default  => "python${version}",
    }

    $virtualenv = $version ? {
      'system' => 'virtualenv',
      default  => "virtualenv-${version}",
    }

    $proxy_flag = $proxy ? {
      false    => '',
      default  => "--proxy=${proxy}",
    }

    $proxy_command = $proxy ? {
      false   => '',
      default => "&& export http_proxy=${proxy}",
    }

    # Virtualenv versions prior to 1.7 do not support the
    # --system-site-packages flag, default off for prior versions
    # Prior to version 1.7 the default was equal to --system-site-packages
    # and the flag --no-site-packages had to be passed to do the opposite
    if (( versioncmp($::virtualenv_version,'1.7') > 0 ) and ( $systempkgs == true )) {
      $system_pkgs_flag = '--system-site-packages'
    } elsif (( versioncmp($::virtualenv_version,'1.7') < 0 ) and ( $systempkgs == false )) {
      $system_pkgs_flag = '--no-site-packages'
    } else {
      $system_pkgs_flag = $systempkgs ? {
        true    => '--system-site-packages',
        false   => '--no-site-packages',
        default => fail('Invalid value for systempkgs. Boolean value is expected')
      }
    }

    $distribute_pkg = $distribute ? {
      true     => 'distribute',
      default  => 'setuptools',
    }
    $pypi_index = $index ? {
        false   => '',
        default => "-i ${index}",
    }

    # Python 2.6 and older does not support setuptools/distribute > 0.8 which
    # is required for pip wheel support, pip therefor requires --no-use-wheel flag
    # if the # pip version is more recent than 1.4.1 but using an old python or
    # setuputils/distribute version
    # To check for this we test for wheel parameter using help and then using
    # version, this makes sure we only use wheels if they are supported

    file { $venv_dir:
      ensure => directory,
      owner  => $owner,
      group  => $group,
    }



    exec { "python_virtualenv_${venv_dir}":
      command     => "true ${proxy_command} && ${virtualenv} ${system_pkgs_flag} -p ${python} ${venv_dir} && ${venv_dir}/bin/pip wheel --help > /dev/null 2>&1 && { ${venv_dir}/bin/pip wheel --version > /dev/null 2>&1 || wheel_support_flag='--no-use-wheel'; } ; { ${venv_dir}/bin/pip --log ${venv_dir}/pip.log install ${pypi_index} ${proxy_flag} \$wheel_support_flag --upgrade pip ${distribute_pkg} || ${venv_dir}/bin/pip --log ${venv_dir}/pip.log install ${pypi_index} ${proxy_flag}  --upgrade pip ${distribute_pkg} ;}",
      user        => $owner,
      creates     => "${venv_dir}/bin/activate",
      path        => $path,
      cwd         => '/tmp',
      environment => $environment,
      unless      => "grep '^[\\t ]*VIRTUAL_ENV=[\\\\'\\\"]*${venv_dir}[\\\"\\\\'][\\t ]*$' ${venv_dir}/bin/activate", #Unless activate exists and VIRTUAL_ENV is correct we re-create the virtualenv
      require     => File[$venv_dir],
    }

    if $requirements {
      exec { "python_requirements_initial_install_${requirements}_${venv_dir}":
        command     => "${venv_dir}/bin/pip wheel --help > /dev/null 2>&1 && { ${venv_dir}/bin/pip wheel --version > /dev/null 2>&1 || wheel_support_flag='--no-use-wheel'; } ; ${venv_dir}/bin/pip --log ${venv_dir}/pip.log install ${pypi_index} ${proxy_flag} \$wheel_support_flag -r ${requirements} ${extra_pip_args}",
        refreshonly => true,
        timeout     => $timeout,
        user        => $owner,
        subscribe   => Exec["python_virtualenv_${venv_dir}"],
        environment => $environment,
        cwd         => $cwd
      }

      python::requirements { "${requirements}_${venv_dir}":
        requirements    => $requirements,
        virtualenv      => $venv_dir,
        proxy           => $proxy,
        owner           => $owner,
        group           => $group,
        cwd             => $cwd,
        require         => Exec["python_virtualenv_${venv_dir}"],
        extra_pip_args  => $extra_pip_args,
      }
    }
  } elsif $ensure == 'absent' {

    file { $venv_dir:
      ensure  => absent,
      force   => true,
      recurse => true,
      purge   => true,
    }
  }
}
