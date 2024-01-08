
# pvdaq_access
A program to facilitate the download of a system's data from the OEDI website for public NREL PVDAQ Data.
<code>
## Overview
Data from public PV Sites is available through the [OEDI Data Lake][1]. This data is refreshed monthly where possible, and is stored in daily CSV or Parquet files for each system. This softeware module will allow a user to downlaod all the data to their local system from the OEDI Data Lake.

## Usage
This is an exectuable python packge. It requires the passing of parameters at the start.
-system : Followed by an integer of the system unique ID which can be found in the metadata file for Available System Information on the [OEDI site][1]
-path : Followed by a string that targets the local computer location/path you wish the data to be stored into.
-parquet : A flag that changes the data type from default CSV to Parquet file for download.

## Processing
The data will be downloaded as the series of daily files. At this point you can then concatenate the files together to create an entire time-series of the system's activity. We suggest using pandas to open each CSV or parquet file and then use pandas.concat() to merge each file's contents as they are opened. 

We decided to maintain the daily files for download, due to the size of the final file. In some cases, this could be quite large and to take an extreme amount of time to download.

</code>
[1]:https://data.openei.org/submissions/4568
