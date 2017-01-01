require 'puppet/util/feature'
require 'puppet/util/npm'

Puppet.features.add(:npm) do
  Puppet::Util::Npm.npm_check
end

Puppet.features.send :meta_def, 'npm?' do
  name = :npm
  final = @results[name]
  @results[name] = Puppet::Util::Npm.npm_check unless final
  @results[name]
end
