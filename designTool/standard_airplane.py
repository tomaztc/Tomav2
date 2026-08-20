import numpy as np
from scipy.optimize import fixed_point
from .constants import ft2m, gravity, nm2m

# estudo_cg_2.xls
XCG_PAYLOAD = 29.52931569

# PreSTo-Cabin_1.0.xls
D_F = 5.87 # Fuselage outer equivalent diameter
L_F = 58.00 # Fuselage length
L_T = 12.32 # Tail length

# Variáveis
D_N = 3.5 # ROLLS-ROYCE TRENT XWB-84: Diâmetro do Fan = 3m
DX_TANK_FLAP = 0.03
ALTURA_RODAS = 2.65 # MÁXIMO POSSÍVEL 
DISTANCIA_EH_TAIL = 3 # MÍNIMO POSSÍVEL
DISTANCIA_EV_TAIL = 3.5 # MÍNIMO POSSÍVEL

def standard_airplane(name, delta_xr_w=-5.1, x_tank_c_w=0.14):
    if name == "Tomav":
        inputs = {
            'delta_xr_w': delta_xr_w, # VARIÁVEL - Longitudinal shift of the wing with respect to the standard configuration [m]
            'type': 'transport', # REQUISITO - Can be 'transport', 'fighter', or 'general'
            'S_w': 330, # VARIÁVEL - Wing area [m2]
            'AR_w': 10.5,  # MÁXIMO POSSÍVEL - Wing aspect ratio
            'taper_w': 0.17, # MÍNIMO POSSÍVEL - Wing taper ratio
            'sweep_w': 35.05 * np.pi/180, # VARIÁVEL - Wing sweep [rad]
            'dihedral_w': 5 * np.pi/180, # Wing dihedral [rad]
            'xr_w': 22 + delta_xr_w, # Longitudinal position of the wing (with respect to the fuselage nose) [m]
            'zr_w': -1.85, # Vertical position of the wing (with respect to the fuselage nose) [m]
            'tcr_w': 0.175, # MÁXIMO POSSÍVEL - t/c of the root section of the wing
            'tct_w': 0.08, # MÍNIMO POSSÍVEL - t/c of the tip section of the wing
            'Cht': 0.85, # MÍNIMO POSSÍVEL - Horizontal tail volume coefficient
            'Lc_h': None, # CALCULADO - Non-dimensional lever of the horizontal tail (lever/wing_mac)
            'AR_h': 4, # MÍNIMO POSSÍVEL - HT aspect ratio
            'taper_h': 0.35, # MÍNIMO POSSÍVEL - HT taper ratio
            'sweep_h': 40 * np.pi/180, # MÁXIMO POSSÍVEL - HT sweep [rad]
            'dihedral_h': 6 * np.pi/180, # HT dihedral [rad]
            'zr_h': D_F/2 - 1, # Vertical position of the HT [m]
            'tcr_h': 0.09, # MÍNIMO POSSÍVEL - t/c of the root section of the HT
            'tct_h': 0.08, # MÍNIMO POSSÍVEL - t/c of the tip section of the HT
            'eta_h': 0.9, # Dynamic pressure factor of the HT
            'Cvt': 0.075, # MÍNIMO POSSÍVEL - Vertical tail volume coefficient
            'Lb_v': None, # CALCULADO - Non-dimensional lever of the vertical tail (lever/wing_span)
            'AR_v': 1.5, # MÍNIMO POSSÍVEL - VT aspect ratio
            'taper_v': 0.35, # MÍNIMO POSSÍVEL - VT taper ratio
            'sweep_v': 42 * np.pi/180, # MÁXIMO POSSÍVEL - VT sweep [rad]
            'zr_v': D_F/2, # Vertical position of the VT [m]
            'tcr_v': 0.095, # MÍNIMO POSSÍVEL - t/c of the root section of the VT
            'tct_v': 0.08, # MÍNIMO POSSÍVEL - t/c of the tip section of the VT
            'L_f': L_F, # Fuselage length [m]
            'D_f': D_F, # Fuselage diameter [m]
            'x_n': 24.3 + delta_xr_w, # Longitudinal position of the nacelle frontal face [m]
            'y_n': 10.5, # Lateral position of the nacelle centerline [m]
            'z_n': -3.075, # Vertical position of the nacelle centerline [m]
            'L_n': 5.8, # ROLLS-ROYCE TRENT XWB-84 - Nacelle length [m]
            'D_n': D_N, # ROLLS-ROYCE TRENT XWB-84 - Nacelle diameter [m]
            'n_engines': 2, # ROLLS-ROYCE TRENT XWB-84 - Number of engines
            'n_engines_under_wing': 2, # ROLLS-ROYCE TRENT XWB-84 - Number of engines installed under the wing
            'x_nlg': 6, # Longitudinal position of the nose landing gear [m]
            'x_mlg': None, # CALCULADO - Longitudinal position of the main landing gear [m]
            'y_mlg': 5.5, # MÁXIMO POSSÍVEL - Lateral position of the main landing gear [m]
            'z_lg': -D_F/2 - ALTURA_RODAS, # Vertical position of the landing gear [m]
            'x_tailstrike': L_F - L_T - 3, # Longitudinal position of critical tailstrike point [m]
            'z_tailstrike': -D_F/2, # Vertical position of critical tailstrike point [m]
            'x_tank_c_w': x_tank_c_w, # VARIÁVEL - Fraction of the wing chord where fuel tank starts
            'c_tank_c_w' : None, # CALCULADO - Fraction of the wing chord occupied by the fuel tank
            'b_tank_b_w_start': 0.0, # MÍNIMO POSSÍVEL - Fraction of the wing semi-span where fuel tank starts
            'b_tank_b_w_end': 0.95, # MÁXIMO POSSÍVEL - Fraction of the wing semi-span where fuel tank ends
            'clmax_w': 1.8, # MÁXIMO POSSÍVEL - Maximum lift coefficient of wing airfoil
            'k_korn': 0.95, # MÁXIMO POSSÍVEL - Airfoil technology factor for Korn equation (wave drag)
            'flap_type': 'double slotted',  # Flap type
            'slat_type': 'slat', # Slat type
            'c_flap_c_wing': 0.33, # VARIÁVEL - Fraction of the wing chord occupied by flaps
            'b_flap_b_wing': 0.65, # VARIÁVEL - Fraction of the wing span occupied by flaps (including fuselage portion)
            'c_slat_c_wing': 0.08, # 0.09, # Fraction of the wing chord occupied by slats
            'b_slat_b_wing': 0.7, # 0.75, # Fraction of the wing span occupied by slats
            'c_ail_c_wing': 0.30, # aileron.png - Fraction of the wing chord occupied by aileron
            'b_ail_b_wing': 0.32, # aileron.png - Fraction of the wing span occupied by aileron
            'h_ground': 35 * ft2m, # Distance to the ground for ground effect computation [m]
            'k_exc_drag': 0.03, # MÍNIMO POSSÍVEL - Excrescence drag factor
            'winglet': True, # Add winglet
            'altitude_takeoff': 0, # REQUISITO - Altitude for takeoff computation [m] - From Obert's paper
            'distance_takeoff': 2900, # REQUISITO - Required takeoff distance [m] - From Obert's paper
            'deltaISA_takeoff': 0, # REQUISITO - Variation from ISA standard temperature [ºC] - From Obert's paper
            'altitude_landing': 0, # REQUISITO - Altitude for landing computation [m]
            'distance_landing': 2900, # Required landing distance [m]
            'deltaISA_landing': 0, # REQUISITO - Variation from ISA standard temperature [ºC]
            'MLW_frac': 207000 / 280000, # A350 - Max Landing Weight / Max Takeoff Weight - From Obert's paper
            'altitude_cruise': 32400*ft2m, # VARIÁVEL - Cruise altitude [m]
            'Mach_cruise': 0.85, # REQUISITO - Cruise Mach number
            'range_cruise': 8000 * nm2m, # REQUISITO - Cruise range [m]
            'altitude_maxcruise': 31000*ft2m, # VARIÁVEL - Altitude for high-speed cruise [m]
            'Mach_maxcruise': 0.90, # REQUISITO - Mach for high-speed cruise [m]
            'time_loiter': 45 * 60, # REQUISITO - Loiter time [s] - DOI: 45/55-3572
            'altitude_loiter': 1500 * ft2m, # VARIÁVEL - Loiter altitude [m] - DOI: 45/55-3572
            'altitude_altcruise': None, # CALCULADO - Alternative cruise altitude [m] - based on: DOI: 10.2514/6.2025-3572
            'Mach_altcruise': 0.72, # VARIÁVEL - Alternative cruise Mach number
            'range_altcruise': 200 * nm2m, # REQUISITO - Alternative cruise range [m]
            'W_payload': 320 * 100 * gravity, # REQUISITO - Payload weight [N]
            'xcg_payload': XCG_PAYLOAD, # Longitudinal position of the Payload center of gravity [m]
            'W_crew': (2 + 2 + 9) * 81 * gravity, # REQUISITO - Crew weight [N]
            'xcg_crew': 22, # Longitudinal position of the Crew center of gravity [m]
            'block_range': 8000 * nm2m, # REQUISITO - Block range [m]
            'block_time': (16 + 0.5) * 3600, # Block time [s]
            'n_captains': 2, # REQUISITO - Number of captains in flight
            'n_copilots': 2, # REQUISITO - Number of copilots in flight
            'rho_fuel': 785, # ROLLS-ROYCE TRENT XWB-84 - Fuel density kg/m3 (This is Jet A-1)
            'W0_guess': 254082.14 * gravity, # Guess for MTOW
            'engine': { # ROLLS-ROYCE TRENT XWB-84
                'model': 'Howe turbofan', # Check engineTSFC function for options
                'BPR': 9.6, # Bypass ratio
                'weight': 7277 * gravity, # Single engine dry weight [N]
                'C_ref': 0.478 / 3600, # Reference thrust-specific fuel consumption [1/s]
                'altitude_ref': 35000 * ft2m, # Standard reference cruise altitude [m]
                'Mach_ref': 0.85, # Typical cruise Mach number for the A350-1000
                'Tmax': 374500 # N
            }
        }
        inputs["altitude_altcruise"] = inputs["altitude_cruise"]
        inputs["c_tank_c_w"] = 1 - inputs["c_flap_c_wing"] - DX_TANK_FLAP - x_tank_c_w
        inputs["x_mlg"] = calcular_x_mlg(inputs)
        inputs["Lc_h"], inputs["Lb_v"] = calcular_Lc_Lb(inputs)
        
    elif name == "fokker100":
        # This model was taken from measuring the 3D view from
        # https://www.icas.org/ICAS_ARCHIVE/ICAS1988/ICAS-88-1.6.2.pdf
        # Obert, E. The Aerodynamic Development of the Fokker 100
        inputs = {
            'type': 'transport', # Can be 'transport', 'fighter', or 'general'
            'S_w' : 93.5, # Wing area [m2] - From Obert's paper
            'AR_w' : 8.32,  # Wing aspect ratio
            'taper_w' : 0.25, # Wing taper ratio
            'sweep_w' : 15.76*np.pi/180, # Wing sweep [rad]
            'dihedral_w' : 3*np.pi/180, # Wing dihedral [rad]
            'xr_w' : 13.38, # Longitudinal position of the wing (with respect to the fuselage nose) [m]
            'zr_w' : -0.99, # Vertical position of the wing (with respect to the fuselage nose) [m]
            'tcr_w' : 0.123, # t/c of the root section of the wing
            'tct_w' : 0.096, # t/c of the tip section of the wing
            'Cht' : 0.976, # Horizontal tail volume coefficient
            'Lc_h' : 4.23, # Non-dimensional lever of the horizontal tail (lever/wing_mac)
            'AR_h' : 4.52, # HT aspect ratio
            'taper_h' : 0.44, # HT taper ratio
            'sweep_h' : 26*np.pi/180, # HT sweep [rad]
            'dihedral_h' : 2*np.pi/180, # HT dihedral [rad]
            'zr_h' : 4.76, # Vertical position of the HT [m]
            'tcr_h' : 0.1, # t/c of the root section of the HT
            'tct_h' : 0.1, # t/c of the tip section of the HT
            'eta_h' : 1.0, # Dynamic pressure factor of the HT (0.9 for conventional tail or 1.0 for T-tail)
            'Cvt' : 0.068, # Vertical tail volume coefficient
            'Lb_v' : 0.469, # Non-dimensional lever of the vertical tail (lever/wing_span)
            'AR_v' : 1.03, # VT aspect ratio
            'taper_v' : 0.73, # VT taper ratio
            'sweep_v' : 39*np.pi/180, # VT sweep [rad]
            'zr_v' : 1.39, # Vertical position of the VT [m]
            'tcr_v' : 0.1, # t/c of the root section of the VT
            'tct_v' : 0.1, # t/c of the tip section of the VT
            'L_f' : 31.6, # Fuselage length [m]
            'D_f' : 3.28, # Fuselage diameter [m]
            'x_n' : 21.4, # Longitudinal position of the nacelle frontal face [m]
            'y_n' : 3.01, # Lateral position of the nacelle centerline [m]
            'z_n' : 0.45, # Vertical position of the nacelle centerline [m]
            'L_n' : 4.91, # Nacelle length [m]
            'D_n' : 1.69, # Nacelle diameter [m]
            'n_engines' : 2, # Number of engines
            'n_engines_under_wing' : 0, # Number of engines installed under the wing
            'engine' : {
                'model' : 'Howe turbofan', # Check engineTSFC function for options
                #'model' : 'Raymer turbofan', # Check engineTSFC function for options
                'BPR' : 3.04, # Engine bypass ratio
                #'weight' : 1500*gravity, # Single engine weight [N] (Can also be omitted to let designTool estimate it)
                'C_ref' : 0.70/3600, # Reference thrust-specific fuel consumption [1/s] (Can also be omitted to let designTool estimate it)
                'altitude_ref': 35000*ft2m, # Altitude that corresponds to the given TSFC [m]
                'Mach_ref': 0.73, # Mach that corresponds to the given TSFC
            },
            'x_nlg' : 3.7, # Longitudinal position of the nose landing gear [m]
            'x_mlg' : 17.4, # Longitudinal position of the main landing gear [m]
            'y_mlg' : 2.47, # Lateral position of the main landing gear [m]
            'z_lg' : -2.53, # Vertical position of the landing gear [m]
            'x_tailstrike' : 23.4, # Longitudinal position of critical tailstrike point [m]
            'z_tailstrike' : -1.54, # Vertical position of critical tailstrike point [m]
            'c_tank_c_w' : 0.4, # Fraction of the wing chord occupied by the fuel tank
            'x_tank_c_w' : 0.2, # Fraction of the wing chord where fuel tank starts
            'b_tank_b_w_start' : 0.0, # Fraction of the wing semi-span where fuel tank starts
            'b_tank_b_w_end' : 0.95, # Fraction of the wing semi-span where fuel tank ends
            'clmax_w' : 1.8, # Maximum lift coefficient of wing airfoil
            'k_korn' : 0.91, # Airfoil technology factor for Korn equation (wave drag)
            'flap_type' : 'double slotted',  # Flap type
            'c_flap_c_wing' : 0.30, # Fraction of the wing chord occupied by flaps
            'b_flap_b_wing' : 0.60, # Fraction of the wing span occupied by flaps (including fuselage portion)
            'slat_type' : None, # Slat type
            'c_slat_c_wing' : 0.0, # Fraction of the wing chord occupied by slats
            'b_slat_b_wing' : 0.0, # Fraction of the wing span occupied by slats
            'c_ail_c_wing' : 0.27, # Fraction of the wing chord occupied by aileron
            'b_ail_b_wing' : 0.34, # Fraction of the wing span occupied by aileron
            'h_ground' : 35.0*ft2m, # Distance to the ground for ground effect computation [m]
            'k_exc_drag' : 0.03, # Excrescence drag factor
            'winglet' : False, # Add winglet
            'altitude_takeoff' : 0.0, # Altitude for takeoff computation [m] - From Obert's paper
            'distance_takeoff' : 2050.0, # Required takeoff distance [m] - From Obert's paper
            'deltaISA_takeoff' : 15.0, # Variation from ISA standard temperature [ºC] - From Obert's paper
            'altitude_landing' : 0.0, # Altitude for landing computation [m]
            'distance_landing' : 1340.0, # Required landing distance [m]
            'deltaISA_landing' : 0.0, # Variation from ISA standard temperature [ºC]
            'MLW_frac' : 40100/43090, # Max Landing Weight / Max Takeoff Weight - From Obert's paper
            'altitude_cruise' : 35000*ft2m, # Cruise altitude for design mission [m] - From Obert's paper
            'Mach_cruise' : 0.73, # Cruise Mach number for design mission - From Obert's paper
            'range_cruise' : 1310*nm2m, # Cruise range for design mission [m] - From Obert's paper
            'altitude_maxcruise' : 35000*ft2m, # Altitude for high-speed cruise [m]
            'Mach_maxcruise' : 0.77, # Mach for high-speed cruise [m]
            'time_loiter' : 45*60, # Loiter time [s]
            'altitude_loiter' : 1500*ft2m, # Loiter time [s] - DOI: 10.2514/6.2025-3572
            'altitude_altcruise' : 15000*ft2m, # Alternative cruise altitude [m] - based on: DOI: 10.2514/6.2025-3572
            'Mach_altcruise' : 0.4, # Alternative cruise Mach number (limitation of 250 kts)
            'range_altcruise' : 200*nm2m, # Alternative cruise range [m]
            'W_payload' : 107*91*gravity, # Payload weight for design mission [N]
            'xcg_payload' : 14.4, # Longitudinal position of the Payload center of gravity [m]
            'W_maxpayload' : 11242*gravity, # Maximum payload weight [N]
            'W_crew' : 5*91*gravity, # Crew weight [N]
            'xcg_crew' : 2.5, # Longitudinal position of the Crew center of gravity [m]
            'block_range' : 400*nm2m, # Block range [m]
            'block_time' : (1.0 + 2*40/60)*3600, # Block time [s]
            'n_captains' : 1, # Number of captains in flight
            'n_copilots' : 1, # Number of copilots in flight
            'rho_fuel' : 804, # Fuel density kg/m3 (This is Jet A-1)
            'W0_guess' : 40000*gravity # Guess for MTOW
        }
    else:
        raise ValueError
    
    airplane = {'inputs': inputs}
    return airplane

