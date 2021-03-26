#!/bin/bash

# Sometimes fixtures are too large to be imported into a single muckrock instance, the COPY statement gets too large, this
# utility isolates each fixture file into its own container. 
# Note this will only work if the fixtures don't have foreign keys that reference each other. 

PATH_TO_MUCKROCK=~/Dev/muckrock
FIXTURE_FILES=
inv=$(command -v inv)

for f in wapo-management/fixtures/*.json
do
  echo "Processing $f"
  # spin up a docker container and load data into the django ORM
	# cd ${PATH_TO_MUCKROCK}
	echo $f
	inv manage "loaddata -v3 $f"
done
