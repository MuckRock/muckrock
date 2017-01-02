#!/bin/bash
set -e

# this runs each of the major platform beaker tests
# this script will run the virtualbox versions of these tests
BEAKER_set=centos-65-x64 BEAKER_destroy=onpass BEAKER_provision=yes bundle exec rake beaker \
    && BEAKER_set=centos-70-x64 BEAKER_destroy=onpass BEAKER_provision=yes bundle exec rake beaker \
    && BEAKER_set=debian-73-x64 BEAKER_destroy=onpass BEAKER_provision=yes bundle exec rake beaker \
    && BEAKER_set=ubuntu-server-12042-x64 BEAKER_destroy=onpass BEAKER_provision=yes bundle exec rake beaker \
    && BEAKER_set=ubuntu-server-1404-x64 BEAKER_destroy=onpass BEAKER_provision=yes bundle exec rake beaker \
