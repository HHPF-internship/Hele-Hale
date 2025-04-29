Ronan Russel Andal
How to run code:
Update the bearer token in fetch_housing_data.py.
You can find your bearer token by logging into mls.hiinfo.com, inspecting any network request (Inspect → Network tab), and copying the token from the Request Headers.

Step 2:
Determine the year of data you need.
Use the website filters to find the range you're interested in, and note the number of entries. Update the corresponding query parameters in the script accordingly.

Step 3:
Run the fetch script. This will generate an unsorted JSON file named housing_data_...json.

Step 4:
Run the processing script with your new file:
python3 scripts/process_housing_data.py --input-file NAME_OF_YOUR_HOUSING_DATA.json


Step 5:
The processed and cleaned data will be saved as processed_transfers_...json.
