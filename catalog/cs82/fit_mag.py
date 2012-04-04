# ====================================================
# Authors:
# Bruno Moraes - bruno.a.l.moraes@gmail.com - 01/Nov/2011
# ====================================================


"""Module to """

##@file fit_mag
#
# This package calculates the limiting magnitude for a given FITS catalogue.
# It has four mandatory arguments: the (input) FITS catalogue path and name,
# the magnitude field name to be used for the calculations (i.e. MAG_AUTO,
# MAG_APER, etc...), the corresponding error field name (i.e. MAGERR_AUTO,
# MAGERR_APER, etc...) and the inferior magnitude value for which a fit of
# of the object number count per magnitude bin should be performed. 
# For a detailed description of the procedure,
# check http://twiki.linea.gov.br/blabla".
# 
# The code can run on an arbitrary list of input FITS catalogues. The outputs
# are a check plot of the number count fitting procedure and an ASCII file,
# with each line corresponding to a FITS catalogue and containing information 
# such as the center coordinates of the image, the mean seeing, the total
# number of objects, the number of galaxies and stars per arcmin^2, the
# limiting magnitude, etc. This output can be used as input for a QA analysis
# of the collection of catalogues.
#
# Executable package: NO


from __future__ import division
import sys
import os
import numpy as np
import matplotlib.pyplot as pl 
import numpy as np
from matplotlib.ticker import MultipleLocator, FormatStrFormatter
import math
import cmath
from scipy import optimize
import collections



def get_tile_name(input_file):

    """
    Gets the tile name from the input file name.

    Given an input in the format 'path/to/file/filename.suffix', this function
    will select the substring 'filename' (using '/' and '.' as cutting points)
    and return it.

    Input:
     - input_file     str : input file path and name

    Output:
     - tile_name      str : filename
    
    ---
    """

    input_name = os.path.basename(input_file)

    string_sup = input_name.index('.')

    tile_name = input_name[0:string_sup]

    return tile_name


def check_if_ldac(hdulist):

    if hdulist[1].name == 'LDAC_IMHEAD' and hdulist[2].name == 'LDAC_OBJECTS':

        return True

    else:

        return False



def get_entry_ldac_header(hdulist_string, entry_name):

    """
    Gets an entry value from a FITS_LDAC header.

    A FITS_LDAC generated by SExtractor has a [1] header in the format
    of a single long string with information on the observing conditions,
    reduction, astrometry, etc. This function takes this LDAC header and
    a field name and outputs the corresponding value (in string format).

    Input:
     - hdulist_string       str : pyfits.open(input_file,ignore_missing_end=True,
                                  memmap=True)[1].data[0][0]
     - entry_name           str : Name of a given LDAC header entry

    Output:
     - entry                str : LDAC header entry value
    
    ---
    """

    entry = hdulist_string[hdulist_string.find(entry_name):]

    entry = entry[0:entry.find('/')]

    entry = ''.join(entry.split())

    entry = str(float(entry[entry.find('=')+1:]))

    return entry


def make_histogram(data, bin_size):

    """
    Performs binning in 1-dimensional data and returns number counts with Poisson errors.

    

    Input:
     - data       numpy.ndarray : Data array (ndim=1,dtype=float)
     - bin_size           float : Size of the regular bins

    Output:
     - binned_data       numpy.ndarray : Bin center values, number counts
                                         and Poisson errors (ndim=3,dtype=float)
    
    ---
    """

    bin_inf = math.floor(data.min()/bin_size)*bin_size

    bin_sup = math.ceil(data.max()/bin_size)*bin_size

    bin_vals = np.arange(bin_inf-bin_size/2, bin_sup + bin_size/2, bin_size)

    N, m = np.histogram(data, bins = bin_vals)

    m = np.delete(m,len(m)-1)+bin_size/2

    binned_data = np.array([m, N, np.sqrt(N)])

    return binned_data



def cut_unpopulated_bins(binned_data, N_min):

    """
    Excludes bins with less than N_min counts from binned_data.

    

    Input:
     - binned_data     numpy.ndarray : Bin center values, number counts
                                       and Poisson errors (ndim=3,dtype=float).
                                       (same format as output of make_histogram)
     - N_min                     int : Minimum number of counts per bin

    Output:
     - binned_data       numpy.ndarray : Bin center values, number counts
                                         and Poisson errors for bins populated
                                         with more than N_min objects 
                                         (ndim=3,dtype=float)
    
    ---
    """

    mask = binned_data[1] >= N_min

    return binned_data[:,mask]



def mag_function(m,a,b):

    """
    Defines analytical number count formula for astronomical observations.

    For large field imaging surveys, there exists an empirical analytical
    formula for the number of objects detected as a function of magnitude,
    given by N = a*10^{b*m}, where a and b are constants and m is the
    magnitude. Deviation from this law at faint magnitudes indicates loss
    of completeness in the observations.
    
    The input magnitude m can either be a single float or a numpy array.
    This second option is particularly important when using the function
    scipy.optimize.curve_fit to find best-fit a and b values to N,m data.

    Input:
     - m    float or numpy.ndarray : magnitude value(s) (ndim=1,dtype=float)
     - a                     float : constant
     - b                     float : constant

    Output:
     - N    float or numpy.ndarray : number of objects calculated with the
                                     formula (ndim=1,dtype=float)
    
    ---
    """
    
    return a*10**(b*m)



