import numpy as np
import scipy.stats as st

import pymc

d2r = np.pi/180.
r2d = 180./np.pi
eps = 1.e-6

def _vmf_random(lon_lat, kappa, size=None):
    # make the appropriate euler rotation matrix
    alpha = 0.
    beta = np.pi/2. - lon_lat[1]*d2r
    gamma = lon_lat[0]*d2r
    rot_alpha = np.array( [ [np.cos(alpha), -np.sin(alpha), 0.],
                            [np.sin(alpha), np.cos(alpha), 0.],
                            [0., 0., 1.] ] )
    rot_beta = np.array( [ [np.cos(beta), 0., np.sin(beta)],
                           [0., 1., 0.],
                           [-np.sin(beta), 0., np.cos(beta)] ] )
    rot_gamma = np.array( [ [np.cos(gamma), -np.sin(gamma), 0.],
                            [np.sin(gamma), np.cos(gamma), 0.],
                            [0., 0., 1.] ] )
    rotation_matrix = np.dot( rot_gamma, np.dot( rot_beta, rot_alpha ) )

    def cartesian_sample_generator():
        # Generate samples around the z-axis, then rotate
        # to the appropriate position using euler angles

        # z-coordinate is determined by inversion of the cumulative
        # distribution function for that coordinate.
        zeta = st.uniform.rvs(loc=0., scale=1.)
        if kappa < eps:
            z = 2.*zeta-1.
        else:
            z = 1. + 1./kappa * np.log(zeta + (1.-zeta)*np.exp(-2.*kappa) )

        # x and y coordinates can be determined by a 
        # uniform distribution in longitude.
        phi = st.uniform.rvs(loc=0., scale=2.*np.pi)
        x = np.sqrt(1.-z*z)*np.cos(phi)
        y = np.sqrt(1.-z*z)*np.sin(phi)

        # Rotate the samples to have the correct mean direction
        unrotated_samples = np.array([x,y,z])
        samples = np.transpose(np.dot(rotation_matrix, unrotated_samples))
        return samples
        
    s = cartesian_sample_generator() 
    lon_lat = np.array( [np.arctan2( s[1], s[0]), np.pi/2. - np.arccos(s[2]/np.sqrt(np.dot(s,s)))] )*r2d
    return lon_lat 

def _vmf_logp(x, lon_lat, kappa):

    if kappa < eps:
        return np.log(1./4./np.pi)
    if lon_lat[1] < - 90. or lon_lat[1] > 90.:
        return -np.inf

    xp = x.reshape((-1,2))
    mu = np.array([ np.cos(lon_lat[1]*d2r) * np.cos(lon_lat[0]*d2r),
                    np.cos(lon_lat[1]*d2r) * np.sin(lon_lat[0]*d2r),
                    np.sin(lon_lat[1]*d2r) ] ) 
    test_point = np.transpose(np.array([ np.cos(xp[:,1]*d2r) * np.cos(xp[:,0]*d2r),
                                         np.cos(xp[:,1]*d2r) * np.sin(xp[:,0]*d2r),
                                         np.sin(xp[:,1]*d2r) ] ))

    logp_elem = np.log( -kappa / ( 2.*np.pi * np.expm1(-2.*kappa)) ) + \
                kappa * (np.dot(test_point,mu)-1.)
    return logp_elem.sum()

VonMisesFisher = pymc.stochastic_from_dist('von_mises_fisher', 
                                           logp=_vmf_logp,
                                           random=_vmf_random,
                                           dtype=np.float,
                                           mv=True)


