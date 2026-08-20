# Sample script on how to use the balance function from designTool.
# Remember to save this script in the same directory as designTool.py

# IMPORTS
from designTool.standard_airplane import standard_airplane
from designTool.geometry import geometry
from designTool.performance import thrust_matching
from designTool.balance import tank_properties
import numpy as np
import pprint

# Load a sample case already defined in designTools.py:
airplane = standard_airplane('fokker100')

# Execute the geometry function
geometry(airplane)

# Guess values for initial iteration
W0_guess = 467500.00000000000000
T0_guess = 140250.00000000000000

# Execute the weight and thrust estimation
thrust_matching(W0_guess, T0_guess, airplane)

V_maxfuel, W_maxfuel, xcg_fuel, ycg_fuel = tank_properties(cr_w = airplane['geometry']['cr_w'],
                                                           ct_w = airplane['geometry']['ct_w'],
                                                           tcr_w = airplane['inputs']['tcr_w'],
                                                           tct_w = airplane['inputs']['tct_w'],
                                                           b_w = airplane['geometry']['b_w'],
                                                           sweep_w = airplane['inputs']['sweep_w'],
                                                           xr_w = airplane['inputs']['xr_w'],
                                                           x_tank_c_w = airplane['inputs']['x_tank_c_w'],
                                                           c_tank_c_w = airplane['inputs']['c_tank_c_w'],
                                                           b_tank_b_w_start = airplane['inputs']['b_tank_b_w_start'],
                                                           b_tank_b_w_end = airplane['inputs']['b_tank_b_w_end'],
                                                           rho_fuel = airplane['inputs']['rho_fuel'],
                                                           gravity = 9.81)

# Print results
print('xcg_fuel:',xcg_fuel)
