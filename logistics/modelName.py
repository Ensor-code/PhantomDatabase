"""
Creates unique model names from the input files and copies the model directories to the database directory
"""

import os
import numpy as np

PREFIX = "wind"
CSV_NAME = "modelName.csv"  # contains all the parameters we include in the new modelname -- if changed, the script needs to run over all models again

# Directory where you want to grab the models
DIR_MODEL = '/STER/hydroModels/jolienm/finalModelsAccrDisks'

# Directory where you want to copy or move your models to
DIR_DEST = '/Users/camille/Documents/runs/phantom/database/windNew'


def main():
    # grab mappings list from the csv file, which should be in the same directory as the script
    dir_csv = os.getcwd()
    csv_path = os.path.join(dir_csv, CSV_NAME)
    labels, _ = read_csv(csv_path)

    # Looks for all models in this directory that have a PREFIX.in, PREFIX.setup and >=1 dump files
    models = search_dir(DIR_MODEL, PREFIX, minDumpFiles=1)

    for m in models:
        print(m)
    # copy
    #s, d, f = copy_dir(DIR_MODEL,models,PREFIX,DIR_DEST,labels,verbose=True)

    # print summary
    #print('Results:')
    #print('Success:',len(s))
    #print('Duplicates:',len(d))
    #print('Failed:',len(f))


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


def make_name(labels, directory, prefix):
    '''
    Get all parameters for the name of the model from the input files
    '''
    import os

    name = {}
    try:
        with open(os.path.join(directory, "%s.setup" % prefix), "r") as data:
            # get data from prefix.setup file
            for line in data:
                if len(line) <= 1 or line.startswith("#"):
                    # discard empty lines and headers
                    continue
                # Get labels and values
                label, _, value, *_ = line.strip().split()

                for l in labels:
                    # quantites for name
                    if l[1] == label:
                        if 'int' in l[2]:
                            name[l[0]] = int(value)
                        elif 'float' in l[2]:
                            name[l[0]] = float(value)
                        else:
                            name[l[0]] = value

                    # quantities that we need for triples' calculations
                    elif label == 'q2':
                        q2 = float(value)
                    elif label == "racc2b" or label == "accr2b":
                        racc2b = float(value)
                    elif label == "racc2a" or label == "accr2a":
                        racc2a = float(value)  #for subst=12

        # Triples calculations
        if name['icompstar'] == 2:
            if name['subst'] == 11:
                #primary mass Mp is divided into m1 and m2, with Mp=m1+m2 and q=m2/m1, so m1=Mp/(1+q)
                name["m1"] = round(float(name["m1"]) / (1 + q2), 3)
                #tertiary mass is the original secondary
                name["m3"] = float(name["m2"])
                name["racc3"] = name["racc2"]
                #secondary mass is m1*q
                name["m2"] = round(float(name["m1"] * q2), 3)
                name["racc2"] = racc2b
            elif name[
                    'subst'] == 11:  #primary mass is original primary mass, original secondary is divided into m2 and m3
                name["m2"] = round(float(name["m2"] / (1 + q2)), 3)
                name["m3"] = round(float(name["m2"] * q2), 3)
                name["racc2"] = racc2a
                name["racc3"] = racc2b

    except FileNotFoundError:
        print(" ERROR: No %s.setup file found!" % prefix)
        return None

    try:
        with open(os.path.join(directory, "%s.in" % prefix), "r") as data:
            # get data from prefix.in file
            for line in data:
                if len(line) <= 1 or line.startswith("#"):
                    # discard empty lines and headers
                    continue
                # Get labels and values
                label, _, value, *_ = line.strip().split()

                for l in labels:
                    # quantities for name
                    if l[1] == label:
                        if 'int' in l[2]:
                            name[l[0]] = int(value)
                        elif 'float' in l[2]:
                            name[l[0]] = float(value)
                        else:
                            name[l[0]] = value

    except FileNotFoundError:
        print(" ERROR: No %s.in file found!" % prefix)
        return None

    # build string for name
    string = ''
    for key, value in name.items():
        string += f'{key}_{value}_'

    return string.strip('_')


def search_dir(loc, prefix, minDumpFiles=20):
    '''
    Search for models in a directory with a certain prefix and a minimum amount of dumpfiles
    '''
    import os

    result = []
    for path, _, files in os.walk(loc):
        dumpFiles = list(
            filter(
                lambda x: (prefix + '_' in x and not '.tmp' in x and not '.txt'
                           in x and not '.png' in x), files))
        setupFiles = list(filter(lambda x: (prefix + '.setup' in x), files))
        inFiles = list(filter(lambda x: (prefix + '.in' in x), files))
        # Only include models with a minimum amount of dumpfiles, because the others can be trown away
        if len(dumpFiles) >= minDumpFiles and len(setupFiles) > 0 and len(
                inFiles) > 0:
            slicedString = path.replace(loc, "").strip("/")
            result.append(slicedString)

    return sorted(result)


def copy_dir(old_dir, MODELS, PREFIX, new_dir, labels, verbose=False):
    '''
    copy the model directories to the database directory
    '''
    import os

    success = []
    duplicates = []
    failed = []

    # check if new_dir exists
    if os.path.isdir(new_dir) == False:
        if verbose:
            print('Database directory does not exist:', new_dir)
        os.system(f'mkdir {new_dir}')

    for model in MODELS:
        # check if the model directory exists
        if os.path.isdir(os.path.join(old_dir, model)) == False:
            if verbose:
                print('Model directory does not exist:',
                      os.path.join(old_dir, model))
            failed.append((model, 'directory does not exist'))
            continue

        # get the model name
        name = make_name(labels, os.path.join(old_dir, model), PREFIX)
        if name == None:
            if verbose:
                print('Could not make name for model:', model)
            failed.append((model, 'could not make name'))
            continue

        # check if the model directory is already in the database directory
        if os.path.isdir(os.path.join(new_dir, name)) == True:
            # check if dir is empty
            if os.listdir(os.path.join(new_dir, name)):
                if verbose:
                    print('Model already has files in database directory:',
                          model)
                    print(
                        'copies are made with rsync so the existing files are not overwritten'
                    )
            duplicates.append((model, name))
        else:
            # make directory in database directory
            os.system(f'mkdir {new_dir}/{name}')
        # copy the model directory to the database directory
        print('Copying model:', model)
        try:
            os.system(f'rsync -ac {old_dir}/{model}/* {new_dir}/{name}')
            success.append((model, name))
        except:
            if verbose:
                print('Failed to copy model:', model)
            failed.append((model, 'failed to copy'))
    return success, duplicates, failed


if __name__ == "__main__":
    main()
