#!/usr/bin/env python

import sys;
import os;

import re;
import string;
import numpy as np;
import pyfits;

import sltools;
from sltools.io import *;
from sltools.image import segment,imcp;
from sltools.string import *;

#---------------------------------------------------------------------------------------------------
def _valid_line(wort):

    wort.rstrip("\n");
    wort = re.sub("^\s*","",wort);
    wort = re.sub("\s+"," ",wort);
    wort = re.sub("#.*","",wort);

    return ( not (bool(re.search("^$",wort))  or  bool(re.search("^#",wort))) );

# ---

# ==============================================================================================
def pickout_obj(fits_image, xo, yo, params=[], args={}, use_header=True, increase=0, preset=''):
    """
    Function to run SExtractor for objects segmentation and poststamp creation of a given image.
    A reference (e.g, a object centroid) point is expected.
    
    The function receives a FITS image and a pair of coordinates [xo,yo] matching a object.
    The output is the matching object image array, header and ID from segmentation step.
    SExtractor's command-line arguments can be passed through a dictionary [args]
    {
    'key_argument' : 'value_option',
    ...
    }
    , and features to output (See SE's default.param file) at catalog through a list [params].
    
    To have borders around the identified object use [increase] to define the size of them.
    The output image will have "increase" times the extracted object size.
    (Notice that 0 < increase < 1 is possible and will return a poststamp with part of the object)
    
    Preset SE's configuration parameters, for different telescope images, are available. The [preset]
    parameters are chosen to be *good* parameters for those instruments: 'HST','DC4','DC5','CFHT'
    Notice that this preset choices do not disable other parameters.
    
    The flag [use_header]  gives the option to use or not the header instance information.
    
    Input:
     - fits_image  <str> : FITs image filename
     - xo          <int> : X object position in pixels
     - yo          <int> : Y object position in pixels
     - params <list str> : list of parameters to output on sextractor catalogue
     - args        <dic> : dictionary with sextractor command-line arguments
     - use_header <bool> : Whether or not to use (and update) header info
     - increase  <float> : multiplicative factor for poststamp sizing
     - preset      <str> : HST, DC4, DC5, CFHT
    
    Output:
     - <dic> : dictionary structure with the keys 'objIDs', 'images' and 'headers'.
               Each of them is a list with corresponding information.
    
    """

    params.append('NUMBER');

    # Deal with fits files and SExtracting the image..
    out = _file_2_imgs(fits_image, use_header, params, args, preset);

    if not out:
        print >> sys.stderr, "Error: An error occured while running SE and extracting FITS files.";
        return (False);

    objimg, segimg, header, cat = out[0], out[1], out[2], out[3];


    # Is there an identified object on given (xo,yo) point?..
    objid = segimg[yo,xo];
    if ( objid != 0 ):
        pass;
    else:
        print >> sys.stdout, "No objects were identified on given (line=%s,column=%s) position." % (yo,xo);
        return (None);


    ## objects_IDfy return a list of arrays; result from the objIDs objects located in seg image merged with obj image.
    # So, each object in objIDs is returned (also inside a/the list) as array with their corresponding pixels..
    #
    objs, hdrs = imcp.sextamp( segimg, objimg, header, increase=increase, relative_increase=True, objIDs=[objid] );
    #objout = objs[0];
    #hdrout = hdrs[0];


    return ({'IDs' : [objid], 'images' : objs, 'headers' : hdrs});

# ---

# \cond
#---------------------------------------------------------------------------------------------------
def _check_config(cfg_file):
    """Check if given config file has the necessary structure.

    In particular, if checking fails, a fixing procedure based on
    Sextractor config file (default.sex) design.
    """

    fp = open(cfg_file, 'r');

    file = filter( _valid_line, fp.readlines() );

    for line in file:

        if ( re.search("\[.*\]",line) ) :
            continue;

        if not ( bool(re.search("=",line))  or  bool(re.search(":",line)) ) :
            return (False);

        if not ( len(string.split(line,sep="=")) >= 2  or  len(string.split(line,sep=":")) >= 2 ) :
            return (False);

    fp.close();


    return (True);

# ---

# =======================================================================================================

