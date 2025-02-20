#!/bin/bash

# Copy the files listed in the filelist.txt file from the remote server to the local machine.

# Define variables
REMOTE_USER="camille"
REMOTE_HOST="copernicus.ster.kuleuven.be"
REMOTE_BASE_DIR="/STER/hydroModels/modelsDatabase"
LOCAL_BASE_DIR="/Users/camille/Documents/runs/phantom/database/wind"
FILE_LIST="/Users/camille/Documents/PhantomDatabase/filelist.txt"

# Read the file list and transfer each file
while IFS= read -r file_path; do
    # Trim the file path to remove useless subdirectories when creating the new local directory
    IFS='/' read -r -a path_array <<< "$file_path"
    array_size=${#path_array[@]}
    target_dir="${LOCAL_BASE_DIR}/${path_array[4]}"
    if [ ! -d "$target_dir" ]; then
        mkdir -p "$target_dir"
    fi
    # copy the file
    rsync -vP "${REMOTE_USER}@${REMOTE_HOST}:${file_path}" "${target_dir}"

done < "$FILE_LIST"