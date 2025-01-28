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
 
def read_model_list(file) -> list:
    """Read a file containing a list of models
    Args:
        file: path to file containing the list of models
        Returns:
        List of strings containing the names of the models
    """
    with open(file) as f:
        models = f.readlines()
    models = [x.strip() for x in models]
    return models

def query_document(client, index: str, query: str) -> str:
    """Query the elastic search index to find if the document exists, get the document id if so.
     Args:
        client (str): elasticsearch client
        index (str): elastic search index
        query (dict): query to search for the document, e.g. model_name

    Returns:
        id: id of the document in the index, None if the document does not exist
 """
    from elasticsearch import Elasticsearch
    response = client.search(index=index, query={"match": {"Model name": {"query": query}}})
    if len(response["hits"]["hits"]) > 0:
        id = response["hits"]["hits"][0]["_id"]
    else:
        id = None
    return id


def LoadDoc(directory: str, model, prefix: str, index_definition) -> Dict[str, Any]:
    """Load document from the files in the simulation directory
    Args:
        directory (str): directory of the simulation
        prefix (str): prefix used for the files
        index_definition (dict): dictionary containing the mappings for the elastic search index

    Returns:
        dict: a dictionary containing all the field mappings
        (!! check units, they are not all in SI or cgs)    
    """
    import os

    print("Loading data for model %s" % model)
    directory = os.path.join(directory, model)
    
    # create mappings for the model 
    modelData = {"Model name": model,
                 "path to folder": directory}   
    
    # get data from the .setup file
    modelData.update(LoadSetupData(directory, prefix, index_definition))

    # get data from the .in file
    modelData.update(LoadInData(directory, prefix, index_definition))

    # get data from the header.txt file
    modelData.update(LoadHeaderData(directory, prefix, index_definition))

    # get data from the .ev file
    modelData.update(LoadEvData(directory, prefix, index_definition))

    # get data from the wind1D.dat file
    if prefix == "wind":
        modelData.update(LoadWindData(directory, prefix, index_definition))
    
    return modelData



def LoadInData(directory: str, prefix: str, index_definition) -> Dict[str, Any]:
    """Load the .in file to get the required information about the model

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

    ini = {}
    # load the prefix.in file
    try:
        with open(os.path.join(directory, "%s.in" % prefix), "r") as data:
            for line in data:
                if len(line) <= 1 or line.startswith("#"):
                    # remove empty lines and headers
                    continue
                # Get labels and values
                label, _, value, *_ = line.strip().split()

                # Booleans
                if value == "F":
                    value = 0

                # Store variable with the type defined in the index dictionary
                if label in index_definition["mappings"]["properties"]:
                    ini[label] = StoreEntry(index_definition, label, value)
    except FileNotFoundError:
        print("")
        print(" ERROR: No %s.in file found!" % prefix)
        print("")
        sys.exit()

    return ini


def LoadSetupData(directory: str, prefix: str, index_definition) -> Dict[str, Any]:
    """Load the .setup file to get the required information about the model

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

    # load the .setup file
    try:
        with open(os.path.join(directory, "%s.setup" % prefix), "r") as data:
            for line in data:
                if len(line) <= 1 or line.startswith("#"):
                    # remove empty lines and headers
                    continue
                # Get labels and values
                label, _, value, *_ = line.strip().split()

                #quantities that we need for triples calculations
                if label =='q2': q2 = float(value)
                elif label == "racc2b" or label == "accr2b": racc2b = float(value)
                elif label == "racc2a" or label == "accr2a": racc2a = float(value) #for subst=12
                    

                # Store variable with the type defined in the index dictionary
                if label in index_definition["mappings"]["properties"]:
                    setup[label] = StoreEntry(index_definition, label, value)

    except FileNotFoundError:
        print("")
        print(" ERROR: No %s.setup file found!" % prefix)
        print("")
        sys.exit()
    
    # For triples, get the correct stellar parameters based on the value of subst
    if setup["icompanion_star"]==2:
        if setup['subst']==11:  
            #primary mass Mp is divided into m1 and m2, with Mp=m1+m2 and q=m2/m1, so m1=Mp/(1+q)
            setup["primary_mass"]=np.round(float(setup["primary_mass"]/(1+q2)),3)
            #tertiary mass is the original secondary
            setup["tertiary_mass"]=setup["secondary_mass"]
            setup["tertiary_racc"]=setup["secondary_racc"]
            #secondary mass is m1*q
            setup["secondary_mass"]=np.round(float(setup["primary_mass"]*q2),3)
            setup["secondary_racc"]= racc2b

        elif setup['subst']==12: #primary mass is original primary mass, original secondary is divided into m2 and m3
            setup["secondary_mass"]=np.round(float(setup["secondary_mass"]/(1+q2)),3)
            setup["tertiary_mass"]=np.round(float(setup["secondary_mass"]*q2),3)
            setup["secondary_racc"]=racc2a
            setup["tertiary_racc"]=racc2b

    return setup

