class { 'nvm':
  user         => 'root',
  nvm_dir      => '/opt/nvm',
  version      => 'v0.29.0',
  profile_path => '/etc/profile.d/nvm.sh',
  install_node => '0.12.7',
}
