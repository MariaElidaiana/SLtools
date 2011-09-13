#!/usr/bin/env python
# ==================================
# Authors:
# Pedro Ferreira - pferreira@dfte.ufrn.br
# ==================================

""" Select the position of sources near the tangential caustic """


##@package select_source_positions
#
#
#  Select the position of sources near the tangential caustic


import os
import pyfits
import math
import random
import numpy as np
import logging


from sltools.pipelines.find_cc import run as run_find_cc
from sltools.gravlens.init_gravlens_parameter import lens_parameters
from sltools.coordinate.translation_and_rotation import translate_and_rotate_coord_system
from sltools.gravlens.find_cc import plot_cc

#========================================================================================================
# find mu_t and mu_r for a point
def get_distortions(x, y, lens_model, mass_scale, model_param_8, model_param_9, model_param_10, galaxy_position=(0,0), e_L=0, theta_L=0, shear=0, theta_shear=0, gravlens_params={}, gravlens_input_file='gravlens_magtensor_in.txt', gravlens_output_file='gravlens_magtensor_out.txt', keep_files=False):
    """
    Computes the tangential and radial local distortions in a list of points.

    
   Input:
     - x                  [float,...] : x coordinates of the points the local distortions will be calculated
     - y                  [float,...] : y coordinates of the points the local distortions will be calculated
     - lens_model                 str : Lens name (see gravlens manual table 3.1)
     - mass_scale               float : Mass scale of the lens - "parameter 1"
     - model_param_8            float : misc. lens parameter - often scale radio (depends on the lens model)
     - model_param_9            float : misc. lens parameter - often scale radio (depends on the lens model)
     - model_param_10           float : misc. lens parameter - often a power law index (depends on the lens model)
     - galaxy_position  [float,float] : [x,y] position of the lens
     - e_L                      float : Horizontal central position for output (cut) image
     - theta_L                  float : Vertical central position for output (cut) image
     - shear                    float : 'pixel' or 'degrees' for size (x_size,y_size) values
     - theta_shear              float : Horizontal size (in pixels) of output image
     - gravlens_params           dict : contains the keys and values of the gravlens configuration (see 
				        default parameters at function set_gravlens_default,inside lens_parameters)
     - gravlens_input_file        str : name of the input file for gravlens
     - gravlens_output_file       str : name of the output file generated by gravlens (with the magnification tensor)
     - keep_files                bool : 'True' to keep gravlens input and output files and 'False' to delete them

    Output:
     - distortions  [[float,float],...] : each pair has respectively the tangential and radial 
                                          distortions of the corresponding input point (x_i,y_i) 

    """

    inputlens, setlens, gravlens_params_updated = lens_parameters(lens_model, kappas, rs, model_param_9, model_param_10, galaxy_position=(0,0), e_L=0.3, theta_L=theta_L, shear=0, theta_shear=0, gravlens_params={} )

    f = open(gravlens_input_file, 'w')
    f.write(inputlens)
    for i in range(len(x)):
        f.write('magtensor %0.9f %0.9f \n' % (x[i], y[i]))
    f.close()
    os.system('gravlens %s > %s' % (gravlens_input_file, gravlens_output_file) )

    f = open(gravlens_output_file, 'r').readlines()
    nlinha = len(f) - 6*len(x) # I am using this to get the matrix elements without worrying about the number of lines the file has (which depends on the number of parameters of gravlens we modify). 'nlinha' is the number of lines that DON'T contain the output data of magtensor
    distortions = []
    for i in range(len(x)): # calculates the magnifications at each point
        a11 = float(f[nlinha + i*6].split()[0]) # element 11 of the mag tensor
        a12 = float(f[nlinha + i*6].split()[1]) # element 12 (=21) of the mag tensor
        a22 = float(f[nlinha + i*6 + 1].split()[1]) # element 22 of the mag tensor
        mu_t = ( ((a11 + a22)/2.)/(a11*a22 - a12**2) - ((( (a22 - a11)/2. )**2 + a12**2 )**0.5 )/(abs(a11*a22 - a12**2)) )**(-1)
        mu_r = ( ((a11 + a22)/2.)/(a11*a22 - a12**2) + ((( (a22 - a11)/2. )**2 + a12**2 )**0.5 )/(abs(a11*a22 - a12**2)) )**(-1)
        distortions.append([mu_t,mu_r])
    if keep_files == False:
        os.system('rm -f %s %s' % (gravlens_input_file, gravlens_output_file) )

    return distortions


