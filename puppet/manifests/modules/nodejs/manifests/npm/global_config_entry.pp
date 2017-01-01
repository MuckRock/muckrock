# See README.md for usage information.
define nodejs::npm::global_config_entry (
  $ensure         = 'present',
  $config_setting = $title,
  $cmd_exe_path   = $::nodejs::cmd_exe_path,
  $npm_path       = $::nodejs::params::npm_path,
  $value          = undef,
) {

  include ::nodejs

  validate_re($ensure, '^(present|absent)$', "${module_name}::npm::global_config_entry : Ensure parameter must be present or absent")

  case $ensure {
    'absent': {
      $command        = "config delete ${config_setting} --global"
      $onlyif_command = $::osfamily ? {
        'Windows' => "${cmd_exe_path} /C ${npm_path} get --global| FINDSTR /B \"${config_setting}\"",
        default   => "${npm_path} get --global | /bin/grep -e \"^${config_setting}\"",
      }
    }
    default: {
      $command        = "config set ${config_setting} ${value} --global"
      $onlyif_command = $::osfamily ? {
        'Windows' => "${cmd_exe_path} /C FOR /F %i IN ('${npm_path} get ${config_setting} --global') DO IF \"%i\" NEQ \"${value}\" ( EXIT 0 ) ELSE ( EXIT 1 )",
        default   => "/usr/bin/test \"$(${npm_path} get ${config_setting} --global | /usr/bin/tr -d '\n')\" != \"${value}\"",
      }
    }
  }

  if $nodejs::npm_package_ensure != 'absent' {
    $exec_require = "Package[${nodejs::npm_package_name}]"
  } else {
    $exec_require = undef
  }

  #Determine exec provider
  $provider = $::osfamily ? {
    'Windows' => 'windows',
    default   => 'shell',
  }

  exec { "npm_config ${ensure} ${title}":
    command  => "${npm_path} ${command}",
    provider => $provider,
    onlyif   => $onlyif_command,
    require  => $exec_require,
  }
}
