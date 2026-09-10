with working_directory(pasta):
        if os.path.exists("results.pickle"):
            with open("results.pickle", "rb") as f:
                opt_result, results, elapsed, Al, Au, alpha = pickle.load(f)
                return opt_result, results, elapsed, Al, Au, alpha
                
        start_time = time.perf_counter()

        results = {}
        #===============================================
        # INPUTS
        # Minimum thickness allowed
        alpha_min = bracket[0]
        alpha_max = bracket[1]

        # Euler solver parameters
        order = 2 # 1 for 1st; 2 for 2nd
        iter = 20000 # max number of iterations (Use 50000 for first order)
        dt = 0.001 # Global time step (only used if use_local_dt==0). Use 0.002 for first order and 0.001 for second order. Reduce if you are getting NaNs or unstable solutions
        CFL = 0.2 # Courant number used to compute local time steps (only used if use_local_dt==1). Reduce if you are getting NaNs or unstable solutions
        use_local_dt = 1 # Time stepping-strategy. 0 for global dt; 1 for local dt based on CFL.
        res_NK = 1e-5 # Tolerance to switch from Runge-Kutta to Newton-Krylov solver. This value should be greater than res_tol.
        res_tol = 1e-8 # Tolerance on residual MSE to stop iterations. I do not recommend using values greater than 1e-6 (e.g. 1e-5), otherwise the numerical noise will break finite-difference estimations

        # Airfoil discretization
        Nchord = 31
        cref = 1.0 # reference chord

        # Number of airfoil CST parameters (design variables of the problem)
        Nvar = len(Al_0) # This value is used for the upper and lower skin separately (the total number of DVs is 2*Nvar)

        # Bounds for design variables
        Al_lower = [Al_lower]*Nvar
        Al_upper = [Al_upper]*Nvar
        Au_lower = [Au_lower]*Nvar
        Au_upper = [Au_upper]*Nvar

        # Select if we should use reinitialization for the first CFD analysis.
        # reinitialize = [0] does not use reinitialization for the first CFD analysis.
        # reinitialize = [1] uses reinitialization for the first CFD analysis.
        # We set it as a list so it remains accessible within the the check_point function.
        reinitialize = [0]

        #===============================================
        # EXECUTION

        # Initial airfoil design variables
        # The structure of the DV array is:
        # xx = [lower skin CST coefficients (Al); upper skin CST coefficients (Au); alpha]
        xx0 = np.hstack([Al_0, Au_0, alpha_0])

        # Initialize optimization history
        xxhist = []
        CDhist = []
        CLhist = []
        maxthist = []
        minthist = []
        gradshist = []


        # Define function to check if the desired point was already executed
        def check_point(xx, tol=1e-11, force_run=False):
            nonlocal results
            # Loop over the history to find previous design point within tolerance
            ii_closest = -1
            for ii,xx_curr in enumerate(xxhist):
                delta = np.sqrt(np.sum((xx_curr - xx)**2))
                if delta < tol:
                    print('Found previous solution')
                    print('ii:',ii)
                    print('delta:',delta)
                    ii_closest = ii
                    break

            # Get design variables
            Al = xx[:Nvar]
            Au = xx[Nvar:2*Nvar]
            alpha = xx[-1]

            print('Evaluating the following point')
            print('Al:',Al)
            print('Au:',Au)
            print('alpha [deg]:',alpha*180/np.pi)

            # Choose whether to run new case or use history
            if (ii_closest == -1) or force_run: # i_closest keeps the default value if no match is found
                # Call Euler solver with adjoint for each function
                results = eb.run_cst(Al, Au, Nchord, alpha, Mach,
                                    gamma=1.4, order=order,
                                    iter=iter, dt=dt, CFL=CFL, use_local_dt=use_local_dt, res_NK=res_NK,
                                    res_tol=res_tol, reinitialize=reinitialize[0], plot=False,
                                    adj_funcs=['cl_jlow','cd_jlow'])
                cl = results['CL']
                cd = results['CD']
                maxt = results['maxt']
                mint = results['mint']
                grads1 = results['grads']

                # Gather gradients w.r.t. xx
                grads = {}
                grads['CL'] = np.hstack([grads1['cl_jlow']['dAl'],
                                        grads1['cl_jlow']['dAu'],
                                        [grads1['cl_jlow']['alpha']]])
                grads['CD'] = np.hstack([grads1['cd_jlow']['dAl'],
                                        grads1['cd_jlow']['dAu'],
                                        [grads1['cd_jlow']['alpha']]])
                grads['maxt'] = np.hstack([grads1['maxt']['dAl'],
                                        grads1['maxt']['dAu'],
                                        [0.0]])
                grads['mint'] = np.hstack([grads1['mint']['dAl'],
                                        grads1['mint']['dAu'],
                                        [0.0]])

                xxhist.append(xx.copy())
                CDhist.append(cd)
                CLhist.append(cl)
                maxthist.append(maxt)
                minthist.append(mint)
                gradshist.append(grads)
                with open('opt_results.pickle','wb') as f:
                    pickle.dump({'xxhist':xxhist,
                                'CDhist':CDhist,
                                'CLhist':CLhist,
                                'maxthist':maxthist,
                                'minthist':minthist,
                                'mach':Mach,
                                'gradshist':gradshist,
                                'Al':Al,
                                'Au':Au}, f)

            else:
                # Gather values from previous solution
                cl = CLhist[ii_closest]
                cd = CDhist[ii_closest]
                maxt = maxthist[ii_closest]
                mint = minthist[ii_closest]
                grads = gradshist[ii_closest]

            # Print and store history
            print('evaluation:',len(CDhist))
            print('CL:',cl)
            print('CD:',cd)
            print('maxt:',maxt)
            print('mint:',mint)
            print('Al:',Al)
            print('Au:',Au)
            print('alpha [deg]:',alpha*180/np.pi)
            print('grads:',grads)
            print('')

            # Check if we need to avoid solution reinitialization if NaNs show up
            if np.isnan(cl) or np.isnan(cd):
                reinitialize[0] = 0
            else:
                reinitialize[0] = 1
            print('')

            # Return design functions
            return cl, cd, maxt, mint, grads


        # Define objective function
        def objfun(xx):
            cl, cd, maxt, mint, grads = check_point(xx)
            return cd

        def objfungrad(xx):
            cl, cd, maxt, mint, grads = check_point(xx)
            return grads['CD']

        # Define constraints
        def ineqconfun(xx):
            cl, cd, maxt, mint, grads = check_point(xx)
            g1 = (maxt - tref)
            return g1

        def ineqconfungrad(xx):
            cl, cd, maxt, mint, grads = check_point(xx)
            return grads['maxt']

        # Define constraints
        def eqconfun(xx):
            cl, cd, maxt, mint, grads = check_point(xx)
            h1 = (cl - CLref)
            return h1

        def eqconfungrad(xx):
            cl, cd, maxt, mint, grads = check_point(xx)
            return grads['CL']

        # Run initial case
        objfun(xx0)
        reinitialize[0] = 1

        # Create list of constraints
        con1 = {'type': 'ineq',
                'fun': ineqconfun,
                'jac': ineqconfungrad}
        con2 = {'type': 'eq',
                'fun': eqconfun,
                'jac': eqconfungrad}
        cons = [con1, con2]

        # Set DV bounds
        #lb = [-Amax]*Nvar + [Amin]*Nvar + [alpha_min]
        #ub = [-Amin]*Nvar + [Amax]*Nvar + [alpha_max]
        lb = Al_lower + Au_lower + [alpha_min]
        ub = Al_upper + Au_upper + [alpha_max]
        bounds = Bounds(lb, ub, keep_feasible=True)

        # Set optimizer options.
        # Adjusted eps (finite difference size) according to expected DV bounds.
        options={'maxiter': 100, 'ftol': 1e-05, 'iprint': 1, 'disp': True}#, 'finite_diff_rel_step': None}

        # Run optimizer
        opt_result = minimize(
            objfun,
            x0=xx0,
            jac=objfungrad,
            constraints=cons,
            bounds=bounds,
            method='slsqp',
            options=options
        )
        success = opt_result.success
        if not success:
            print("Otimização falhou:")
            pprint(opt_result)
            raise Exception

        # Print results
        print('')
        print('=========================================')
        print('OPTIMIZATION RESULTS')
        print(opt_result)
        print('=========================================')
        print('')
        xopt = opt_result.x

        # Run optimum point to make sure it is the last item
        # of the history file
        cl, cd, maxt, mint, grads = check_point(xopt, force_run=True)
        print('')
        print('=========================================')
        print('OPTIMUM POINT')
        print('cl:',cl)
        print('cd:',cd)
        print('maxt:',maxt)
        print('xopt:',xopt)
        print('=========================================')
        print('')

        Al = xopt[:Nvar]
        Au = xopt[Nvar:2*Nvar]
        alpha = xopt[-1]
        elapsed = time.perf_counter() - start_time
        with open('results.pickle','wb') as f:
            pickle.dump((opt_result, results, elapsed, Al, Au, alpha), f)
        return opt_result, results, elapsed, Al, Au, alpha