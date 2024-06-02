import os
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from tabulate import tabulate


def get_dates_from_kedro_output(kedro_output_dir):
    """
    Retrieve a list of dates from the subdirectory names under the kedro_output directory.

    Args:
    kedro_output_dir (Path): Path to the kedro_output directory.

    Returns:
    List[str]: List of date strings in 'YYYY-MM-DD' format.
    """
    # Initialize an empty list to store the dates
    dates = []

    # Iterate through the items in the kedro_output directory
    for item in kedro_output_dir.iterdir():
        # Check if the item is a directory and its name starts with 'output_'
        if item.is_dir() and item.name.startswith("output_"):
            # Extract the date part from the directory name
            date_str = item.name.split("output_")[1]
            dates.append(date_str)

    # Sort the dates list
    dates.sort()

    return dates


project_dir = Path("~/zalo-chatlog/")
output_dir = Path(project_dir / "kedro_output")

dates = get_dates_from_kedro_output(output_dir)

# Initialize the report DataFrame
report = pd.DataFrame(columns=["percentage.negative", "percentage.oos", "n_samples"])

# Iterate over each date, read the corresponding Parquet files, and compute the average predictions
for date in dates:
    # Construct the file paths
    negative_file = output_dir / f"output_{date}/chatlog_negative.parquet"
    oos_file = output_dir / f"output_{date}/chatlog_oos.parquet"

    # Initialize averages for the current date
    percentage_negative = None
    percentage_oos = None

    # Check if the negative file exists before attempting to read it
    if negative_file.exists():
        report_negative = pd.read_parquet(negative_file)
        # Compute the average prediction for negative
        percentage_negative = round(report_negative["prediction"].mean() * 100, 2)
    else:
        print(f"Warning: File {negative_file} does not exist.")

    # Check if the oos file exists before attempting to read it
    if oos_file.exists():
        report_oos = pd.read_parquet(oos_file)
        # Compute the average prediction for oos
        percentage_oos = round(report_oos["prediction"].mean() * 100, 2)
    else:
        print(f"Warning: File {oos_file} does not exist.")
    n_samples = len(report_oos)
    # Add the computed averages to the report DataFrame
    report.loc[date] = [percentage_negative, percentage_oos, n_samples]

report = report.dropna()

# Save the report DataFrame to a file if needed
report.to_csv(output_dir / "report.csv")

# Only plot upto recent 30 days
report = report.tail(min(60, len(report)))

report["wd"] = pd.to_datetime(report.index).strftime("%a")

# Plotting
fig, ax1 = plt.subplots(figsize=(15, 5))

# Plot n_samples as bars
ax1.bar(report.index, report["n_samples"], color="lightgrey", label="n_samples")
ax1.set_xlabel("Date")
ax1.set_ylabel("n_samples", color="black")
ax1.tick_params(axis="y", labelcolor="black")

# Rotate x-tick labels
ax1.set_xticklabels(report.index, rotation=90)

# Create a second y-axis for the line plots
ax2 = ax1.twinx()
ax2.plot(
    report.index,
    report["percentage.negative"],
    color="red",
    marker="o",
    label="percentage.negative",
)
ax2.plot(
    report.index,
    report["percentage.oos"],
    color="blue",
    marker="o",
    label="percentage.oos",
)
ax2.set_ylabel("%", color="black")
ax2.tick_params(axis="y", labelcolor="black")

# Title and legends
# plt.title("n_samples as Bars and percentage.negative & percentage.oos as Lines")
# ax1.legend(loc='lower left')
ax2.legend(loc="upper left", bbox_to_anchor=(1, 1))

# Create a secondary x-axis on the top
ax3 = ax1.secondary_xaxis("top")
## Set the day names as the tick labels for the secondary x-axis
ax3.set_xticks(range(len(report)))
ax3.set_xticklabels(report["wd"], rotation=90)

# Show plot
# plt.xticks(rotation=90)
plt.tight_layout()
plt.savefig(output_dir / "oos_neg_chart.png")
