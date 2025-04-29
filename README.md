Ronan Russel Andal
How to use:

Step 1: update bearer token on the code
you will find this bearer token when you log into https://mls.hiinfo.com/
and click inspect->network->request headers

step 2: find out what specific year of data you want
and filter it out on the website and replace the code with the specific nubmers

step 3: run the code and it will return the unsorted data as housing_data_....json

step 4: now you will want to run python3/process_housing_data.py --input *NAME OF YOUR HOUSING DATA JSON FILE*

step 5: your files should be saved in a file called processed_transfers....json
