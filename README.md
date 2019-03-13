# GHCNDaily
Tools to download and read GHCN daily data

## Example

```python
# download stations meta information to the file and read it
inv = GHCNInventory('ghcn-inventory.txt', download=True)
# select precipitation data in Kazahstan
st_list = inv.filter(country = 'KZ', element = 'PRCP')
# download data for selected stations and save in to the ./data/ directory
download_data(st_list['st_id'], './data/')
fn = "./data/{}.dly".format(st_list['st_id'][0])
# read station data to pandas array
dat = read_dly(fn, 'PRCP', include_flags=True) 
```
