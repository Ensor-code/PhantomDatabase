'''
Connect to elasticsearch, create an index with proper mappings, and upload multiple 
documents to the index according to the list of file in model_list.txt.
'''

import os
import sys
import time

from dotenv import load_dotenv
from elasticsearch import helpers  # For bulk Data Uploading
from elasticsearch import Elasticsearch  # Base function for interacting with Elasticsearch
from elasticsearch import RequestError

from load_func import *

# Directories of models to load
DATA_DIR = "/cosma/apps/dr011/dc-land2/database/wind"   # Careful, this is a local path - change it to your own
PREFIX = "wind"    

# Directory of scripts
DIR_CURRENT = os.getcwd()

# model list file
LIST = "/cosma/home/dr011/dc-land2/PhantomDatabase/model_list.txt"
MODELS = read_model_list(LIST)

# elastic search index name
INDEX_NAME = "wind"

# indicate if you want to update existing documents
UPDATE = True

# indicate if you want to recreate the index
RECREATE_INDEX = True

# remove excessive HTTPS request warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

### Connect to Elastic search 
# This is done using your own API key, generated using kibana, which should be stored localy on your machine. 
# We stored our API key in a .env file in the same folder as this script, 
# and use the python module dotenv to load it as an environment variable.
load_dotenv()
print("- Connecting to Elasticsearch...")
client = Elasticsearch("https://localhost:9200/", api_key=os.getenv('API_KEY'),verify_certs=False,ssl_show_warn=False)
client.ping()
print("     ... Connected!")

### Create the dictionnaries containing all the mappings
# We read the mappings list from the metadata.csv file, which is generated externally from a shared excel file, 
# and the list is then transformed into a dictionnary of mappings with the proper formatting.

# grab mappings list from the csv file, which should be in the same directory as the script
CSV_PATH = os.path.join(DIR_CURRENT, "metadata.csv")
data, header = read_csv(CSV_PATH)


# create the dictionnary of mappings
print(" - Creating index mappings...")
mappings = create_mapping(data, header)
#pprint(mappings)

# Add other settings to the index parameters
index_definition = {
    "settings": {
        "number_of_shards": 1,
    },
    "mappings": {"properties": mappings},
}

# Create the index using the parameters set above.
print(" - Creating index...")
if client.indices.exists(index=INDEX_NAME):
    if RECREATE_INDEX:
        print(" - Deleting existing index...")
        client.indices.delete(index=INDEX_NAME)
        print(" - Creating new index...")
        client.indices.create(index=INDEX_NAME, body=index_definition)
    else:
        print("     ... Index already exists, delete it if you want to recreate it")
else:
    client.indices.create(index=INDEX_NAME, body=index_definition)


# Generate the operations list to upload multiple documents
print(" - Preparing files for upload...")
operations = []
count = 0
update_count = 0
skip_count = 0
err_count = 0
for model in MODELS:
    base_command = {"_index": INDEX_NAME, "_op_type": "index"}
    # check if document already exists
    count += 1
    print(f"\r     ... Progress: {count}/{len(MODELS)}")
    id = query_document(client, INDEX_NAME,model)
    # load data
    modelData = LoadDoc(DATA_DIR, model, PREFIX, index_definition)
    if modelData == {}:
        err_count += 1
        continue
    # check if existing document should be updated
    if id and UPDATE:
        # delete and reupload
        update_count += 1
        client.delete(index=INDEX_NAME, id=id)
    elif id and not UPDATE:
        skip_count += 1
        continue
    # check that all the entries are correctly filled
    if CheckEntries(model,modelData) == 1:
        err_count += 1
        continue
    operations.append((base_command | {"_source": modelData}))

if UPDATE and update_count>0 : print(f'\r     ... {update_count}/{len(MODELS)} documents already exist and will be updated.')
elif skip_count>0: print(f'\r     ... {skip_count}/{len(MODELS)} documents already exist and will be skipped.')
if err_count>0 : print(f'\r     ... {err_count}/{len(MODELS)} documents could not be loaded due to errors.')
else: print(f'\r     ... All {len(MODELS)} documents will be uploaded.')

# Upload the documents
print(" - Uploading documents...")
helpers.bulk(client, operations, refresh=True)
print("     ... Upload complete!")

# Update the publication status of the Documents
# get list of documents to udpate
print(" - Filling in the publication fields...")
FILE_PATH = os.path.join(DIR_CURRENT, "publications.csv")
models, _ = read_csv(FILE_PATH)

# Query models then update the publication field
for m in models:
    q = {
        "script": {
            "source": f"ctx._source.Publication='{m[1]}'",  # update publication field
            "lang": "painless"
        },
        "query": {
            "match": {
                'Model name': m[0]
            }
        }
    }
    try :
        client.update_by_query(body=q, index='wind')
    except Exception as e:
        print(f"Failed to update {m[0]}: {e}")
        continue
print("     ... Publication fields updated!")

