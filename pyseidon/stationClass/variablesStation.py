#!/usr/bin/python2.7
# encoding: utf-8

from __future__ import division
import numpy as np
from itertools import groupby
from operator import itemgetter
#Local import
from miscellaneous import time_to_index
from miscellaneous import mattime_to_datetime

class _load_grid:
    '''
'Grid' subset in Station class contains grid related quantities:
-------------------------------------------------------------
Some grid data are directly passed on from Station output:
                _lon = longitudes at nodes (deg.), 2D array (ntime, nnode)
               |_lat = latitudes at nodes (deg.), 2D array (ntime, nnode)
 Station.Grid._|_x = x coordinates at nodes (m), 2D array (ntime, nnode)
               |_y = y coordinates at nodes (m), 2D array (ntime, nnode)
               |_h = bathymetry (m), 2D array (ntime, nnode)
               |_nele = element dimension, integer
               |_nnode = node dimension, integer
               |_nlevel = vertical level dimension, integer
               |_ntime = time dimension, integer
               |_siglay = sigma layers, 2D array (nlevel, nnode)
               |_siglay = sigma levels, 2D array (nlevel+1, nnode)
               |_name = name of the stations, (nnode, 20)


Some others shall be generated as methods are being called, ex:
             ...
             |_triangle = triangulation object for plotting purposes    
    '''
    def __init__(self, data, elements, History, debug=False):  
        if debug:
            print 'Loading grid...'
        #Pointer to History
        self._History = History
        History = self._History

        self.x = data.variables['x'][elements]
        self.y = data.variables['y'][elements]
        self.lon = data.variables['lon'][elements]
        self.lat = data.variables['lat'][elements]
        self.siglay = data.variables['siglay'][:,elements]
        self.siglev = data.variables['siglev'][:,elements]
        self.h = data.variables['h'][elements]
        self.name = data.variables['name_station'][elements,:]
        self.nlevel = self.siglay.shape[0]
        self.nele = self.x.shape[0]
        self.nnode = self.x.shape[0]

        #Computing bounding box
        lon = self.lon[:]
        lat = self.lat[:]
        if debug: print "Computing bounding box..."
        ax = [lon.min(), lon.max(), lat.min(), lat.max()]
        self._ax = ax
        # Add metadata entry
        text = 'Bounding box =' + str(ax)
        self._History.append(text)
    
        if debug:
            print '...Passed'

