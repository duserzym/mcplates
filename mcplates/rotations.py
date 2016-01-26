import numpy as np
import theano.tensor as tt

d2r = np.pi/180.
r2d = 180./np.pi

def spherical_to_cartesian( longitude, latitude, norm ):
#    assert(tt.all(tt.ge(longitude, 0.)) and tt.all(tt.le(longitude,360.)))
    assert(tt.all(tt.ge(latitude, -90.)) and tt.all(tt.le(latitude,90.)))
    assert(tt.all(tt.ge(norm, 0.)))
    colatitude = 90.-latitude
    return [ norm * tt.sin(colatitude*d2r)*tt.cos(longitude*d2r),
             norm * tt.sin(colatitude*d2r)*tt.sin(longitude*d2r),
             norm * tt.cos(colatitude*d2r) ]

def cartesian_to_spherical( vecs ):
    v = tt.reshape(vecs, (3,-1))
    norm = tt.sqrt(v[0,:]*v[0,:] + v[1,:]*v[1,:] + v[2,:]*v[2,:])
    latitude = 90. - tt.arccos(v[2,:]/norm)*r2d
    longitude = tt.arctan2(v[1,:], v[0,:] )*r2d
    return longitude, latitude, norm

def rotate_x(vector, theta):
    flat_rot = tt.as_tensor_variable([1., 0., 0.,
                                      0., tt.cos(theta), -tt.sin(theta),
                                      0., tt.sin(theta), tt.cos(theta)])
    rot = flat_rot.reshape((3,3))
    return tt.dot(rot, vector.T)

def rotate_y(vector, theta):
    flat_rot = tt.as_tensor_variable([tt.cos(theta), 0., tt.sin(theta),
                                      0., 1., 0.,
                                      -tt.sin(theta), 0., tt.cos(theta)])
    rot = flat_rot.reshape((3,3))
    return tt.dot(rot, vector.T)

def rotate_z(vector, theta):
    flat_rot = tt.as_tensor_variable([tt.cos(theta), -tt.sin(theta), 0.,
                                      tt.sin(theta), tt.cos(theta), 0.,
                                      0., 0., 1.])
    rot = flat_rot.reshape((3,3))
    return tt.dot(rot, vector.T)

def construct_euler_rotation_matrix(alpha, beta, gamma):
    """
    Make a 3x3 matrix which represents a rigid body rotation,
    with alpha being the first rotation about the z axis,
    beta being the second rotation about the y axis, and
    gamma being the third rotation about the z axis.
 
    All angles are assumed to be in radians
    """
    flat_rot_alpha = tt.as_tensor_variable([ tt.cos(alpha), -tt.sin(alpha), 0.,
                                             tt.sin(alpha), tt.cos(alpha), 0.,
                                             0., 0., 1.])
    flat_rot_beta = tt.as_tensor_variable([ tt.cos(beta), 0., tt.sin(beta),
                                            0., 1., 0.,
                                            -tt.sin(beta), 0., tt.cos(beta)])
    flat_rot_gamma = tt.as_tensor_variable([ tt.cos(gamma), -tt.sin(gamma), 0.,
                                             tt.sin(gamma), tt.cos(gamma), 0.,
                                             0., 0., 1.])
    rot_alpha = flat_rot_alpha.reshape((3,3))
    rot_beta = flat_rot_beta.reshape((3,3))
    rot_gamma = flat_rot_gamma.reshape((3,3))

    rot = tt.dot( rot_gamma, tt.dot( rot_beta, rot_alpha ) )
    return rot

def rotate(pole, rotation_pole, angle):
    # The idea is to rotate the pole so that the Euler pole is
    # at the pole of the coordinate system, then perform the
    # requested rotation, then restore things to the original
    # orientation 
    lon,lat,norm = cartesian_to_spherical(rotation_pole)
    colat = 90.-lat
    p = rotate_z(pole, -lon[0]*d2r)
    p = rotate_y(p, -colat[0]*d2r)
    p = rotate_z(p, angle*d2r)
    p = rotate_y(p, colat[0]*d2r)
    return rotate_z(p, lon[0]*d2r)

def rotate_numpy(pole, rotation_pole, angle):
    # The idea is to rotate the pole so that the Euler pole is
    # at the pole of the coordinate system, then perform the
    # requested rotation, then restore things to the original
    # orientation 
    lon,lat,norm = cartesian_to_spherical_numpy(rotation_pole)
    colat = 90.-lat
    m1 = construct_euler_rotation_matrix_numpy( -lon[0]*d2r, -colat[0]*d2r, angle*d2r )
    m2 = construct_euler_rotation_matrix_numpy( 0., colat[0]*d2r, lon[0]*d2r )
    return np.dot( m2, np.dot(m1, pole) )

def construct_euler_rotation_matrix_numpy(alpha, beta, gamma):
    """
    Make a 3x3 matrix which represents a rigid body rotation,
    with alpha being the first rotation about the z axis,
    beta being the second rotation about the y axis, and
    gamma being the third rotation about the z axis.
 
    All angles are assumed to be in radians
    """
    rot_alpha = np.array( [ [np.cos(alpha), -np.sin(alpha), 0.],
                            [np.sin(alpha), np.cos(alpha), 0.],
                            [0., 0., 1.] ] )
    rot_beta = np.array( [ [np.cos(beta), 0., np.sin(beta)],
                           [0., 1., 0.],
                           [-np.sin(beta), 0., np.cos(beta)] ] )
    rot_gamma = np.array( [ [np.cos(gamma), -np.sin(gamma), 0.],
                            [np.sin(gamma), np.cos(gamma), 0.],
                            [0., 0., 1.] ] )
    rot = np.dot( rot_gamma, np.dot( rot_beta, rot_alpha ) )
    return rot

def spherical_to_cartesian_numpy( longitude, latitude, norm ):
#    assert(np.all(longitude >= 0.) and np.all(longitude <= 360.))
    assert(np.all(latitude >= -90.) and np.all(latitude <= 90.))
    assert(np.all(norm >= 0.))
    colatitude = 90.-latitude
    return np.array([ norm * np.sin(colatitude*d2r)*np.cos(longitude*d2r),
                      norm * np.sin(colatitude*d2r)*np.sin(longitude*d2r),
                      norm * np.cos(colatitude*d2r) ] )

def cartesian_to_spherical_numpy( vecs ):
    v = np.reshape(vecs, (3,-1))
    norm = np.sqrt(v[0,:]*v[0,:] + v[1,:]*v[1,:] + v[2,:]*v[2,:])
    latitude = 90. - np.arccos(v[2,:]/norm)*r2d
    longitude = np.arctan2(v[1,:], v[0,:] )*r2d
    return longitude, latitude, norm