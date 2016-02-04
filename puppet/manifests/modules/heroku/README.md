Puppet module to install the [Heroku
Toolbelt](https://toolbelt.heroku.com) on linux. Note that this does not
install the bundled git, forman and other tools, just the heroku client.

[![Build
Status](https://secure.travis-ci.org/garethr/garethr-heroku.png)](http://travis-ci.org/garethr/garethr-heroku)

## Usage

    include 'heroku'

## Configuration

If you were being particularly fancy you can configure a few things,
specifically the destination directory, the download directory for the
tar and the URL where the client will be downloaded from.

    class { 'heroku':
      heroku_client_url  => 'http://assets.heroku.com.s3.amazonaws.com/heroku-client/heroku-client.tgz',
      install_parent_dir => '/usr/local',
      artifact_dir       => '/usr/local/src/heroku',
      link_dir           => '/usr/local/heroku'
    }

The above examples show the defaults if you don't override anything.

## Dependencies

Note that this module requires the
[maestrodev/wget](http://forge.pupppetabs.com/maestrodev/wget) module
which is marked as a dependency in the Modulefile.
