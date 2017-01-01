require 'puppet/provider/package'

Puppet::Type.type(:package).provide :npm, parent: Puppet::Provider::Package do
  desc 'npm is the package manager for Node.js. This provider only handles global packages.'

  confine feature: :npm

  has_feature :versionable, :install_options

  if Puppet::Util::Package.versioncmp(Puppet.version, '3.0') >= 0
    has_command(:npm, 'npm') do
      is_optional
      environment HOME: '/root'
    end
  else
    optional_commands npm: 'npm'
  end

  def self.npmlist
    # Ignore non-zero exit codes as they can be minor, just try and parse JSON
    output = execute([command(:npm), 'list', '--json', '--global'], combine: false)
    Puppet.debug("Warning: npm list --json exited with code #{$CHILD_STATUS.exitstatus}") unless $CHILD_STATUS.success?
    begin
      # ignore any npm output lines to be a bit more robust
      output = PSON.parse(output.lines.select { |l| l =~ %r{^((?!^npm).*)$} }.join("\n"), max_nesting: 100)
      @npmlist = output['dependencies'] || {}
    rescue PSON::ParserError => e
      Puppet.debug("Error: npm list --json command error #{e.message}")
      @npmlist = {}
    end
  end

  def npmlist
    self.class.npmlist
  end

  def self.instances
    @npmlist ||= npmlist
    @npmlist.map do |k, v|
      new(name: k, ensure: v['version'], provider: 'npm')
    end
  end

  def query
    list = npmlist

    if list.key?(resource[:name]) && list[resource[:name]].key?('version')
      version = list[resource[:name]]['version']
      { ensure: version, name: resource[:name] }
    else
      { ensure: :absent, name: resource[:name] }
    end
  end

  def latest
    npm('view', resource[:name], 'version').lines.reject { |l| l.start_with?('npm') }.join("\n").strip
  end

  def update
    install
  end

  def install
    package = if resource[:ensure].is_a? Symbol
                resource[:name]
              else
                "#{resource[:name]}@#{resource[:ensure]}"
              end

    options = %w(--global)
    options += install_options if @resource[:install_options]

    if resource[:source]
      npm('install', *options, resource[:source])
    else
      npm('install', *options, package)
    end
  end

  def uninstall
    npm('uninstall', '--global', resource[:name])
  end

  def install_options
    join_options(@resource[:install_options])
  end
end
