# See README.md for usage information
class nvm::install (
  $user,
  $home,
  $version,
  $nvm_dir,
  $nvm_repo,
  $dependencies,
  $refetch,
) {

  exec { "git clone ${nvm_repo} ${nvm_dir}":
    command => "git clone ${nvm_repo} ${nvm_dir}",
    cwd     => $home,
    user    => $user,
    unless  => "/usr/bin/test -d ${nvm_dir}/.git",
    require => $dependencies,
    notify  => Exec["git checkout ${nvm_repo} ${version}"],
  }

  if $refetch {
    exec { "git fetch ${nvm_repo} ${nvm_dir}":
      command => 'git fetch',
      cwd     => $nvm_dir,
      user    => $user,
      require => Exec["git clone ${nvm_repo} ${nvm_dir}"],
      notify  => Exec["git checkout ${nvm_repo} ${version}"],
    }
  }

  exec { "git checkout ${nvm_repo} ${version}":
    command     => "git checkout --quiet ${version}",
    cwd         => $nvm_dir,
    user        => $user,
    refreshonly => true,
  }

}
