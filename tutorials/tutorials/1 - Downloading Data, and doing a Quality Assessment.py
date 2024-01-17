#!/usr/bin/env python
# coding: utf-8

# # 1 - Downloading Data, and doing a Quality Assessment
# 
# **Objectives:**
# 1. Install software
# 2. Donwload dataset
# 3. Run a clear-sky pvanalytics routine (or other)

# ## 1. Setup

# In[ ]:


# if running on google colab, uncomment the next line and execute this cell to install the dependencies and prevent "ModuleNotFoundError" in later cells:
# Dev branch example: !pip install git+https://github.com/NREL/PV_ICE.git@development
get_ipython().system('pip install -r https://raw.githubusercontent.com/NREL/pvdaq_access/main/requirements.txt')
get_ipython().system('pip install pvanalytics')


# In[ ]:


import pvanalytics
pvanalytics.__version__
from pvanalytics.features.clearsky import reno       #update to just do a pvanalytics import?
import pvlib
import matplotlib.pyplot as plt
import pandas as pd
import pathlib  # this might not be needed as working on same directory as data here?


# In[ ]:


# This information helps with debugging and getting support :)
import sys, platform
print("Working on a ", platform.system(), platform.release())
print("Python version ", sys.version)
print("Pandas version ", pd.__version__)
print("PVlib version ", pvlib.__version__)
print("pvanalytics version ", pvanalytics.__version__)
print("pvdaq_access version ", None)


# In[ ]:


testfolder = 'Tuesday'

if not os.path.exists(testfolder):
    os.makedirs(testfolder)


# ## 2. Download

# pvdaq Script :( 

# In[ ]:


import os
import boto3
import botocore
import argparse
from botocore.handlers import disable_signing
import pandas as pd

#---------------------------------------------------------------------------   
def downloadSolarPrizeData(system_id, path, file_type='csv'):
    '''
    Method to access and pull Solar Data Bounty Prize datasets from 
    the OEDI Data Lake for PVDAQ
    Parameters:
    -----------------------
    system_id : str - system id value found from query of Solar Data Prize systems 
    available .
    path : str - local system location files are to be stored in.
    file_type : str - default is .csv, but parquet canbe passed in as option
    
    Returns
    -----------------------
    void
    
    '''
    s3 = boto3.resource("s3")
    s3.meta.client.meta.events.register("choose-signer.s3.*", disable_signing)
    bucket = s3.Bucket("oedi-data-lake")
    
    #Find each target file in buckets
    target_dir = system_id + '_OEDI'
    prefix =  "pvdaq/2023-solar-data-prize/" +  target_dir + "/data/"
    objects = bucket.objects.filter(Prefix=prefix)
    
    for obj in objects:
        if obj.key == prefix:
            continue            
        try:
            bucket.download_file(obj.key, os.path.join(path, os.path.basename(obj.key)).replace("\\", "/"))
        except botocore.exceptions.ClientError as e:
            print ('ERROR: Boto3 exception ' + str(e))
        else:
            print ('File ' + os.path.join(path, os.path.basename(obj.key)) + " downloaded successfully.")
            
    return


#---------------------------------------------------------------------------   
def downloadData(system_id, path, file_type='csv'):
    '''
    Method to access and pull data from the OEDI Data Lake for PVDAQ
    Parameters:
    -----------------------
    system_id : str - system id value found from query of OEDI PVDAQ queue 
    of available .
    path : str - local system location files are to be stored in.
    file_type : str - default is .csv, but parquet canbe passed in as option
    
    Returns
    -----------------------
    void
    
    '''
    s3 = boto3.resource("s3")
    s3.meta.client.meta.events.register("choose-signer.s3.*", disable_signing)
    bucket = s3.Bucket("oedi-data-lake")
    
    #Find each target file in buckets
    objects = bucket.objects.filter(
        Prefix="pvdaq/" + file_type + "/pvdata/system_id=" + system_id )
    
    for obj in objects:
        try:
            bucket.download_file(obj.key, os.path.join(path, os.path.basename(obj.key)))
        except botocore.exceptions.ClientError as e:
            print ('ERROR: Boto3 exception ' + str(e))
        else:
            print ('File ' + os.path.join(path, os.path.basename(obj.key)) + " downloaded successfully.")
            
    return