class _load_var:
    """
'Variables' subset in Station class contains the numpy arrays:
-----------------------------------------------------------
Some variables are directly passed on from Station output:
                     _el = elevation (m), 2D array (ntime, nnode)
                    |_julianTime = julian date, 1D array (ntime)
                    |_matlabTime = matlab time, 1D array (ntime)
                    |_ua = depth averaged u velocity component (m/s),
                    |      2D array (ntime, nele)
                    |_va = depth averaged v velocity component (m/s),
 Station.Variables._|      2D array (ntime, nele)
                    |_u = u velocity component (m/s),
                    |     3D array (ntime, nlevel, nele)
                    |_v = v velocity component (m/s),
                    |     3D array (ntime, nlevel, nele)
                    |_w = w velocity component (m/s),
                          3D array (ntime, nlevel, nele)

Some others shall be generated as methods are being called, ex:
                    ...
                    |_hori_velo_norm = horizontal velocity norm (m/s),
                    |                  2D array (ntime, nele)
                    |_velo_norm = velocity norm (m/s),
                    |             3D array (ntime, nlevel, nele)
                    |_verti_shear = vertical shear (1/s),
                                  3D array (ntime, nlevel, nele)           
    """
    def __init__(self, data, elements, grid, History, debug=False):
        if debug: print 'Loading variables...'

        #Pointer to History
        self._History = History
        History = self._History

        #List of keywords
        kwl2D = ['ua', 'va', 'zeta']
        kwl3D = ['ww', 'u', 'v', 'gls', 'tke']
        #List of aliaSes
        al2D = ['ua', 'va', 'el']
        al3D = ['u', 'u', 'v', 'gls', 'tke']         

        if debug: print '...time variables...'
        self.julianTime = data.variables['time_JD'][:]
        self.secondTime = data.variables['time_second'][:]
        self.matlabTime = self.julianTime[:] + 678942.0 + self.secondTime[:] / (24*3600)
        grid.ntime = self.matlabTime.shape[0]

        if debug: print '...hydro variables...'

        region_e = elements
        region_n = elements
        #Redefine variables in bounding box
        #Check if OpenDap variables or not
        if type(data.variables).__name__=='DatasetType':
            #loading hori data
            keyCount = 0
            for key, aliaS in zip(kwl2D, al2D):
                #Special loading for zeta
                H = 0 #local counter
                if key == 'zeta':
                    for k, g in groupby(enumerate(region_n), lambda (i,x):i-x):
                        ID = map(itemgetter(1), g)
                        if debug: print 'Index bound: ' +\
                            str(ID[0]) + '-' + str(ID[-1]+1)
                        if H==0:
                            setattr(self, aliaS,
                            data.variables[key].data[:,ID[0]:(ID[-1]+1)])
                            H=1
                        else:
                            setattr(self, aliaS,                            
                            np.hstack((getattr(self, aliaS),
                            data.variables[key].data[:,ID[0]:(ID[-1]+1)])))
                else:
                    try:                        
                        for k, g in groupby(enumerate(region_e), lambda (i,x):i-x):
                            ID = map(itemgetter(1), g)
                            if debug: print 'Index bound: ' +\
                                      str(ID[0]) + '-' + str(ID[-1]+1)
                            if H==0:
                                setattr(self, aliaS,
                                        data.variables[key].\
                                        data[:,ID[0]:(ID[-1]+1)])
                                H=1
                            else:
                                setattr(self, aliaS,
                                np.hstack((getattr(self, aliaS),
                                data.variables[key].data[:,ID[0]:(ID[-1]+1)])))
                            keyCount +=1
                    except KeyError:
                        if debug: print key, " is missing !"
                        continue
            if keyCount==0:
                print "---Horizontal variables are missing---"
            self._3D = False 
                    
            #loading verti data
            keyCount = 0
            for key, aliaS in zip(kwl3D, al3D):
                try:
                    H = 0 #local counter
                    for k, g in groupby(enumerate(region_e), lambda (i,x):i-x):
                        ID = map(itemgetter(1), g)
                        if debug: print 'Index bound: ' +\
                                  str(ID[0]) + '-' + str(ID[-1]+1)
                        if H==0:
                            setattr(self, aliaS,
                            data.variables[key].data[:,:,ID[0]:(ID[-1]+1)])
                            H=1
                        else:
                            setattr(self, aliaS,
                            np.dstack((getattr(self, aliaS),
                            data.variables[key].data[:,:,ID[0]:(ID[-1]+1)])))
                    keyCount +=1
                except KeyError:
                    if debug: print key, " is missing !"
                    continue
            if keyCount==0:
                print "---Vertical variables are missing---"
            else:
                self._3D = True
        #Not OpenDap
        else:
            #loading hori data
            keyCount = 0
            for key, aliaS in zip(kwl2D, al2D):
                try:
                    if key=='zeta':
                        setattr(self, aliaS, np.zeros((grid.ntime, grid.nnode)))
                        for i in range(grid.ntime):
                            #TR comment: looping on time indices is a trick from
                            #            Mitchell to improve loading time
                            #TR comment: no idea why I have to transpose here but
                            #            I do !!
                            getattr(self, aliaS)[i,:] =\
                            np.transpose(data.variables[key].data[i,region_n])
                    else:
                        setattr(self, aliaS, np.zeros((grid.ntime, grid.nele)))
                        for i in range(grid.ntime):
                            #TR comment: looping on time indices is a trick from
                            #            Mitchell to improve loading time
                            #TR comment: no idea why I have to transpose here but
                            #            I do !!
                            getattr(self, aliaS)[i,:] =\
                            np.transpose(data.variables[key].data[i,region_e])
                    keyCount +=1
                except KeyError:
                    if debug: print key, " is missing !"
                    continue
            if keyCount==0:
                print "---Horizontal variables are missing---"
            self._3D = False 
            
            #loading verti data
            keyCount = 0
            for key, aliaS in zip(kwl3D, al3D):
                try:
                    testKey = data.variables[key]
                    del testKey
                    setattr(self, aliaS,
                    np.zeros((grid.ntime,grid.nlevel, grid.nele)))
                    for i in range(grid.ntime):
                        #TR comment: looping on time indices is a trick from
                        #            Mitchell to improve loading time
                        #TR comment: no idea why I have to transpose here but
                        #            I do !!
                        getattr(self, aliaS)[i,:,:] =data.variables[key].data[i,:,region_e]
                    keyCount +=1
                except KeyError:
                    if debug: print key, " is missing !"
                    continue
            if keyCount==0:
                print "---Vertical variables are missing---"
            else:
                self._3D = True 
        if debug:
           print '...Passed'

