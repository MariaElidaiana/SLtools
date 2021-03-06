#---------------------------------------------------------------------------------------------------------------------
# Maria's compute_source_density: I changed the way she uses the X variable (she used to name the catalog with argv; I define X inside the function with the name of the UDF catalog)
##@ package compute_source_density COMPUTES THE SOURCE DENSITY BASED ON THE UDF CATALOG
# Based on the Hubble Ultra Deep Field (HUDF) catalog, computes the source density for a given redshift and redshift bin. 
#
#@param zs
#@param delta_zs
#@param zl
#@param source_selection_criteria (to get the catalog path and enhance_nsource, that artificially increases the source density by a multiplicative factor)
#
#@return Return the source density (increased by enhance_nsource)
import sys
from .. import *
def future_compute_source_density(zS, delta_zS, source_catalog): 
	"""Returns the number of sources (objects) from given catalog per unit area

	Input:
	 zS : source (central) redshift
	 delta_zS : width of redshift slice to look for
	 source_catalog : string with source catalog filename

	Output:
	 N_area : number of objects per unit area

	"""
	UDF = source_catalog;
	X = open_fits_catalog(UDF)
	z = get_fits_data(X,'z').values()
	zs = []
	for i in range(len(z[0])):
		if z[0][i]>= (zS-delta_zS/2.0) and z[0][i]< (zS+delta_zS/2.0): 
			zs.append(z[0][i])
	N_area = len(zs)/43092.0

	return N_area

def compute_source_density(zS, delta_zS, source_selection_criteria):

	source_catalog = source_selection_criteria['source_catalog']
	return future_compute_source_density(zS, delta_zS, source_catalog);

