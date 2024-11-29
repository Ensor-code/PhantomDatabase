""" Functions to read csv files and return a dictionary for elastic search"""

def read_csv(file_path)->list:
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


def create_mapping(data,header)->dict:
    """ Create dictionary for db mappings
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
        for i in range(2,len(item)):
            if item[i] != "0":
                meta[header[i]] = item[i]
        if meta:
            data_dict[item[0]]["meta"] = meta
    return data_dict


