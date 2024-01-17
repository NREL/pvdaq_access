#!/usr/bin/env python
# coding: utf-8

# # 2 - Running RdTools on the data
# 
# **Objectives:**
# 1. Load the already downloaded data from tutorial 1
# 2. Run an RdTools analysis

# ## 1. Setup

# In[ ]:


# if running on google colab, uncomment the next line and execute this cell to install the dependencies and prevent "ModuleNotFoundError" in later cells:
get_ipython().system('pip install rdtools')
get_ipython().system('pip install -r https://raw.githubusercontent.com/NREL/rdtools/main/docs/notebook_requirements.txt')


# In[ ]:


import pvanalytics
pvanalytics.__version__
import pvlib
import matplotlib
import matplotlib.pyplot as plt
import pandas as pd
import pathlib  # this might not be needed as working on same directory as data here?
from datetime import timedelta
import rdtools


# In[ ]:


# This information helps with debugging and getting support :)
import sys, platform
print("Working on a ", platform.system(), platform.release())
print("Python version ", sys.version)
print("Pandas version ", pd.__version__)
print("PVlib version ", pvlib.__version__)
print("rdtools version ", rdtools.__version__)


# In[ ]:


testfolder = 'Tuesday'

if not os.path.exists(testfolder):
    os.makedirs(testfolder)


# In[2]:


#Update the style of plots
matplotlib.rcParams.update({'font.size': 12,
                           'figure.figsize': [4.5, 3],
                           'lines.markeredgewidth': 0,
                           'lines.markersize': 2
                           })
# Register time series plotting in pandas > 1.0
from pandas.plotting import register_matplotlib_converters
register_matplotlib_converters()


# In[3]:


# Set the random seed for numpy to ensure consistent results
np.random.seed(0)


# ## 1. Load data and run RdTools

# ## Degradation and soiling example with clearsky workflow
# 
# The calculations consist of several steps illustrated here:
# 
# <ol start="0">
#   <li><b>Import and preliminary calculations</b></li>
#   <li><b>Normalize</b> data using a performance metric</li>
#   <li><b>Filter</b> data that creates bias</li>
#   <li><b>Aggregate data</b></li>
#   <li> <b>Analyze</b> aggregated data to estimate the degradation rate</li>
#   <li> <b>Analyze</b> aggregated data to estimate the soiling loss</li>
# </ol>
# 
# After demonstrating these steps using sensor data, a modified version of the workflow is illustrated using modled clear sky irradiance and temperature. The results from the two methods are compared
# 

# # UPDTE THIS TO PVDAQ DATA
# This notebook works with public data from the the Desert Knowledge Australia Solar Centre. Please download the site data from Site 12, and unzip the csv file in the folder:
# ./rdtools/docs/
# 
# http://dkasolarcentre.com.au/download?location=alice-springs

# ## 0: Import and preliminary calculations
# 
# 
# This section prepares the data necesary for an `rdtools` calculation. The first step of the `rdtools` workflow is normaliztion, which requires a time series of energy yield, a time series of cell temperature, and a time series of irradiance, along with some metadata (see Step 1: Normalize)
# 
# The following section loads the data, adjusts units where needed, and renames the critical columns. The irradiance sensor data source is transposed to plane-of-array, and the temperature sensor data source is converted into estimated cell temperature.
# 
# A common challenge is handling datasets with and without daylight savings time. Make sure to specify a `pytz` timezone that does or does not include daylight savings time as appropriate for your dataset.
# 
# <b>The steps of this section may change depending on your data source or the system being considered. Note that nothing in this first section utlizes the `rdtools` library.</b> Transposition of irradiance and modeling of cell temperature are generally outside the scope of `rdtools`. A variety of tools for these calculations are avaialble in [pvlib](https://github.com/pvlib/pvlib-python).

# In[4]:


file_name = '84-Site_12-BP-Solar.csv'

df = pd.read_csv(file_name)
try:
    df.columns = [col.decode('utf-8') for col in df.columns]
except AttributeError:
    pass  # Python 3 strings are already unicode literals
df = df.rename(columns = {
    u'12 BP Solar - Active Power (kW)':'power',
    u'12 BP Solar - Wind Speed (m/s)': 'wind_speed',
    u'12 BP Solar - Weather Temperature Celsius (\xb0C)': 'Tamb',
    u'12 BP Solar - Global Horizontal Radiation (W/m\xb2)': 'ghi',
    u'12 BP Solar - Diffuse Horizontal Radiation (W/m\xb2)': 'dhi'
})

