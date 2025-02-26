# Database for Phantom models

Here are the scripts we use to upload models and make queries to our database, hosted with Elastic Search.

The fields and metada used to map to the elastic search indices are stored in metadata.csv, which is generated from our shared excel file listing the necessary field labels and metadata.

We can create a new index (or use an existing one) and load Documents using LoadModel.ipynb. The paths to the data files is currently hardcoded so be careful to change that to your local directories when uploading.

The dahsboard is handled by streamlit. To run the dahsboard, use 'streamlit run dashboard/dashboard.py'. It should automatically open the dashboard in a new tab in your default web browser.

Various python and bash scripts made to create standardised names for models, transfer or create files can be found in the directory logistics.

Python dependencies:
 - Database:
    elasticsearch
    dotenv (for API key storage)
    streamlit (dashboard)
    numpy

 - Dashboard:
    altair
    dotenv
    numpy
    panda
    plotly
    streamlit
    streamlit_js_eval
