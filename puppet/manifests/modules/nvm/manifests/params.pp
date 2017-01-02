# See README.md for usage information
class nvm::params {
  $manage_user         = false
  $manage_dependencies = true
  $manage_profile      = true
  $version             = 'v0.29.0'
  $nvm_repo            = 'https://github.com/creationix/nvm.git'
  $refetch             = false
  $install_node        = undef
  $node_instances      = {}
}