# Specify the Metadata
meta = {"latitude": -23.762028,
        "longitude": 133.874886,
        "timezone": 'Australia/North',
        "gamma_pdc": -0.005,
        "azimuth": 0,
        "tilt": 20,
        "power_dc_rated": 5100.0,
        "temp_model_params": pvlib.temperature.TEMPERATURE_MODEL_PARAMETERS['sapm']['open_rack_glass_polymer']}

df.index = pd.to_datetime(df.Timestamp)
# TZ is required for irradiance transposition
df.index = df.index.tz_localize(meta['timezone'], ambiguous = 'infer') 

# Explicitly trim the dates so that runs of this example notebook 
# are comparable when the sourec dataset has been downloaded at different times
df = df['2008-11-11':'2017-05-15']

# Chage power from kilowatts to watts
df['power'] = df.power * 1000.0

# There is some missing data, but we can infer the frequency from the first several data points
freq = pd.infer_freq(df.index[:10])

# Then set the frequency of the dataframe.
# It is reccomended not to up- or downsample at this step
# but rather to use interpolate to regularize the time series
# to it's dominant or underlying frequency. Interpolate is not
# generally recomended for downsampleing in this applicaiton.
df = rdtools.interpolate(df, freq)

# Calculate energy yield in Wh
df['energy'] = rdtools.energy_from_power(df.power)

# Calculate POA irradiance from DHI, GHI inputs
loc = pvlib.location.Location(meta['latitude'], meta['longitude'], tz = meta['timezone'])
sun = loc.get_solarposition(df.index)

# calculate the POA irradiance
sky = pvlib.irradiance.isotropic(meta['tilt'], df.dhi)
df['dni'] = (df.ghi - df.dhi)/np.cos(np.deg2rad(sun.zenith))
beam = pvlib.irradiance.beam_component(meta['tilt'], meta['azimuth'], sun.zenith, sun.azimuth, df.dni)
df['poa'] = beam + sky

# Calculate cell temperature
df['Tcell'] = pvlib.temperature.sapm_cell(df.poa, df.Tamb, df.wind_speed, **meta['temp_model_params'])

# plot the AC power time series
fig, ax = plt.subplots(figsize=(4,3))
ax.plot(df.index, df.power, 'o', alpha = 0.01)
ax.set_ylim(0,7000)
fig.autofmt_xdate()
ax.set_ylabel('AC Power (W)');


# ## 1: Normalize
# 
# Data normalization is achieved with `rdtools.normalize_with_pvwatts()`. We provide a time sereis of energy, along with keywords used to run a pvwatts model of the system. More information available in the docstring.

# In[5]:


# Specify the keywords for the pvwatts model
pvwatts_kws = {"poa_global" : df.poa,
              "power_dc_rated" : meta['power_dc_rated'],
              "temperature_cell" : df.Tcell,
              "poa_global_ref" : 1000,
              "temperature_cell_ref": 25,
              "gamma_pdc" : meta['gamma_pdc']}

# Calculate the normaliztion, the function also returns the relevant insolation for
# each point in the normalized PV energy timeseries
normalized, insolation = rdtools.normalize_with_pvwatts(df.energy, pvwatts_kws)

df['normalized'] = normalized
df['insolation'] = insolation

# Plot the normalized power time series
fig, ax = plt.subplots()
ax.plot(normalized.index, normalized, 'o', alpha = 0.05)
ax.set_ylim(0,2)
fig.autofmt_xdate()
ax.set_ylabel('Normalized energy');


# ## 2: Filter
# 
# Data filtering is used to exclude data points that represent invalid data, create bias in the analysis, or introduce significant noise.
# 
# It can also be useful to remove outages and outliers. Sometimes outages appear as low but non-zero yield. Automatic functions for this are not yet included in `rdtools`. Such filters should be implimented by the analyst if needed.

# In[6]:


# Calculate a collection of boolean masks that can be used
# to filter the time series
normalized_mask = rdtools.normalized_filter(df['normalized'])
poa_mask = rdtools.poa_filter(df['poa'])
tcell_mask = rdtools.tcell_filter(df['Tcell'])
clip_mask = rdtools.clip_filter(df['power'])

# filter the time series and keep only the columns needed for the
# remaining steps
filtered = df[normalized_mask & poa_mask & tcell_mask & clip_mask]
filtered = filtered[['insolation', 'normalized']]

fig, ax = plt.subplots()
ax.plot(filtered.index, filtered.normalized, 'o', alpha = 0.05)
ax.set_ylim(0,2)
fig.autofmt_xdate()
ax.set_ylabel('Normalized energy');


