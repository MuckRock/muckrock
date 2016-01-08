require 'spec_helper'

describe 'heroku', :type => :class do

  context 'with no parameters' do
    it { should contain_wget__fetch('download_heroku_toolbelt').with_destination('/usr/local/src/heroku/heroku-client.tgz')}
    it { should contain_exec('untar_heroku_toolbelt').with_cwd('/usr/local')}
    it { should contain_exec('untar_heroku_toolbelt').with_creates('/usr/local/heroku-client')}
    it { should contain_file('/usr/local/src/heroku').with_ensure('directory')}
    it { should contain_file('/usr/local/heroku').with_ensure('link')}
  end

end
