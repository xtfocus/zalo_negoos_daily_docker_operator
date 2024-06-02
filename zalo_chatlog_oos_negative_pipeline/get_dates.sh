#!/bin/bash

# Check if the correct number of arguments is provided
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <start_date> <end_date>"
    echo "Dates should be in the format YYYY-MM-DD"
    exit 1
fi

# Assign arguments to variables
start_date=$1
end_date=$2

# Validate date format
if ! [[ "$start_date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ && "$end_date" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
    echo "Error: Dates must be in the format YYYY-MM-DD"
    exit 1
fi

# Convert dates to seconds since epoch for comparison
start_date_seconds=$(date -d "$start_date" +%s)
end_date_seconds=$(date -d "$end_date" +%s)

# Validate that end_date is greater than start_date
if [ "$end_date_seconds" -lt "$start_date_seconds" ]; then
    echo "Error: end_date must be later than or equal to start_date"
    exit 1
fi

# Output file
output_file="dates.txt"

# Ensure the output file is empty before starting
> $output_file

# Loop from start_date to end_date
current_date="$start_date"
while [ "$current_date" != "$(date -I -d "$end_date + 1 day")" ]; do
    echo "$current_date" >> $output_file
    current_date=$(date -I -d "$current_date + 1 day")
done

echo "Dates from $start_date to $end_date have been written to $output_file"

