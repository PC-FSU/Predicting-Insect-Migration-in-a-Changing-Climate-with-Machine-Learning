import numpy as np
import rasterio
import xarray as xr
import glob
import os
import pathlib
import matplotlib.pyplot as plt
from maxent_insect_dir.config import *

def compute_rolling_val(data, period=12, window_size=3):
    """
    Computes rolling sums for a given period and window size. This function adds padding 
    to wrap around and include data from previous months.

    Parameters:
        data (xarray.DataArray): The input data (e.g., temperature or precipitation).
        period (int): The period over which rolling is performed (e.g., 12 months).
        window_size (int): The window size for rolling.

    Returns:
        xarray.DataArray: Rolling sums aligned with the original time dimension.
    """
    pad_length = window_size - 1
    time_size = data.time.size

    # Calculate padding indices to wrap around and include data from 12 months back
    pad_indices = [(data.shape[0] // period - 1) * period + i for i in range(pad_length)]
    padding_data = data.isel(time=pad_indices)

    # Concatenate the data along the 'time' dimension
    padded_da = xr.concat([data, padding_data], dim='time')

    # Perform the rolling sum along 'time'
    rolling_sum = padded_da.rolling(time=window_size, center=False).sum()

    # Shift the rolling sum to align with the starting index
    aligned_rolling_sum = rolling_sum.shift(time=-(window_size - 1))

    # Slice back to the original 'time' dimension size
    aligned_rolling_sum = aligned_rolling_sum.isel(time=slice(0, time_size))

    # Reassign the original 'time' coordinate
    aligned_rolling_sum = aligned_rolling_sum.assign_coords(time=data.time)
    
    return aligned_rolling_sum


def compute_quarterly_extremes(data_prec, data_tavg, period=12, mode='max', on='prec'):
    """
    Computes quarterly extremes for precipitation or temperature data, identifying 
    the wettest, driest, warmest, or coldest quarter.

    Parameters:
        data_prec (xarray.DataArray): Precipitation data.
        data_tavg (xarray.DataArray): Average temperature data.
        period (int): Period to evaluate (e.g., 12 months).
        mode (str): 'max' or 'min' to compute the respective extremes.
        on (str): Variable to compute the extremes on ('prec' or 'temp').

    Returns:
        tuple: A tuple containing the precipitation, temperature, and index for the extreme quarter.
    """
    assert data_prec.shape[0] % period == 0

    idx = []
    precip = []
    tavg = []
    num_year = data_prec.shape[0] / period

    data = data_prec if on == 'prec' else data_tavg    
    nan_replacement = -1e10 if mode == 'max' else 1e10

    # Replace nodata values
    data_cleaned = data.where(data != np.nan, np.nan)
    data = data_cleaned.fillna(nan_replacement)

    for i in range(int(num_year)):
        
        if mode == 'max':
            id = period * i + data[period * i: period * (i + 1)].argmax(dim='time')
        elif mode == 'min':
            id = period * i + data[period * i: period * (i + 1)].argmin(dim='time')

        idx.append(id)
        precip.append(data_prec[id])
        tavg.append(data_tavg[id])

    # Remove time dimension and concatenate the results
    precip = xr.concat([da.reset_coords('time', drop=True) for da in precip], dim='time')
    tavg = xr.concat([da.reset_coords('time', drop=True) for da in tavg], dim='time')
    idx = xr.concat(idx, dim='time')

    precip = precip.assign_coords(time=range(len(precip.time)))
    tavg = tavg.assign_coords(time=range(len(tavg.time)))
    idx = idx.assign_coords(time=range(len(idx.time)))

    return precip, tavg, idx




# Bioclimatic Variables Computation Functions

# Bio 1: Annual Mean Temperature
def compute_BIO1(tavg, period=12):
    """
    Computes Bio1: Annual Mean Temperature. This is the average temperature for a given year.

    Parameters:
        tavg (xarray.DataArray): Average temperature data.
        period (int): Period (e.g., 12 for 12 months).

    Returns:
        xarray.DataArray: Annual mean temperature.
    """
    return tavg.coarsen(time=period, boundary='exact').mean()

# Bio 2: Mean Diurnal Range
def compute_BIO2(tdiff, period=12):
    """
    Computes Bio2: Annual Mean Diurnal Range. This is the average monthly difference 
    between daily maximum and minimum temperatures.

    Parameters:
        tdiff (xarray.DataArray): Temperature difference (tmax - tmin).
        period (int): Period (e.g., 12 for 12 months).

    Returns:
        xarray.DataArray: Annual mean diurnal range.
    """
    return tdiff.coarsen(time=period, boundary='exact').mean()

# Bio 3: Isothermality
def compute_BIO3(Bio2, Bio7):
    """
    Computes Bio3: Isothermality. This is the ratio of Bio2 (mean diurnal range) to Bio7 
    (annual temperature range), multiplied by 100.

    Parameters:
        Bio2 (xarray.DataArray): Mean diurnal range.
        Bio7 (xarray.DataArray): Annual temperature range.

    Returns:
        xarray.DataArray: Isothermality.
    """
    return (Bio2 * 100) / Bio7

# Bio 4: Temperature Seasonality
def compute_BIO4(tavg, period=12):
    """
    Computes Bio4: Temperature Seasonality. This is the standard deviation of monthly 
    temperature averages over a given year.

    Parameters:
        tavg (xarray.DataArray): Average temperature data.
        period (int): Period (e.g., 12 for 12 months).

    Returns:
        xarray.DataArray: Temperature seasonality (standard deviation).
    """
    return tavg.coarsen(time=period, boundary='exact').std(skipna=True)

# Bio 4a: Temperature Seasonality (Coefficient of Variation)
def compute_BIO4a(tkavg, Bio1, period=12):
    """
    Computes Bio4a: Temperature Seasonality (Coefficient of Variation), expressed as a percentage.

    Parameters:
        tkavg (xarray.DataArray): Temperature in Kelvin (tavg + 273.15).
        Bio1 (xarray.DataArray): Annual mean temperature.
        period (int): Period (e.g., 12 for 12 months).

    Returns:
        xarray.DataArray: Temperature seasonality (CV).
    """
    return tkavg.coarsen(time=period, boundary='exact').std(skipna=True) * 100 / (Bio1 + 273.15)

# Bio 5: Max Temperature of Warmest Month
def compute_BIO5(tmax, period=12):
    """
    Computes Bio5: Max Temperature of Warmest Month.

    Parameters:
        tmax (xarray.DataArray): Maximum temperature data.
        period (int): Period (e.g., 12 for 12 months).

    Returns:
        xarray.DataArray: Maximum temperature of the warmest month.
    """
    return tmax.coarsen(time=period, boundary='exact').max()

# Bio 6: Min Temperature of Coldest Month
def compute_BIO6(tmin, period=12):
    """
    Computes Bio6: Min Temperature of Coldest Month.

    Parameters:
        tmin (xarray.DataArray): Minimum temperature data.
        period (int): Period (e.g., 12 for 12 months).

    Returns:
        xarray.DataArray: Minimum temperature of the coldest month.
    """
    return tmin.coarsen(time=period, boundary='exact').min()

# Bio 7: Annual Temperature Range
def compute_BIO7(Bio5, Bio6):
    """
    Computes Bio7: Annual Temperature Range. This is the difference between Bio5 and Bio6.

    Parameters:
        Bio5 (xarray.DataArray): Max temperature of warmest month.
        Bio6 (xarray.DataArray): Min temperature of coldest month.

    Returns:
        xarray.DataArray: Annual temperature range.
    """
    return Bio5 - Bio6

# Bio 8: Mean Temperature of Wettest Quarter
def compute_BIO8(temp, period=3):
    """
    Computes Bio8: Mean Temperature of Wettest Quarter.

    Parameters:
        temp (xarray.DataArray): Temperature during the wettest quarter.
        period (int): Period for the quarter (e.g., 3 months).

    Returns:
        xarray.DataArray: Mean temperature of the wettest quarter.
    """
    return temp / period

# Bio 9: Mean Temperature of Driest Quarter
def compute_BIO9(temp, period=3):
    """
    Computes Bio9: Mean Temperature of Driest Quarter.

    Parameters:
        temp (xarray.DataArray): Temperature during the driest quarter.
        period (int): Period for the quarter (e.g., 3 months).

    Returns:
        xarray.DataArray: Mean temperature of the driest quarter.
    """
    return temp / period

# Bio 10: Mean Temperature of Warmest Quarter
def compute_BIO10(temp, period=3):
    """
    Computes Bio10: Mean Temperature of Warmest Quarter.

    Parameters:
        temp (xarray.DataArray): Temperature during the warmest quarter.
        period (int): Period for the quarter (e.g., 3 months).

    Returns:
        xarray.DataArray: Mean temperature of the warmest quarter.
    """
    return temp / period

# Bio 11: Mean Temperature of Coldest Quarter
def compute_BIO11(temp, period=3):
    """
    Computes Bio11: Mean Temperature of Coldest Quarter.

    Parameters:
        temp (xarray.DataArray): Temperature during the coldest quarter.
        period (int): Period for the quarter (e.g., 3 months).

    Returns:
        xarray.DataArray: Mean temperature of the coldest quarter.
    """
    return temp / period

# Bio 12: Annual Precipitation
def compute_BIO12(prec, period=12):
    """
    Computes Bio12: Annual Precipitation. This is the total precipitation for a given year.

    Parameters:
        prec (xarray.DataArray): Precipitation data.
        period (int): Period (e.g., 12 for 12 months).

    Returns:
        xarray.DataArray: Annual precipitation.
    """
    return prec.coarsen(time=period, boundary='exact').sum()

# Bio 13: Precipitation of Wettest Month
def compute_BIO13(prec, period=12):
    """
    Computes Bio13: Precipitation of Wettest Month.

    Parameters:
        prec (xarray.DataArray): Precipitation data.
        period (int): Period (e.g., 12 for 12 months).

    Returns:
        xarray.DataArray: Precipitation of the wettest month.
    """
    return prec.coarsen(time=period, boundary='exact').max()

# Bio 14: Precipitation of Driest Month
def compute_BIO14(prec, period=12):
    """
    Computes Bio14: Precipitation of Driest Month.

    Parameters:
        prec (xarray.DataArray): Precipitation data.
        period (int): Period (e.g., 12 for 12 months).

    Returns:
        xarray.DataArray: Precipitation of the driest month.
    """
    return prec.coarsen(time=period, boundary='exact').min()

# Bio 15: Precipitation Seasonality
def compute_BIO15(prec, Bio12, period=12):
    """
    Computes Bio15: Precipitation Seasonality, measured as the coefficient of variation 
    of monthly precipitation totals over a given year.

    Parameters:
        prec (xarray.DataArray): Precipitation data.
        Bio12 (xarray.DataArray): Annual precipitation.
        period (int): Period (e.g., 12 for 12 months).

    Returns:
        xarray.DataArray: Precipitation seasonality.
    """
    return prec.coarsen(time=period, boundary='exact').std(skipna=True) * 100 / (Bio12 / period + 1)

# Bio 16: Precipitation of Wettest Quarter
def compute_BIO16(prec_wettest_quarter):
    """
    Computes Bio16: Precipitation of Wettest Quarter.

    Parameters:
        prec_wettest_quarter (xarray.DataArray): Precipitation during the wettest quarter.

    Returns:
        xarray.DataArray: Precipitation of the wettest quarter.
    """
    return prec_wettest_quarter

# Bio 17: Precipitation of Driest Quarter
def compute_BIO17(prec_driest_quarter):
    """
    Computes Bio17: Precipitation of Driest Quarter.

    Parameters:
        prec_driest_quarter (xarray.DataArray): Precipitation during the driest quarter.

    Returns:
        xarray.DataArray: Precipitation of the driest quarter.
    """
    return prec_driest_quarter

# Bio 18: Precipitation of Warmest Quarter
def compute_BIO18(prec_warmest_quarter):
    """
    Computes Bio18: Precipitation of Warmest Quarter.

    Parameters:
        prec_warmest_quarter (xarray.DataArray): Precipitation during the warmest quarter.

    Returns:
        xarray.DataArray: Precipitation of the warmest quarter.
    """
    return prec_warmest_quarter

# Bio 19: Precipitation of Coldest Quarter
def compute_BIO19(prec_coldest_quarter):
    """
    Computes Bio19: Precipitation of Coldest Quarter.

    Parameters:
        prec_coldest_quarter (xarray.DataArray): Precipitation during the coldest quarter.

    Returns:
        xarray.DataArray: Precipitation of the coldest quarter.
    """
    return prec_coldest_quarter


def get_yearly_bioclim(tmax, tmin, prec):
    
    # Ensure tmax, tmin, and prec have the same shape
    assert tmax.shape == tmin.shape == prec.shape

    # Calculate average temperature and temperature difference
    tavg = (tmax + tmin) / 2
    tdiff = tmax - tmin

    # Convert average temperature to Kelvin
    tkavg = tavg + 273.15

    # Compute 3-month rolling values for precipitation and temperature
    print("Computing 3-month rolling values for precipitation and temperature...")
    consecutive_prec_3month = compute_rolling_val(prec)
    consecutive_tavg_3month = compute_rolling_val(tavg)

    # Compute quarterly extremes
    print("Computing quarterly extremes for wettest and driest quarters based on precipitation...")
    prec_wettest_quarter, max_temp_wettest_quarter, _ = compute_quarterly_extremes(
        data_prec=consecutive_prec_3month,
        data_tavg=consecutive_tavg_3month,
        mode='max',
        on='prec'
    )
    
    prec_driest_quarter, min_temp_driest_quarter, _ = compute_quarterly_extremes(
        data_prec=consecutive_prec_3month,
        data_tavg=consecutive_tavg_3month,
        mode='min',
        on='prec'
    )

    print("Computing quarterly extremes for warmest and coldest quarters based on temperature...")
    prec_warmest_quarter, max_temp_warmest_quarter, _ = compute_quarterly_extremes(
        data_prec=consecutive_prec_3month,
        data_tavg=consecutive_tavg_3month,
        mode='max',
        on='temp'
    )

    prec_coldest_quarter, min_temp_coldest_quarter, _ = compute_quarterly_extremes(
        data_prec=consecutive_prec_3month,
        data_tavg=consecutive_tavg_3month,
        mode='min',
        on='temp'
    )

    # Compute BIO variables
    print("Computing BIO variables...")

    # Bio 1
    print("Computing Bio1 (Mean Annual Temperature)...")
    Bio1 = compute_BIO1(tavg)

    # Bio 2
    print("Computing Bio2 (Mean Diurnal Range)...")
    Bio2 = compute_BIO2(tdiff)
    
    # Bio 4
    print("Computing Bio4 (Temperature Seasonality)...")
    Bio4 = compute_BIO4(tavg)
        
    # Bio 4a
    print("Computing Bio4a (Temperature Seasonality alternative)...")
    Bio4a = compute_BIO4a(tkavg, Bio1)
    
    # Bio 5
    print("Computing Bio5 (Max Temperature of Warmest Month)...")
    Bio5 = compute_BIO5(tmax)
    
    # Bio 6
    print("Computing Bio6 (Min Temperature of Coldest Month)...")
    Bio6 = compute_BIO6(tmin)
    
    # Bio 7
    print("Computing Bio7 (Temperature Annual Range)...")
    Bio7 = compute_BIO7(Bio5, Bio6)
    
    # Bio 3
    print("Computing Bio3 (Isothermality)...")
    Bio3 = compute_BIO3(Bio2, Bio7)
    
    # Bio 8
    print("Computing Bio8 (Mean Temperature of Wettest Quarter)...")
    Bio8 = compute_BIO8(max_temp_wettest_quarter)
    
    # Bio 9
    print("Computing Bio9 (Mean Temperature of Driest Quarter)...")
    Bio9 = compute_BIO9(min_temp_driest_quarter)
    
    # Bio 10
    print("Computing Bio10 (Mean Temperature of Warmest Quarter)...")
    Bio10 = compute_BIO10(max_temp_warmest_quarter)
    
    # Bio 11
    print("Computing Bio11 (Mean Temperature of Coldest Quarter)...")
    Bio11 = compute_BIO11(min_temp_coldest_quarter)
    
    # Bio 12
    print("Computing Bio12 (Annual Precipitation)...")
    Bio12 = compute_BIO12(prec)
    
    # Bio 13
    print("Computing Bio13 (Precipitation of Wettest Month)...")
    Bio13 = compute_BIO13(prec)
    
    # Bio 14
    print("Computing Bio14 (Precipitation of Driest Month)...")
    Bio14 = compute_BIO14(prec)
    
    # Bio 15
    print("Computing Bio15 (Precipitation Seasonality)...")
    Bio15 = compute_BIO15(prec, Bio12)
    
    # Bio 16
    print("Computing Bio16 (Precipitation of Wettest Quarter)...")
    Bio16 = prec_wettest_quarter
    
    # Bio 17
    print("Computing Bio17 (Precipitation of Driest Quarter)...")
    Bio17 = prec_driest_quarter
    
    # Bio 18
    print("Computing Bio18 (Precipitation of Warmest Quarter)...")
    Bio18 = prec_warmest_quarter
    
    # Bio 19
    print("Computing Bio19 (Precipitation of Coldest Quarter)...")
    Bio19 = prec_coldest_quarter
    
    # Create a dictionary of Bio variables
    bio_vars = {
        'Bio1': Bio1,
        'Bio2': Bio2,
        'Bio3': Bio3,
        'Bio4': Bio4,
        'Bio4a': Bio4a,
        'Bio5': Bio5,
        'Bio6': Bio6,
        'Bio7': Bio7,
        'Bio8': Bio8,
        'Bio9': Bio9,
        'Bio10': Bio10,
        'Bio11': Bio11,
        'Bio12': Bio12,
        'Bio13': Bio13,
        'Bio14': Bio14,
        'Bio15': Bio15,
        'Bio16': Bio16,
        'Bio17': Bio17,
        'Bio18': Bio18,
        'Bio19': Bio19
    }

    # Extract the shapes of all Bio variables
    shapes = {name: var.shape for name, var in bio_vars.items()}

    # Get the reference shape (shape of the first Bio variable)
    first_shape = next(iter(shapes.values()))

    # Assert that all Bio variables have the same shape
    assert all(shape == first_shape for shape in shapes.values()), (
        f"Not all Bio variables have the same shape. Mismatched shapes: "
        f"{ {name: shape for name, shape in shapes.items() if shape != first_shape} }"
    )

    return bio_vars



def get_avg_bioclims(tmax, tmin, prec):
    bio_vars = get_yearly_bioclim(tmax, tmin, prec)
    res = {}
    for key, value in bio_vars.items():
        res[key] = value.mean(dim='time') # Compute the mean over time
    return res


if __name__ == '__main__':
    
    ################### Use this to debug     
    # Your NumPy arrays
    tmax = np.random.randint(low=0, high=10, size=(24, 2, 2))
    tmin = np.random.randint(low=0, high=10, size=(24, 2, 2))
    prec = np.random.randint(low=0, high=10, size=(24, 2, 2))
    


    # Define dimensions and coordinates
    time = np.arange(1, 25)          # Time steps from 1 to 24
    lat = np.array([10.0, 20.0])     # Example latitude coordinates
    lon = np.array([100.0, 110.0])   # Example longitude coordinates

    # Convert to xarray DataArrays
    tmax = xr.DataArray(
        tmax,
        dims=['time', 'lat', 'lon'],
        coords={'time': time, 'lat': lat, 'lon': lon}
    )

    tmin = xr.DataArray(
        tmin,
        dims=['time', 'lat', 'lon'],
        coords={'time': time, 'lat': lat, 'lon': lon}
    )

    prec = xr.DataArray(
        prec,
        dims=['time', 'lat', 'lon'],
        coords={'time': time, 'lat': lat, 'lon': lon}
    )


    # Ensure tmax, tmin, and prec have the same shape
    assert tmax.shape == tmin.shape == prec.shape
    
    get_avg_bioclims(tmax, tmin, prec) 
    
    tavg = (tmax + tmin) / 2
    tdiff = tmax - tmin
    # convert tavg to tkavg
    tkavg = tavg + 273.15
    
    consecutive_prec_3month = compute_rolling_val(prec, period=3, window_size=2)
    consecutive_tavg_3month = compute_rolling_val(tavg, period=3, window_size=2)


    
    prec_wettest_quarter, max_temp_wettest_quarter, _  = compute_quarterly_extremes(
        consecutive_prec_3month,
        consecutive_tavg_3month,
        period=2,
        mode='max',
        on = 'prec'
    )
    
    prec_driest_quarter, min_temp_driest_quarter, _  = compute_quarterly_extremes(
        consecutive_prec_3month,
        consecutive_tavg_3month,
        period=2,
        mode='min',
        on = 'prec'
    )
    
    prec_warmest_quarter, max_temp_warmest_quarter, _ = compute_quarterly_extremes(
        consecutive_prec_3month,
        consecutive_tavg_3month,
        period=2,
        mode='max',
        on='temp' 
    )
    
    prec_coldest_quarter, min_temp_coldest_quarter, _ = compute_quarterly_extremes(
        consecutive_prec_3month,
        consecutive_tavg_3month,
        period=2,
        mode='min',
        on='temp' 
    )

    
    # Bio 1
    Bio1 = compute_BIO1(tavg, 2)

    # Bio 2
    Bio2 = compute_BIO2(tdiff, 2)
    
    # Bio 4
    Bio4 = compute_BIO4(tavg, 2)
        
    # Bio 4a
    Bio4a = compute_BIO4a(tkavg, Bio1, 2)
    
    # Bio 5
    Bio5 = compute_BIO5(tmax, 2)
    
    # Bio 6
    Bio6 = compute_BIO6(tmin, 2)
    
    # Bio 7
    Bio7 = compute_BIO7(Bio5, Bio6)
    
    # Bio 3
    Bio3 = compute_BIO3(Bio2, Bio7)
    
    # Bio 8
    Bio8 = compute_BIO8(max_temp_wettest_quarter, period=2)
    
    # Bio 9
    Bio9 = compute_BIO9(min_temp_driest_quarter, period=2)
    
    # Bio 10
    Bio10 = compute_BIO10(max_temp_warmest_quarter, period=2)
    
    # Bio 11
    Bio11 = compute_BIO11(min_temp_coldest_quarter, period=2)
    
    # Bio 12
    Bio12 = compute_BIO12(prec, period=2)
    
    # Bio 13
    Bio13 = compute_BIO13(prec, period=2)
    
    
    # Bio 14
    Bio14 = compute_BIO14(prec, period=2)
    
    # Bio 15
    Bio15 = compute_BIO15(prec, Bio12, period=2)
    
    # Bio 16
    Bio16 = prec_wettest_quarter
    
    # Bio 17
    Bio17 = prec_driest_quarter
    
    # Bio 18
    Bio18 = prec_warmest_quarter
    
    # Bio 19
    Bio19 = prec_coldest_quarter
    
