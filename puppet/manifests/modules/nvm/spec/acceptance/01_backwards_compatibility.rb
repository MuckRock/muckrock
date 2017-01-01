require 'spec_helper_acceptance'

describe 'nvm::node::install define' do

  describe 'running puppet code' do
    pp = <<-EOS
        class { 'nvm':
            user        => 'bar',
            manage_user => true,
        }

        nvm::node::install { '5.6.0':
            user    => 'bar',
            default => true,
        }
    EOS
    let(:manifest) { pp }

    it 'should work with no errors' do
      apply_manifest(manifest, :catch_failures => true)
    end

    it 'should not be idempotent and should throw a deprection warning' do
      apply_manifest(manifest, :expect_changes => true)
    end

    describe command('su - foo -c ". /home/foo/.nvm/nvm.sh && nvm --version" -s /bin/bash') do
      its(:exit_status) { should eq 0 }
      its(:stdout) { should match /0.29.0/ }
    end

    describe command('su - foo -c ". /home/foo/.nvm/nvm.sh && node --version" -s /bin/bash') do
      its(:exit_status) { should eq 0 }
      its(:stdout) { should match /5.6.0/ }
    end

  end

end
