""" Module to deal with ascii (CSV/Block-Data) catalog files """

##@package text_file

"""
The following functions are meant to help in reading and
writing text/csv catalogs given fieldnames and data.

"""

import sys;
import logging;
import csv;
import re;
import string;

# ---

def dict_to_csv(dictionary, fieldnames=[], filename='cat.csv', mode='w', delimiter=','):
    """ Write a CSV catalog from dictionary contents
    
    Input:
     - dictionary : {str,}
        Contents to be write in csv catalog
     - fieldnames : [str,]
        Fieldnames to read from 'dictionary'
     - filename : str
        Name of csv catalog to write
     - mode : str
        Write a new catalog, 'w', or append to an existing one, 'a'.
     - delimiter : str
        Delimiter to use between columns in 'filename'
    
    Output:
     <bool>
    
    
    Example:

    >>> D = {'x':[0,0,1,1],'y':[0,1,0,1],'id':['0_0','0_1','1_0','1_1'],'z':[0,0.5,0.5,1]}
    >>> fields = ['id','x','y','z']
    >>> 
    >>> dict_to_csv( D, fields, filename='test.csv')
    >>> 
    >>> import os
    >>> s = os.system('cat test.csv')
    id,x,y,z
    0_0,0,0,0
    0_1,0,1,0.5
    1_0,1,0,0.5
    1_1,1,1,1
    >>> 
    
    """
    
    if fieldnames == []:
        fieldnames = dictionary.keys();
        
    list_lengths = [ len(dictionary[_k])  for _k in fieldnames if type(dictionary[_k])==type([]) ];
    leng = max(list_lengths);
    
    for _k in fieldnames:
        if type(dictionary[_k])!=type([]) and type(dictionary[_k])!=type(()):
            dictionary[_k] = [dictionary[_k]]*leng;
        
    logging.debug("Fields being written to (csv) catalog: %s",fieldnames);
    
    catFile = open(filename,mode);
    catObj = csv.writer(catFile, delimiter=delimiter);
    catObj.writerow(fieldnames);
    
    LL = [ dictionary[_k] for _k in fieldnames ];
    for _row in zip(*LL):
        catObj.writerow(_row);
    catFile.close();

    return
    
# ---

def dict_from_csv(filename, fieldnames, header_lines=1, delimiter=',',dialect='excel'):
    """ Read CSV catalog and return a dictionary with the contents
    
    It is assumed that the first line to be read is the catalog header,
    where the column names are defined('fieldnames'), that's why
    'header_lines'==1 by default. (Although header lines are *not* read)
    
    Use 'header_lines' to remove non-data lines from the head of the
    file. Header lines are taken as comments and are not read.
    
    Input:
     - filename : str
        Name of csv catalog to read
     - fieldnames : [str,]
        Fieldnames to be read from catalog
     - remove_n_lines : int
        Number of lines to remove from the head of 'filename'
     - delimiter : str
        Delimiter to use between columns in 'filename'
    
    Output:
     -> {*fieldnames}
    
    
    Example:

    >>> import os    
    >>> os.system('grep -v "^#" /etc/passwd | head -n 3 > test.asc')
    0
    >>> s = os.system('cat test.asc')
    nobody:*:-2:-2:Unprivileged User:/var/empty:/usr/bin/false
    root:*:0:0:System Administrator:/var/root:/bin/sh
    daemon:*:1:1:System Services:/var/root:/usr/bin/false
    >>>
    >>> D = dict_from_csv('test.asc',['user','star'],delimiter=':',header_lines=0)
    >>>

    """

    # Initialize output dictionary
    Dout = {};
    for k in fieldnames:
        Dout[k] = [];
    
    #Initialize csv reader
    catFile = open(filename,'r');

    lixo_head = [ catFile.next() for i in range(header_lines) ];

    catObj = csv.DictReader(catFile,fieldnames,delimiter=delimiter,dialect=dialect);
    for row in catObj:
        for k in fieldnames:
            Dout[k].append(row[k]);

    return Dout;

# ---