def find_mag_sup(data):

    """
    Selects maximum argument of data[1] and returns correponding data[0] value,
    subtracted by one.

    This is a very specific function to find the maximum magnitude at which
    number count data will be fitted to the analytical formula described in
    mag_function. The criterium is to get one full magnitude lower than the
    one at which the number count is maximum.


    Input:
     - data       numpy.ndarray : Image array (ndim=2 or more,dtype=float)

    Output:
     - mag_sup    float : data[0] entry corresponding to maximum data[1] value
                          subtracted by one
    
    ---
    """

    mag_sup = data[0][data[1].argmax()] - 1

    return mag_sup



def cut_mag_data(data, m_inf, m_sup):

    """
    Excludes data rows for which data[0] <= m_inf and data[0] >= m_sup.


    Input:
     - data       numpy.ndarray : Data array (ndim=1 or larger,dtype=float)
     - m_inf              float : Inferior cut value
     - m_sup              float : Superior cut value

    Output:
     - cut_data   numpy.ndarray : Cut data array (ndim=1 or larger,dtype=float)
    
    ---
    """

    mag_inf_mask = data[0] >= m_inf
    mag_sup_mask = data[0] <= m_sup

    cut_data = data[:, mag_sup_mask & mag_inf_mask]

    return cut_data



def fit_mag_data(data,a,b):

    """
    Fits data to number count analytical formula described in mag_function.

    Data must be of dimension 3, with data[0] being x-axis (magnitude) values,
    data[1] being y-axis (number count) values and data[2] being y-error values.
    The fit is performed using mag_function as the analytical form.

    blabla

    Input:
     - data       numpy.ndarray : Data array (ndim=3,dtype=float)
     - a                  float : Initial guess for a fit
     - b                  float : Initial guess for b fit

    Output:
     - p          [float,float] : List of best-fit parameters
    
    ---
    """

    x = data[0]
    y = data[1]
    yerror = data[2]
    
    p0=[a,b]

    p, cov = optimize.curve_fit(mag_function, x, y, p0, yerror)

    return list(p)



def find_mag_lim(data,fit_params,bin_size):

    """
    Finds the limiting magnitude of given data.
    
    Finds the minimum data[0] entry for which the relative difference between
    data[1] and mag_function(data[0],fit_params) is larger than 10% and then
    subtracts one bin_size (supposed to be the same size as adjacent data[0]
    entries). In particular, fit_params should come from a fit of the analytical
    function mag_function to the same data.

    Also note that the moduls of the relative difference is not taken, which
    means that the difference will only be considered bigger than 10% for the
    case where data[1] < mag_function(data[0],fit_params).

    Input:
     - data          numpy.ndarray : Data array (ndim=2 or more,dtype=float)
     - fit_params   [float, float] : a and b parameters for mag_function
     - bin_size              float : size of the bins 

    Output:
     - mag_lim               float : limiting magnitude value
    
    ---
    """
    
    a = fit_params[0]
    b = fit_params[1]

    rel_diff = 1-data[1]/mag_function(data[0],a,b)
    
    mag_mask = rel_diff > 0.1

    mag_lim = data[0][mag_mask].min()-bin_size

    return mag_lim



def make_plot_mag_pipe(binned_data, tile_name, folder_path, fit_params, m_inf, m_sup, mag_lim, bin_size, gal_cut, S2N_cut, stell_idx, plot_inf, plot_sup):

    """
    Makes a check plot of the limiting magnitude procedure.

    """

    pl.clf()
    
    pl.figure(figsize=(15,10))

    ax=pl.subplot(1,1,1)
    ax.set_yscale("log", nonposy='mask')

    plot_data = pl.errorbar(binned_data[0], binned_data[1], binned_data[2], color='g', ecolor='k', fmt='-', elinewidth=0.5)

    fit_x = np.arange(m_inf, binned_data[0].max(), 0.01)
    fit_y = mag_function(fit_x, fit_params[0], fit_params[1])

    plot_fit = pl.plot(fit_x, fit_y, 'r', lw=1, label='A='+str('%.3e' % float(fit_params[0]))+', b='+str('%.3f' % float(fit_params[1]))+' - ($mag_{inf}$'+'= '+str(m_inf)+', $mag_{sup}$'+'= '+str(m_sup)+') - '+'$m_{comp}$'+'= '+str(mag_lim)+' , bin='+str(bin_size)+' , S/N>='+str(S2N_cut)+' , CLASS_STAR >(<)'+str(stell_idx))
    
    pl.axvline(x=mag_lim, color='k',ls='--')
    
    pl.xlim(plot_inf, plot_sup)
    pl.ylim(0, binned_data[1].max()*1.1)

    pl.legend(loc='best')

    pl.xlabel('mag', fontsize=25)
    pl.ylabel('N', fontsize=25)

    if gal_cut:
        pl.title(tile_name + '_gal', fontsize=25)
        pl.savefig(folder_path + '/Plots/'+ tile_name + '_gal_bins_'+ str(bin_size) + '_S2N_'+ str(int(S2N_cut)) + '_stell_'+ str(stell_idx) + '.png')

    else:
        pl.title(tile_name + '_star', fontsize=25)
        pl.savefig(folder_path + '/Plots/'+ tile_name + '_star_bins_'+ str(bin_size) + '_S2N_'+ str(int(S2N_cut)) + '_stell_'+ str(stell_idx) + '.png')