if __name__ == "__main__" :

    # Checking dependencies..
    stat = check_dependencies( { 'binaries':['sex'] } );
    if not stat:
        print >> sys.stderr, "Error: Dependencies check failed. Fix it!";
        sys.exit(2);

    # Read input options..
    usage="Usage:  %prog [options] <objects_image.fits>";
    parser = OptionParser(usage=usage);

    parser.add_option('-p',
                      dest='params', default='default.param',
                      help="File with parameters to output (SE's default.param)");
    parser.add_option('-c',
                      dest='config', default=None,
                      help="Config file for (S)extraction");
    parser.add_option('-o',
                      dest='file_name', default='pstamp_',
                      help="Name component for output images, before '#id.fits'");
    parser.add_option('--increase',
                      dest='incr', default=0,
                      help="Multiplicative factor (relative to object size) for image border");
    parser.add_option('--no-header', action='store_false',
                      dest='use_header', default=True,
                      help="Do not use existing image header.");
    parser.add_option('--xo',
                      dest='xo', default=0,
                      help="Postion (X) to search for an identified object");
    parser.add_option('--yo',
                      dest='yo', default=0,
                      help="Postion (Y) to search for an identified object");
    parser.add_option('--preset',
                      dest='preset', default='',
                      help="DC4/DC5/HST/CFHT");
    parser.add_option('--outdir',
                      dest='dir_name', default='out_objsshot',
                      help="Directory name to put output images");

    (opts,args) = parser.parse_args();

    if ( len(args) != 1 ):
        parser.error("Wrong number of arguments. Try option '--help' for usage and help messages.");

    fits_image = args[0];
    configfile = opts.config;
    paramsfile = opts.params;
    use_header = opts.use_header;
    increase   = opts.incr;
    xc = opts.xo;
    yc = opts.yo;
    dir_name   = opts.dir_name;
    out_name   = opts.file_name;
    instrument = opts.preset;


    # Check if config file and then ewad it..
    #
    if ( configfile != None ):

        # Check if config file is valid:
        #
        stat = _check_config(configfile)
        if not (stat):
            print >> sys.stderr, "\nError: Given config file, %s, seems not to be a valid one." % (configfile);
            print >> sys.stderr, "        Check if it has a [default] section and valid <key : value> lines.\n";
            sys.exit(2);

        # Try to read it:
        #
        try:
            config = cp.read_config(configfile, 'default');
            if ( config == {} ):
                raise ValueError;
        except:
            print >> sys.stderr, "Error: Check your config file. Remember to place SE's options below [default] section.";
            sys.exit(2);

    else:
        config = {'default' : {}};


    # Read parameters from given file..
    #
    try:
        params = open( paramsfile ).readlines();
        params = regexp.line_filter( params, comments="#" );
    except:
        print >> sys.stderr, "Error: No SE's parameters file (.param). Use -p option to pass the filename.";
        sys.exit(1);

    # ===================================================================================


    # OK.. Now lets run the objects identification procedure..
    # I'll first create a directory to put the output images in there
    #
    try:
        os.mkdir( dir_name );
    except OSError:
        pass;

    owd = os.getcwd()+"/";
    os.chdir( dir_name );


    # Run ObjSShot main function. It passes fits filename and read params and config settings.
    # The output is a list of image arrays (numpy) with identified objects on them.
    #
    if ( xc != 0 and yc != 0 ):
        outdic = pickout_obj( owd+fits_image, xo=xc, yo=yc, params=params, args=config['default'], header=use_header, increase=float(increase), preset=instrument );
    else:
        outdic = readout_objs( owd+fits_image, params, config['default'], header=use_header, increase=float(increase), preset=instrument );

    if ( outdic == False ):
        print >> sys.stderr,"Finished.";
        sys.exit(1);
    if ( outdic == None ):
        print >> sys.stdout,"Finished.";
        sys.exit(0);

    objIDs = outdic['IDs'];
    objs_list = outdic['images'];
    hdrs_list = outdic['headers'];


    # And for each object array in list, write down their pixels ;-)
    #
    for i in xrange( len(objIDs) ):

        print >> sys.stdout, "Writing object (id:) %s image..." % (objIDs[i]);
        outname = out_name+"%04d.fits" % (objIDs[i]);
        os.system( 'rm %s &> /dev/null' % (outname) );
        pyfits.writeto( outname, objs_list[i], hdrs_list[i] );


    print >> sys.stdout, "Done.";
    os.chdir( owd );
    sys.exit(0);

# \endcond