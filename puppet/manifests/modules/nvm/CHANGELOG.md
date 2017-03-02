# Change Log for puppet module artberri-nvm

## 2016-02-20 - v1.1.1

### Summary

Ability to install multiple node.js instances with a new parameter.
Minor fixes.

#### Features/Improvements

- New parameter `node_instances` in the `nvm` class accepts a hash for installing multiple node.js instances

#### Deprecated params

- The `default` parameter in the define `nvm::node::install` is now deprecated because [is a reserved word](https://docs.puppetlabs.com/puppet/latest/reference/lang_reserved.html#reserved-words), use `set_default` instead. Backguard compatibilty is added but throws a warning message.

#### Fixes

- All `exec` calls set now a `cwd` param
- Rspec and Beaker tests improved

## 2015-11-11 - v1.0.0

### Summary

After being tested in a production server this module leaves the beta state.
This version include also the first acceptance tests.

#### Features/Improvements

- README.md and CONTRIBUTING.md file improvements and fixes
- Acceptance tests included
- Examples added
