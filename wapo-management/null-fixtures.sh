#!/bin/bash

# recursively find/replace foreign key references in a batch of fixture files

find fixtures -name *.json | xargs sed -iE '.bak' s/'"form":\ [0-9]..*/\"form\":\ null,'/g

# this generates copies of your old files with .bak extensions, run this to cleanup:

# rm fixtures/*.bak
