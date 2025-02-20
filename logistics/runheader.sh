#!/bin/bash

# Directory to parse
directory="/Users/camille/Documents/runs/phantom/database/wind"
exec_dir="/Users/camille/Documents/PhantomDatabase"
exec='showheader'
file='wind_*'


for subfolder in "$directory"/*/; do
    if [ -d "$subfolder" ]; then
        echo "Running showheader in $subfolder"
        cp $exec_dir/$exec $subfolder
        cd "$subfolder" 
        ./$exec wind_* > header.txt
    fi
done
