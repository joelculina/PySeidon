#!/usr/bin/python2.7
# encoding: utf-8

from __future__ import division
import numpy as np
import sys
import numexpr as ne
from datetime import datetime
from datetime import timedelta
from interpolation_utils import *
from miscellaneous import *
from BP_tools import *
from shortest_element_path import *
import time
import seaborn

#TR comment: This all routine needs to be tested and debugged
class FunctionsFvcomThreeD:
    """
    Description:
    -----------
    'Utils3D' subset of FVCOM class gathers
    useful methods and functions for 3D runs
    """
    def __init__(self, variable, grid, plot, util, History, debug):
        #Inheritance
        self._debug = debug
        self._var = variable
        self._grid = grid
        self._plot = plot
        self._History = History
        self._util = util
        self.interpolation_at_point = self._util.interpolation_at_point
        self.hori_velo_norm = self._util.hori_velo_norm

        #Create pointer to FVCOM class
        variable = self._var
        grid = self._grid
        History = self._History

    def depth(self, debug=False):
        """
        This method computes new grid variable: 'depth' (m)
        -> FVCOM.Grid.depth

        Notes:
        -----
          - depth convention: 0 = free surface
          - Can take time over the full domain
        """
        debug = debug or self._debug
        if debug:
            start = time.time()

        print "Computing depth..."
        #Compute depth      
        size = self._grid.nele
        size1 = self._grid.ntime
        size2 = self._grid.nlevel
        elc = np.zeros((size1, size))
        hc = np.zeros((size))
        siglay = np.zeros((size2, size))

        try:
            for ind, value in enumerate(self._grid.trinodes):
                elc[:, ind] = np.mean(self._var.el[:, value], axis=1)
                hc[ind] = np.mean(self._grid.h[value])
                siglay[:,ind] = np.mean(self._grid.siglay[:,value],1)

            zeta = self._var.el[:,:] + h[None,:]
            dep = zeta[:,None,:]*siglay[None,:,:]
        except MemoryError:
            print '---Data too large for machine memory---'
            print 'Tip: use ax or tx during class initialisation'
            print '---  to use partial data'
            raise

        if debug:
            end = time.time()
            print "Computation time in (s): ", (end - start)

        # Add metadata entry
        self._grid.depth = dep
        self._History.append('depth computed')
        print '-Depth added to FVCOM.Variables.-'

    def depth_at_point(self, pt_lon, pt_lat, index=[], debug=False):
        """
        This function computes depth at any given point.

        Inputs:
        ------
          - pt_lon = longitude in decimal degrees East, float number
          - pt_lat = latitude in decimal degrees North, float number

        Outputs:
        -------
          - dep = depth, 2D array (ntime, nlevel)

        Keywords:
        --------
          - index = element index, interger. Use only if closest element
                    index is already known

        Notes:
        -----
          - depth convention: 0 = free surface
          - index is used in case one knows already at which
            element depth is requested
        """
        debug = debug or self._debug
        if debug:
            print "Computing depth..."
            start = time.time()

        #Finding index
        if index==[]:      
            index = closest_point([pt_lon], [pt_lat],
                                  self._grid.lonc,
                                  self._grid.latc, debug=debug)[0]

        if not hasattr(self._grid, 'depth'):
            #Compute depth
            h = self.interpolation_at_point(self._grid.h, pt_lon, pt_lat,
                                            index=index, debug=debug)
            el = self.interpolation_at_point(self._var.el, pt_lon, pt_lat,
                                             index=index, debug=debug)
            siglay = self.interpolation_at_point(self._grid.siglay, pt_lon, pt_lat,
                                                 index=index, debug=debug)
            zeta = el + h
            dep = zeta[:,None]*siglay[None,:]
        else:
            dep = self.interpolation_at_point(self._grid.depth,
                                              pt_lon, pt_lat, index=index,
                                              debug=debug)          
        if debug:
            end = time.time()
            print "Computation time in (s): ", (end - start)

        return dep

    def verti_shear(self, debug=False):
        """
        This method computes a new variable: 'vertical shear' (1/s)
        -> FVCOM.Variables.verti_shear

        Notes:
        -----
          - Can take time over the full doma
        """
        debug = debug or self._debug
        if debug:
            print 'Computing vertical shear...'
              
        #Compute depth if necessary
        if not hasattr(self._grid, 'depth'):        
           depth = self.depth(debug=debug)
        depth = self._grid.depth

        # Checking if horizontal velocity norm already exists
        if not hasattr(self._var, 'hori_velo_norm'):
            self.hori_velo_norm()
        vel = self._var.hori_velo_norm

        try:
            #Sigma levels to consider
            top_lvl = self._grid.nlevel - 1
            bot_lvl = 0
            sLvl = range(bot_lvl, top_lvl+1)

            # Compute shear
            dz = depth[:,sLvl[1:],:] - depth[:,sLvl[:-1],:]
            dvel = vel[:,sLvl[1:],:] - vel[:,sLvl[:-1],:]           
            dveldz = dvel / dz
        except MemoryError:
            print '---Data too large for machine memory---'
            print 'Tip: use ax or tx during class initialisation'
            print '---  to use partial data'
            raise

        #Custom return
        self._var.verti_shear = dveldz 
            
        # Add metadata entry
        self._History.append('vertical shear computed')
        print '-Vertical shear added to FVCOM.Variables.-'

        if debug:
            print '...Passed'

    def verti_shear_at_point(self, pt_lon, pt_lat, t_start=[], t_end=[],  time_ind=[],
                             bot_lvl=[], top_lvl=[], graph=True, debug=False):
        """
        This function computes vertical shear at any given point.

        Inputs:
        ------
          - pt_lon = longitude in decimal degrees East, float number
          - pt_lat = latitude in decimal degrees North, float number

        Outputs:
        -------
          - dveldz = vertical shear (1/s), 2D array (time, nlevel - 1)

        Keywords:
        --------
          - t_start = start time, as a string ('yyyy-mm-ddThh:mm:ss'),
                      or time index as an integer
          - t_end = end time, as a string ('yyyy-mm-ddThh:mm:ss'),
                    or time index as an integer
          - time_ind = time indices to work in, list of integers
          - bot_lvl = index of the bottom level to consider, integer
          - top_lvl = index of the top level to consider, integer
          - graph = plots graph if True

        Notes:
        -----
          - use time_ind or t_start and t_end, not both
        """
        debug = debug or self._debug
        if debug:
            print 'Computing vertical shear at point...'

        # Find time interval to work in
        argtime = []
        if not time_ind==[]:
            argtime = time_ind
        elif not t_start==[]:
            if type(t_start)==str:
                argtime = time_to_index(t_start, t_end, self._var.matlabTime, debug=debug)
            else:
                argtime = np.arange(t_start, t_end) 

        # Finding closest point
        index = closest_point([pt_lon], [pt_lat],
                              self._grid.lonc,
                              self._grid.latc, debug=debug)[0]
        #Compute depth
        depth = self.depth_at_point(pt_lon, pt_lat, index=index, debug=debug)

        #Sigma levels to consider
        if top_lvl==[]:
            top_lvl = self._grid.nlevel - 1
        if bot_lvl==[]:
            bot_lvl = 0
        sLvl = range(bot_lvl, top_lvl+1)


        # Checking if vertical shear already exists
        if not hasattr(self._var, 'verti_shear'): 
            u = self._var.u
            v = self._var.v

            #Extraction at point
            if debug:
                print 'Extraction of u and v at point...'
            U = self.interpolation_at_point(u, pt_lon, pt_lat,
                                            index=index, debug=debug)  
            V = self.interpolation_at_point(v, pt_lon, pt_lat,
                                            index=index, debug=debug)
            norm = ne.evaluate('sqrt(U**2 + V**2)')     

            # Compute shear
            dz = depth[:,sLvl[1:]] - depth[:,sLvl[:-1]]
            dvel = norm[:,sLvl[1:]] - norm[:,sLvl[:-1]]           
            dveldz = dvel / dz
        else:
            dveldz = interpolation_at_point(self._var.verti_shear,
                                            pt_lon, pt_lat,
                                            index=index, debug=debug)

        if debug:
            print '...Passed'
        #use time indices of interest
        if not argtime==[]:
            dveldz = dveldz[argtime,:]
            depth = depth[argtime,:]

        #Plot mean values
        if graph:
            mean_depth = np.mean((depth[:,sLvl[1:]]
                       + depth[:,sLvl[:-1]]) / 2.0, 0)
            mean_dveldz = np.mean(dveldz,0)
            self._plot.plot_xy(mean_dveldz, mean_depth, title='Shear profile ',
                               xLabel='Shear (1/s) ', yLabel='Depth (m) ')

        return dveldz             

    def velo_norm(self, debug=False):
        """
        This method computes a new variable: 'velocity norm' (m/s)
        -> FVCOM.Variables.velo_norm

        Notes:
        -----
          -Can take time over the full domain
        """
        if debug or self._debug:
            print 'Computing velocity norm...'
        #Check if w if there
        try:
            try:
                #Computing velocity norm
                u = self._var.u[:]
                v = self._var.v[:]
                w = self._var.w[:]
                vel = ne.evaluate('sqrt(u**2 + v**2 + w**2)')
            except MemoryError:
                print '---Data too large for machine memory---'
                print 'Tip: use ax or tx during class initialisation'
                print '---  to use partial data'
                raise
        except AttributeError:
            try:
                #Computing velocity norm
                u = self._var.u[:]
                v = self._var.v[:]
                vel = ne.evaluate('sqrt(u**2 + v**2)')
            except MemoryError:
                print '---Data too large for machine memory---'
                print 'Tip: use ax or tx during class initialisation'
                print '---  to use partial data'
                raise

        #Custom return    
        self._var.velo_norm = vel 
       
        # Add metadata entry
        self._History.append('Velocity norm computed')
        print '-Velocity norm added to FVCOM.Variables.-'

        if debug or self._debug:
            print '...Passed'

    def velo_norm_at_point(self, pt_lon, pt_lat, t_start=[], t_end=[], time_ind=[],
                           debug=False):
        """
        This function computes the velocity norm at any given point.

        Inputs:
        ------
          - pt_lon = longitude in decimal degrees East, float number
          - pt_lat = latitude in decimal degrees North, float number

        Outputs:
        -------
          - velo_norm = velocity norm, 2D array (time, level)

        Keywords:
        --------
          - t_start = start time, as a string ('yyyy-mm-ddThh:mm:ss'),
                      or time index as an integer
          - t_end = end time, as a string ('yyyy-mm-ddThh:mm:ss'),
                    or time index as an integer
          - time_ind = time indices to work in, list of integers

        Notes:
        -----
          - use time_ind or t_start and t_end, not both
        """
        debug = debug or self._debug
        if debug:
            print 'Computing velocity norm at point...'
       
        # Find time interval to work in
        argtime = []
        if not time_ind==[]:
            argtime = time_ind
        elif not t_start==[]:
            if type(t_start)==str:
                argtime = time_to_index(t_start, t_end, self._var.matlabTime, debug=debug)
            else:
                argtime = arange(t_start, t_end)

        try:
            if not hasattr(self._var, 'velo_norm'):             
                u = self._var.u
                v = self._var.v
                w = self._var.w
            else:
                vel = self._var.velo_norm
        except AttributeError:
            if not hasattr(self._var, 'velo_norm'):             
                u = self._var.u
                v = self._var.v
            else:
                vel = self._var.velo_norm


        # Finding closest point
        index = closest_point([pt_lon], [pt_lat],
                              self._grid.lonc,
                              self._grid.latc, debug=debug)[0]

        #Computing horizontal velocity norm
        if debug:
            print 'Extraction of u, v and w at point...'
        if not hasattr(self._var, 'velo_norm'): 
            U = self.interpolation_at_point(u, pt_lon, pt_lat,
                                            index=index, debug=debug)  
            V = self.interpolation_at_point(v, pt_lon, pt_lat,
                                            index=index, debug=debug)
            if 'w' in locals():
                W = self.interpolation_at_point(w, pt_lon, pt_lat,
                                                index=index, debug=debug)
                velo_norm = ne.evaluate('sqrt(U**2 + V**2 + W**2)')
            else:
                velo_norm = ne.evaluate('sqrt(U**2 + V**2)')
        else:
            velo_norm = self.interpolation_at_point(vel, pt_lon, pt_lat,
                                                    index=index, debug=debug)
        if debug:
            print '...passed'

        #use only the time indices of interest
        if not argtime==[]:
            velo_norm = velo_norm[argtime[:],:]  

        return velo_norm 


    def flow_dir_at_point(self, pt_lon, pt_lat, t_start=[], t_end=[], time_ind=[], 
                          vertical=True, debug=False):
        """
        This function computes flow directions and associated norm
        at any given location.

        Inputs:
        ------
          - pt_lon = longitude in decimal degrees East to find
          - pt_lat = latitude in decimal degrees North to find

        Outputs:
        -------
          - flowDir = flowDir at (pt_lon, pt_lat), 2D array (ntime, nlevel)
          - norm = velocity norm at (pt_lon, pt_lat), 2D array (ntime, nlevel)

        Keywords:
        -------
          - t_start = start time, as a string ('yyyy-mm-ddThh:mm:ss'),
                      or time index as an integer
          - t_end = end time, as a string ('yyyy-mm-ddThh:mm:ss'),
                    or time index as an integer
          - time_ind = time indices to work in, list of integers
          - vertical = True, compute flowDir for each vertical level
        Notes:
        -----
          - directions between -180 and 180 deg., i.e. 0=East, 90=North,
            +/-180=West, -90=South
          - use time_ind or t_start and t_end, not both
        """
        debug = debug or self._debug
        if debug:
            print 'Computing flow directions at point...'

        # Finding closest point
        index = closest_point([pt_lon], [pt_lat],
                              self._grid.lonc,
                              self._grid.latc, debug=debug)[0]

        # Find time interval to work in
        argtime = []
        if not time_ind==[]:
            argtime = time_ind
        elif not t_start==[]:
            if type(t_start)==str:
                argtime = time_to_index(t_start, t_end, self._var.matlabTime, debug=debug)
            else:
                argtime = arange(t_start, t_end)
        
        #Checking if dir_flow already computed
        if not hasattr(self._var, 'flow_dir'):
            #Choose the right pair of velocity components
            if self._var._3D and vertical:
                u = self._var.u
                v = self._var.v
            else:
                u = self._var.ua
                v = self._var.va

            #Extraction at point
            if debug:
                print 'Extraction of u and v at point...'
            U = self._util.interpolation_at_point(u, pt_lon, pt_lat,
                                                  index=index, debug=debug)  
            V = self._util.interpolation_at_point(v, pt_lon, pt_lat,
                                                  index=index, debug=debug)       

            #Compute directions
            if debug:
                print 'Computing arctan2 and norm...'
            dirFlow = np.rad2deg(np.arctan2(V,U))

        else:
            dirFlow = self._util.interpolation_at_point(self._var.flow_dir,
                                                            pt_lon, pt_lat,
                                                            index=index, debug=debug) 
         
        if debug: print '...Passed'
        #use only the time indices of interest
        if not argtime==[]:
            dirFlow = dirFlow[argtime[:],:]
            norm = norm[argtime[:],:] 

        return dirFlow, norm

    def flow_dir(self, debug=False):
        """"
        This method computes a new variable: 'flow directions' (deg.)
        -> FVCOM.Variables.flow_dir

        Notes:
        -----
          - directions between -180 and 180 deg., i.e. 0=East, 90=North,
            +/-180=West, -90=South
          - Can take time over the full domain
        """
        if debug or self._debug:
            print 'Computing flow directions...'

        try:
            u = self._var.u
            v = self._var.v
            dirFlow = np.rad2deg(np.arctan2(V,U))
        except MemoryError:
            print '---Data too large for machine memory---'
            print 'Tip: use ax or tx during class initialisation'
            print '---  to use partial data'
            raise

        #Custom return    
        self._var.flow_dir = dirFlow 

        # Add metadata entry
        self._History.append('flow directions computed')
        print '-Flow directions added to FVCOM.Variables.-'

        if debug or self._debug:
            print '...Passed'

    def vorticity(self, debug=False):
        """
        This method creates a new variable: 'depth averaged vorticity' (1/s)
        -> FVCOM.Variables.vorticity
     
        Notes:
        -----
          - Can take time over the full domain
        """
        debug = (debug or self._debug)
        if debug:
            print 'Computing vorticity...'
            start = time.time()

        t = arange(self._grid.ntime)  

        #Surrounding elements
        n1 = self._grid.triele[:,0]
        n2 = self._grid.triele[:,1]
        n3 = self._grid.triele[:,2]
        #TR comment: not quiet sure what this step does
        n1[np.where(n1==0)[0]] = self._grid.trinodes.shape[1]
        n2[np.where(n2==0)[0]] = self._grid.trinodes.shape[1]
        n3[np.where(n3==0)[0]] = self._grid.trinodes.shape[1]
        if debug:
            end = time.time()
            print "Check element=0, computation time in (s): ", (end - start)
            print "start np.multiply" 

        x0 = self._grid.xc
        y0 = self._grid.yc
        
        dvdx = np.zeros((self._grid.ntime,self._grid.nlevel,self._grid.nele))
        dudy = np.zeros((self._grid.ntime,self._grid.nlevel,self._grid.nele))

        j=0
        for i in t:
            dvdx[j,:,:] = np.multiply(self._grid.a1u[0,:], self._var.v[i,:,:]) \
                        + np.multiply(self._grid.a1u[1,:], self._var.v[i,:,n1]) \
                        + np.multiply(self._grid.a1u[2,:], self._var.v[i,:,n2]) \
                        + np.multiply(self._grid.a1u[3,:], self._var.v[i,:,n3])
            dudy[j,:,:] = np.multiply(self._grid.a2u[0,:], self._var.u[i,:,:]) \
                        + np.multiply(self._grid.a2u[1,:], self._var.u[i,:,n1]) \
                        + np.multiply(self._grid.a2u[2,:], self._var.u[i,:,n2]) \
                        + np.multiply(self._grid.a2u[3,:], self._var.u[i,:,n3])
            j+=1
        if debug:
            print "loop number ", i

        vort = dvdx - dudy

        # Add metadata entry
        self._var.vorticity = vort
        self._History.append('vorticity computed')
        print '-Vorticity added to FVCOM.Variables.-'

        if debug:
            end = time.time()
            print "Computation time in (s): ", (end - start) 

    def vorticity_over_period(self, time_ind=[], t_start=[], t_end=[], debug=False):
        """
        This function computes the vorticity for a time period.
     
        Outputs:
        -------
          - vort = horizontal vorticity (1/s), 2D array (time, nele)

        Keywords:
        -------
          - time_ind = time indices to work in, list of integers
          - t_start = start time, as a string ('yyyy-mm-ddThh:mm:ss'),
                      or time index as an integer
          - t_end = end time, as a string ('yyyy-mm-ddThh:mm:ss'),
                    or time index as an integer
        Notes:
        -----
          - Can take time over the full domain
        """
        debug = (debug or self._debug)
        if debug:
            print 'Computing vorticity...'
            start = time.time()

        # Find time interval to work in
        t = []
        if not time_ind==[]:
            t = time_ind
        elif not t_start==[]:
            if type(t_start)==str:
                t = time_to_index(t_start, t_end, self._var.matlabTime, debug=debug)
            else:
                t = arange(t_start, t_end)
        else:
            t = arange(self._grid.ntime)  

        #Checking if vorticity already computed
        if not hasattr(self._var, 'vorticity'): 
            #Surrounding elements
            n1 = self._grid.triele[:,0]
            n2 = self._grid.triele[:,1]
            n3 = self._grid.triele[:,2]
            #TR comment: not quiet sure what this step does
            n1[np.where(n1==0)[0]] = self._grid.trinodes.shape[1]
            n2[np.where(n2==0)[0]] = self._grid.trinodes.shape[1]
            n3[np.where(n3==0)[0]] = self._grid.trinodes.shape[1]
            if debug:
                end = time.time()
                print "Check element=0, computation time in (s): ", (end - start)
                print "start np.multiply" 

            x0 = self._grid.xc
            y0 = self._grid.yc
        
            dvdx = np.zeros((t.shape[0],self._grid.nlevel,self._grid.nele))
            dudy = np.zeros((t.shape[0],self._grid.nlevel,self._grid.nele))

            j=0
            for i in t:
                dvdx[j,:,:] = np.multiply(self._grid.a1u[0,:], self._var.v[i,:,:]) \
                          + np.multiply(self._grid.a1u[1,:], self._var.v[i,:,n1]) \
                          + np.multiply(self._grid.a1u[2,:], self._var.v[i,:,n2]) \
                          + np.multiply(self._grid.a1u[3,:], self._var.v[i,:,n3])
                dudy[j,:,:] = np.multiply(self._grid.a2u[0,:], self._var.u[i,:,:]) \
                          + np.multiply(self._grid.a2u[1,:], self._var.u[i,:,n1]) \
                          + np.multiply(self._grid.a2u[2,:], self._var.u[i,:,n2]) \
                          + np.multiply(self._grid.a2u[3,:], self._var.u[i,:,n3])
                j+=1
            if debug:
                print "loop number ", i

            vort = dvdx - dudy
        else:
            vort = self._var.vorticity[t[:],:,:]

        if debug:
            end = time.time()
            print "Computation time in (s): ", (end - start) 
        return vort

    def power_density(self, debug=False):
        """
        This method creates a new variable: 'power density' (W/m2)
        -> FVCOM.Variables.power_density

        The power density (pd) is then calculated as follows:
            pd = 0.5*1025*(u**3)

        Notes:
        -----
          - This may take some time to compute depending on the size
            of the data set
        """
        debug = (debug or self._debug)
        if debug: print "Computing power assessment..."

        if not hasattr(self._var, 'velo_norm'):
            if debug: print "Computing velo norm..."
            self.velo_norm(debug=debug)
        if debug: print "Computing powers of velo norm..."
        u = self._var.velo_norm
        if debug: print "Computing pd..."
        pd = ne.evaluate('0.5*1025.0*(u**3)')  

        # Add metadata entry
        self._var.power_density = pd
        self._History.append('power density computed')
        print '-Power density to FVCOM.Variables.-' 

    def power_assessment(self, cut_in=1.0, cut_out=4.5, tsr=4.3, 
                                        a4=0.002, a3=-0.03, a2=0.1,
                                        a1=-0.1, a0=0.8,
                                        b2=-0.02, b1=0.2, b0=-0.005, debug=False):
        """
        This method creates a new variable: 'power assessment' (W/m2)
        -> FVCOM.Variables.power_assessment

        This function performs tidal turbine power assessment by accounting for
        cut-in and cut-out speed, power curve (pc):
            pc = a4*(u**4) + a3*(u**3) + a2*(u**2) + a1*u + a0
        (where u is the flow speed)
        and device controled power coefficient (dcpc):
            dcpc =  b2*(tsr**2) + b1*tsr + b0
        The power density (pd) is then calculated as follows:
            pd = pc*dcpc*(1/2)*1025*(u**3)

        Keywords:
        --------
          - cut_in = cut-in speed in m/s, float
          - cut_out = cut-out speed in m/s, float
          - tsr = tip speed ratio, float
          - a4 = pc curve parameter, float
          - a3 = pc curve parameter, float        
          - a2 = pc curve parameter, float
          - a1 = pc curve parameter, float
          - a0 = pc curve parameter, float    
          - b2 = dcpc curve parameter, float
          - b1 = dcpc curve parameter, float
          - b0 = dcpc curve parameter, float
        Notes:
        -----
          - This may take some time to compute depending on the size
            of the data set
        """
        debug = (debug or self._debug)
        if debug: print "Computing power assessment..."

        if not hasattr(self._var, 'velo_norm'):
            if debug: print "Computing velo norm..."
            self.velo_norm(debug=debug)
        if debug: print "Computing powers of velo norm..."
        u = self._var.velo_norm
        if debug: print "Computing pc and dcpc..."
        pc = ne.evaluate('a4*(u**4) + a3*(u**3) + a2*(u**2) + a1*u + a0')
        dcpc = ne.evaluate('b2*(tsr**2) + b1*tsr + b0')
        if debug: print "Computing pd..."
        pd = ne.evaluate('pc*dcpc*0.5*1025.0*(u**3)')

        if debug: print "finding cut-in..."
        u = cut_in
        pcin = ne.evaluate('a4*(u**4) + a3*(u**3) + a2*(u**2) + a1*u + a0')
        dcpcin = ne.evaluate('b2*(tsr**2) + b1*tsr + b0')
        pdin = ne.evaluate('pcin*dcpcin*0.5*1025.0*(u**3)')
        #TR comment huge bottleneck here
        #ind = np.where(pd<pdin)[0]
        #if not ind.shape[0]==0:
        #    pd[ind] = 0.0
        for i in range(pd.shape[0]):
            for j in range(pd.shape[1]):
                for k in range(pd.shape[2]):
                    if pd[i,j,k] < pdin:
                       pd[i,j,k] = 0.0 

        if debug: print "finding cut-out..."
        u = cut_out
        pcout = ne.evaluate('a4*(u**4) + a3*(u**3) + a2*(u**2) + a1*u + a0')
        dcpcout = ne.evaluate('b2*(tsr**2) + b1*tsr + b0')
        pdout = ne.evaluate('pcout*dcpcout*0.5*1025.0*(u**3)')
        #TR comment huge bottleneck here
        #ind = np.where(pd>pdout)[0]
        #if not ind.shape[0]==0:
        #    pd[ind] = pdout
        for i in range(pd.shape[0]):
            for j in range(pd.shape[1]):
                for k in range(pd.shape[2]):
                    if pd[i,j,k] > pdout:
                       pd[i,j,k] = pdout       

        # Add metadata entry
        self._var.power_assessment = pd
        self._History.append('power assessment computed')
        print '-Power assessment to FVCOM.Variables.-'  

    def _vertical_slice(self, var, start_pt, end_pt,
                        time_ind=[], t_start=[], t_end=[],
                        title='Title', cmax=[], cmin=[], debug=False):
        """
        Draw vertical slice in var along the shortest path between
        start_point, end_pt.
 
        Inputs:
        ------
          - var = 2D dimensional (sigma level, element) variable, array
          - start_pt = starting point, [longitude, latitude]
          - end_pt = ending point, [longitude, latitude]

        Keywords:
        --------
          - time_ind = reference time indices for surface elevation, list of integer
          - t_start = start time, as a string ('yyyy-mm-ddThh:mm:ss'),
                      or time index as an integer
          - t_end = end time, as a string ('yyyy-mm-ddThh:mm:ss'),
                    or time index as an integer

        Keywords for plot:
        -----------------
          - title = plot title, string
          - cmin = minimum limit colorbar
          - cmax = maximum limit colorbar
        """
        debug = debug or self._debug
        if not self._var._3D:
            print "Error: Only available for 3D runs."
            raise
        else: 
            lons = [start_pt[0], end_pt[0]]
            lats = [start_pt[1], end_pt[1]]
            #Finding the closest elements to start and end points
            ind = closest_point(lons, lats, self._grid.lonc, self._grid.latc, debug)

            #Finding the shortest path between start and end points
            if debug : print "Computing shortest path..."
            short_path = shortest_element_path(self._grid.lonc[:],
                                               self._grid.latc[:],
                                               self._grid.lon[:],
                                               self._grid.lat[:],
                                               self._grid.trinodes[:],
                                               self._grid.h[:], debug=debug)
            el, _ = short_path.getTargets([ind])           
            # Plot shortest path
            short_path.graphGrid(plot=True)

            # Find time interval to work in
            argtime = []
            if not time_ind==[]:
                argtime = time_ind
            elif not t_start==[]:
                if type(t_start)==str:
                    argtime = time_to_index(t_start, t_end,
                                            self._var.matlabTime, debug=debug)
                else:
                    argtime = arange(t_start, t_end)
 
            #Extract along line
            ele=np.asarray(el[:])[0,:]
            varP = var[:,ele]
            # Depth along line
            if debug : print "Computing depth..."
            depth = np.zeros((self._grid.ntime, self._grid.nlevel, ele.shape[0]))
            I=0
            for ind in ele:
                value = self._grid.trinodes[ind]
                h = np.mean(self._grid.h[value])
                zeta = np.mean(self._var.el[:,value],1) + h
                siglay = np.mean(self._grid.siglay[:,value],1)
                depth[:,:,I] =  zeta[:,None]*siglay[None,:]
                I+=1
            # Average depth over time
            if not argtime==[]:
                depth = np.mean(depth[argtime,:,:], 0)
            else:
                depth = np.mean(depth, 0)
              
            # Compute distance along line
            x = self._grid.xc[ele]
            y = self._grid.yc[ele]
            # Pythagore + cumulative path 
            line = np.zeros(depth.shape)
            dl = np.sqrt(np.square(x[1:]-x[:-1]) + np.square(y[1:]-y[:-1]))
            for i in range(1,dl.shape[0]):
                dl[i] = dl[i] + dl[i-1]
            line[:,1:] = dl[:]
           
            #turn into gridded
            #print 'Compute gridded data'
            #nx, ny = 100, 100
            #xi = np.linspace(x.min(), x.max(), nx)
            #yi = np.linspace(y.min(), y.max(), ny)

            #Plot features
            #setting limits and levels of colormap
            if cmax==[]:
                cmax = varP[:].max()
            if cmin==[]:
                cmin = varP[:].min()
            step = (cmax-cmin) / 20.0
            levels=np.arange(cmin, (cmax+step), step)
            #plt.clf()
            fig = plt.figure(figsize=(18,10))
            plt.rc('font',size='22')
            fig.add_subplot(111) #,aspect=(1.0/np.cos(np.mean(lat)*np.pi/180.0)))
            #levels = np.linspace(0,3.3,34)
            #cs = ax.contourf(line,depth,varP,levels=levels, cmap=plt.cm.jet)
            cs = plt.contourf(line,depth,varP,levels=levels, vmax=cmax,vmin=cmin,
                              cmap=plt.get_cmap('jet'))
            cbar = fig.colorbar(cs)
            #cbar.set_label(title, rotation=-90,labelpad=30)
            plt.contour(line,depth,varP,cs.levels) #, linewidths=0.5,colors='k')
            #ax.set_title()
            plt.title(title)
            #scale = 1
            #ticks = ticker.FuncFormatter(lambda lon, pos: '{0:g}'.format(lon/scale))
            #ax.xaxis.set_major_formatter(ticks)
            #ax.yaxis.set_major_formatter(ticks)
            plt.xlabel('Distance along line (m)')
            plt.ylabel('Depth (m)')
