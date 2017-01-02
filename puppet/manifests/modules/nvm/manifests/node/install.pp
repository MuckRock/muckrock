# See README.md for usage information
define nvm::node::install (
  $user,
  $nvm_dir     = undef,
  $version     = $title,
  $set_default = false,
  $from_source = false,
  $default     = false,
) {

  # The base class must be included first because it is used by parameter defaults
  if ! defined(Class['nvm']) {
    fail('You must include the nvm base class before using any nvm defined resources')
  }

  # Notify users that uses the deprecated default parameter
  if $default {
    notify { 'The `default` parameter is now deprecated because is a reserved word use `set_default` instead': }
    $is_default = true
  }
  else {
    $is_default = $set_default
  }

  if $nvm_dir == undef {
    $final_nvm_dir = "/home/${user}/.nvm"
  }
  else {
    $final_nvm_dir = $nvm_dir
  }

  validate_string($user)
  validate_string($final_nvm_dir)
  validate_string($version)
  validate_bool($default)
  validate_bool($set_default)
  validate_bool($from_source)

  if $from_source {
    $nvm_install_options = ' -s '
  }
  else {
    $nvm_install_options = ''
  }

  exec { "nvm install node version ${version}":
    cwd         => $final_nvm_dir,
    command     => ". ${final_nvm_dir}/nvm.sh && nvm install ${nvm_install_options} ${version}",
    user        => $user,
    unless      => ". ${final_nvm_dir}/nvm.sh && nvm which ${version}",
    environment => [ "NVM_DIR=${final_nvm_dir}" ],
    require     => Class['nvm::install'],
    provider    => shell,
  }

  if $is_default {
    exec { "nvm set node version ${version} as default":
      cwd         => $final_nvm_dir,
      command     => ". ${final_nvm_dir}/nvm.sh && nvm alias default ${version}",
      user        => $user,
      environment => [ "NVM_DIR=${final_nvm_dir}" ],
      unless      => ". ${final_nvm_dir}/nvm.sh && nvm which default | grep ${version}",
      provider    => shell,
      require     => Exec["nvm install node version ${version}"],
    }
  }
}