#========================================================================================================
# find point images of given point sources
def get_point_images(x, y, lens_model, mass_scale, model_param_8, model_param_9, model_param_10, galaxy_position=(0,0), e_L=0, theta_L=0, shear=0, theta_shear=0, gravlens_params={}, gravlens_input_file='findimg_input.txt', gravlens_output_file='findimg_out.txt', keep_files=False):
    """
    Computes the positions of point images of a list of point sources.

    
   Input:
     - x                  [float,...] : x coordinates of the point sources
     - y                  [float,...] : y coordinates of the point sources
     - lens_model                 str : Lens name (see gravlens manual table 3.1)
     - mass_scale               float : Mass scale of the lens - "parameter 1"
     - model_param_8            float : misc. lens parameter - often scale radio (depends on the lens model)
     - model_param_9            float : misc. lens parameter - often scale radio (depends on the lens model)
     - model_param_10           float : misc. lens parameter - often a power law index (depends on the lens model)
     - galaxy_position  [float,float] : [x,y] position of the lens
     - e_L                      float : Horizontal central position for output (cut) image
     - theta_L                  float : Vertical central position for output (cut) image
     - shear                    float : 'pixel' or 'degrees' for size (x_size,y_size) values
     - theta_shear              float : Horizontal size (in pixels) of output image
     - gravlens_params           dict : contains the keys and values of the gravlens configuration (see 
				        default parameters at function set_gravlens_default,inside lens_parameters)
     - gravlens_input_file        str : name of the input file for gravlens
     - gravlens_output_file       str : name of the output file generated by gravlens (with the magnification tensor)
     - keep_files                bool : 'True' to keep gravlens input and output files and 'False' to delete them

    Output:
    ??? - x_img  [[float,float],...] : each pair has respectively the tangential and radial 
                                          distortions of the corresponding input point (x_i,y_i) 

    """

    inputlens, setlens, gravlens_params_updated = lens_parameters(lens_model, kappas, rs, model_param_9, model_param_10, galaxy_position=(0,0), e_L=0.3, theta_L=theta_L, shear=0, theta_shear=0, gravlens_params={} )

    # run gravlens to get the images ========================================================
    f = open(gravlens_input_file, 'w')
    f.write(inputlens)
    out_file = []
    for i in range(len(x)):
        out_file.append(gravlens_output_file[:-4] + '_' + str(i) + gravlens_output_file[-4:])
        f.write('findimg %0.6f %0.6f %s \n' % (x[i], y[i], out_file[-1] ))
    f.close()
    os.system('gravlens %s > /dev/null' % (gravlens_input_file) )
    # now we have 'len(x)' files with the images information (pos, magnification, time delay)
    #========================================================================================

    # we now read the files ======================================================== 
    x_img, y_img, magnification, time_delay = [], [], [], []
    for i in range (len(x)): # len(x) = len(out_file)
        img_properties = loadtxt(out_file[i], comments='#', skiprows=1, unpack=True)
        x_img.append(img_properties)[0]
        y_img.append(img_properties)[1]
        magnification.append(img_properties)[2]
        time_delay.append(img_properties)[3]
    # ==============================================================================

    if keep_files == False:
        os.system('rm -f %s %s' % (gravlens_input_file, gravlens_output_file) )

    return x_img, y_img, magnification, time_delay, out_file


