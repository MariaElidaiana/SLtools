#!/usr/bin/env python
# ====================================================
# Authors:
# Bruno Moraes - bruno.a.l.moraes@gmail.com - 01/Nov/2011
# ====================================================


"""Module to calculate the limiting magnitude for a given FITS catalogue"""

##@package mag_pipeline
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
# Executable package: YES
#
# To see the package help message, type:
#
# > python mag_pipeline.py --help
#
# To run the code:
#
# > python mag_pipeline.py 'input_file' 'mag_field_name' 'mag_error_field_name' mag_inf_value plot_x_lim_inf plot_x_lim_sup



from __future__ import division
from ast import literal_eval as lit
import sys
import os
import errno
import numpy as np
import math
import cmath
from scipy import optimize
import collections
import glob
import pyfits

from sltools.catalog.cs82 import fit_mag as fmg
from sltools.catalog import fits_data as fd
from sltools.coordinate import wcs_conversion as wcscv
from sltools.image import header_funcs as hdrf
from sltools.io import io_addons as ioadd

# =================================================================================================================


def mag_pipeline(input_file, field_names, folder_path, mag_inf, bin_size, gal_cut, flag_cut, mag99, S2N_cut, stell_idx, plot_inf, plot_sup):

    """
    Calculate the limiting magnitude for a given FITS catalogue.

    This function performs specified cuts to the catalogue, proceeds to bin 
    the data and then fit it to an analytical (number count) x (magnitude)
    function. A difference of more than 10% between the data and the fit
    defines the limiting magnitude. This value and several other catalogue
    properties are returned as a list of strings. Additionally, a check plot
    of the fitting procedure is saved to folder_path.


    Input:
     - input_file          str : Input file name
     - field_names  [str, str] : Magnitude and magnitude error field names
     - folder_path         str : Folder path
     - mag_inf           float : Inferior magnitude to perform fitting
     - bin_size          float : (Uniform) binning size
     - gal_cut            bool : Galaxy or Star fit (according to stell_idx cut)
     - flag_cut           bool : Use only FLAGS=0 objects
     - mag99              bool : Inclusion of unidentified magnitudes
     - S2N_cut           float : Signal-to-noise minimum cut
     - stell_idx         float : CLASS_STAR value (defines what is a Galaxy/Star)
     - plot_inf          float : Check plot inferior x-axis value
     - plot_sup          float : Check plot superior x-axis value

    Output:
     - [str,...,str] : a list of the following properties of the catalog in
                       string format: catalogue name, original image center RA,
                       original image center DEC, original image seeing, fitting 
                       bin size, S/N cut value, CLASS_STAR value, constant 
                       coefficient of the linear fit, linear coefficient of the
                       linear fit, inferior magnitude of the performed fit,
                       superior magnitude of the performed fit, limiting
                       magnitude, total number of objects, total number of
                       galaxies (stars), total number of identified-magnitude
                       galaxies (stars), total number of identified magnitude
                       galaxies (stars) above S/N cut, percentage of FLAGS = 0
                       objects over total number of objects, number of galaxies 
                       per arcmin^2, number of stars per arcmin^2.

     - check plot    : plot showing the binned number count data and the
                       corresponding analytical fit, saved to folder_path.
    
    ---
    """

# Getting data and info from the header
#
# This part can still be improved: the normal FITS part can be modularized,
# and a Try/Except test should be written for when the field isn't present.
# Also the tile area calculation is wrong and the pixel scale is hardcoded
# (and doesn't need to be).

    hdulist = pyfits.open(input_file,ignore_missing_end=True,memmap=True)

    header_info = ['CRVAL1','CRVAL2','SEEING','TEXPTIME','SEXBKGND','SEXBKDEV','MAGZP','MAGZPERR']

    if fmg.check_if_ldac(hdulist):

        hdudata = hdulist[2].data

        column_names = hdulist[2].columns.names
    
        hdulist_string = hdulist[1].data[0][0]

        tile_ra = fmg.get_entry_ldac_header(hdulist_string, header_info[0])
        tile_dec = fmg.get_entry_ldac_header(hdulist_string,header_info[1])
        tile_seeing = fmg.get_entry_ldac_header(hdulist_string,header_info[2])
        tile_texptime = fmg.get_entry_ldac_header(hdulist_string,header_info[3])
        tile_bkgnd = fmg.get_entry_ldac_header(hdulist_string,header_info[4])
        tile_bkgrms = fmg.get_entry_ldac_header(hdulist_string,header_info[5])
        tile_magzp = fmg.get_entry_ldac_header(hdulist_string,header_info[6])
        tile_magzperr = fmg.get_entry_ldac_header(hdulist_string,header_info[7])
    
        tile_name = fmg.get_tile_name(input_file)

    
    else:

        hdudata = hdulist[1].data

        column_names = hdulist[1].columns.names

        header_vals = []

        for i in xrange(len(header_info)):

            header_vals.append(hdulist[0].header.get(header_info[i]))

            if hdulist[0].header.get(header_info[i]) == None:
                print "The field "+header_info[i]+ " wasn't found in the header. 'None' will be taken as its value."

        tile_ra = header_vals[0]
        tile_dec = header_vals[1]
        tile_seeing = header_vals[2]
        tile_name = 'full'


