# == Class: nodejs: See README.md for documentation.
class nodejs(
  $cmd_exe_path                = $nodejs::params::cmd_exe_path,
  $legacy_debian_symlinks      = $nodejs::params::legacy_debian_symlinks,
  $manage_package_repo         = $nodejs::params::manage_package_repo,
  $nodejs_debug_package_ensure = $nodejs::params::nodejs_debug_package_ensure,
  $nodejs_debug_package_name   = $nodejs::params::nodejs_debug_package_name,
  $nodejs_dev_package_ensure   = $nodejs::params::nodejs_dev_package_ensure,
  $nodejs_dev_package_name     = $nodejs::params::nodejs_dev_package_name,
  $nodejs_package_ensure       = $nodejs::params::nodejs_package_ensure,
  $nodejs_package_name         = $nodejs::params::nodejs_package_name,
  $npm_package_ensure          = $nodejs::params::npm_package_ensure,
  $npm_package_name            = $nodejs::params::npm_package_name,
  $npm_path                    = $nodejs::params::npm_path,
  $npmrc_auth                  = $nodejs::params::npmrc_auth,
  $repo_class                  = $nodejs::params::repo_class,
  $repo_enable_src             = $nodejs::params::repo_enable_src,
  $repo_ensure                 = $nodejs::params::repo_ensure,
  $repo_pin                    = $nodejs::params::repo_pin,
  $repo_priority               = $nodejs::params::repo_priority,
  $repo_proxy                  = $nodejs::params::repo_proxy,
  $repo_proxy_password         = $nodejs::params::repo_proxy_password,
  $repo_proxy_username         = $nodejs::params::repo_proxy_username,
  $repo_url_suffix             = $nodejs::params::repo_url_suffix,
  $use_flags                   = $nodejs::params::use_flags,
) inherits nodejs::params {

  # Validate repo_url_suffix. Not every versions of NodeJS are available
  # for all distros at Nodesource. We need to check that.
  if ($manage_package_repo) and ($repo_class == '::nodejs::repo::nodesource') {
    $suffix_error_msg = "Var \$repo_url_suffix with value '${repo_url_suffix}' is not set correctly for ${::operatingsystem} ${::operatingsystemrelease}. See README."
    case $::osfamily {
      'Debian': {
        # Nodesource repos for Ubuntu lucid only provide nodejs version 0.10
        if $::operatingsystemrelease =~ /^(10\.04|13.10)$/ {
          validate_re($repo_url_suffix, '^0\.10$', $suffix_error_msg)
        }
        elsif $::operatingsystemrelease =~ /^14\.10$/ {
          validate_re($repo_url_suffix, '^0\.1[02]$', $suffix_error_msg)
        }
        elsif $::operatingsystemrelease =~ /^15\.04$/ {
          validate_re($repo_url_suffix, '^(0\.1[02]|[45]\.x)x$', $suffix_error_msg)
        }
        elsif $::operatingsystemrelease =~ /^15\.10$/ {
          validate_re($repo_url_suffix, '^(0\.1[02]|[456]\.x)x$', $suffix_error_msg)
        }
        elsif $::operatingsystemrelease =~ /^1[246]\.04$/ { #LTS
          validate_re($repo_url_suffix, '^(0\.1[02]|[456]\.x)$', $suffix_error_msg)
        }
        # All NodeJS versions are available for Debian 7 and 8
        else {
          validate_re($repo_url_suffix, '^(0\.1[02]|[456]\.x)$', $suffix_error_msg)
        }
      }
      'RedHat': {
        # At the moment, only node v0.10 and v0.12 repos are available on
        # nodesource for RedHat 5.
        if $::operatingsystemrelease =~ /^5\.(\d+)/ {
          validate_re($repo_url_suffix, '^0\.1[02]$', $suffix_error_msg)
        }
        elsif $::operatingsystemrelease =~ /^[67]\.(\d+)/ {
          validate_re($repo_url_suffix, '^(0\.1[02]|[456]\.x)$', $suffix_error_msg)
        }
        # Fedora
        elsif $::operatingsystem == 'Fedora' {
          if $::operatingsystemrelease =~ /^19|20$/ {
            validate_re($repo_url_suffix, '^(0\.1[02]|4\.x)$', $suffix_error_msg)
          }
          elsif $::operatingsystemrelease =~ /^21|22$/ {
            validate_re($repo_url_suffix, '^(0\.1[02]|[45]\.x)$', $suffix_error_msg)
          }
          elsif $::operatingsystemrelease == '23' {
            validate_re($repo_url_suffix, '^[45]\.x$', $suffix_error_msg)
          }
        }
      }
      'Linux': {
        if $::operatingsystem == 'Amazon' {
          # Based on RedHat 7
          if $::operatingsystemrelease =~ /^201[4-9]\./ {
            validate_re($repo_url_suffix, '^(0\.1[02]|[45]\.x)$', $suffix_error_msg)
          }
          # Based on Redhat 6
          else {
            validate_re($repo_url_suffix, '^0\.1[02]$', $suffix_error_msg)
          }
        }
      }
      default: {
        fail("Nodesource repositories don't provide package for ${::operatingsystem} ${::operatingsystemrelease}. Try to set \$repo_class to match your needs.")
      }
    }
  }

  validate_bool($legacy_debian_symlinks)
  validate_bool($manage_package_repo)

  if $manage_package_repo and !$repo_class {
    fail("${module_name}: The manage_package_repo parameter was set to true but no repo_class was provided.")
  }

  if $nodejs_debug_package_name {
    validate_string($nodejs_debug_package_name)
  }

  if $nodejs_dev_package_name {
    validate_string($nodejs_dev_package_name)
  }

  if $npm_package_name and $npm_package_name != false {
    validate_string($npm_package_name)
  }

  if $npmrc_auth {
    if is_string($npmrc_auth) == false {
      fail('npmrc_auth must be a string')
    }
  }

  validate_array($use_flags)

  include '::nodejs::install'

  if $manage_package_repo {
    include $repo_class
    anchor { '::nodejs::begin': } ->
    Class[$repo_class] ->
    Class['::nodejs::install'] ->
    anchor { '::nodejs::end': }
  }
}