#=======================================================================================================
def compute_deformation_rhombus(theta_L, tan_caustic_x, tan_caustic_y, control_rhombus=1):
    """
    Determines the 4 cusps of the tangential caustic and determines a rhombus that encloses it. 

    The rhombus vertices are on distances proportional to the cusp distance.

    Input:
     - theta_L               float : inclination (in degrees) of the lens with respect to the vertical
                                    (counterclockwise)
     - tan_caustic_x  [float,...] : list of x coordinates of the tangential caustic
     - tan_caustic_y  [float,...] : list of y coordinates of the tangential caustic
     - control_rhombus      float : determines how many times the vertices of the losangle 
                                    (inscribed in the rhombus) will be away from the cusps.

    Output:
     - deformation_rhombus_x  [float,...] :  list of the four x coordinates of the rhombus corners
     - deformation_rhombus_y  [float,...] : list of the four y coordinates of the rhombus corners

    """

    # converts tan_caustic_x and tan_caustic_y to the system of coordinates in which theta_L = 0 (to find the 4 cusps)
    # xcrit0 = cos(theta)*x + sin(theta)*y
    # ycrit0 = -sin(theta)*x + cos(theta)*y
    #theta = theta_L*(math.pi)/180. # convert theta_L to radians
    tan_caustic_x = np.array(tan_caustic_x)
    tan_caustic_y = np.array(tan_caustic_y)
    xcrit0, ycrit0 = translate_and_rotate_coord_system(tan_caustic_x, tan_caustic_y, 0, 0, -theta_L, angle='degree')
    #global cusp1, cusp2, cusp3, cusp4, xlosango, ylosango
    cusp1 = np.argmax(ycrit0)
    cusp2 = np.argmax(xcrit0)
    cusp3 = np.argmin(ycrit0)
    cusp4 = np.argmin(xcrit0)
    xlosango1 = tan_caustic_x[cusp1]*control_rhombus # x coord of point 1 of the losangle
    ylosango1 = tan_caustic_y[cusp1]*control_rhombus # y coord of point 1 of the losangle
    xlosango2 = tan_caustic_x[cusp2]*control_rhombus # x coord of point 2 of the losangle
    ylosango2 = tan_caustic_y[cusp2]*control_rhombus # y coord of point 2 of the losangle
    xlosango3 = tan_caustic_x[cusp3]*control_rhombus # x coord of point 3 of the losangle
    ylosango3 = tan_caustic_y[cusp3]*control_rhombus # y coord of point 3 of the losangle
    xlosango4 = tan_caustic_x[cusp4]*control_rhombus # x coord of point 4 of the losangle
    ylosango4 = tan_caustic_y[cusp4]*control_rhombus # y coord of point 4 of the losangle
    xlosango = [xlosango1, xlosango2, xlosango3, xlosango4]
    ylosango = [ylosango1, ylosango2, ylosango3, ylosango4]

    return xlosango, ylosango
 

#=======================================================================================================
def source_positions(minimum_distortion, deformation_rhombus, nsources, inputlens):

    """ Determines the source centers that are candidates to generate an arc. """

    # source_positions must be divided: a function to calculate the random points; a function to calculate
    # the point images of a list of sources, a function to calculate mu_t and mu_r of a list of points (done!)
    # and maybe a function to identify which sources will be selected

    x_vert_1, y_vert_1 = deformation_rhombus[0] # vert_1 : lower left  corner 
    x_vert_2, y_vert_2 = deformation_rhombus[1] # vert_2 : upper right corner

    #GENERATE RANDOM POINTS NEAR THE CAUSTIC ------------------------------------------------------------
    usq = np.random.uniform(x_vert_1, x_vert_2, nsources) # x coord of a point inside the square, but outside the rhombus
    vsq = np.random.uniform(y_vert_1, y_vert_2, nsources) # y coord of a point inside the square, but outside the rhombus

    ########### DETERMINE WHICH CENTERS HAS mu_t/mu_r > minimum_distortion IN ORDER TO GENERATE SERSIC SOURCES IN THESE CENTERS ############

    f = open('findimginput.txt', 'w')
    f.write(inputlens)
    for i in range (0,len(usq)): # determine the positions of the images of the source
        #f = open('findimginput.txt', 'a')
        f.write('findimg %0.6f %0.6f findimgoutput%05d.txt\n'  % ( usq[i],vsq[i], i ))
    f.close()
    # runs gravlens to obtain the images of the positions inside the rhombus (usq,vsq)
    os.system('gravlens findimginput.txt > /dev/null')
    f1 = open('gravlensmagtensorcorte.txt', 'w')
    f1.write(inputlens)
    imagens = [] # contains the number of images of the source j
    image_positions = [] # image_positions[i][j] is the (x,y) position of the image j of the source i
    for i in range (0,len(usq)):
        filemag = open('findimgoutput%05d.txt' % i , 'r').readlines()
        imagens.append(len(filemag)-2)
        image_positions.append([])
        for j in range (2,len(filemag)):    
            f1.write('magtensor %0.6f %0.6f\n' % ( float(filemag[j].split()[0]), float(filemag[j].split()[1])  ) )
            image_positions[i].append( [float(filemag[j].split()[0]), float(filemag[j].split()[1])] )
    # if gravlens does not find any images, the grid is not big enough
    if 0 in imagens and len(imagens) != 0:
        logging.debug( 'There are %d point images outside the grid' % imagens.count(0) )
        return False
    f1.close()
    # obtain with the magtensor all the magnifications
    os.system('gravlens gravlensmagtensorcorte.txt > saidamagtensorcorte.txt')
    f = open('saidamagtensorcorte.txt' , 'r').readlines()
    nlinha = len(f) - 6*(np.sum(imagens)) # I am using this to get the matrix elements without worrying about the number of lines the file has (which depends on the number of parameters of gravlens we modify). 'nlinha' is the number of lines that DON'T contain the output data of magtensor
    source_centers = []
    image_centers = [] # image_positions[i][j] is the (x,y) position of the image j of the source i
    image_distortions = [] # image_distortions[i][j] is the (mu_t,mu_r) distortion of the image j of the source i
    usq2 = []
    vsq2 = []
    contj = 0
    for i in range(0,len(imagens) ): # calculates the magnifications at each point
        mutemp = 0    
        distortion_temp = []
        for j in range (0,imagens[i]): # note that the index 'i' is the same as of usq
            a11 = float(f[nlinha + (contj)*6].split()[0]) # element 11 of the mag tensor
            a12 = float(f[nlinha + (contj)*6].split()[1]) # element 12 (=21) of the mag tensor
            a22 = float(f[nlinha + (contj)*6 + 1].split()[1]) # element 22 of the mag tensor
            mu_t = ( ((a11 + a22)/2.)/(a11*a22 - a12**2) - ((( (a22 - a11)/2. )**2 + a12**2 )**0.5 )/(abs(a11*a22 - a12**2)) )**(-1)
            mu_r = ( ((a11 + a22)/2.)/(a11*a22 - a12**2) + ((( (a22 - a11)/2. )**2 + a12**2 )**0.5 )/(abs(a11*a22 - a12**2)) )**(-1)
            distortion_temp.append( [mu_t,mu_r] )
            contj = contj + 1
            if abs(mu_t/mu_r) > mutemp:
                mutemp = abs(mu_t/mu_r)
        if mutemp > minimum_distortion:
            source_centers.append([usq[i], vsq[i]])
            image_centers.append( image_positions[i] )
            image_distortions.append( distortion_temp )
        else:
            usq2.append(usq[i])
            vsq2.append(vsq[i])
    os.system('rm -f findimgoutput*.txt')
    return source_centers, image_centers, image_distortions  #, usq2, vsq2, cusp1, cusp2, cusp3, cusp4, xlosango, ylosango, usq, vsq