# ## 3: Aggregate
# 
# Data is aggregated with an irradiance weighted average. This can be useful, for example with daily aggregation, to reduce the impact of high-error data points in the morning and evening.

# In[7]:


daily = rdtools.aggregation_insol(filtered.normalized, filtered.insolation, frequency = 'D')

fig, ax = plt.subplots()
ax.plot(daily.index, daily, 'o', alpha = 0.1)
ax.set_ylim(0,2)
fig.autofmt_xdate()
ax.set_ylabel('Normalized energy');


# ## 4: Degradation calculation
# 
# Data is then analyzed to estimate the degradation rate representing the PV system behavior. The results are visualized and statistics are reported, including the 68.2% confidence interval, and the P95 exceedence value.

# In[8]:


# Calculate the degradation rate using the YoY method
yoy_rd, yoy_ci, yoy_info = rdtools.degradation_year_on_year(daily, confidence_level=68.2)
# Note the default confidence_level of 68.2 is approrpriate if you would like to 
# report a confidence interval analogous to the standard deviation of a normal
# distribution. The size of the confidence interval is adjustable by setting the
# confidence_level variable.

# Visualize the results

degradation_fig = rdtools.degradation_summary_plots(yoy_rd, yoy_ci, yoy_info, daily,
                                                    summary_title='Sensor-based degradation results',
                                                    scatter_ymin=0.5, scatter_ymax=1.1,
                                                    hist_xmin=-30, hist_xmax=45)


# In addition to the confidence interval, the year-on-year method yields an exceedence value (e.g. P95), the degradation rate that was exceeded (slower degradation) with a given probability level. The probability level is set via the `exceedence_prob` keyword in `degradation_year_on_year`.

# In[9]:


print('The P95 exceedance level is %.2f%%/yr' % yoy_info['exceedance_level'])


# ## 5: Soiling calculations  
# 
# This section illustrates how the aggreagated data can be used to estimate soiling losses using the stochastic rate and recovery (SRR) method.<sup>1</sup>
# 
# <sup>1</sup>M. G. Deceglie, L. Micheli and M. Muller, "Quantifying Soiling Loss Directly From PV Yield," IEEE Journal of Photovoltaics, vol. 8, no. 2, pp. 547-551, March 2018. doi: 10.1109/JPHOTOV.2017.2784682

# In[10]:


# Calculate the daily insolation, required for the SRR calculation
daily_insolation = filtered['insolation'].resample('D').sum()

# Perform the SRR calculation
from rdtools.soiling import soiling_srr
cl = 68.2
sr, sr_ci, soiling_info = soiling_srr(daily, daily_insolation, confidence_level=cl)


# In[11]:


print('The P50 insolation-weighted soiling ratio is %0.3f'%sr)


# In[12]:


print('The %0.1f confidence interval for the insolation-weighted'
      ' soiling ratio is %0.3f–%0.3f'%(cl, sr_ci[0], sr_ci[1]))


# In[13]:


# Plot Monte Carlo realizations of soiling profiles
fig = rdtools.plotting.soiling_monte_carlo_plot(soiling_info, daily, profiles=200);


# In[14]:


# Plot the slopes for "valid" soiling intervals identified,
# assuming perfect cleaning events
fig = rdtools.plotting.soiling_interval_plot(soiling_info, daily);


# In[15]:


# View the first several rows of the soiling interval summary table
soiling_summary = soiling_info['soiling_interval_summary']
soiling_summary.head()


# In[16]:


# View a histogram of the valid soiling rates found for the data set
fig = rdtools.plotting.soiling_rate_histogram(soiling_info, bins=15)


# ## Clear sky workflow
# The clear sky workflow is useful in that it avoids problems due to drift or recalibration of ground-based sensors. We use `pvlib` to model the clear sky irradiance. This is renormalized to align it with ground-based measurements. Finally we use `rdtools.get_clearsky_tamb()` to model the ambient temperature on clear sky days. This modeled ambient temperature is used to model cell temperature with `pvlib`. If high quality amabient temperature data is available, that can be used instead of the modeled ambient; we proceed with the modeled ambient temperature here for illustrative purposes.
# 
# In this example, note that we have omitted wind data in the cell temperature calculations for illustrative purposes. Wind data can also be included when the data source is trusted for improved results
# 
# **Note that the claculations below rely on some objects from the steps above**

# ## Clear Sky 0: Preliminary Calculations

# In[17]:


