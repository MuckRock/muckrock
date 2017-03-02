require 'beaker-rspec'
require 'beaker/puppet_install_helper'

run_puppet_install_helper

UNSUPPORTED_PLATFORMS = []

RSpec.configure do |c|
  proj_root = File.expand_path(File.join(File.dirname(__FILE__), '..'))

  c.formatter = :documentation

  # Configure all nodes in nodeset
  c.before :suite do
    # Install module
    puppet_module_install(:source => proj_root, :module_name => 'nvm')
    hosts.each do |host|
      on host, puppet('module','install','puppetlabs-stdlib','--version','4.9.0'), { :acceptable_exit_codes => [0,1] }
    end
  end
end
