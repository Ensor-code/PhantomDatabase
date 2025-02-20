#!/bin/bash

# Use splash in each model directories to create snapshots of models

# Directory to parse
directory="/Users/camille/Documents/runs/phantom/database/wind"
exec_dir="/Users/camille/Documents/PhantomDatabase/logistics"

#subfolder='/Users/camille/Documents/runs/phantom/database/wind/icompstar_2_subst_11_m1_1.6_aIn_5.0_eIn_0.0_m2_0.4_racc2_0.04_a_35.0_e_0.0_gamma_1.2_m3_0.6_racc3_0.04_eos_2_mu_1.26_icooling_1_icoolmeth_0_HIexcit_1_Tfloor_0.0_f_acc_0.8_vw_15.0_Rinj_1.2_mlr_1.1e-06_Tw_3000.0_iwr_4_wss_1.0_bound_1500.0'

for subfolder in "$directory"/*/; do
    if [ -d "$subfolder" ]; then
        echo "Running splash in $subfolder"
        cp $exec_dir/splash.defaults $subfolder
        cp $exec_dir/splash.limits $subfolder
        cp $exec_dir/splash.units $subfolder
        cd $subfolder

        # get max vals of data for plot bounds
        splash calc max wind_*

        # read file to determine limits
        IFS=$'\n' rows=($(cat maxvals.out))                                         
        # split line
        col=$(echo ${rows[5]} | tr "   " "\n")
        col=( $(IFS="   " echo "$col") )
        # get max x
        x=${col[1]}

        # make limits
        x1=$(echo "$x -1" | awk '{print $1 * $2}')
        x2=$(echo "$x 1" | awk '{print $1 * $2}')

        # backup and rename splash.limits
        mv splash.limits splash.limits.bak1
        # read limits in splash.limits
        IFS=$'\n' rows=($(cat splash.limits.bak1)) 
        # change lines
        rows[0]="  $x1   $x2"
        rows[1]="  $x1   $x2"
        rows[2]="  $x1   $x2"
        #rows[5]="  $dens1   $dens2"
        # write new limits
        for i in ${!rows[@]}; do
            echo ${rows[$i]} >> splash.limits
        done

        # make plots
        splash -x 1 -y 2 -r 6 -dev orbital.png wind_0* --sink=1 
        #splash -x 1 -y 3 -r 6 -dev meridional.png wind_0* --sink=1

        # make zoomed plots if x > 100
        if awk "BEGIN {exit !($x >= 100)}"; then
            # backup and rename splash.limits
            mv splash.limits splash.limits.bak2
            # read limits in splash.limits
            IFS=$'\n' rows=($(cat splash.limits.bak2)) 
            # change lines
                rows[0]="  -40   40"
                rows[1]="  -40   40"
                rows[2]="  -40   40"
            # write new limits
                for i in ${!rows[@]}; do
                    echo ${rows[$i]} >> splash.limits
                done
            splash -x 1 -y 2 -r 6 -dev orbital_zoom.png wind_0* --sink=1
        fi
    fi
done