# Calculate the clear sky POA irradiance
# Note: an earlier version of this notebook modeled clear-sky POA irradiance as
# instantaneous values rather than interval averages.  See https://github.com/NREL/rdtools/issues/243
times = pd.date_range(df.index.min(), df.index.max(), freq='1min')
sun1min = loc.get_solarposition(times)
clearsky = loc.get_clearsky(times, solar_position=sun1min)
# Note: An earlier version of this notebook used pvlib<0.6. In pvlib 0.6, the default 
# behavior of get_clearsky() changed, which affects the results of this example notebook.
# More details: https://github.com/pvlib/pvlib-python/issues/435
cs_sky = pvlib.irradiance.isotropic(meta['tilt'], clearsky.dhi)
cs_beam = pvlib.irradiance.beam_component(meta['tilt'], meta['azimuth'], sun1min.zenith, sun1min.azimuth, clearsky.dni)
cs_total = cs_beam + cs_sky
# aggregate 1-minute model to the resolution of the measured data:
df['clearsky_poa'] = cs_total.resample(freq, label='right').mean()

# Renormalize the clear sky POA irradiance
df['clearsky_poa'] = rdtools.irradiance_rescale(df.poa, df.clearsky_poa, method='iterative')

# Calculate the clearsky temperature
df['clearsky_Tamb'] = rdtools.get_clearsky_tamb(df.index, meta['latitude'], meta['longitude'])
df['clearsky_Tcell'] = pvlib.temperature.sapm_cell(df.clearsky_poa, df.clearsky_Tamb, 0, **meta['temp_model_params'])


# ## Clear Sky 1: Normalize
# Normalize as in step 1 above, but this time using clearsky modeled irradiance and cell temperature

# In[18]:


clearsky_pvwatts_kws = {"poa_global" : df.clearsky_poa,
              "power_dc_rated" : meta['power_dc_rated'],
              "temperature_cell" :df.clearsky_Tcell,
              "poa_global_ref" : 1000,
              "temperature_cell_ref": 25,
              "gamma_pdc" : meta['gamma_pdc']}

clearsky_normalized, clearsky_insolation = rdtools.normalize_with_pvwatts(df.energy, clearsky_pvwatts_kws)

df['clearsky_normalized'] = clearsky_normalized
df['clearsky_insolation'] = clearsky_insolation


# ## Clear Sky 2: Filter
# Filter as in step 2 above, but with the addition of a clear sky index (csi) filter so we consider only points well modeled by the clear sky irradiance model.

# In[19]:


# Perform clearsky filter
cs_normalized_mask = rdtools.normalized_filter(df['clearsky_normalized'])
cs_poa_mask = rdtools.poa_filter(df['clearsky_poa'])
cs_tcell_mask = rdtools.tcell_filter(df['clearsky_Tcell'])

csi_mask = rdtools.csi_filter(df.insolation, df.clearsky_insolation)


clearsky_filtered = df[cs_normalized_mask & cs_poa_mask & cs_tcell_mask & clip_mask & csi_mask]
clearsky_filtered = clearsky_filtered[['clearsky_insolation', 'clearsky_normalized']]


# ## Clear Sky 3: Aggregate
# Aggregate the clear sky version of of the filtered data 

# In[20]:


clearsky_daily = rdtools.aggregation_insol(clearsky_filtered.clearsky_normalized, clearsky_filtered.clearsky_insolation)


# ## Clear Sky 4: Degradation Calculation
# Estimate the degradation rate and compare to the results obtained with sensors. In this case, we see that irradiance sensor drift may have biased the sensor-based results, a problem that is corrected by the clear sky approach.

# In[21]:


# Calculate the degradation rate using the YoY method
cs_yoy_rd, cs_yoy_ci, cs_yoy_info = rdtools.degradation_year_on_year(clearsky_daily, confidence_level=68.2)
# Note the default confidence_level of 68.2 is approrpriate if you would like to 
# report a confidence interval analogous to the standard deviation of a normal
# distribution. The size of the confidence interval is adjustable by setting the
# confidence_level variable.

# Visualize the results
clearsky_fig = rdtools.degradation_summary_plots(cs_yoy_rd, cs_yoy_ci, cs_yoy_info, clearsky_daily,
                                                    summary_title='Clear-sky-based degradation results',
                                                    scatter_ymin=0.5, scatter_ymax=1.1,
                                                    hist_xmin=-30, hist_xmax=45, plot_color='orangered');

print('The P95 exceedance level with the clear sky analysis is %.2f%%/yr' % cs_yoy_info['exceedance_level'])


# In[22]:


# Compare to previous sensor restuls
degradation_fig


# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:





# In[ ]:




