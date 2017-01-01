require 'spec_helper'

describe 'nvm', :type => :class do

  context 'with required param user and default params' do
    let :params do
    {
      :user => 'foo'
    }
    end

    it { should contain_class('nvm::params') }
    it { should contain_class('nvm::install')
            .with_user('foo')
            .with_version('v0.29.0')
            .with_nvm_dir('/home/foo/.nvm')
            .with_nvm_repo('https://github.com/creationix/nvm.git')
            .with_dependencies('[Package[git]{:name=>"git"}, Package[wget]{:name=>"wget"}, Package[make]{:name=>"make"}]')
            .with_refetch(false)
    }
    it { should contain_package('git') }
    it { should contain_package('make') }
    it { should contain_package('wget') }
    it { should_not contain_user('foo') }
    it { should contain_file('ensure /home/foo/.bashrc')
            .with_path('/home/foo/.bashrc')
            .with_owner('foo')
    }
    it { should contain_file_line('add NVM_DIR to profile file')
            .with_path('/home/foo/.bashrc')
    }
    it { should contain_file_line('add . ~/.nvm/nvm.sh to profile file')
            .with_path('/home/foo/.bashrc')
    }
    it { should_not contain_nvm__node__install() }
  end

  context 'with manage_dependencies => false' do
    let :params do
    {
      :user => 'foo',
      :manage_dependencies => false
    }
    end

    it { should contain_class('nvm::install')
            .with_user('foo')
            .with_version('v0.29.0')
            .with_nvm_dir('/home/foo/.nvm')
            .with_nvm_repo('https://github.com/creationix/nvm.git')
            .with_dependencies(nil)
            .with_refetch(false)
    }
    it { should_not contain_package('git') }
    it { should_not contain_package('make') }
    it { should_not contain_package('wget') }
  end

  context 'with manage_user => true and default home' do
    let :params do
    {
      :user => 'foo',
      :manage_user => true
    }
    end

    it { should contain_user('foo')
            .with_ensure('present')
            .with_home('/home/foo')
            .with_managehome(true)
            .that_comes_before('Class[Nvm::Install]')
    }
  end

  context 'with manage_user => true and custom home' do
    let :params do
    {
      :user => 'foo',
      :manage_user => true,
      :home => '/bar/foo'
    }
    end

    it { should contain_user('foo')
            .with_ensure('present')
            .with_home('/bar/foo')
            .with_managehome(true)
            .that_comes_before('Class[Nvm::Install]')
    }
  end

  context 'with manage_profile => false' do
    let :params do
    {
      :user => 'foo',
      :manage_profile => false
    }
    end

    it { should_not contain_file_line('add NVM_DIR to profile file') }
  end

  context 'with install_node => dummyversion' do
    let :params do
    {
      :user => 'foo',
      :install_node => 'dummyversion'
    }
    end

    it { should contain_nvm__node__install('dummyversion')
                    .with_user('foo')
                    .with_nvm_dir('/home/foo/.nvm')
                    .with_set_default(true)
    }
  end

  context 'with multiple node_instances' do
    let :params do
    {
      :user => 'foo',
      :node_instances => {
          '0.10.40' => {},
          '0.12.7'  => {},
      }
    }
    end

    it { should contain_nvm__node__install('0.10.40')
                    .with_user('foo')
                    .with_nvm_dir('/home/foo/.nvm')
    }
    it { should contain_nvm__node__install('0.12.7')
                    .with_user('foo')
                    .with_nvm_dir('/home/foo/.nvm')
    }
  end

  context 'without required param user' do
    it { expect { catalogue }.to raise_error }
  end


end
