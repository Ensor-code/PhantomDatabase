
'''
 Filling in the "publication" field is complicated in batch uploads to the database, 
 so this script is a faster option to update the publication field for models based 
 on an input .csv file containing a list of models and the corresponding publication.
'''

from dotenv import load_dotenv
import os
from elasticsearch import Elasticsearch  # Base function for interacting with Elasticsearch
from load_func import *

# remove excessive HTTPS request warnings
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# connect to Elasticsearch
load_dotenv()
client = Elasticsearch("https://localhost:9200/", api_key=os.getenv('API_KEY'),verify_certs=False)

# index name
INDEX_NAME = "wind"

print("Getting list of models to update")
# get list of documents to udpate
DIR_NAME = os.getcwd()
FILE_NAME = "publications.csv"
FILE_PATH = os.path.join(DIR_NAME, FILE_NAME)
models, _ = read_csv(FILE_PATH)
print("Updating models")
for m in models:
    print(f"Updating {m[0]}")
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

print("-- Done -- ")
print(r"Happy browsing (๑ᵔ⤙ᵔ๑)")
