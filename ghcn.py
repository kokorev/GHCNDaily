"""
This module provide basic functions for downloading and reading GHCN daily data
"""

__author__ = 'V. Kokorev'
__email__ = "v.kokorev@utwente.nl"

import numpy as np
import pandas as pd
import os.path
import urllib
import shutil

_base_url = 'ftp://ftp.ncdc.noaa.gov/pub/data/ghcn/daily/'

class GHCNInventory:
    """
    class for reading GHCN inventory and selecting subset of stations to download
    """
    download_url = _base_url + 'ghcnd-inventory.txt'

    def __init__(self, fn, download=False):
        if download:
            self._download(fn)
        self.stations = self.read_file(fn)

    def read_file(self, fn):
        dat = pd.read_fwf(fn, widths=[2, 1, 8, 9, 10, 5, 5, 5],
                          names=('country', 'network_code', 'id', 'lat', 'lon', 'element', 'first_year', 'last_year'))
        dat['st_id'] = dat['country'] + dat['network_code'] + dat['id']
        return dat

    def _download(self, fn):
        with urllib.request.urlopen(self.download_url) as response, open(fn, 'wb') as out_file:
            shutil.copyfileobj(response, out_file)

    def filter(self, country=None, element=None, lat_lon_box=None):
        """
        :param country: country FIPS code or list of codes
        :param element: element type as specified in GHCN documentation
        :param lat_lon_box:
        :return: records from the inventory that fit specified parameters
        """
        mask = np.ones(self.stations.shape[0], bool)
        if country is not None:
            if type(country) is str:
                country = [country]
            for cc in country:
                mask = mask & self._get_mask_country(cc)
        if element is not None:
            if type(element) is str:
                element = [element]
            for v in element:
                mask = mask & self._get_mask_variable(v)
        if lat_lon_box is not None:
            if not hasattr(lat_lon_box[0], '__iter__'):
                lat_lon_box = [lat_lon_box]
            for llb in lat_lon_box:
                mask = mask & self._get_mask_latlonbox(llb)
        return self.stations[mask]

    def _get_mask_country(self, country_code):
        """
        :param country_code: FIPS country code
        :return: bool mask
        """
        country_code = country_code.upper()
        mask = self.stations['country'] == country_code
        return mask

    def _get_mask_variable(self, var):
        return self.stations['element'] == var

    def _get_mask_latlonbox(self, llbox):
        lt_lat, lt_lon, rb_lat, rb_lon = llbox
        ssi = self.stations
        mask = (ssi['lat'] <= lt_lat) & (ssi['lon'] >= lt_lon) & (ssi['lat'] >= rb_lat) & (ssi['lon'] <= rb_lon)
        return mask


class GHCNMeta(GHCNInventory):
    """
    class for reading GHCN meta data as provided in 'ghcnd-stations.txt' and selecting subset of stations to download
    """

    download_url = _base_url + 'ghcnd-stations.txt'

    def read_file(self, fn):
        dat = pd.read_fwf(fn, widths=[2, 1, 8, 9, 10, 7, 3, 31, 4, 4, 6],
                          names=('country', 'network_code', 'id', 'lat', 'lon', 'elevation', 'state',
                                 'name', 'gsn_flag', 'hcn/crn_flag', 'wmo_id'))
        dat['st_id'] = dat['country'] + dat['network_code'] + dat['id']
        return dat

    def get_meta(self, st_ids):
        mask = np.isin(self.stations['st_id'], st_ids)
        return self.stations[mask]


def _flatten(lst):
    return [item for sublist in lst for item in sublist]


dly_fmt_widths = [11, 4, 2, 4] + [5, 1, 1, 1] * 31

dly_fmt_names = ['id', 'year', 'month', 'var'] + \
                _flatten([['val_%i' % i, 'mf_%i' % i, 'qf_%i' % i, 'sf_%i' % i] for i in range(1, 32)])


def read_dly(fn, var, include_flags=True):
    """
    Reads a single element from *.dly file
    :param fn: path to the input file
    :param var: element type to read from the file
    :param include_flags: Include quality control flags in the resulting array
    :return: pandas.Series with Datetime index
    """
    dat = pd.read_fwf(fn, widths=dly_fmt_widths, names=dly_fmt_names)
    var_mask = dat['var'] == var
    dat = dat[var_mask]
    var_vals = dat[dat.columns.intersection(['val_%i' % i for i in range(1, 32)])].values.flatten()
    mf_vals = dat[dat.columns.intersection(['mf_%i' % i for i in range(1, 32)])].values.flatten()
    qf_vals = dat[dat.columns.intersection(['qf_%i' % i for i in range(1, 32)])].values.flatten()
    sf_vals = dat[dat.columns.intersection(['sf_%i' % i for i in range(1, 32)])].values.flatten()
    year_vals = dat['year'].repeat(31).values
    mon_vals = dat['month'].repeat(31).values
    day_vals = list(range(1, 32)) * dat.shape[0]
    dates = pd.to_datetime({'year': year_vals, 'month': mon_vals, 'day': day_vals}, errors='coerce')
    dates_mask = dates.notna()
    dti = pd.DatetimeIndex(dates[dates_mask])
    if include_flags:
        df = pd.DataFrame(
            {var: var_vals[dates_mask], 'mflag': mf_vals[dates_mask],
             'qflag': qf_vals[dates_mask], 'sflag': sf_vals[dates_mask]},
            index=dti)
    else:
        df = pd.DataFrame(
            {var: var_vals[dates_mask]}, index=dti)
    return df[df[var] != -9999]


def download_data(station_ids, directory):
    """
    Download data by station index
    :param station_ids: list of station IDs as used in GHCN
    :param directory: path to directory to store data
    :return: None
    """
    url_template = _base_url + 'all/{}.dly'
    for st_id in station_ids:
        with urllib.request.urlopen(url_template.format(st_id)) as response, \
                open(os.path.join(directory, '{}.dly'.format(st_id)), 'wb') as out_file:
            shutil.copyfileobj(response, out_file)
