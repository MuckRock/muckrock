class heroku (
  $heroku_client_url = $heroku::params::client_url,
  $install_parent_dir = $heroku::params::install_parent_dir,
  $artifact_dir = $heroku::params::artifact_dir,
  $link_dir = $heroku::params::link_dir
) inherits heroku::params {

  file { $artifact_dir:
    ensure => directory,
    before => Wget::Fetch['download_heroku_toolbelt'],
  }

  wget::fetch { 'download_heroku_toolbelt':
    source      => $heroku_client_url,
    destination => "${artifact_dir}/heroku-client.tgz",
    before      => Exec['untar_heroku_toolbelt'],
  }

  exec { 'untar_heroku_toolbelt':
    command => "/bin/tar xfz ${artifact_dir}/heroku-client.tgz",
    cwd     => $install_parent_dir,
    creates => "${install_parent_dir}/heroku-client",
    before  => File[$link_dir],
  }

  file { $link_dir:
    ensure => link,
    target => "${install_parent_dir}/heroku-client",
  }

}
