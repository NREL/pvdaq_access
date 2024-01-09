
# pvdaq_access
A program to facilitate the download of a system's data from the OEDI website for public NREL PVDAQ Data.

## Overview
Data from public PV Sites is available through the [OEDI Data Lake][1]. This data is refreshed monthly where possible, and is stored in daily CSV or Parquet files for each system. This softeware module will allow a user to downlaod all the data to their local system from the OEDI Data Lake.

### Solar Bounty Data Prize Datasets
Part of the data archives in PVDAQ contains the winning data sets from the 2023 Solar Data Bounty Prize systems. This storage architecture is a bit different, therefore a new function has been added to facilitate this download.

When the software runs it will ask via a console prompt if the system you are downloading is one of the prize sites. If it is, it will extract data from those archives instead of the PVDAQ basic archives.

## Usage
This is an exectuable python packge. It requires the passing of parameters at the start.
* system : Followed by an integer of the system unique ID. 
* path : Followed by a string that targets the local computer location/path you wish the data to be stored into.
* parquet : A flag that changes the data type from default CSV to Parquet file for download.

System IDs for PVDAQ basic sites can be found in the metadata file for Available System Information on the [OEDI site][1]</br>
System IDs for the Prize sites can be found on their repository folders within the PVDAQ Data Lake or from information on the [PVDAQ interactive website][2] 

## Infomation on running the program
When the software starts the user may be prompted for additional information. The software will prompt the user to identify if this is a Solar Data Bounty Prize request or one of the 
PVDAQ basic sites. If the this is one of the PVDAQ basic sites the software will further ask, after the download of files,  if the user wants to concatenate all the files into a single time-series 
file for analysis.  

### Processing
The PVDAQ basic data will be downloaded as the series of daily files. At this point you can then concatenate the files together using the built in function to create a full time-series for the system. 
We decided to maintain the daily files for download, due to the size of the final file. In some cases, this could be quite large and to take an extreme amount of time to download.

For the Solar Data Bounty Prize files, these are curated files that have been broken down into a series of hardware specific and in some cases, yearly files. To concatenate these files could be 
difficult to do without prepration since some systems have many years of data and thousands of columns. 

For these larger Data Prize systems we advise assuring the local system being downloaded to has enough space and that there are not any bandwidth network issues to address. In some cases
you could be downloading hundreds of gigabytes of data. Plan accordingly.

[1]:https://data.openei.org/submissions/4568
[2]:https://openei.org/wiki/PVDAQ
