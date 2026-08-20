# Sample script on how to use the weight function from designTool.
# Remember to save this script in the same directory as designTool.py

# IMPORTS
from designTool.standard_airplane import standard_airplane
from designTool.geometry import geometry
from designTool.weight import weight
import numpy as np
import pprint

# Load a sample case already defined in designTools.py:
airplane = standard_airplane('fokker100')

# Execute the geometry function
geometry(airplane)

# Guess values for initial iteration
W0_guess = 467500.00000000000000
T0_guess = 140250.00000000000000

# Execute the weight estimation
W0, W_empty, W_fuel, W_cruise = weight(W0_guess, T0_guess, airplane)

# Print results
print("W0 = ",W0)
print("W_empty = ",W_empty)
print("W_fuel = ",W_fuel)
print("W_cruise = ",W_cruise)
print()
print("Wempty_dict = " + pprint.pformat(airplane['empty_weight']))
print()
print("Wfuel_dict = " + pprint.pformat(airplane['fuel_weight']))
