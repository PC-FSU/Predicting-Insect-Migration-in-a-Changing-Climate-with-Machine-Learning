#!/bin/bash

# Define the list of insects and their corresponding download sources
declare -A insects
insects=(
    # ["Brown_Marmorated_Stink_bug"]="EDD"
    ["Corn_Earworm"]="EDD"
    # ["Large_Lady_Beetle"]="EDD"
    # ["Brown_Marmorated_Stink_bug_2"]="GBIF"
    # ["Root_Weevil"]="GBIF"
)

# Define the list of climate data sources and their types
declare -A climate_sources
climate_sources=(
    # ["Worldclim"]="WorldClim"
    ["Cds"]="CDS"
)

# Iterate over each insect and download source
for insect in "${!insects[@]}"; do
    DOWNLOAD_SOURCE="${insects[$insect]}"
    INSECT_NAME="$insect"

    echo "Processing Insect: $INSECT_NAME"
    echo "Download Source: $DOWNLOAD_SOURCE"

    # Iterate over each climate data source
    for climate in "${!climate_sources[@]}"; do
        CLIMATE_SOURCE="${climate_sources[$climate]}"
        
        echo "Using Climate Data Source: $CLIMATE_SOURCE"

        # Add your command to run the Python script or code here, e.g.
        python pipeline_prepare_presence_points.py --insect_name "$INSECT_NAME" --download_source "$DOWNLOAD_SOURCE" --climate_source "$CLIMATE_SOURCE"

        #python pipeline_prepare_background_points.py --insect_name "$INSECT_NAME" --download_source "$DOWNLOAD_SOURCE" --climate_source "$CLIMATE_SOURCE" --use_Bias_raster True

        echo "Finished processing $INSECT_NAME with $DOWNLOAD_SOURCE using $CLIMATE_SOURCE"
        echo ""
    done
done