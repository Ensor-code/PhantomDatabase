""" Functions to read files and return dictionaries for elastic search"""

from typing import Dict, Any
import numpy as np

def read_csv(file_path: str) -> list:
    """Read csv file
    Args:
        file_path: path to csv file
    Returns:
        List of lists containing the elements of each line of the csv file
    """
    data = []
    with open(file_path, "r") as csvfile:
        for line in csvfile:
            if line.startswith("#"):
                # get header
                header = line[1:].strip().split(",")
                continue
            if line.startswith("0"):
                # skip separation lines
                continue
            data.append(line.strip().split(","))
    return data, header


def create_mapping(data: list, header: list) -> Dict[str, Any]:
    """Create dictionary for db mappings
    Args:
        data: list of lists of len(4) containing each mapping's label and the
        corresponding metadata.
        First element of each list is the label, second is the type of variable stored,
        third and fourth are the units and file storing the information (both can be 0)
    Returns:
        Dictionary containing the mapping labels and metadata
    """
    data_dict = {}
    for item in data:
        # add field label
        data_dict[item[0]] = {"type": item[1]}
        # if the field comes with metadata, add it
        meta = {}
        for i in range(2, len(item)):
            if item[i] != "0":
                meta[header[i]] = item[i]
        if meta:
            data_dict[item[0]]["meta"] = meta
    return data_dict


def LoadSetupData(directory: str, prefix: str, index_definition) -> Dict[str, Any]:
    """Load the prefix.in and prefix.setup files to get the required information about the phantom model

    Args:
        directory (str): directory of the simulation
        prefix (str): prefix used for the files
        index_definition (dict): dictionary containing the mappings for the elastic search index

    Returns:
        dict: a dictionary containing the info from the setup and .in files
        (!! check units, they are not all in SI or cgs)
    """
    import os
    import sys

    setup = {}
    # load the prefix.setup file
    try:
        with open(os.path.join(directory, "%s.setup" % prefix), "r") as data:
            for line in data:
                if len(line) <= 1 or line.startswith("#"):
                    # remove empty lines and headers
                    continue
                # Get labels and values
                label, _, value, *_ = line.strip().split()
                # Change labels to make them easier to read for the human eye
                if label == "primary_mass":
                    label = "primary mass"
                elif label == "primary_racc":
                    label = "primary Racc"
                elif label == "primary_Reff":
                    label = "primary Reff"
                elif label == "primary_Teff":
                    label = "primary Teff"
                elif label == "secondary_mass":
                    label = "secondary mass"
                elif label == "secondary_racc":
                    label = "secondary Racc"
                elif label == "secondary_Reff":
                    label = "secondary Reff"
                elif label == "secondary_Teff":
                    label = "secondary Teff"
                elif label == "semi_major_axis":
                    label = "semi-major axis"
                elif label == "wind_gamma" or label == "temp_exponent":
                    label = "wind polytropic index"
                # For triples
                elif label == "binary2_a":
                    label = "semi-major axis thight orbit"
                elif label == "binary2_e":
                    label = "eccentricity thight orbit"
                #quantities that we need for triples but don't want in the setup dictionary
                elif label =='q2':
                    q2 = float(value)
                elif label == "racc2b" or label == "accr2b":
                    racc2b = float(value)
                elif label == "racc2a" or label == "accr2a": #for subst=12
                    racc2a = float(value)
                
                # # For triples
                # elif label == 'secondary_mass': label = 'massComp_ini'
                # elif label == 'binary2_a' : label = 'sma_in_ini'
                # elif label == 'binary2_e' : label = 'ecc_in'
                # elif label == 'secondary_racc': label = 'rAccrComp'
                # elif label == 'accr2b' : label = 'rAccrComp_in'
                # elif label == 'racc2b' : label = 'rAccrComp_in'

                # Store variable with the type stored in the index definition
                if (label in index_definition["mappings"]["properties"]) and (
                    index_definition["mappings"]["properties"][label]["type"] == "float"
                ):
                    setup[label] = float(value)
                elif (label in index_definition["mappings"]["properties"]) and (
                    index_definition["mappings"]["properties"][label]["type"]
                    == "integer"
                ):
                    setup[label] = int(value)
                elif (label in index_definition["mappings"]["properties"]) and (
                    index_definition["mappings"]["properties"][label]["type"]
                    == "string"
                ):
                    setup[label] = str(value)

                # Boolean
                if label == "icompanion_star":
                    if int(value) == 0:
                        setup["single_star"] = True
                    else:
                        setup["single_star"] = False
                    if int(value) == 2:
                        setup["triple_star"] = True
                    else:
                        setup["triple_star"] = False

    except FileNotFoundError:
        print("")
        print(" ERROR: No %s.setup file found!" % prefix)
        print("")
        sys.exit()
    
    if setup["triple_star"]==True:
        if setup['subst']==11:  
            #primary mass Mp is divided into m1 and m2, with Mp=m1+m2 and q=m2/m1, so m1=Mp/(1+q)
            setup["primary mass"]=np.round(float(setup["primary mass"]/(1+q2)),3)
            #tertiary mass is the original secondary
            setup["tertiary mass"]=setup["secondary mass"]
            setup["tertiary Racc"]=setup["secondary Racc"]
            #secondary mass is m1*q
            setup["secondary mass"]=np.round(float(setup["primary mass"]*q2),3)
            setup["secondary Racc"]= racc2b

        elif setup['subst']==12: #primary mass is original primary mass, original secondary is divided into m2 and m3
            setup["secondary mass"]=np.round(float(setup["secondary mass"]/(1+q2)),3)
            setup["tertiary mass"]=np.round(float(setup["secondary mass"]*q2),3)
            setup["secondary Racc"]=racc2a
            setup["tertiary Racc"]=racc2b

    # load the prefix.in file
    try:
        with open(os.path.join(directory, "%s.in" % prefix), "r") as data:
            for line in data:
                if len(line) <= 1 or line.startswith("#"):
                    # remove empty lines and headers
                    continue
                # Get labels and values
                label, _, value, *_ = line.strip().split()

                # Change labels to make them easier to read for the human eye
                if label == "wind_mass_rate":
                    label = "wind mass rate"
                elif label == "wind_velocity":
                    label = "init wind velocity"
                elif label == "wind_inject_radius":
                    label = "wind inject radius"
                elif label == "wind_temperature":
                    label = "wind temperature"
                elif label == "mu":
                    label = "mean molecular weight"
                elif label == "ieos":
                    label = "equation of state"
                elif label == "outer_boundary":
                    label = "outer boundary"

                # Booleans
                if value == "F":
                    value = 0

                # Store variable with the type stored in the index definition
                if (label in index_definition["mappings"]["properties"]) and (
                    index_definition["mappings"]["properties"][label]["type"] == "float"
                ):
                    setup[label] = float(value)
                elif (label in index_definition["mappings"]["properties"]) and (
                    index_definition["mappings"]["properties"][label]["type"]
                    == "integer"
                ):
                    setup[label] = int(value)
                elif (label in index_definition["mappings"]["properties"]) and (
                    index_definition["mappings"]["properties"][label]["type"]
                    == "string"
                ):
                    setup[label] = str(value)
    except FileNotFoundError:
        print("")
        print(" ERROR: No %s.in file found!" % prefix)
        print("")
        sys.exit()

    return setup