# Performing cuts in different columns


    if field_names[0] not in column_names:
        print field_names[0]+" is not present in this FITS file! Aborting... "
        sys.exit(1)

    elif field_names[1] not in column_names:
        print field_names[1]+" is not present in this FITS file! Aborting... "
        sys.exit(1)

    else:
        magdata = hdudata.field(field_names[0]).astype(np.float64)
        magerrdata = hdudata.field(field_names[1]).astype(np.float64)


 
    try:
        class_star = hdudata.field('CLASS_STAR').astype(np.float64)

        if gal_cut:
            stell_mask = (class_star < stell_idx)
 
        else:
            stell_mask = (class_star > stell_idx)

    except:
        print "There's no field called CLASS_STAR to perform a cut. All objects will be considered."
        class_star = (np.zeros(len(hdudata)) == 0)



    if flag_cut:

        print 'Cutting in FLAGS = 0 for calculation purposes only...'
        try:
            flags = hdudata.field('FLAGS').astype(np.float64)
            flag_mask = (flags == 0)
        except:
            print "There's no field called FLAGS to perform a cut. All objects will be considered."
            flag_mask = (np.zeros(len(hdudata)) == 0)

    else:
        flag_mask = (np.zeros(len(hdudata)) == 0)
    

 
    if mag99:
        mag99_mask = (magdata != 99)
 
    else:
        mag99_mask = (np.zeros(len(hdudata)) == 0)



    S2N_mask = magerrdata < 1.086/S2N_cut
     
    objs = []
 
    objs.append(len(magdata))
    objs.append(len(magdata[stell_mask & mag99_mask]))
    objs.append(len(magdata[~stell_mask & mag99_mask]))
 
    data = magdata[stell_mask & mag99_mask & S2N_mask]

    objs.append(len(data))

    objs.append(len(magdata[stell_mask & mag99_mask & S2N_mask & flag_mask]))

 
    # Bin and cut the data
 
    binned_data = fmg.make_histogram(data, bin_size)

    binned_data = fmg.cut_unpopulated_bins(binned_data, 10) # Attention! Hard-coded value for the minimum number of counts for keeping bins 

    mag_sup = fmg.find_mag_sup(binned_data)

    cut_data = fmg.cut_mag_data(binned_data, mag_inf, mag_sup)


    # Perform fit

    a0 = 0; b0 = 0.3;  # Attention! Hard-coded initial parameter values for the fit

    fit_params = fmg.fit_mag_data(cut_data, a0, b0)


    # Get limit magnitude

    cut_inf_data = fmg.cut_mag_data(binned_data, mag_sup, 99)

    mag_lim = fmg.find_mag_lim(cut_inf_data, fit_params, bin_size)

    
    # Make the plots and save them to a given folder
    
    ioadd.create_folder(folder_path + '/Plots/')

    fmg.make_plot_mag_pipe(binned_data, tile_name, folder_path, fit_params, mag_inf, mag_sup, mag_lim, bin_size, gal_cut, S2N_cut, stell_idx, plot_inf, plot_sup)

    
    # Return results of the fit
    
    return [tile_name, str(tile_ra), str(tile_dec), str(tile_seeing), str(tile_texptime), str(tile_bkgnd), str(tile_bkgrms), str(tile_magzp), str(tile_magzperr), str(fit_params[0]), str(fit_params[1]), str(mag_inf), str(mag_sup), str(mag_lim), str(objs[0]), str(objs[1]), str(objs[2]), str(objs[3]), str(objs[4]/objs[3])]


# \cond
# ============================================================================

# Main function: Include ifs (or try/excepts to prevent crashing), and other minor changes


