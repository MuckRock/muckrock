## 2016-12-08 Release 2.2.0

- Modulesync with latest Vox Pupuli defaults
- provider: add support for install_options
- Fix: Nodesource 6.x nodejs package replaces nodejs-dev & npm packages on 16.04
- Actually remove gpg_key dependency

## 2016-10-04 Release 2.1.0

### Added

- Fedora 22 and 23 support

### Fixed

- Fix Ubuntu 16.04 support
- Ignore npm cache lines when calling 'npm view' for latest version

### Maintenance

- Modulesync with latest Vox Pupuli defaults


## 2016-06-02 Release 2.0.1

### Fixed

- fix broken Ubuntu Xenial support


## 2016-05-08 Release 2.0.0

### Added

- allow absent for ensure attribute

### Fixed

- Link to badges
- Correct handle of ensure attribute for nodejs

### Maintenance

- partial reformat of code for better readability
- Change npm_package_name default value from "undef" to "false" for better comparison
- Update apt-get database before package installation
- Add node6 support for RHEL6 and RHEL7
- enhance BSD support
- Drop Ruby1.8.7 support


## 2016-01-07 Release 1.3.0

### Fixed

- Improved documentation
- remove dependency on `treydock/gpg_key`
- Fix `repo_url_suffix`
- Minimum Puppet version is now set at >= 3.7.0
- Maximum Puppet version is set to < 5.0.0
- Expanded `global_config_entry`, made more robust

### Maintenance

- Integrated now with modulesync
- Fixed loads of Rubocop complaints


## 2015-08-18 Release 1.2.0

### Added

- Enhanced support for Amazon Linux
- Ability to set HOME environment variable when installing npm

### Fixed

- Misc lint/spec fixes
- Metadata dependency on `treydock/gpg_key`

## 2015-06-23 Release 1.1.0

### Backwards-incompatible changes

nodejs::repo::nodesource::apt is now compatible with puppetlabs-apt 2.x only

### Summary

Debian-based platforms now require puppetlabs-apt 2.x rather than puppetlabs-apt 1.x

## 2015-05-20 Release 1.0.0

### Summary

Module donated by Puppetlabs to Puppet Community.
This release fixes support for ArchLinux, since npm recently moved to its own
package.

## 2015-05-12 Release 0.8.0

### Backwards-incompatible changes

- Puppet versions below 3.4.0 are no longer supported
- Debian Squeeze and Fedora version 18 and below are explicitly no longer
  supported
- Parameter naming changes to node_pkg, npm_pkg, dev_pkg, manage_repo,
  dev_pkg to approximate equivalents: nodejs_package_name, npm_package_name,
  nodejs_dev_package_name, manage_package_repo, nodejs_dev_package_ensure
- RedHat-family operating systems now use the NodeSource repository by default
  rather than the Fedora People repositories
- Debian Wheezy now uses the NodeSource repository by default rather than the
  Debian Sid repository
- The proxy parameter has been removed. Equivalent functionality can be
  obtained by using the nodejs::npm::global_config_entry defined type
- The version parameter has been removed. The approximate equivalent is
  nodejs_package_ensure (or nodejs_dev_package_ensure)
- The nodejs::npm defined type title is now an arbitary unique string rather
  than 'destination_dir:package'. The same functionality is now done with
  the target and package parameters.
- The nodejs::npm version parameter has been removed. The same functionality
  can now be performed with the ensure parameter
- Parameter naming changes to install_opt, remove_opt in nodejs::npm to
  approximate equivalents install_options and uninstall_options. Both must
  now be an array of strings and not strings.

### Summary

This release performs major API changes and defaults to using the NodeSource
repository where possible.

#### Features

- Defaults to using the NodeSource repositories where possible, but allows
  native packages to be installed when appropriate parameters are set
- Introduces a parameter repo_class, which allows one to use alternative
  repositories like EPEL for the Node.js packages
- Adds Windows installation support via Chocolatey
- Adds FreeBSD and OpenBSD installation support
- Adds tag and scope support to the defined type nodejs::npm
- Adds a defined type nodejs::npm::global_config_entry, which allows one to
  set and delete global npm config options

#### Bugfixes

- Supercedes PRs 99 (MODULES-1075), 97, 96, 94, 93, 85, 82, 80, 79, 51, 69, 66
  and 102
- apt: update. pin to version. change key to 40 characters.
- Debian: Handle NodeSource. Improve Repository handling.
- windows: dont use deprecated chocolately module.
- testing: Pin RSpec version.

## 2015-01-21 - Release 0.7.1

### Summary

This fixes the incorrect application of https://github.com/puppetlabs/puppetlabs-nodejs/pull/70 so that the code will actually run.

## 2015-01-20 - Release 0.7.0

### Summary

This release adds some new features and improvements, including archlinux support and improved ubuntu support.

#### Features

- Add max_nesting parameter to npm list json parse
- Replace Chris's PPA with the Nodesource repo
- Parameterize package names
- Add archlinux support
- TravisCI updates

#### Bugfixes

- Fix proxy config requiers for Ubunutu
- Fix rspec tests
- Fix typo in README.md

## 2014-07-15 - Release 0.6.1

### Summary

This release merely updates metadata.json so the module can be uninstalled and
upgraded via the puppet module command.

## 2014-06-18 - Release 0.6.0

### Summary

This release primarily has improved support for Gentoo and testing
improvements.

#### Features

- Improved Gentoo support.
- Test updates

## 2014-03-20 - Release 0.5.0

### Summary

This release is just a wrap up of a number of submitted PRs, mostly around
improvements to operating system support, as well as some improvements to
handling npm.

#### Features

- Update travis to test more recent versions of Puppet.
- Changed package name for Amazon Linux.
- Add support for Scientific Linux.

#### Bugfixes

- Ubuntu uses uppercase for the operatingsystem fact.
- Ignore exit codes from "npm list --json" as they can be misleading, and instead just parse the JSON.
- Set $HOME for npm commands.
- Don't include development version accidently.
- Fix for chrislea ppa that already installs npm.

## 2013-08-29 - Release 0.4.0

### Summary

This release removes the precise special handling
and adds the ability to pass in $version.

#### Features

- Precise uses the same ppa as every other release.
- New parameters in nodejs:
- `version`: Set the version to install.

## 2013-08-01 - Release 0.3.0

### Summary

The focus of this release is ensuring the module
still works on newer distributions.

#### Features

- New parameters in nodejs:
- `manage_repo`: Enable/Disable repo management.

#### Bugfixes

- Fixed npm on Ubuntuwhen using Chris Lea's PPA
- Make RHEL6 variants the default.
- Fix yumrepo file ordering.

## Release 0.2.1 2012-12-28 Puppet Labs <info@puppetlabs.com>

- Updated EL RPM repositories

## Release 0.2.0 2012-05-22 Puppet Labs <info@puppetlabs.com>

- Add RedHat family support
- Use npm package instead of exec script.
- Remove ppa repo for Ubuntu Precise.

## Release 0.1.1 2012-05-04 Puppet Labs <info@puppetlabs.com>

- Use include for apt class and add spec tests.

## Release 0.1.0 2012-04-30 Puppet Labs <info@puppetlabs.com>

- Initial module release.
