# //////////////////////////////////////////////////////////////////////////////
#                             pvdaq_access.py
# An example method on how to access and extract data
# from the AWS OEDI Datalake for the PVDAQ public
# PV site data.
#
#              -------------------
# author 	         : Robert White
# date         	     : Jan 30, 2023
# copyright       : (C) 2023 by  NREL
# email              : robert.white@nrel.gov
# //////////////////////////////////////////////////////////////////////////////

# //////////////////////////////////////////////////////////////////////////////
#  Copyright (C):  2023 Robert R. White and  NREL
#  This file is part of the PVDRDB/PVDAQ Scripts
#
#  See License.txt file for full description of terms of 
#  BSD 3 - Clause License
# //////////////////////////////////////////////////////////////////////////////

import os
import boto3
import botocore
import argparse
from botocore.handlers import disable_signing
import pandas as pd

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


#---------------------------------------------------------------------------   
#---------------------------------------------------------------------------   
if __name__ == '__main__':
    print (" ..: Starting data access script for PVDAQ OEDI datasets :..")
    
    #Get parameters from command line
    parser = argparse.ArgumentParser()
    parser.add_argument('-system', type=str,  help="Target system ID")
    parser.add_argument('-path', type=str,  help="Location to store files locally")
    parser.add_argument('-parquet', help="Access parquet files (default is .csv)", action="store_true")
    args = parser.parse_args()
       
    if args.system:
        if args.parquet:
            downloadData(args.system, args.path, file_type='parquet')
        else:
            downloadData(args.system, args.path)
            #Create single file from data
            concatenateData(args.system, args.path)            
    else:
        print('Missing system_id, Exiting.')
    
    quit()
    