def calcular_x_mlg(inputs):
    w_lg = 0.05 * inputs['D_f']
    d_lg = 4 * w_lg
    b_w  = np.sqrt(inputs['S_w'] * inputs['AR_w'])
    cr_w = 2 * inputs['S_w'] / (1 + inputs['taper_w']) / b_w
    te_slope = np.tan(inputs['sweep_w']) - 3*cr_w*(1 - inputs['taper_w']) / (2*b_w)
    x_te_rear_tip = inputs['xr_w'] + cr_w + (inputs['y_mlg'] - w_lg/2) * te_slope
    return x_te_rear_tip - d_lg / 2

def calcular_Lc_Lb(inputs):
    b_w   = np.sqrt(inputs['S_w'] * inputs['AR_w'])
    cr_w  = 2*inputs['S_w'] / (1 + inputs['taper_w']) / b_w
    cm_w  = 2*cr_w/3 * (1 + inputs['taper_w'] + inputs['taper_w']**2) / (1 + inputs['taper_w'])
    ym_w  = b_w/6 * (1 + 2*inputs['taper_w']) / (1 + inputs['taper_w'])
    xmqc_w = inputs['xr_w'] + cr_w/4 + ym_w*np.tan(inputs['sweep_w'])
    
    #   xr_h + cr_h = xmqc_w + L_h + 3*cr_h/4 - ym_h*tan(sweep_h) = L_f
    #   => L_h = L_f - xmqc_w - 3*cr_h/4 + ym_h*tan(sweep_h)
    def Lc_h_iter(Lc_h):
        L_h  = Lc_h * cm_w
        S_h  = inputs['Cht'] * inputs['S_w'] * cm_w / L_h
        b_h  = np.sqrt(inputs['AR_h'] * S_h)
        cr_h = 2*S_h / (1 + inputs['taper_h']) / b_h
        ym_h = b_h/6 * (1 + 2*inputs['taper_h']) / (1 + inputs['taper_h'])
        return ((inputs['L_f']-DISTANCIA_EH_TAIL) - xmqc_w - 3*cr_h/4 + ym_h*np.tan(inputs['sweep_h'])) / cm_w

    Lc_h = float(fixed_point(Lc_h_iter, 4.07, xtol=1e-6))

    #   xr_v + cr_v = xmqc_w + L_v + 3*cr_v/4 - (zm_v-zr_v)*tan(sweep_v) = L_f
    #   => L_v = L_f - xmqc_w - 3*cr_v/4 + (zm_v-zr_v)*tan(sweep_v)
    def Lb_v_iter(Lb_v):
        L_v     = Lb_v * b_w
        S_v     = inputs['Cvt'] * inputs['S_w'] * b_w / L_v
        b_v     = np.sqrt(inputs['AR_v'] * S_v)
        cr_v    = 2*S_v / (1 + inputs['taper_v']) / b_v
        zm_v_dz = b_v/3 * (1 + 2*inputs['taper_v']) / (1 + inputs['taper_v'])
        return ((inputs['L_f']-DISTANCIA_EV_TAIL) - xmqc_w - 3*cr_v/4 + zm_v_dz*np.tan(inputs['sweep_v'])) / b_w

    Lb_v = float(fixed_point(Lb_v_iter, 0.39, xtol=1e-6))

    return Lc_h, Lb_v