#---------------------------------------------------------------------------------------------------------------------

##@package select_source_positions [formerly SourceSelector]
# Identifies source_positions close to caustics (i.e. that could produce arcs)
#
# Given the lens parameters and source surface density, identifies the source_positions that have a local distortion above minimum_distortion 
# 
#@param lens_model (kappas, xsl,el,theta_L) currently a dictionary with the lens model parameters 
#@param gravlens_params (set of gravlens parameters: gridhi1, maxlev, etc)
#@param source_selector_control_params (minimum_distortion, control_rhombus) 
#@param minimum_distortion : minimum ratio of the tangential and radial magnifications to an image be considered an arc 
#@param control_rhombus : control parameter to define distance to cusps 
#@param src_density_or_number
#@return source_centers [former potarcxy] or "False" (in cases where no critical curves are found), and image_centers, image_distortions
def select_source_positions(lens_model, mass_scale, model_param_8, model_param_9, model_param_10, galaxy_position=[0.,0.], e_L=0, theta_L=0, shear=0, theta_shear=0, gravlens_params={}, src_density_or_number=1, minimum_distortion=0., control_rhombus=2., caustic_CC_file='crit.txt', gravlens_input_file='gravlens_CC_input.txt', rad_curves_file='lens_curves_rad.dat', tan_curves_file='lens_curves_tan.dat', curves_plot='crit-caust_curves.png', show_plot=0, write_to_file=0, max_delta_count=20, delta_increment=1.1, grid_factor=5., grid_factor2=3., max_iter_number=20, min_n_lines=200, gridhi1_CC_factor=2., accept_res_limit=2E-4):
    """
    
    If src_density_or_number is a float (and therefore a density), nsources is given by np.random.poisson(rectangle_area*src_density_or_number )

    """

    # find and separate critical curves
    out_run_find_cc = run_find_cc(lens_model, mass_scale, model_param_8, model_param_9, model_param_10, galaxy_position, e_L, theta_L, shear, theta_shear, gravlens_params, caustic_CC_file, gravlens_input_file, rad_curves_file, tan_curves_file, curves_plot=0, show_plot=show_plot, write_to_file=write_to_file, max_delta_count=max_delta_count, delta_increment=delta_increment, grid_factor=grid_factor, grid_factor2=grid_factor2, max_iter_number=max_iter_number, min_n_lines=min_n_lines, gridhi1_CC_factor=gridhi1_CC_factor, accept_res_limit=accept_res_limit)

    logging.info('Ran pipelines.find_cc.run and obtained and separated the caustic and critical curves')

    rad_CC_x, rad_CC_y, tan_CC_x, tan_CC_y, rad_caustic_x, rad_caustic_y, tan_caustic_x, tan_caustic_y = out_run_find_cc
    #----------------------------------------------------------

    #------------ call compute_deformation_rhombus ---------------------------
    xlosango, ylosango = compute_deformation_rhombus(float(theta_L), tan_caustic_x, tan_caustic_y, control_rhombus)
    #---------------------------------------------------------------------------

    #-----------------------------------------------------------------------------------------------------------

    x_vert_1, y_vert_1 = min(xlosango), min(ylosango) # vert_1 : lower left corner 
    x_vert_2, y_vert_2 = max(xlosango), max(ylosango) # vert_2 : upper right corner
    deformation_rhombus = [x_vert_1,y_vert_1],[x_vert_2, y_vert_2]
    logging.debug('Obtained the deformation rhombus: %s' % str(deformation_rhombus) )

    rectangle_area = ( x_vert_1 - x_vert_2 )*( y_vert_1 - y_vert_2 ) # deltaX*deltaY
    # if src_density_or_number is a float, it is a density, if it is a integer it is the number of sources
    if type(src_density_or_number) == int:
        nsources = src_density_or_number
    if type(src_density_or_number) == float:    
        nsources = np.random.poisson(rectangle_area*src_density_or_number )
    logging.debug('Number of point sources generated = %d' % nsources)
    #-----------------------------------------------------------------------------------------------------------
    # redefine gridhi1
    tan_CC_x = np.array(tan_CC_x)
    tan_CC_y = np.array(tan_CC_y)
    index = np.argmax(tan_CC_x**2 + tan_CC_y**2)
    image_plane_factor = float(gridhi1_CC_factor);
    gravlens_params['gridhi1'] =  image_plane_factor * ( (tan_CC_x[index]**2 + tan_CC_y[index]**2)**0.5 )
    inputlens, setlens, gravlens_params = lens_parameters(lens_model, mass_scale, model_param_8, model_param_9, model_param_10, galaxy_position, e_L, theta_L, shear, theta_shear, gravlens_params)
    #-----------------------------------------------------------------------------------------------------------
    source_positions_output = source_positions(minimum_distortion, deformation_rhombus, nsources, inputlens)
    while source_positions_output == False:
        gravlens_params['gridhi1'] = float( gravlens_params['gridhi1'] ) * 1.15;
        logging.debug( 'loop in source_positions: gridhi1 = %f' % float( gravlens_params['gridhi1'] ) )
        inputlens, setlens, gravlens_params = lens_parameters(lens_model, mass_scale, model_param_8, model_param_9, model_param_10, galaxy_position, e_L, theta_L, shear, theta_shear, gravlens_params)       
        source_positions_output = source_positions(minimum_distortion, deformation_rhombus, nsources, inputlens)
    logging.debug( 'gridhi1 = %s' % float( gravlens_params['gridhi1'] ) )
    source_centers = source_positions_output[0]
    image_centers = source_positions_output[1]
    image_distortions = source_positions_output[2]

    logging.debug('Selected positions for finite sources: %s' % str(source_centers) )
    logging.debug('Images of the point sources: %s' % str(image_centers) )
    logging.debug('Corresponding mu_t and mu_r for each image: %s' % str(image_distortions) )

    src_x, src_y = zip(*source_centers)
    img_x, img_y = zip(*image_centers)
    plot_cc(tan_caustic_x, tan_caustic_y, rad_caustic_x, rad_caustic_y, tan_CC_x, tan_CC_y, rad_CC_x, rad_CC_y, curves_plot, show_plot=0, src_x=src_x, src_y=src_y, img_x=img_x, img_y=img_y )


    return source_centers, image_centers, image_distortions 