def LoadHeaderData(directory: str, prefix: str, index_definition) -> Dict[str, Any]:
    '''Load the header.txt file to get the required information about the model
    Args:
        directory: directory of the simulation
        prefix: prefix used for the files
        index_definition: dictionary containing the mappings for the elastic search index
    
    Returns:
        dict: a dictionary containing the info from the header.txt file
    '''

    import os
    import sys

    header = {}

    try:
        with open(os.path.join(directory, "header.txt"), "r") as data:
            for line in data:
                if len(line) <= 1 \
                or line.startswith("#") \
                or line.startswith("::")\
                or "ERROR" in line:
                    # remove empty lines, headers and useless lines
                    continue

                # special workaround for the line with the version field 
                # that isn't formatted like the others
                if line.startswith("FT"):
                    value = line.strip().split()[0]
                    value = value.strip("FT:")
                    label = 'version'
                elif line.startswith("ST"):
                    value = line.strip().split()[0]
                    value = value.strip("ST:")
                    label = 'version'

                else:
                    # Get labels and values
                    label, value = line.strip().split()
                    if 'naparttot' in label:
                        label = 'resolution (current)'
                    if 'massoftype' in label \
                        and float(value) != 0.0 \
                        and 'particle mass' not in header:
                        # there are multiple fields in header for particle mass,
                        # so only store the first one.
                        # Needs to be refined if we ever use different types
                        # of particles in the same simulation.
                        label = 'particle mass'

                # Store variable with the type defined in the index dictionary
                if label in index_definition["mappings"]["properties"]:
                    header[label] = StoreEntry(index_definition, label, value)
            
    except FileNotFoundError:
        print("ERROR: No header.txt file found!")
        sys.exit()
        return
    return header
    
def LoadEvData(directory: str, prefix: str, index_definition) -> Dict[str, Any]:
    """Load the .ev file to get the required information about the model
    Args:
        directory (str): directory of the simulation
        prefix (str): prefix used for the files
        index_definition (dict): dictionary containing the mappings for the elastic search index

    Returns:
        dict: a dictionary containing the info from the .ev file
    """
    import glob
    import os
    import sys

    ev = {}

    # find latest .ev file
    # find all files matching the pattern wind*.ev
    ev_files = glob.glob( "*.ev",root_dir=directory)
    if not ev_files:
        print("ERROR: No *.ev files found!")
        sys.exit()

    # extract the number from the filenames and find the one with the largest number
    max_number = -1
    max_file = None
    for file in ev_files:
        try:
            number = int(file.split(prefix)[1].split(".ev")[0])
            if number > max_number:
                max_number = number
                max_file = file
        except ValueError:
            continue

    if max_file is None:
        print("ERROR: No valid wind*.ev files found!")
        sys.exit()

    with open(os.path.join(directory, max_file), "r") as data:
        # everything we need is in the last line
        line = data.readlines()[-1]
        ev['simulation time'] = float(line.strip().split()[0])
            
    return ev


def LoadWindData(directory: str, prefix: str, index_definition) -> Dict[str, Any]:
    """Load the wind1D.data file to get the required information about the model

    Args:
        directory (str): directory of the simulation
        prefix (str): prefix used for the files
        index_definition (dict): dictionary containing the mappings for the elastic search index

    Returns:
        dict: a dictionary containing the info from the setup and .in files
    """
    import os
    import sys

    cm_to_km = 1e-5

    wind = {}
    # load the prefix.in file
    try:
        with open(os.path.join(directory, "wind_1D.dat"), "r") as data:
            # everything we need is in the last line
            line = data.readlines()[-1]
            # Get wind terminal velocity
            wind['wind_terminal_velocity'] = float(line.strip().split()[2])*cm_to_km
            
    except FileNotFoundError:
        try:
            with open(os.path.join(directory, "windprofile1D.dat"), "r") as data:
                # Get wind terminal velocity (in km/s, it's in cm/s in the file)
                line = data.readlines()[-1]
                wind['wind_terminal_velocity'] = float(line.strip().split()[2])*cm_to_km

        except FileNotFoundError:
            print("ERROR: No wind_1D.data or windprofile1D.dat file found! Some wind data will be missing -")
    return wind

def StoreEntry(index_definition: dict, label:str, value:str):
    """Store the entry in the elastic search database if it appears in the index_definition.
    The variable type is then based on the entry type defined in index_definition. 
    For now only string, integer and float are supported.
    Args:
        index_definition (dict): dictionary containing the mappings for the elastic search index
        label (str): label of the entry
        value (str): value of the entry
    """
    import sys

    # Return variable with the type defined in the index dictionary
    if index_definition["mappings"]["properties"][label]["type"] == "float":
        return float(value)
    elif index_definition["mappings"]["properties"][label]["type"] == "integer":
        return int(value)
    elif index_definition["mappings"]["properties"][label]["type"] == "keyword":
        return str(value)
    else:
        sys.exit("ERROR: Entry type " + index_definition["mappings"]["properties"][label]["type"] \
                 + " not found in index definition. Check metadata.csv.")