def write_ds9cat(x,y,size=20,marker='circle',color='red',outputfile='ds9.reg',filename='None'):
    """ Function to write a ds9 region file given a set of centroids
    
    It works only with a circular 'marker' with fixed
    radius for all (x,y) - 'centroids' - given.
    
    Input:
     - x : int | []
        X-axis points
     - y : int | []
        Y-axis points
     - size : int | []
     - marker : str | [str]
     - outputfile : str | [str]

    Output:
     <bool>

    Example:
    
    >>> write_ds9cat(x=100,y=100,outputfile='test.reg')
    >>> 
    >>> import os
    >>> s = os.system('cat test.reg')
    # Region file format: DS9 version 4.1
    # Filename: None 
    global color=green dashlist=8 3 width=1 font="helvetica 10 normal" select=1 highlite=1 dash=0 fixed=0 edit=1 move=1 delete=1 include=1 source=1
    image
    circle(100,100,20) # color=red
    >>> 
    >>> 
    >>> 
    >>> write_ds9cat(x=[1,2],y=[0,3],outputfile='test.reg',size=[10,15],marker=['circle','box'])
    >>> 
    >>> s = os.system('cat test.reg')
    # Region file format: DS9 version 4.1
    # Filename: None
    global color=green dashlist=8 3 width=1 font="helvetica 10 normal" select=1 highlite=1 dash=0 fixed=0 edit=1 move=1 delete=1 include=1 source=1
    image
    circle(1,0,10) # color=red
    box(2,3,15,15,0) # color=red
    >>> 
    
    """


    try:
        if len(x) != len(y):
            print >> sys.stderr,"X and Y lengths do not math. Check their sizes.";
            return False;
    except:
        x = [x];
        y = [y];
        
    centroids = zip(x,y);
    length = len(centroids);
    
    # Lets verify if everyone here is a list/tuple:
    #
    try:
        len(size);
    except TypeError:
        size = [size];
    _diff = max(0,length-len(size))
    if _diff:
        size.extend([ size[-1] for i in range(0,_diff+1) ]);
    #
    if type(marker) == type(str()):
        marker = [marker];
    _diff = max(0,length-len(marker))
    if _diff:
        marker.extend([ marker[-1] for i in range(0,_diff+1) ]);
    #
    if type(color) == type(str()):
        color = [color];
    _diff = max(0,length-len(color))
    if _diff:
        color.extend([ color[-1] for i in range(0,_diff+1) ]);

    output = open(outputfile,'w');
    # DS9 region file header
    output.write("# Region file format: DS9 version 4.1\n");
    output.write("# Filename: %s\n" % (filename));
    output.write("global color=green dashlist=8 3 width=1 font=\"helvetica 10 normal\" ");
    output.write("select=1 highlite=1 dash=0 fixed=0 edit=1 move=1 delete=1 include=1 source=1\n");
    output.write("image\n");

    for i in range(length):
        if marker[i] == 'circle':
            output.write("circle(%s,%s,%s) # color=%s\n" % (x[i],y[i],size[i],color[i]));
        elif marker[i] == 'box':
            output.write("box(%s,%s,%s,%s,0) # color=%s\n" % (x[i],y[i],size[i],size[i],color[i]));
        
    output.close();
    
    return
    
# ---

def read_ds9cat(regionfile):
    """ Function to read ds9 region file

    Only regions marked with a 'circle' or 'box' are read.
    'color' used for region marks (circle/box) are given as
    output together with 'x','y','dx','dy' as list in a 
    dictionary. The key 'image' in the output (<dict>) gives
    the filename in the 'regionfile'.
    
    Input:
     - regionfile   :   ASCII (ds9 format) file
     
    Output:
     -> {'image':str,'x':[],'y':[],'size':[],'marker':[],'color':[]}
    
    
    Example:
    
    >>> write_ds9cat(x=[1,2],y=[0,3],outputfile='test.reg',size=[10,15])
    >>> 
    >>> D = read_ds9cat('test.reg')
    >>> 
    
    """
    
    D_out = {'filename':'', 'marker':[], 'color':[], 'x':[], 'y':[], 'size':[]};

    fp = open(regionfile,'r');

    for line in fp.readlines():

        if (re.search("^#",line)):
            if (re.search("Filename",line)):
                imagename = string.split(line,"/")[-1];
                D_out['filename'] = re.sub("# Filename: ","",imagename).rstrip('\n');
            continue;

        else:
            try:
                _cl = re.search('(?<=color\=).*',line).group();
                color = string.split(_cl)[0];
            except AttributeError:
                pass;

            if re.search("circle",line) or re.search("box",line):
                marker = string.split(line,"(")[0];
            else:
                continue;

            try:
                _fg = re.sub("\)","",re.search('(?<=box\().*\)',line).group());
                x,y,dx,dy = string.split(_fg,sep=",")[:4];
                D_out['x'].append(eval(x));
                D_out['y'].append(eval(y));
                D_out['size'].append(max(eval(dx),eval(dy)));
                D_out['color'].append(color);
                D_out['marker'].append(marker);
                continue;
            except AttributeError:
                pass;

            try:
                _fg = re.sub("\)","",re.search('(?<=circle\().*\)',line).group());
                x,y,R = string.split(_fg,sep=",")[:3];
                D_out['x'].append(eval(x));
                D_out['y'].append(eval(y));
                D_out['size'].append(eval(R));
                D_out['color'].append(color);
                D_out['marker'].append(marker);
                continue;
            except AttributeError:
                pass;

    fp.close();
    return D_out;
    
# ---
if __name__ == "__main__":
    import doctest;
    doctest.testmod()
