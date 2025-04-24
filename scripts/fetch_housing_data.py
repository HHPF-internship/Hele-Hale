import requests
import json
import argparse
from typing import Dict, List, Optional
from datetime import datetime

class APIClient:
    def __init__(self, base_url: str, bearer_token: str, output_file: str = None):
        """
        Initialize the API client with base URL and bearer token.
        
        Args:
            base_url (str): The base URL of the API
            bearer_token (str): The bearer token for authentication
            output_file (str, optional): Path to file where output will be written
        """
        self.base_url = base_url.rstrip('/')
        # Check if token already includes 'Bearer' prefix
        auth_header = bearer_token if bearer_token.startswith('Bearer ') else f'Bearer {bearer_token}'
        self.headers = {
            'Authorization': auth_header,
            'Content-Type': 'application/json'
        }
        self.output_file = output_file
        # Initialize the output file with an opening bracket for JSON array
        if output_file:
            with open(output_file, 'w') as f:
                f.write('[\n')

    def _write_to_file(self, message: str, is_last: bool = False):
        """
        Write message to output file if specified, otherwise print to console.
        
        Args:
            message (str): The message to write
            is_last (bool): Whether this is the last item in the JSON array
        """
        if self.output_file:
            with open(self.output_file, 'a') as f:
                f.write(message)
                if not is_last:
                    f.write(',\n')
                else:
                    f.write('\n')
        else:
            print(message)

    def _write_error(self, error_message: str):
        """Write error message to file without affecting JSON structure"""
        if self.output_file:
            with open(self.output_file, 'a') as f:
                f.write(f'// ERROR: {error_message}\n')

    def _extract_taxmapkey_fields(self, taxmapkey: Dict) -> Dict:
        """Extract specific fields from a TaxMapKey object and filter Transfers"""
        # Extract base fields
        result = {
            'ParcelNumber': taxmapkey.get('ParcelNumber'),
            'LastSaleDate': taxmapkey.get('LastSaleDate'),
            'LastSalePrice': taxmapkey.get('LastSalePrice'),
            'LastSaleInstrument': taxmapkey.get('LastSaleInstrument'),
        }

        # Filter Transfers
        if 'Transfers' in taxmapkey:
            filtered_transfers = []
            for transfer in taxmapkey['Transfers']:
                # Check if all required fields exist and meet criteria
                if all(key in transfer['Grantor'] for key in ['Date', 'Price', 'InstrumentType', 'BureauOfConveyancesLink']):
                    # Parse the date string to check if it's in 2024
                    try:
                        transfer_date = datetime.strptime(transfer['Grantor']['Date'], '%Y-%m-%dT%H:%M:%S%z')
                        if (transfer_date.year == 2024 and 
                            transfer['Grantor']['Price'] >= 200000 and 
                            transfer['Grantor']['InstrumentType'] == 'DEED' and 
                            transfer['Grantor']['BureauOfConveyancesLink']):
                            filtered_transfers.append(transfer)
                    except (ValueError, TypeError):
                        # Skip transfers with invalid date format
                        continue
            
            result['Transfers'] = filtered_transfers
        
        return result

    def fetch_results(self, endpoint: str, query: str, start_index: int, end_index: int, batch_size: int = 1000) -> None:
        """
        Fetch results by making multiple requests with increasing offsets.
        
        Args:
            endpoint (str): The API endpoint to send the request to
            query (str): The search query
            start_index (int): Starting index of results to fetch
            end_index (int): Ending index of results to fetch (exclusive)
            batch_size (int): Number of results to fetch per request (default: 250)
        """
        # Calculate number of requests needed
        total_results = end_index - start_index
        num_requests = (total_results + batch_size - 1) // batch_size
        
        for i in range(num_requests):
            offset = start_index + (i * batch_size)
            # Adjust limit for the last request if needed
            limit = min(batch_size, end_index - offset)
            
            request_data = {
                "offset": offset,
                "limit": limit,
                "query": query,
                "search": ""
            }
            
            try:
                response = requests.post(
                    f"{self.base_url}/{endpoint.lstrip('/')}",
                    headers=self.headers,
                    json=request_data
                )
                response.raise_for_status()
                response_data = response.json()
                
                if 'data' in response_data:
                    batch_results = []
                    for item in response_data['data']:
                        if 'TaxMapKey' in item:
                            taxmapkey_info = self._extract_taxmapkey_fields(item['TaxMapKey'])
                            batch_results.append(taxmapkey_info)
                    
                    # Write this batch of results to the file
                    for j, result in enumerate(batch_results):
                        is_last = (i == num_requests - 1) and (j == len(batch_results) - 1)
                        self._write_to_file(json.dumps(result, indent=2), is_last=is_last)
                
                print(f"Fetched {offset + limit} of {end_index} results...")
                
            except requests.exceptions.RequestException as e:
                error_msg = f"Error making request at offset {offset}: {e}"
                self._write_error(error_msg)
                if hasattr(e, 'response') and e.response is not None:
                    self._write_error(f"Error response: {e.response.text}")
                # Continue with next batch instead of raising the exception
                continue
        
        # Close the JSON array
        if self.output_file:
            with open(self.output_file, 'a') as f:
                f.write(']\n')

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Fetch TaxMapKey data from HI Info API')
    parser.add_argument('--output-file', type=str,
                      help='Output file path (default: housing_data_TIMESTAMP.json)')
    
    args = parser.parse_args()
    
    # Replace these with your actual values
    BASE_URL = "https://mls.hiinfo.com"
    BEARER_TOKEN = "eyJraWQiOiJyc2ExIiwiYWxnIjoiUlMyNTYifQ.eyJzdWIiOiJUTUsxNDE0MyIsImF6cCI6Im1scyIsImlzcyI6Imh0dHBzOlwvXC9hdXRoLmhpaW5mby5jb20iLCJleHAiOjE3NDU0NTY4NDcsImlhdCI6MTc0NTQ0MjQ0NywianRpIjoiYjhlMWMwNzgtMWVhMS00ZDVmLTkxODctMmUzMzg5NGVkMDMyIn0.M6DnIqpnANkZALa-2fVGSM1fWnonG1XxC-iN-gEMam3XImPbjKFP9kufF9LVR_1U1dC4CfO6_UwgaI6IyJwC-ENQr2VilYYNHMBeNsPJ7jvBpaPIQ1QVi3AcyA43-wK9PILc4iWEUrSXAyLnPEW4elotlEC0vDoJ4nW71fZf-OU"
    
    # Use provided output file or generate one with timestamp
    output_file = args.output_file or f'housing_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    
    # Initialize the client
    client = APIClient(BASE_URL, BEARER_TOKEN, output_file)
    
    query_first_half = "(TaxMapKey.Transfers.Grantor.Date: from 2024-01-01T00:00:00-10:00 to 2024-06-30T23:59:59-10:00) AND (TaxMapKey.LastSaleInstrument: \"DEED\") AND (TaxMapKey.Transfers.Grantor.Price: from 200000)"
    total_results_first_half = 7967
    
    query_second_half = "(TaxMapKey.Transfers.Grantor.Date: from 2024-07-01T00:00:00-10:00 to 2024-12-31T23:59:59-10:00) AND (TaxMapKey.LastSaleInstrument: \"DEED\") AND (TaxMapKey.Transfers.Grantor.Price: from 200000)"
    total_results_second_half = 8512
    
    try:
        # Fetch results for first half of 2024
        print(f"Fetching results for first half of 2024 (total: {total_results_first_half})...")
        client.fetch_results(
            endpoint="/api/search/tax-map-keys/",
            query=query_first_half,
            start_index=0,
            end_index=total_results_first_half,
            batch_size=1000
        )
        
        # Fetch results for second half of 2024
        print(f"Fetching results for second half of 2024 (total: {total_results_second_half})...")
        client.fetch_results(
            endpoint="/api/search/tax-map-keys/",
            query=query_second_half,
            start_index=0,
            end_index=total_results_second_half,
            batch_size=1000
        )
        
    except Exception as e:
        # Write error to file without affecting JSON structure
        client._write_error(f"Fatal error: {e}")
        # Ensure JSON array is properly closed
        if client.output_file:
            with open(client.output_file, 'a') as f:
                f.write(']\n')

if __name__ == "__main__":
    main() 