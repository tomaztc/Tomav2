'''
This script executes the Fokker 100 example
'''

#IMPORTS
import numpy as np
from designTool.standard_airplane import standard_airplane
from designTool.geometry import geometry
from designTool.plots import plot_geometry
from designTool.aerodynamics import aerodynamics
import pprint

#=========================================

# SETUP

# Constants
ft2m = 0.3048
kt2ms = 0.514444
lb2N = 4.44822
gravity = 9.81

# Select airplane name from the standard_airplane function in designTool
airplane_name = 'fokker100'
#airplane_name = 'my_airplane'

#=========================================

# EXECUTION

# Load the airplane dictionary
airplane = standard_airplane(airplane_name)

# Execute the geometry module to compute all dimensions.
# This updates the airplane dictionary with new entries.
geometry(airplane)

# Plot airplane
plot_geometry(airplane, figname='3dview.png', az1=45, az2=-135)

print(pprint.pformat(airplane))

# Cruise conditions for aerodynamic analysis
Mach = 0.73000000000000
altitude = 10668.00000000000000
CL = 0.50000000000000
n_engines_failed = 0.00000000000000
highlift_config = 'clean'
lg_down = 0.00000000000000
h_ground = 0.00000000000000

# Execute the aerodynamic analysis
CD, CLmax, dragDict = aerodynamics(airplane, Mach, altitude, CL,
                                   n_engines_failed=n_engines_failed, highlift_config=highlift_config,
                                   lg_down=lg_down, h_ground=h_ground)

# Print results
print()
print("Aerodynamic data")
print("CD = ",CD)
print("CLmax = ",CLmax)
print("dragDict = " + pprint.pformat(dragDict))
print("")