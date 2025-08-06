''' Browses directories and creates snapshots of the latest dump in them. '''

import os
from subprocess import call, STDOUT, DEVNULL, TimeoutExpired

VERBOSE = False

# define directories
DIR = "/Users/camille/Documents/runs/phantom/database/wind/"
DIR_SETTINGS = "/Users/camille/Documents/PhantomDatabase/logistics"

PREFIX='wind'

km_to_cm = 1e5
Msun_to_g = 1.989e33
yr_to_s = 31557600

#check if directory exists
if not os.path.exists(DIR):
    print(f'Directory does not exist. {DIR}')

# browse directories
corrupt = []
weird = []
wrongscale = []
for root, dirs, files in os.walk(DIR):
    dumpFiles = list(
        filter(
            lambda x: (PREFIX + '_' in x and not '.tmp' in x and not '.txt'
                        in x and not '.png' in x and not '.dat' in x), files))
    if len(dumpFiles) > 0:
        print(f'Processing {root}')
        # Use latest dump file
        dumpFiles.sort()
        dumpFile = dumpFiles[-1]
        # get input files
        setupFiles = list(filter(lambda x: (PREFIX + '.setup' in x), files))
        inFiles = list(filter(lambda x: (PREFIX + '.in' in x), files))
        if len(setupFiles) > 1:
            print(f'Warning: more than one setup file in {root}, taking the first one found.')
        if len(inFiles) > 1:
            print(f'Warning: more than one input file in {root}, taking the first one found.')
        setupFile=setupFiles[0]
        inFile=inFiles[0]
    else:
        continue
    
    # Copy standard splash files (splash.defaults, splash.limits, splash.units) to directory
    for f in ('splash.defaults', 'splash.limits', 'splash.units'):
        call(f'cp {DIR_SETTINGS}/{f} {root}', shell=True)


    # read wind mass loss rate and initial velocity from .in file
    with open(os.path.join(root, inFile), 'r') as f:
        for line in f:
            if 'wind_mass_rate' in line:
                mdot = line.split('=')[1].strip().split()[0]
            if 'wind_velocity' in line:
                wvel = line.split('=')[1].strip().split()[0]
        # put variables in cgs units
        mdot = float(mdot) * Msun_to_g / yr_to_s
        wvel = float(wvel) * km_to_cm
        #print(mdot, wvel)
        # make scaling factor (in g/cm)
        scale = mdot / wvel

    # run splash calculations for min and max values
    coords, rho = [], []
    try:
        for f in ('min', 'max'):
            # remove if it exist
            if os.path.exists(os.path.join(root, f"{f}vals.out")):
                call(f'cd {root} && rm {f}vals.out', shell=True)
            # run splash calc with a timeout to catch corrupted dumpfiles (otherwise splash will wait for user input forever)
            # 5 seconds should be enough since we're making the splash calculations for one dumpfile only
            if VERBOSE:
                call(f'cd {root} && splash calc {f} {dumpFile}', shell=True, timeout=5)
            else:
                call(f'cd {root} && splash calc {f} {dumpFile}', shell=True, stdout=DEVNULL, stderr=STDOUT, timeout=5)
            # read max and min values
            with open(os.path.join(root, f"{f}vals.out"), 'r') as f:
                line = f.readlines()[-1].split()
                coords.append(abs(float(line[1])))
                coords.append(abs(float(line[2])))
                coords.append(abs(float(line[3])))
                rho.append(float(line[6]))
    except ValueError:
        print(f'Error: {f}vals.out file likely contains weird values, use another dumpfile for this model - {root}')
        weird.append(root)
        continue
    except TimeoutExpired:
        print(f'Error: Timeout in splash calc {f} {dumpFile} - {root}, the dumpfile is probably corrupted')
        corrupt.append(root)
        continue
    # rescale max density
    rho[1] /= scale
    # catch when the scaling is too intense
    bounds = [1e-16, 1e-14]
    if rho[1] < bounds[0]:
        print(f'Error: Density scaling factor too intense (max < 1e-16), setting more reasonable bounds (max = 1e-16)')
        rho[1] = bounds[0]
    elif rho[1] > bounds[1]:
        print(f'Error: Density scaling factor not intense enough (min > 1e-14), setting more reasonable bounds (max = 1e-14)')
        rho[1] = bounds[1]
    if rho[1]/rho[0] < 1e3 :
        print(f'Error: Density scaling factor too intense (max/min < 1e3), setting more reasonable bounds (max/min = 10^3)')
        rho[1] = 1e3 * rho[0]
        wrongscale.append(root)



    # max
    x_max = max(coords)
    
    # edit limits in splash.limits
    with open(os.path.join(root, 'splash.limits'), 'r') as f:
        lines = f.readlines()
    lines[0] = f'  {-x_max}   {x_max} \n'
    lines[1] = f'  {-x_max}   {x_max} \n'
    lines[2] = f'  {-x_max}   {x_max} \n'
    lines[5] = f'   {rho[0]}   {rho[1]} \n'
    with open(os.path.join(root, 'splash.limits'), 'w') as f:
        f.writelines(lines)

    # run splash
    if VERBOSE:
        call(f'cd {root} && splash -x 1 -y 2 -r 6 -dev orbital.png {dumpFile} --sink=1', shell=True)
        call(f'cd {root} && splash -x 1 -y 3 -r 6 -dev meridional.png {dumpFile} --sink=1', shell=True)
    else:
        call(f'cd {root} && splash -x 1 -y 2 -r 6 -dev orbital.png {dumpFile} --sink=1', shell=True,stdout=DEVNULL,stderr=STDOUT)
        call(f'cd {root} && splash -x 1 -y 3 -r 6 -dev meridional.png {dumpFile} --sink=1', shell=True,stdout=DEVNULL,stderr=STDOUT)

print('-----------------------------------')
print('Done')
print(f'Corrupted files: {corrupt}')
print(f'Weird files: {weird}')
print(f'Wrong scaling: {wrongscale}')