if __name__ == "__main__" :

    
    from optparse import OptionParser;

    usage="\n\n python %prog [flags] [options] 'input_file' 'mag_field_name' 'mag_error_field_name' \n\n This pipeline calculates the limiting magnitude for a given FITS catalogue. It has four mandatory arguments: the (input) FITS catalogue path and name, the magnitude field name to be used for the calculations (i.e. MAG_AUTO, MAG_APER, etc...) and the corresponding error field name (i.e. MAGERR_AUTO, MAGERR_APER, etc...). For a description of the procedure, check http://twiki.linea.gov.br/blabla"
    
    parser = OptionParser(usage=usage);

    parser.add_option('-b','--bin_size', dest='bin_size', default=0.2,
                      help='magnitude bin size [default=0.2]');

    parser.add_option('-f','--flag_cut', dest='flag_cut', default=1,
                      help='perform analysis using only FLAGS=0 objects [default=True]');

    parser.add_option('-g','--galaxy_cut', dest='gal_cut', default=1,
                      help='perform analysis on galaxies (CLASS_STAR < stell_idx) if True, stars  (CLASS_STAR > stell_idx) if False [default=True]');

    parser.add_option('-i','--include_unid_mags', dest='mag99', default=0, 
                      help='include objects with unidentified magnitudes (MAG = 99) [default=False]');

    parser.add_option('-m','--mag_inf', dest='mag_inf', default=21, 
                      help='inferior magnitude value for which a fit of the object number count per magnitude bin should be performed [default=21]');

    parser.add_option('-n','--signal2noise_cut', dest='S2N_cut', default=5,
                      help='S/N cut value [default=5]');

    parser.add_option('--plot_x_inf', dest='plot_inf', default=16,
                      help='x-axis inferior limit of the plots [default=16]');

    parser.add_option('--plot_x_sup', dest='plot_sup', default=25,
                      help='x-axis superior limit of the plots [default=25]');

    parser.add_option('-s','--stellarity_index', dest='stell_idx', default=0.95,
                      help='stellarity index value [default=0.95]');


    (opts,args) = parser.parse_args();

    bin_size = float(opts.bin_size);

    gal_cut = int(opts.gal_cut);
    flag_cut = int(opts.flag_cut);
    mag99 = int(opts.mag99);
    mag_inf = float(opts.mag_inf);
    plot_inf = float(opts.plot_inf);
    plot_sup = float(opts.plot_sup);
    S2N_cut = float(opts.S2N_cut);
    stell_idx = float(opts.stell_idx);

  
    if (len(args)!=3):
        print "\n\nThe number of arguments is wrong. Check documentation for usage instructions:\n\n";
        parser.print_help();
        print "";
        sys.exit(1);
    

# Get all the files in the given folder

# Mudar de sys.argv para args

    filenames = glob.glob(args[0])

    field_names = [args[1],args[2]]

    folder_path = os.path.dirname(filenames[0])


# Run the program for each file and send the results to the folder in question. The sending of plots is inside the pipeline, the sending of the final results for all files is here.

    results = []

    for i in range(len(filenames)):

        print i
       
        results.append(mag_pipeline(filenames[i], field_names, folder_path, mag_inf, bin_size, gal_cut, flag_cut, mag99, S2N_cut, stell_idx, plot_inf, plot_sup))

    results = np.array(results)


    np.savetxt(folder_path + '/fit_results_bins_'+ str(bin_size) + '_S2N_'+ str(int(S2N_cut))+ '_stell_'+str(stell_idx)+'.txt', results,fmt='%7s       %s        %s        %.4s      %.8s      %.8s      %.8s      %.8s      %.8s      %.8s       %.5s       %s        %s        %s           %s      %6s      %6s      %6s      %s')

    # Numpy 1.5 doesn't have header options for savetxt yet (to come in Numpy 2.0). Add a header using file commands
    
     
    file = open(folder_path + '/fit_results_bins_'+ str(bin_size) + '_S2N_'+ str(int(S2N_cut))+ '_stell_'+str(stell_idx)+'.txt', "r+")
     
    old = file.read() # read everything in the file
     
    file.seek(0) # rewind

    if gal_cut:
        file.write("ID_test       ra         dec         seeing    texptime    SEx_bkgnd     SEx_bkgrms    magzp    magzp_err    A_fit         b_fit     mag_inf     mag_sup    mag_comp    N_tot        N_gal      N_star    N_gal_S2N       N_flags_0/N_gal_S2N\n" + old)

    else:
        file.write("ID_test       ra         dec         seeing    texptime    SEx_bkgnd     SEx_bkgrms    magzp    magzp_err    A_fit         b_fit     mag_inf     mag_sup    mag_comp    N_tot        N_gal      N_star    N_gal_S2N       N_flags_0/N_gal_S2N\n" + old)
     
    file.close()
    

    sys.exit(0);



# ------------------
# \endcond
