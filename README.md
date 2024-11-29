# Database for Phantom models

Here are the scripts we use to upload models and make queries to our database, hosted with Elastic Search.

The fields and metada used to map to the elastic search indices are stored in metadata.csv, which is generated from our shared excel file listing the necessary field labels and metadata.

We can create a new index (or use an existing one) and load data using LoadModel.ipynb. The paths to the data files is currently hardcoded so be careful to change that to your local directories when uploading.

Python dependencies:
    elasticsearch
    dotenv (for API key storage)
