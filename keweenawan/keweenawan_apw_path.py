from __future__ import print_function
import itertools
import numpy as np
import scipy.stats as st
import pandas as pd
import matplotlib.pyplot as plt
import cartopy.crs as ccrs
import sys

import mcplates

# Shift all longitudes by 180 degrees to get around some plotting
# issues. This is error prone, so it should be fixed eventually
lon_shift = 180.

# List of colors to use
colors = ['#a6cee3', '#1f78b4', '#b2df8a', '#33a02c', '#fb9a99', '#e31a1c',
          '#fdbf6f', '#ff7f00', '#cab2d6', '#6a3d9a', '#ffff99', '#b15928']


# Parse input
#Get number of euler rotations
if len(sys.argv) < 2:
    raise Exception("Please enter the number of Euler rotations to fit.")
n_euler_rotations = int(sys.argv[1])
if n_euler_rotations < 1:
    raise Exception("Number of Euler rotations must be greater than zero")
# Read in optional map projection info
if len(sys.argv) > 2:
    proj_type = sys.argv[2].split(',')[0]
    assert proj_type == 'M' or proj_type == 'O'
    proj_lon = float(sys.argv[2].split(',')[1]) - lon_shift
    if proj_type == 'O':
        proj_lat = float(sys.argv[2].split(',')[2])
else:
    proj_type = 'M'
    proj_lon = -lon_shift
    proj_lat = 0.

print("Fitting Keweenawan APW track with "+str(n_euler_rotations)+" Euler rotation" + ("" if n_euler_rotations == 1 else "s") )


data = pd.read_csv("pole_means.csv")
# Give unnamed column an appropriate name
data.rename(columns={'Unnamed: 14': 'GaussianOrUniform'}, inplace=True)
data.drop(2, inplace=True, axis=0)  # Remove data row with huge uncertainty
data.sort_values('AgeNominal', ascending=False, inplace=True)

poles = []
for i, row in data.iterrows():
    pole_lat = row['PLat']
    pole_lon = row['PLon'] - lon_shift
    a95 = row['A95']
    age = row['AgeNominal']

    if row['GaussianOrUniform'] == 'gaussian':
        sigma_age = row['gaussian_2sigma'] / 2.
    elif row['GaussianOrUniform'] == 'uniform':
        sigma_age = (row['AgeLower'], row['AgeUpper'])
    else:
        raise Exception("Unrecognized age error type")

    pole = mcplates.PaleomagneticPole(
        pole_lon, pole_lat, angular_error=a95, age=age, sigma_age=sigma_age)
    poles.append(pole)

slat = 46.8  # Duluth lat
slon = 360. - 92.1 - lon_shift  # Duluth lon

path = mcplates.APWPath(
    'keweenawan_apw_' + str(n_euler_rotations), poles, n_euler_rotations)
path.create_model(site_lon_lat=(slon, slat), watson_concentration=-1.0)


def plot_synthetic_paths():

    if proj_type == 'M':
        ax = plt.axes(projection=ccrs.Mollweide(proj_lon))
    elif proj_type == 'O':
        ax = plt.axes(projection = ccrs.Orthographic(proj_lon,proj_lat))

    ax.gridlines()
    ax.set_global()

    direction_samples = path.euler_directions()

    for directions in direction_samples:
        mcplates.plot.plot_distribution(ax, directions[:, 0], directions[:, 1])

    mcplates.plot.plot_continent(ax, 'laurentia', rotation_pole=mcplates.Pole(0., 90., 1.0), angle=-lon_shift, color='k')

    pathlons, pathlats = path.compute_synthetic_paths(n=1000)
    for pathlon, pathlat in zip(pathlons, pathlats):
        ax.plot(pathlon, pathlat, transform=ccrs.PlateCarree(),
                color='b', alpha=0.05)

    colorcycle = itertools.cycle(colors)
    for p in poles:
        p.plot(ax, color=colorcycle.next())

    ax.scatter(slon, slat, transform=ccrs.PlateCarree(), marker="*", s=100)
    #plt.show()
    plt.savefig("keweenawan_paths" + str(n_euler_rotations)+".pdf")


def plot_age_samples():
    fig = plt.figure()
    ax = fig.add_subplot(111)

    colorcycle = itertools.cycle(colors)
    for p, age_samples in zip(poles, path.ages()):
        c = colorcycle.next()
        age = np.linspace(1080, 1115, 1000)
        if p.age_type == 'gaussian':
            dist = st.norm.pdf(age, loc=p.age, scale=p.sigma_age)
        else:
            dist = st.uniform.pdf(age, loc=p.sigma_age[
                                  0], scale=p.sigma_age[1] - p.sigma_age[0])
        plt.hist(age_samples, normed=True, alpha=0.3)
        ax.fill_between(age, 0, dist, color=c, alpha=0.7)
    #plt.show()
    plt.savefig("keweenawan_ages" + str(n_euler_rotations)+".pdf")


def plot_synthetic_poles():
    if proj_type == 'M':
        ax = plt.axes(projection=ccrs.Mollweide(proj_lon))
    elif proj_type == 'O':
        ax = plt.axes(projection = ccrs.Orthographic(proj_lon,proj_lat))

    ax.gridlines()
    ax.set_global()

    direction_samples = path.euler_directions()

    for directions in direction_samples:
        mcplates.plot.plot_distribution( ax, directions[:,0], directions[:,1])

    mcplates.plot.plot_continent(ax, 'laurentia', rotation_pole=mcplates.Pole(0., 90., 1.0), angle=-lon_shift, color='k')

    colorcycle = itertools.cycle(colors)
    lons, lats, ages = path.compute_synthetic_poles(n=1000)
    for i in range(len(poles)):
        c = colorcycle.next()
        poles[i].plot(ax, color=c)
        ax.scatter(lons[:, i], lats[:, i], color=c,
                   transform=ccrs.PlateCarree())

    #plt.show()
    plt.savefig("keweenawan_poles" + str(n_euler_rotations)+".pdf")


def plot_plate_speeds():
    euler_directions = path.euler_directions()
    euler_rates = path.euler_rates()
    duluth = mcplates.PlateCentroid(slon, slat)

    fig = plt.figure()
    i = 1
    for directions, rates in zip(euler_directions, euler_rates):
        speed_samples = np.empty_like(rates)
        for j in range(len(rates)):
            euler = mcplates.EulerPole(
                directions[j, 0], directions[j, 1], rates[j])
            speed_samples[j] = euler.speed_at_point(duluth)

        ax = fig.add_subplot(1, n_euler_rotations, i)
        ax.hist(speed_samples, bins=30, normed=True)
        #ax = fig.add_subplot(2, n_euler_rotations, n_euler_rotations + i)
        #ax.hist(rates, bins=30, normed=True)
        i += 1
    #plt.show()
    plt.savefig("keweenawan_speeds" + str(n_euler_rotations)+".pdf")


if __name__ == "__main__":
    import os
    if os.path.isfile(path.dbname):
        path.load_mcmc()
    else:
        path.sample_mcmc(1000000)
    plot_synthetic_paths()
    plot_age_samples()
    plot_synthetic_poles()
    plot_plate_speeds()
