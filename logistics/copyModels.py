"""
Creates unique model names from the input files and copies the model directories to the database directory
"""

import os


PREFIX = "wind"

# Directory where you want to grab the models
DIR_MODEL='/STER/hydroModels/published/'

# Directory where you want to copy or move your models to
DIR_DEST = '/STER/hydroModels/published/database/'


def main():
    # Looks for all models in this directory that have a PREFIX.in, PREFIX.setup and >=1 dump files
    models = search_dir(DIR_MODEL, PREFIX, minDumpFiles=1)

    # copy
    s, d, f = copy_dir(DIR_MODEL,models,DIR_DEST,PREFIX,verbose=True)

    # print summary
    print('Results:')
    print('Success:',len(s))
    print('Duplicates:',len(d))
    print('Failed:',len(f))


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


def search_dir(loc, prefix, minDumpFiles=5):
    '''
    Search for models in a directory with a certain prefix and a minimum amount of dumpfiles
    '''
    import os

    result = []
    for path, _, files in os.walk(loc):
        # skip subdirs containing resumed runs etc
        if 'cont' in os.path.basename(path) or 'resume'in os.path.basename(path) or 'final' in os.path.basename(path) or 'test' in os.path.basename(path):
            print(f"        skipping {path}")
            continue
        if DIR_DEST in path:
            # don't check the destination directory
            continue
        dumpFiles = list(
            filter(
                lambda x: (prefix + '_' in x and not '.tmp' in x and not '.txt'
                           in x and not '.png' in x and not '.dat' in x), files))
        setupFiles = list(filter(lambda x: (prefix + '.setup' in x), files))
        inFiles = list(filter(lambda x: (prefix + '.in' in x), files))
        # Only include models with a minimum amount of dumpfiles, because the others can be trown away
        if len(dumpFiles) >= minDumpFiles and len(setupFiles) > 0 and len(
                inFiles) > 0:
            slicedString = path.replace(loc, "").strip("/")
            result.append(slicedString)

    return sorted(result)


def copy_dir(old_dir, MODELS, new_dir, prefix, verbose=False):
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

        # make the model name, just the subdirectories where it is stored
        name = model.replace('/','_')

        # don't copy everything, just all .ev, .in, .setup and prefix_1D.dat
        to_copy = []
        count = 0
        for f in os.listdir(os.path.join(old_dir, model)):
            if '1D.dat' in f:
                to_copy.append(f)
            elif '.ev' in f:
                to_copy.append(f)
            elif '.setup' in f:
                to_copy.append(f)
            elif '.in' in f:
                to_copy.append
            elif prefix+'_'in f and '.' not in f:
                # find dump with highest number
                number = int(f.split('_')[-1])
                if number > count:
                    count = number
                    f_dump = f
        to_copy.append(f_dump)

        # check if the new model directory exists
        if not os.path.isdir(os.path.join(new_dir, name)):
            os.system(f'mkdir {new_dir}/{name}')

        # copy the model directory to the database directory        
        if len(os.listdir(os.path.join(new_dir, name))) >= len(to_copy):
            # check if the new dir already has the files needed
            if verbose:
                print('Model already has all necessary files in database directory:',
                        model)
            duplicates.append((model, name))
        else:
            print('Copying model:', model, 'to', name)
            try:
                for f in to_copy:
                    os.system(f'rsync -ac {old_dir}/{model}/{f} {new_dir}/{name}')
                success.append((model, name))
            except:
                if verbose:
                    print('Failed to copy model:', model)
                failed.append((model, 'failed to copy'))
    return success, duplicates, failed


if __name__ == "__main__":
    main()
