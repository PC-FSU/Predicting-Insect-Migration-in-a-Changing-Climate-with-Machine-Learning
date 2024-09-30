#!/bin/bash

# Define the list of insects and their corresponding download sources
declare -A insects
insects=(
    ["Brown_Marmorated_Stink_bug"]="EDD"
    ["Corn_Earworm"]="EDD"
    ["Large_Lady_Beetle"]="EDD"
    ["Brown_Marmorated_Stink_bug_2"]="GBIF"
    ["Root_Weevil"]="GBIF"
)

# Iterate over each insect and download source
for insect in "${!insects[@]}"; do
    DOWNLOAD_SOURCE="${insects[$insect]}"
    INSECT_NAME="$insect"

    echo "Processing Insect: $INSECT_NAME"
    echo "Download Source: $DOWNLOAD_SOURCE"

    # Add your command to run the Python script or code here, e.g.
    python pipeline_clean_merge_visualize_raw_data_worldclim.py --insect_name "$INSECT_NAME" --download_source "$DOWNLOAD_SOURCE"

    echo "Finished processing $INSECT_NAME with $DOWNLOAD_SOURCE"
    echo ""
done
