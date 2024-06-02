#!/bin/bash

# Check if dates.txt exists
if [ ! -f dates.txt ]; then
    echo "Error: dates.txt not found!"
    exit 1
fi

mkdir -p kedro_output

# Loop through each line in dates.txt
while IFS= read -r date; do
    export DAY_REQUEST="$date"
    echo "DAY_REQUEST=\"$DAY_REQUEST\" has been set"

    output_dir=kedro_output/output_${date}

    # Check if the output directory is not empty
    if [ -d "${output_dir}" ] && [ "$(ls -A ${output_dir})" ]; then
        echo "Directory ${output_dir} already exists and is not empty. Skipping iteration."
        continue
    fi

    mkdir -p ${output_dir} # Create the directory if it does not exist or is empty
    kedro run
    mv data/08_model_output/* ${output_dir}
done < dates.txt

python3 oos_neg_count_report.py