#---------------------------------------------------------------------------   
def concatenateData(system_id, path):
    '''
    Method to merge the multiple files coming in from OEDI
    Parameters:
    -----------------------
    system_id : str - system id value found from query of OEDI PVDAQ queue 
    of available .
    path : str - local system location files are to be stored in.
    
    Returns
    -----------------------
    void
    
    '''
    dfs = []
    #get list of files in directory
    file_list=os.listdir(path)
    column_name = 'sensor_name'
    #Build a dataframe from current file
    print ("Starting data extraction")
    for file in file_list:
        print("Extracting file " + file)
        df_file= pd.read_csv(path + '/' + file)
        dfs.append(df_file)
         
    #Build the master data frame from the assembled individual frames.
    print ("Concatenating all files")
    df = pd.concat(dfs, ignore_index=True)
    target_outputfile = path + "/system_" + system_id + "_data.csv"
    print ("File is " + target_outputfile)
    df.to_csv(target_outputfile, sep=",", index=False)
    return


# Actually running now

# In[ ]:


print (" ..: Starting data access script for PVDAQ OEDI datasets :..")

#Get parameters from command line
parser = argparse.ArgumentParser()
parser.add_argument('-system', type=str,  help="Target system ID")
parser.add_argument('-path', type=str,  help="Location to store files locally")
parser.add_argument('-parquet', help="Access parquet files (default is .csv)", action="store_true")
args = parser.parse_args()

if args.system:
    input_string = input("Are you accessing data from the DOE Solar Data Bounty Prize: (Y/N): ")
    #Handle Solar Data Bounty Prize archives
    if input_string.lower() == 'y':
        downloadSolarPrizeData(args.system, args.path, file_type='csv')
        quit()

    else:   #Normal PVDAQ archives
        if args.parquet:
            downloadData(args.system, args.path, file_type='parquet')
        else:
            downloadData(args.system, args.path)
            #Create single file from data
            input_string = input("Do you wish to concatenate the files (Y/N): ") 
            if input_string.lower() == 'y':
                concatenateData(args.system, args.path)
else:
    print('Missing system_id, Exiting.')


# # 3. Look at the data
# 
# just one plot

# In[ ]:





# # 4. Do PVAnalytics Clear-Sky Detection
# 
# Identifying periods of clear-sky conditions using measured irradiance.
# 

# Identifying and filtering for clear-sky conditions is a useful way to
# reduce noise when analyzing measured data.  This example shows how to
# use :py:func:`pvanalytics.features.clearsky.reno` to identify clear-sky
# conditions using measured GHI data.  For this example we'll use
# GHI measurements downloaded
# 
# 

# In[ ]:


import pvanalytics
from pvanalytics.features.clearsky import reno
import pvlib
import matplotlib.pyplot as plt
import pandas as pd
import pathlib


# First, read in the GHI measurements.  For this example we'll use an example
# file included in pvanalytics covering a single day, but the same process
# applies to data of any length.
# 
# 

# In[ ]:


pvanalytics_dir = pathlib.Path(pvanalytics.__file__).parent
ghi_file = pvanalytics_dir / 'data' / 'midc_bms_ghi_20220120.csv'
data = pd.read_csv(ghi_file, index_col=0, parse_dates=True)

# or you can fetch the data straight from the source using pvlib:
# date = pd.to_datetime('2022-01-20')
# data = pvlib.iotools.read_midc_raw_data_from_nrel('BMS', date, date)

measured_ghi = data['Global CMP22 (vent/cor) [W/m^2]']


# Now model clear-sky irradiance for the location and times of the
# measured data:
# 
# 

# In[ ]:


location = pvlib.location.Location(39.742, -105.18)
clearsky = location.get_clearsky(data.index)
clearsky_ghi = clearsky['ghi']


# Finally, use :py:func:`pvanalytics.features.clearsky.reno` to identify
# measurements during clear-sky conditions:
# 
# 

# In[ ]:


is_clearsky = reno(measured_ghi, clearsky_ghi)

# clear-sky times indicated in black
measured_ghi.plot()
measured_ghi[is_clearsky].plot(ls='', marker='o', ms=2, c='k')
plt.ylabel('Global Horizontal Irradiance [W/m2]')
plt.show()

