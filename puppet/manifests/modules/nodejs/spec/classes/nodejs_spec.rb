require 'spec_helper'

describe 'nodejs', type: :class do
  context 'when run on Debian Squeeze' do
    let :facts do
      {
        osfamily: 'Debian',
        operatingsystemrelease: '6.0.10'
      }
    end

    it 'fails' do
      expect { catalogue }.to raise_error(Puppet::Error, %r{The nodejs module is not supported on Debian Squeeze.})
    end
  end

  on_supported_os.each do |os, facts|
    next unless facts[:osfamily] == 'Debian'

    context "on #{os} " do
      let :facts do
        facts
      end

      it 'the file resource root_npmrc should be in the catalog' do
        is_expected.to contain_file('root_npmrc').with(
          'ensure' => 'file',
          'path'    => '/root/.npmrc',
          'owner'   => 'root',
          'group'   => '0',
          'mode'    => '0600'
        )
      end

      context 'with npmrc_auth set to a string' do
        let :params do
          {
            npmrc_auth: 'dXNlcjpwYXNzd29yZA=='
          }
        end

        it { is_expected.to contain_file('root_npmrc').with_content(%r{^_auth="dXNlcjpwYXNzd29yZA=="$}) }
      end

      context 'with npmrc_auth set to an invalid type (non-string)' do
        let :params do
          {
            npmrc_auth: %w(invalid type)
          }
        end

        it 'fails' do
          expect { catalogue }.to raise_error(Puppet::Error, %r{npmrc_auth must be a string})
        end
      end

      # legacy_debian_symlinks
      context 'with legacy_debian_symlinks set to true' do
        let :params do
          {
            legacy_debian_symlinks: true
          }
        end

        it 'the file resource /usr/bin/node should be in the catalog' do
          is_expected.to contain_file('/usr/bin/node')
        end
        it 'the file resource /usr/share/man/man1/node.1.gz should be in the catalog' do
          is_expected.to contain_file('/usr/share/man/man1/node.1.gz')
        end
      end

      context 'with legacy_debian_symlinks set to false' do
        let :params do
          {
            legacy_debian_symlinks: false
          }
        end

        it 'the file resource /usr/bin/node should not be in the catalog' do
          is_expected.not_to contain_file('/usr/bin/node')
        end
        it 'the file resource /usr/share/man/man1/node.1.gz should not be in the catalog' do
          is_expected.not_to contain_file('/usr/share/man/man1/node.1.gz')
        end
      end

      # manage_package_repo
      context 'with manage_package_repo set to true' do
        let :default_params do
          {
            manage_package_repo: true
          }
        end

        context 'and repo_class set to ::nodejs::repo::nodesource' do
          let :params do
            default_params.merge!(repo_class: 'nodejs::repo::nodesource')
          end

          it '::nodejs::repo::nodesource should be in the catalog' do
            is_expected.to contain_class('nodejs::repo::nodesource')
          end

          it '::nodejs::repo::nodesource::apt should be in the catalog' do
            is_expected.to contain_class('nodejs::repo::nodesource::apt')
          end
        end

        context 'and repo_enable_src set to true' do
          let :params do
            default_params.merge!(repo_enable_src: true)
          end

          it 'the repo apt::source resource should contain include => { src => true}' do
            is_expected.to contain_apt__source('nodesource').with('include' => { 'src' => true })
          end
        end

        context 'and repo_enable_src set to false' do
          let :params do
            default_params.merge!(repo_enable_src: false)
          end

          it 'the repo apt::source resource should contain include => { src => false}' do
            is_expected.to contain_apt__source('nodesource').with('include' => { 'src' => false })
          end
        end

        context 'and repo_pin set to 10' do
          let :params do
            default_params.merge!(repo_pin: '10')
          end

          it 'the repo apt::source resource should contain pin = 10' do
            is_expected.to contain_apt__source('nodesource').with('pin' => '10')
          end
        end

        context 'and repo_pin not set' do
          let :params do
            default_params.merge!(repo_pin: 'false')
          end

          it 'the repo apt::source resource should contain pin = false' do
            is_expected.to contain_apt__source('nodesource').with('pin' => 'false')
          end
        end

        context 'and repo_url_suffix set to 0.12' do
          let :params do
            default_params.merge!(repo_url_suffix: '0.12')
          end

          if facts[:operatingsystemrelease] == '10.04'
            it 'NodeJS 0.12 package not provided for Ubuntu Lucid' do
              expect { catalogue }.to raise_error(Puppet::Error, %r{Var \$repo_url_suffix with value '0\.12' is not set correctly for Ubuntu 10\.04\. See README\.})
            end
          else
            it 'the repo apt::source resource should contain location = https://deb.nodesource.com/node_0.12' do
              is_expected.to contain_apt__source('nodesource').with('location' => 'https://deb.nodesource.com/node_0.12')
            end
          end
        end

        # repo_url_suffix regex checks validation
        context 'and repo_url_suffix set to 0.1O.0' do
          let :params do
            default_params.merge!(repo_url_suffix: '0.10.0')
          end

          it 'repo_url_suffix regex checks should fail' do
            expect { catalogue }.to raise_error(Puppet::Error, %r{Var \$repo_url_suffix with value '0\.10\.0' is not set correctly for \w+ \d+(\.\d+)+\. See README\.})
          end
        end

        context 'and repo_ensure set to present' do
          let :params do
            default_params.merge!(repo_ensure: 'present')
          end

          it 'the nodesource apt sources file should exist' do
            is_expected.to contain_apt__source('nodesource')
          end
        end

        context 'and repo_ensure set to absent' do
          let :params do
            default_params.merge!(repo_ensure: 'absent')
          end

          it 'the nodesource apt sources file should not exist' do
            is_expected.to contain_apt__source('nodesource').with('ensure' => 'absent')
          end
        end
      end

      context 'with manage_package_repo set to false' do
        let :params do
          {
            manage_package_repo: false
          }
        end

        it '::nodejs::repo::nodesource should not be in the catalog' do
          is_expected.not_to contain_class('::nodejs::repo::nodesource')
        end
      end

      # nodejs_debug_package_ensure
      context 'with nodejs_debug_package_ensure set to present' do
        let :params do
          {
            nodejs_debug_package_ensure: 'present'
          }
        end

        it 'the nodejs package with debugging symbols should be installed' do
          is_expected.to contain_package('nodejs-dbg').with('ensure' => 'present')
        end
      end

      context 'with nodejs_debug_package_ensure set to absent' do
        let :params do
          {
            nodejs_debug_package_ensure: 'absent'
          }
        end

        it 'the nodejs package with debugging symbols should not be present' do
          is_expected.to contain_package('nodejs-dbg').with('ensure' => 'absent')
        end
      end

      # nodejs_dev_package_ensure
      context 'with nodejs_dev_package_ensure set to present' do
        let :params do
          {
            nodejs_dev_package_ensure: 'present'
          }
        end

        if facts[:operatingsystemrelease] == '10.04' || facts[:operatingsystemmajrelease] == '7'
          it 'the nodejs development package resource should not be present' do
            is_expected.not_to contain_package('nodejs-dev')
          end
        else
          it 'the nodejs development package should be installed' do
            is_expected.to contain_package('nodejs-dev').with('ensure' => 'present')
          end
        end
      end

      context 'with nodejs_dev_package_ensure set to absent' do
        let :params do
          {
            nodejs_dev_package_ensure: 'absent'
          }
        end

        if facts[:operatingsystemrelease] == '10.04' || facts[:operatingsystemmajrelease] == '7'
          it 'the nodejs development package resource should not be present' do
            is_expected.not_to contain_package('nodejs-dev')
          end
        else
          it 'the nodejs development package should not be present' do
            is_expected.to contain_package('nodejs-dev').with('ensure' => 'absent')
          end
        end
      end

      # nodejs_package_ensure
      context 'with nodejs_package_ensure set to present' do
        let :params do
          {
            nodejs_package_ensure: 'present'
          }
        end

        it 'the nodejs package should be present' do
          is_expected.to contain_package('nodejs').with('ensure' => 'present')
        end
      end

      context 'with nodejs_package_ensure set to absent' do
        let :params do
          {
            nodejs_package_ensure: 'absent'
          }
        end

        it 'the nodejs package should be absent' do
          is_expected.to contain_package('nodejs').with('ensure' => 'absent')
        end
      end

      # npm_package_ensure
      context 'with npm_package_ensure set to present' do
        let :params do
          {
            npm_package_ensure: 'present'
          }
        end

        if facts[:operatingsystemrelease] == '10.04' || facts[:operatingsystemmajrelease] == '7'
          it 'the npm package resource should not be present' do
            is_expected.not_to contain_package('npm')
          end
        else
          it 'the npm package should be present' do
            is_expected.to contain_package('npm').with('ensure' => 'present')
          end
        end
      end

      context 'with npm_package_ensure set to absent' do
        let :params do
          {
            npm_package_ensure: 'absent'
          }
        end

        if facts[:operatingsystemrelease] == '10.04' || facts[:operatingsystemmajrelease] == '7'
          it 'the npm package resource should not be present' do
            is_expected.not_to contain_package('npm')
          end
        else
          it 'the npm package should be absent' do
            is_expected.to contain_package('npm').with('ensure' => 'absent')
          end
        end
      end

      # npm_package_name
      context 'with npm_package_name set to false' do
        let :params do
          {
            npm_package_name: 'false'
          }
        end
        it 'the npm package resource should not be present' do
          is_expected.not_to contain_package('npm')
        end
      end
    end
  end

  context 'when run on Fedora 18' do
    let :facts do
      {
        osfamily: 'RedHat',
        operatingsystem: 'Fedora',
        operatingsystemrelease: '18'
      }
    end

    it do
      expect { catalogue }.to raise_error(Puppet::Error, %r{The nodejs module is not supported on Fedora 18.})
    end
  end

  ['5.0', '6.0', '7.0', '20', '21'].each do |operatingsystemrelease|
    osversions = operatingsystemrelease.split('.')
    operatingsystemmajrelease = osversions[0]

    if operatingsystemrelease =~ %r{^[5-7]\.(\d+)}
      operatingsystem     = 'CentOS'
      dist_type           = 'el'
      repo_baseurl        = "https://rpm.nodesource.com/pub_0.10/#{dist_type}/#{operatingsystemmajrelease}/\$basearch"
      repo_source_baseurl = "https://rpm.nodesource.com/pub_0.10/#{dist_type}/#{operatingsystemmajrelease}/SRPMS"
      repo_descr          = "Node.js Packages for Enterprise Linux #{operatingsystemmajrelease} - \$basearch"
      repo_source_descr   = "Node.js for Enterprise Linux #{operatingsystemmajrelease} - \$basearch - Source"
    else
      operatingsystem     = 'Fedora'
      dist_type           = 'fc'
      repo_baseurl        = "https://rpm.nodesource.com/pub_0.10/#{dist_type}/#{operatingsystemmajrelease}/\$basearch"
      repo_source_baseurl = "https://rpm.nodesource.com/pub_0.10/#{dist_type}/#{operatingsystemmajrelease}/SRPMS"
      repo_descr          = "Node.js Packages for Fedora Core #{operatingsystemmajrelease} - \$basearch"
      repo_source_descr   = "Node.js for Fedora Core #{operatingsystemmajrelease} - \$basearch - Source"
    end

    context "when run on #{operatingsystem} release #{operatingsystemrelease}" do
      let :facts do
        {
          operatingsystem: operatingsystem,
          operatingsystemmajrelease: operatingsystemmajrelease,
          operatingsystemrelease: operatingsystemrelease,
          osfamily: 'RedHat'
        }
      end

      # manage_package_repo
      context 'with manage_package_repo set to true' do
        let :default_params do
          {
            manage_package_repo: true
          }
        end

        context 'and repo_class set to ::nodejs::repo::nodesource' do
          let :params do
            default_params.merge!(repo_class: 'nodejs::repo::nodesource')
          end

          it '::nodejs::repo::nodesource should be in the catalog' do
            is_expected.to contain_class('nodejs::repo::nodesource')
          end

          it '::nodejs::repo::nodesource::yum should be in the catalog' do
            is_expected.to contain_class('nodejs::repo::nodesource::yum')
          end

          it 'the nodesource and nodesource-source repos should contain the right description and baseurl' do
            is_expected.to contain_yumrepo('nodesource').with('baseurl' => repo_baseurl,
                                                              'descr'   => repo_descr)

            is_expected.to contain_yumrepo('nodesource-source').with('baseurl' => repo_source_baseurl,
                                                                     'descr'   => repo_source_descr)
          end
        end

        context 'and repo_url_suffix set to 5.x' do
          let :params do
            default_params.merge!(repo_url_suffix: '5.x')
          end

          if operatingsystemrelease =~ %r{^(5\.\d+|20)$}
            it 'NodeJS 5.x package not provided for Centos 5 and Fedora 20' do
              expect { catalogue }.to raise_error(Puppet::Error, %r{Var \$repo_url_suffix with value '5\.x' is not set correctly for \w+ \d+(\.\d+)*\. See README\.})
            end
          else
            it "the yum nodesource repo resource should contain baseurl = https://rpm.nodesource.com/pub_5.x/#{dist_type}/#{operatingsystemmajrelease}/\$basearch" do
              is_expected.to contain_yumrepo('nodesource').with('baseurl' => "https://rpm.nodesource.com/pub_5.x/#{dist_type}/#{operatingsystemmajrelease}/\$basearch")
            end
          end
        end

        # repo_url_suffix regex checks validation
        context 'and repo_url_suffix set to 0.1O.0' do
          let :params do
            default_params.merge!(repo_url_suffix: '0.10.0')
          end

          it 'repo_url_suffix regex checks should fail' do
            expect { catalogue }.to raise_error(Puppet::Error, %r{Var \$repo_url_suffix with value '0\.10\.0' is not set correctly for \w+ \d+(\.\d+)*\. See README\.})
          end
        end

        context 'and repo_enable_src set to true' do
          let :params do
            default_params.merge!(repo_enable_src: true)
          end

          it 'the yumrepo resource nodesource-source should contain enabled = 1' do
            is_expected.to contain_yumrepo('nodesource-source').with('enabled' => '1')
          end
        end

        context 'and repo_enable_src set to false' do
          let :params do
            default_params.merge!(repo_enable_src: false)
          end

          it 'the yumrepo resource should contain enabled = 0' do
            is_expected.to contain_yumrepo('nodesource-source').with('enabled' => '0')
          end
        end

        context 'and repo_priority set to 50' do
          let :params do
            default_params.merge!(repo_priority: '50')
          end

          it 'the yumrepo resource nodesource-source should contain priority = 50' do
            is_expected.to contain_yumrepo('nodesource-source').with('priority' => '50')
          end
        end

        context 'and repo_priority not set' do
          let :params do
            default_params.merge!(repo_priority: 'absent')
          end

          it 'the yumrepo resource nodesource-source should contain priority = absent' do
            is_expected.to contain_yumrepo('nodesource-source').with('priority' => 'absent')
          end
        end

        context 'and repo_ensure set to present' do
          let :params do
            default_params.merge!(repo_ensure: 'present')
          end

          it 'the nodesource yum repo files should exist' do
            is_expected.to contain_yumrepo('nodesource')
            is_expected.to contain_yumrepo('nodesource-source')
          end
        end

        context 'and repo_ensure set to absent' do
          let :params do
            default_params.merge!(repo_ensure: 'absent')
          end

          it 'the nodesource yum repo files should not exist' do
            is_expected.to contain_yumrepo('nodesource').with('enabled' => 'absent')
            is_expected.to contain_yumrepo('nodesource-source').with('enabled' => 'absent')
          end
        end

        context 'and repo_proxy set to absent' do
          let :params do
            default_params.merge!(repo_proxy: 'absent')
          end

          it 'the yumrepo resource should contain proxy = absent' do
            is_expected.to contain_yumrepo('nodesource').with('proxy' => 'absent')
            is_expected.to contain_yumrepo('nodesource-source').with('proxy' => 'absent')
          end
        end

        context 'and repo_proxy set to http://proxy.localdomain.com' do
          let :params do
            default_params.merge!(repo_proxy: 'http://proxy.localdomain.com')
          end

          it 'the yumrepo resource should contain proxy = http://proxy.localdomain.com' do
            is_expected.to contain_yumrepo('nodesource').with('proxy' => 'http://proxy.localdomain.com')
            is_expected.to contain_yumrepo('nodesource-source').with('proxy' => 'http://proxy.localdomain.com')
          end
        end

        context 'and repo_proxy_password set to absent' do
          let :params do
            default_params.merge!(repo_proxy_password: 'absent')
          end

          it 'the yumrepo resource should contain proxy_password = absent' do
            is_expected.to contain_yumrepo('nodesource').with('proxy_password' => 'absent')
            is_expected.to contain_yumrepo('nodesource-source').with('proxy_password' => 'absent')
          end
        end

        context 'and repo_proxy_password set to password' do
          let :params do
            default_params.merge!(repo_proxy_password: 'password')
          end

          it 'the yumrepo resource should contain proxy_password = password' do
            is_expected.to contain_yumrepo('nodesource').with('proxy_password' => 'password')
            is_expected.to contain_yumrepo('nodesource-source').with('proxy_password' => 'password')
          end
        end

        context 'and repo_proxy_username set to absent' do
          let :params do
            default_params.merge!(repo_proxy_username: 'absent')
          end

          it 'the yumrepo resource should contain proxy_username = absent' do
            is_expected.to contain_yumrepo('nodesource').with('proxy_username' => 'absent')
            is_expected.to contain_yumrepo('nodesource-source').with('proxy_username' => 'absent')
          end
        end

        context 'and repo_proxy_username set to proxyuser' do
          let :params do
            default_params.merge!(repo_proxy_username: 'proxyuser')
          end

          it 'the yumrepo resource should contain proxy_username = proxyuser' do
            is_expected.to contain_yumrepo('nodesource').with('proxy_username' => 'proxyuser')
            is_expected.to contain_yumrepo('nodesource-source').with('proxy_username' => 'proxyuser')
          end
        end
      end

      context 'with manage_package_repo set to false' do
        let :params do
          {
            manage_package_repo: false
          }
        end

        it '::nodejs::repo::nodesource should not be in the catalog' do
          is_expected.not_to contain_class('::nodejs::repo::nodesource')
        end
      end

      # nodejs_debug_package_ensure
      context 'with nodejs_debug_package_ensure set to present' do
        let :params do
          {
            nodejs_debug_package_ensure: 'present'
          }
        end

        it 'the nodejs package with debugging symbols should be installed' do
          is_expected.to contain_package('nodejs-debuginfo').with('ensure' => 'present')
        end
      end

      context 'with nodejs_debug_package_ensure set to absent' do
        let :params do
          {
            nodejs_debug_package_ensure: 'absent'
          }
        end

        it 'the nodejs package with debugging symbols should not be present' do
          is_expected.to contain_package('nodejs-debuginfo').with('ensure' => 'absent')
        end
      end

      # nodejs_dev_package_ensure
      context 'with nodejs_dev_package_ensure set to present' do
        let :params do
          {
            nodejs_dev_package_ensure: 'present'
          }
        end

        it 'the nodejs development package should be installed' do
          is_expected.to contain_package('nodejs-devel').with('ensure' => 'present')
        end
      end

      context 'with nodejs_dev_package_ensure set to absent' do
        let :params do
          {
            nodejs_dev_package_ensure: 'absent'
          }
        end

        it 'the nodejs development package should not be present' do
          is_expected.to contain_package('nodejs-devel').with('ensure' => 'absent')
        end
      end

      # nodejs_package_ensure
      context 'with nodejs_package_ensure set to present' do
        let :params do
          {
            nodejs_package_ensure: 'present'
          }
        end

        it 'the nodejs package should be present' do
          is_expected.to contain_package('nodejs').with('ensure' => 'present')
        end
      end

      context 'with nodejs_package_ensure set to absent' do
        let :params do
          {
            nodejs_package_ensure: 'absent'
          }
        end

        it 'the nodejs package should be absent' do
          is_expected.to contain_package('nodejs').with('ensure' => 'absent')
        end
      end

      # npm_package_ensure
      context 'with npm_package_ensure set to present' do
        let :params do
          {
            npm_package_ensure: 'present'
          }
        end

        it 'the npm package should be present' do
          is_expected.to contain_package('npm').with('ensure' => 'present')
        end
      end

      context 'with npm_package_ensure set to absent' do
        let :params do
          {
            npm_package_ensure: 'absent'
          }
        end

        it 'the npm package should be absent' do
          is_expected.to contain_package('npm').with('ensure' => 'absent')
        end
      end
    end
  end

  context 'when running on Suse' do
    let :facts do
      {
        osfamily: 'Suse',
        operatingsystem: 'SLES'
      }
    end

    # nodejs_debug_package_ensure
    context 'with nodejs_debug_package_ensure set to present' do
      let :params do
        {
          nodejs_debug_package_ensure: 'present'
        }
      end

      it 'the nodejs package with debugging symbols should be installed' do
        is_expected.to contain_package('nodejs-debuginfo').with('ensure' => 'present')
      end
    end

    context 'with nodejs_debug_package_ensure set to absent' do
      let :params do
        {
          nodejs_debug_package_ensure: 'absent'
        }
      end

      it 'the nodejs package with debugging symbols should not be present' do
        is_expected.to contain_package('nodejs-debuginfo').with('ensure' => 'absent')
      end
    end

    # nodejs_dev_package_ensure
    context 'with nodejs_dev_package_ensure set to present' do
      let :params do
        {
          nodejs_dev_package_ensure: 'present'
        }
      end

      it 'the nodejs development package should be installed' do
        is_expected.to contain_package('nodejs-devel').with('ensure' => 'present')
      end
    end

    context 'with nodejs_dev_package_ensure set to absent' do
      let :params do
        {
          nodejs_dev_package_ensure: 'absent'
        }
      end

      it 'the nodejs development package should not be present' do
        is_expected.to contain_package('nodejs-devel').with('ensure' => 'absent')
      end
    end

    # nodejs_package_ensure
    context 'with nodejs_package_ensure set to present' do
      let :params do
        {
          nodejs_package_ensure: 'present'
        }
      end

      it 'the nodejs package should be present' do
        is_expected.to contain_package('nodejs').with('ensure' => 'present')
      end
    end

    context 'with nodejs_package_ensure set to absent' do
      let :params do
        {
          nodejs_package_ensure: 'absent'
        }
      end

      it 'the nodejs package should be absent' do
        is_expected.to contain_package('nodejs').with('ensure' => 'absent')
      end
    end

    # npm_package_ensure
    context 'with npm_package_ensure set to present' do
      let :params do
        {
          npm_package_ensure: 'present'
        }
      end

      it 'the npm package should be present' do
        is_expected.to contain_package('npm').with('ensure' => 'present')
      end
    end

    context 'with npm_package_ensure set to absent' do
      let :params do
        {
          npm_package_ensure: 'absent'
        }
      end

      it 'the npm package should be absent' do
        is_expected.to contain_package('npm').with('ensure' => 'absent')
      end
    end
  end

  context 'when running on Archlinux' do
    let :facts do
      {
        osfamily: 'Archlinux',
        operatingsystem: 'Archlinux'
      }
    end

    # nodejs_package_ensure
    context 'with nodejs_package_ensure set to present' do
      let :params do
        {
          nodejs_package_ensure: 'present'
        }
      end

      it 'the nodejs package should be present' do
        is_expected.to contain_package('nodejs').with('ensure' => 'present')
      end
    end

    context 'with nodejs_package_ensure set to absent' do
      let :params do
        {
          nodejs_package_ensure: 'absent'
        }
      end

      it 'the nodejs package should be absent' do
        is_expected.to contain_package('nodejs').with('ensure' => 'absent')
      end
    end
  end

  context 'when running on FreeBSD' do
    let :facts do
      {
        osfamily: 'FreeBSD',
        operatingsystem: 'FreeBSD'
      }
    end

    # nodejs_dev_package_ensure
    context 'with nodejs_dev_package_ensure set to present' do
      let :params do
        {
          nodejs_dev_package_ensure: 'present'
        }
      end

      it 'the nodejs development package should be installed' do
        is_expected.to contain_package('www/node-devel').with('ensure' => 'present')
      end
    end

    context 'with nodejs_dev_package_ensure set to absent' do
      let :params do
        {
          nodejs_dev_package_ensure: 'absent'
        }
      end

      it 'the nodejs development package should not be present' do
        is_expected.to contain_package('www/node-devel').with('ensure' => 'absent')
      end
    end

    # nodejs_package_ensure
    context 'with nodejs_package_ensure set to present' do
      let :params do
        {
          nodejs_package_ensure: 'present'
        }
      end

      it 'the nodejs package should be present' do
        is_expected.to contain_package('www/node').with('ensure' => 'present')
      end
    end

    context 'with nodejs_package_ensure set to absent' do
      let :params do
        {
          nodejs_package_ensure: 'absent'
        }
      end

      it 'the nodejs package should be absent' do
        is_expected.to contain_package('www/node').with('ensure' => 'absent')
      end
    end

    # npm_package_ensure
    context 'with npm_package_ensure set to present' do
      let :params do
        {
          npm_package_ensure: 'present'
        }
      end

      it 'the npm package should be present' do
        is_expected.to contain_package('www/npm').with('ensure' => 'present')
      end
    end

    context 'with npm_package_ensure set to absent' do
      let :params do
        {
          npm_package_ensure: 'absent'
        }
      end

      it 'the npm package should be absent' do
        is_expected.to contain_package('www/npm').with('ensure' => 'absent')
      end
    end
  end

  context 'when running on OpenBSD' do
    let :facts do
      {
        osfamily: 'OpenBSD',
        operatingsystem: 'OpenBSD'
      }
    end

    # nodejs_package_ensure
    context 'with nodejs_package_ensure set to present' do
      let :params do
        {
          nodejs_package_ensure: 'present'
        }
      end

      it 'the nodejs package should be present' do
        is_expected.to contain_package('node').with('ensure' => 'present')
      end
    end

    context 'with nodejs_package_ensure set to absent' do
      let :params do
        {
          nodejs_package_ensure: 'absent'
        }
      end

      it 'the nodejs package should be absent' do
        is_expected.to contain_package('node').with('ensure' => 'absent')
      end
    end
  end

  context 'when running on Darwin' do
    let :facts do
      {
        osfamily: 'Darwin',
        operatingsystem: 'Darwin'
      }
    end

    # nodejs_dev_package_ensure
    context 'with nodejs_dev_package_ensure set to present' do
      let :params do
        {
          nodejs_dev_package_ensure: 'present'
        }
      end

      it 'the nodejs development package should be installed' do
        is_expected.to contain_package('nodejs-devel').with('ensure' => 'present')
      end
    end

    context 'with nodejs_dev_package_ensure set to absent' do
      let :params do
        {
          nodejs_dev_package_ensure: 'absent'
        }
      end

      it 'the nodejs development package should not be present' do
        is_expected.to contain_package('nodejs-devel').with('ensure' => 'absent')
      end
    end

    # nodejs_package_ensure
    context 'with nodejs_package_ensure set to present' do
      let :params do
        {
          nodejs_package_ensure: 'present'
        }
      end

      it 'the nodejs package should be present' do
        is_expected.to contain_package('nodejs').with('ensure' => 'present')
      end
    end

    context 'with nodejs_package_ensure set to absent' do
      let :params do
        {
          nodejs_package_ensure: 'absent'
        }
      end

      it 'the nodejs package should be absent' do
        is_expected.to contain_package('nodejs').with('ensure' => 'absent')
      end
    end

    # npm_package_ensure
    context 'with npm_package_ensure set to present' do
      let :params do
        {
          npm_package_ensure: 'present'
        }
      end

      it 'the npm package should be present' do
        is_expected.to contain_package('npm').with('ensure' => 'present')
      end
    end

    context 'with npm_package_ensure set to absent' do
      let :params do
        {
          npm_package_ensure: 'absent'
        }
      end

      it 'the npm package should be absent' do
        is_expected.to contain_package('npm').with('ensure' => 'absent')
      end
    end
  end

  context 'when running on Windows' do
    let :facts do
      {
        osfamily: 'Windows',
        operatingsystem: 'Windows'
      }
    end

    # nodejs_package_ensure
    context 'with nodejs_package_ensure set to present' do
      let :params do
        {
          nodejs_package_ensure: 'present'
        }
      end

      it 'the nodejs package should be present' do
        is_expected.to contain_package('nodejs').with('ensure' => 'present')
      end
    end

    context 'with nodejs_package_ensure set to absent' do
      let :params do
        {
          nodejs_package_ensure: 'absent'
        }
      end

      it 'the nodejs package should be absent' do
        is_expected.to contain_package('nodejs').with('ensure' => 'absent')
      end
    end

    # npm_package_ensure
    context 'with npm_package_ensure set to present' do
      let :params do
        {
          npm_package_ensure: 'present'
        }
      end

      it 'the npm package should be present' do
        is_expected.to contain_package('npm').with('ensure' => 'present')
      end
    end

    context 'with npm_package_ensure set to absent' do
      let :params do
        {
          npm_package_ensure: 'absent'
        }
      end

      it 'the npm package should be absent' do
        is_expected.to contain_package('npm').with('ensure' => 'absent')
      end
    end
  end

  context 'when running on Gentoo' do
    let :facts do
      { osfamily: 'Linux', operatingsystem: 'Gentoo' }
    end

    # nodejs_package_ensure
    context 'with nodejs_package_ensure set to present' do
      let :params do
        {
          nodejs_package_ensure: 'present'
        }
      end

      it 'the nodejs package should be present' do
        is_expected.to contain_package('net-libs/nodejs').with('ensure' => 'present')
      end
    end

    context 'with nodejs_package_ensure set to absent' do
      let :params do
        {
          nodejs_package_ensure: 'absent'
        }
      end

      it 'the nodejs package should be absent' do
        is_expected.to contain_package('net-libs/nodejs').with('ensure' => 'absent')
      end
    end

    context 'with use_flags set to npm, snapshot' do
      let :params do
        {
          use_flags: %w(npm snapshot)
        }
      end

      it 'the nodejs package should have npm, snapshot use flags' do
        is_expected.to contain_package_use('net-libs/nodejs').with('use' => %w(npm snapshot))
      end
    end
  end

  context 'when running on Amazon Linux 2014.09' do
    let :facts do
      {
        osfamily: 'Linux',
        operatingsystem: 'Amazon',
        operatingsystemrelease: '2014.09'
      }
    end

    repo_baseurl        = 'https://rpm.nodesource.com/pub_0.10/el/7/$basearch'
    repo_source_baseurl = 'https://rpm.nodesource.com/pub_0.10/el/7/SRPMS'
    repo_descr          = 'Node.js Packages for Enterprise Linux 7 - $basearch'
    repo_source_descr   = 'Node.js for Enterprise Linux 7 - $basearch - Source'

    # manage_package_repo
    context 'with manage_package_repo set to true' do
      let :default_params do
        {
          manage_package_repo: true
        }
      end

      context 'and repo_class set to ::nodejs::repo::nodesource' do
        let :params do
          default_params.merge!(repo_class: 'nodejs::repo::nodesource')
        end

        it '::nodejs::repo::nodesource should be in the catalog' do
          is_expected.to contain_class('nodejs::repo::nodesource')
        end

        it '::nodejs::repo::nodesource::yum should be in the catalog' do
          is_expected.to contain_class('nodejs::repo::nodesource::yum')
        end

        it 'the nodesource and nodesource-source repos should contain the right description and baseurl' do
          is_expected.to contain_yumrepo('nodesource').with('baseurl' => repo_baseurl,
                                                            'descr'   => repo_descr)

          is_expected.to contain_yumrepo('nodesource-source').with('baseurl' => repo_source_baseurl,
                                                                   'descr'   => repo_source_descr)
        end
      end

      context 'and repo_enable_src set to true' do
        let :params do
          default_params.merge!(repo_enable_src: true)
        end

        it 'the yumrepo resource nodesource-source should contain enabled = 1' do
          is_expected.to contain_yumrepo('nodesource-source').with('enabled' => '1')
        end
      end

      context 'and repo_enable_src set to false' do
        let :params do
          default_params.merge!(repo_enable_src: false)
        end

        it 'the yumrepo resource should contain enabled = 0' do
          is_expected.to contain_yumrepo('nodesource-source').with('enabled' => '0')
        end
      end

      context 'and repo_ensure set to present' do
        let :params do
          default_params.merge!(repo_ensure: 'present')
        end

        it 'the nodesource yum repo files should exist' do
          is_expected.to contain_yumrepo('nodesource')
          is_expected.to contain_yumrepo('nodesource-source')
        end
      end

      context 'and repo_ensure set to absent' do
        let :params do
          default_params.merge!(repo_ensure: 'absent')
        end

        it 'the nodesource yum repo files should not exist' do
          is_expected.to contain_yumrepo('nodesource').with('enabled' => 'absent')
          is_expected.to contain_yumrepo('nodesource-source').with('enabled' => 'absent')
        end
      end

      context 'and repo_proxy set to absent' do
        let :params do
          default_params.merge!(repo_proxy: 'absent')
        end

        it 'the yumrepo resource should contain proxy = absent' do
          is_expected.to contain_yumrepo('nodesource').with('proxy' => 'absent')
          is_expected.to contain_yumrepo('nodesource-source').with('proxy' => 'absent')
        end
      end

      context 'and repo_proxy set to http://proxy.localdomain.com' do
        let :params do
          default_params.merge!(repo_proxy: 'http://proxy.localdomain.com')
        end

        it 'the yumrepo resource should contain proxy = http://proxy.localdomain.com' do
          is_expected.to contain_yumrepo('nodesource').with('proxy' => 'http://proxy.localdomain.com')
          is_expected.to contain_yumrepo('nodesource-source').with('proxy' => 'http://proxy.localdomain.com')
        end
      end

      context 'and repo_proxy_password set to absent' do
        let :params do
          default_params.merge!(repo_proxy_password: 'absent')
        end

        it 'the yumrepo resource should contain proxy_password = absent' do
          is_expected.to contain_yumrepo('nodesource').with('proxy_password' => 'absent')
          is_expected.to contain_yumrepo('nodesource-source').with('proxy_password' => 'absent')
        end
      end

      context 'and repo_proxy_password set to password' do
        let :params do
          default_params.merge!(repo_proxy_password: 'password')
        end

        it 'the yumrepo resource should contain proxy_password = password' do
          is_expected.to contain_yumrepo('nodesource').with('proxy_password' => 'password')
          is_expected.to contain_yumrepo('nodesource-source').with('proxy_password' => 'password')
        end
      end

      context 'and repo_proxy_username set to absent' do
        let :params do
          default_params.merge!(repo_proxy_username: 'absent')
        end

        it 'the yumrepo resource should contain proxy_username = absent' do
          is_expected.to contain_yumrepo('nodesource').with('proxy_username' => 'absent')
          is_expected.to contain_yumrepo('nodesource-source').with('proxy_username' => 'absent')
        end
      end

      context 'and repo_proxy_username set to proxyuser' do
        let :params do
          default_params.merge!(repo_proxy_username: 'proxyuser')
        end

        it 'the yumrepo resource should contain proxy_username = proxyuser' do
          is_expected.to contain_yumrepo('nodesource').with('proxy_username' => 'proxyuser')
          is_expected.to contain_yumrepo('nodesource-source').with('proxy_username' => 'proxyuser')
        end
      end
    end

    context 'with manage_package_repo set to false' do
      let :params do
        {
          manage_package_repo: false
        }
      end

      it '::nodejs::repo::nodesource should not be in the catalog' do
        is_expected.not_to contain_class('::nodejs::repo::nodesource')
      end
    end

    # nodejs_debug_package_ensure
    context 'with nodejs_debug_package_ensure set to present' do
      let :params do
        {
          nodejs_debug_package_ensure: 'present'
        }
      end

      it 'the nodejs package with debugging symbols should be installed' do
        is_expected.to contain_package('nodejs-debuginfo').with('ensure' => 'present')
      end
    end

    context 'with nodejs_debug_package_ensure set to absent' do
      let :params do
        {
          nodejs_debug_package_ensure: 'absent'
        }
      end

      it 'the nodejs package with debugging symbols should not be present' do
        is_expected.to contain_package('nodejs-debuginfo').with('ensure' => 'absent')
      end
    end

    # nodejs_dev_package_ensure
    context 'with nodejs_dev_package_ensure set to present' do
      let :params do
        {
          nodejs_dev_package_ensure: 'present'
        }
      end

      it 'the nodejs development package should be installed' do
        is_expected.to contain_package('nodejs-devel').with('ensure' => 'present')
      end
    end

    context 'with nodejs_dev_package_ensure set to absent' do
      let :params do
        {
          nodejs_dev_package_ensure: 'absent'
        }
      end

      it 'the nodejs development package should not be present' do
        is_expected.to contain_package('nodejs-devel').with('ensure' => 'absent')
      end
    end

    # nodejs_package_ensure
    context 'with nodejs_package_ensure set to present' do
      let :params do
        {
          nodejs_package_ensure: 'present'
        }
      end

      it 'the nodejs package should be present' do
        is_expected.to contain_package('nodejs').with('ensure' => 'present')
      end
    end

    context 'with nodejs_package_ensure set to absent' do
      let :params do
        {
          nodejs_package_ensure: 'absent'
        }
      end

      it 'the nodejs package should be absent' do
        is_expected.to contain_package('nodejs').with('ensure' => 'absent')
      end
    end

    # npm_package_ensure
    context 'with npm_package_ensure set to present' do
      let :params do
        {
          npm_package_ensure: 'present'
        }
      end

      it 'the npm package should be present' do
        is_expected.to contain_package('npm').with('ensure' => 'present')
      end
    end

    context 'with npm_package_ensure set to absent' do
      let :params do
        {
          npm_package_ensure: 'absent'
        }
      end

      it 'the npm package should be absent' do
        is_expected.to contain_package('npm').with('ensure' => 'absent')
      end
    end
  end
  context 'when running on Amazon Linux 2015.03' do
    let :facts do
      {
        osfamily: 'RedHat',
        operatingsystem: 'Amazon',
        operatingsystemrelease: '2015.03'
      }
    end

    repo_baseurl        = 'https://rpm.nodesource.com/pub_0.10/el/7/$basearch'
    repo_source_baseurl = 'https://rpm.nodesource.com/pub_0.10/el/7/SRPMS'
    repo_descr          = 'Node.js Packages for Enterprise Linux 7 - $basearch'
    repo_source_descr   = 'Node.js for Enterprise Linux 7 - $basearch - Source'

    # manage_package_repo
    context 'with manage_package_repo set to true' do
      let :default_params do
        {
          manage_package_repo: true
        }
      end

      context 'and repo_class set to ::nodejs::repo::nodesource' do
        let :params do
          default_params.merge!(repo_class: 'nodejs::repo::nodesource')
        end

        it '::nodejs::repo::nodesource should be in the catalog' do
          is_expected.to contain_class('nodejs::repo::nodesource')
        end

        it '::nodejs::repo::nodesource::yum should be in the catalog' do
          is_expected.to contain_class('nodejs::repo::nodesource::yum')
        end

        it 'the nodesource and nodesource-source repos should contain the right description and baseurl' do
          is_expected.to contain_yumrepo('nodesource').with('baseurl' => repo_baseurl,
                                                            'descr'   => repo_descr)

          is_expected.to contain_yumrepo('nodesource-source').with('baseurl' => repo_source_baseurl,
                                                                   'descr'   => repo_source_descr)
        end
      end

      context 'and repo_enable_src set to true' do
        let :params do
          default_params.merge!(repo_enable_src: true)
        end

        it 'the yumrepo resource nodesource-source should contain enabled = 1' do
          is_expected.to contain_yumrepo('nodesource-source').with('enabled' => '1')
        end
      end

      context 'and repo_enable_src set to false' do
        let :params do
          default_params.merge!(repo_enable_src: false)
        end

        it 'the yumrepo resource should contain enabled = 0' do
          is_expected.to contain_yumrepo('nodesource-source').with('enabled' => '0')
        end
      end

      context 'and repo_ensure set to present' do
        let :params do
          default_params.merge!(repo_ensure: 'present')
        end

        it 'the nodesource yum repo files should exist' do
          is_expected.to contain_yumrepo('nodesource')
          is_expected.to contain_yumrepo('nodesource-source')
        end
      end

      context 'and repo_ensure set to absent' do
        let :params do
          default_params.merge!(repo_ensure: 'absent')
        end

        it 'the nodesource yum repo files should not exist' do
          is_expected.to contain_yumrepo('nodesource').with('enabled' => 'absent')
          is_expected.to contain_yumrepo('nodesource-source').with('enabled' => 'absent')
        end
      end

      context 'and repo_proxy set to absent' do
        let :params do
          default_params.merge!(repo_proxy: 'absent')
        end

        it 'the yumrepo resource should contain proxy = absent' do
          is_expected.to contain_yumrepo('nodesource').with('proxy' => 'absent')
          is_expected.to contain_yumrepo('nodesource-source').with('proxy' => 'absent')
        end
      end

      context 'and repo_proxy set to http://proxy.localdomain.com' do
        let :params do
          default_params.merge!(repo_proxy: 'http://proxy.localdomain.com')
        end

        it 'the yumrepo resource should contain proxy = http://proxy.localdomain.com' do
          is_expected.to contain_yumrepo('nodesource').with('proxy' => 'http://proxy.localdomain.com')
          is_expected.to contain_yumrepo('nodesource-source').with('proxy' => 'http://proxy.localdomain.com')
        end
      end

      context 'and repo_proxy_password set to absent' do
        let :params do
          default_params.merge!(repo_proxy_password: 'absent')
        end

        it 'the yumrepo resource should contain proxy_password = absent' do
          is_expected.to contain_yumrepo('nodesource').with('proxy_password' => 'absent')
          is_expected.to contain_yumrepo('nodesource-source').with('proxy_password' => 'absent')
        end
      end

      context 'and repo_proxy_password set to password' do
        let :params do
          default_params.merge!(repo_proxy_password: 'password')
        end

        it 'the yumrepo resource should contain proxy_password = password' do
          is_expected.to contain_yumrepo('nodesource').with('proxy_password' => 'password')
          is_expected.to contain_yumrepo('nodesource-source').with('proxy_password' => 'password')
        end
      end

      context 'and repo_proxy_username set to absent' do
        let :params do
          default_params.merge!(repo_proxy_username: 'absent')
        end

        it 'the yumrepo resource should contain proxy_username = absent' do
          is_expected.to contain_yumrepo('nodesource').with('proxy_username' => 'absent')
          is_expected.to contain_yumrepo('nodesource-source').with('proxy_username' => 'absent')
        end
      end

      context 'and repo_proxy_username set to proxyuser' do
        let :params do
          default_params.merge!(repo_proxy_username: 'proxyuser')
        end

        it 'the yumrepo resource should contain proxy_username = proxyuser' do
          is_expected.to contain_yumrepo('nodesource').with('proxy_username' => 'proxyuser')
          is_expected.to contain_yumrepo('nodesource-source').with('proxy_username' => 'proxyuser')
        end
      end
    end

    context 'with manage_package_repo set to false' do
      let :params do
        {
          manage_package_repo: false
        }
      end

      it '::nodejs::repo::nodesource should not be in the catalog' do
        is_expected.not_to contain_class('::nodejs::repo::nodesource')
      end
    end

    # nodejs_debug_package_ensure
    context 'with nodejs_debug_package_ensure set to present' do
      let :params do
        {
          nodejs_debug_package_ensure: 'present'
        }
      end

      it 'the nodejs package with debugging symbols should be installed' do
        is_expected.to contain_package('nodejs-debuginfo').with('ensure' => 'present')
      end
    end

    context 'with nodejs_debug_package_ensure set to absent' do
      let :params do
        {
          nodejs_debug_package_ensure: 'absent'
        }
      end

      it 'the nodejs package with debugging symbols should not be present' do
        is_expected.to contain_package('nodejs-debuginfo').with('ensure' => 'absent')
      end
    end

    # nodejs_dev_package_ensure
    context 'with nodejs_dev_package_ensure set to present' do
      let :params do
        {
          nodejs_dev_package_ensure: 'present'
        }
      end

      it 'the nodejs development package should be installed' do
        is_expected.to contain_package('nodejs-devel').with('ensure' => 'present')
      end
    end

    context 'with nodejs_dev_package_ensure set to absent' do
      let :params do
        {
          nodejs_dev_package_ensure: 'absent'
        }
      end

      it 'the nodejs development package should not be present' do
        is_expected.to contain_package('nodejs-devel').with('ensure' => 'absent')
      end
    end

    # nodejs_package_ensure
    context 'with nodejs_package_ensure set to present' do
      let :params do
        {
          nodejs_package_ensure: 'present'
        }
      end

      it 'the nodejs package should be present' do
        is_expected.to contain_package('nodejs').with('ensure' => 'present')
      end
    end

    context 'with nodejs_package_ensure set to absent' do
      let :params do
        {
          nodejs_package_ensure: 'absent'
        }
      end

      it 'the nodejs package should be absent' do
        is_expected.to contain_package('nodejs').with('ensure' => 'absent')
      end
    end

    # npm_package_ensure
    context 'with npm_package_ensure set to present' do
      let :params do
        {
          npm_package_ensure: 'present'
        }
      end

      it 'the npm package should be present' do
        is_expected.to contain_package('npm').with('ensure' => 'present')
      end
    end

    context 'with npm_package_ensure set to absent' do
      let :params do
        {
          npm_package_ensure: 'absent'
        }
      end

      it 'the npm package should be absent' do
        is_expected.to contain_package('npm').with('ensure' => 'absent')
      end
    end
  end
end
