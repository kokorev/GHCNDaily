# GHCN Daily
Unofficial tools to download and read meteorological data from GHCN daily archive.

GHCN daily homepage - https://www.ncdc.noaa.gov/ghcn-daily-description

## Requirements
This project was only tested in the following enviroment but in principle should work with any recent version of Python, NumPy, and Pandas

Python 3.6

Numpy 1.15

Pandas 0.23


## Example

```python
# download stations meta information to the file and read it
inv = GHCNInventory('ghcn-inventory.txt', download=True)
# select precipitation data in Kazahstan
st_list = inv.filter(country = 'KZ', element = 'PRCP')
# download data for selected stations and save in to the ./data/ directory
download_data(st_list['st_id'], './data/')
fn = "./data/{}.dly".format(st_list['st_id'].iloc[0])
# read station data to pandas array
dat = read_dly(fn, 'PRCP', include_flags=True)
dat['PRCP'].plot()
```
