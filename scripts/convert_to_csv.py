import json
import csv
import argparse
from datetime import datetime

'''
This script converts the JSON output from process_housing_data.py to a CSV file.
It does not include the ConveyanceTaxLink field for easy import into Excel.
For conveyance tax fields that have an error, it will simplify to just "ERROR" in 
the CSV file.  You are required to pass an --input-file. The --output-file 
parameter is optional and will default to housing_data_TIMESTAMP.csv
'''

def convert_to_csv(input_file: str, output_file: str) -> None:
    """
    Convert JSON file to CSV format with specific fields.
    
    Args:
        input_file (str): Path to the input JSON file
        output_file (str): Path to the output CSV file
    """
    try:
        # Read the JSON file
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        # Open CSV file for writing
        with open(output_file, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(['ParcelNumber', 'Date', 'Price', 'ConveyanceTax'])
            
            # Write data rows
            for item in data:
                # Clean ConveyanceTax value (remove commas and convert to number)
                conveyance_tax = item.get('ConveyanceTax', '')
                if conveyance_tax not in ['ERROR', 'Not found']:
                    try:
                        # Try to convert to number (removing commas)
                        conveyance_tax = conveyance_tax.replace(',', '')
                        float(conveyance_tax)  # Verify it's a valid number
                    except (ValueError, AttributeError):
                        conveyance_tax = "ERROR"
                else:
                    conveyance_tax = "ERROR"
                
                writer.writerow([
                    item.get('ParcelNumber', ''),
                    item.get('Date', ''),
                    item.get('Price', ''),
                    conveyance_tax
                ])
        
        print(f"Successfully converted {len(data)} records to CSV")
        print(f"Output written to {output_file}")
        
    except json.JSONDecodeError as e:
        print(f"Error reading input file: {e}")
    except Exception as e:
        print(f"Error converting data: {e}")

def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(description='Convert housing data JSON to CSV')
    parser.add_argument('--input-file', type=str, required=True,
                      help='Input JSON file path')
    parser.add_argument('--output-file', type=str,
                      help='Output CSV file path (default: sales_data_TIMESTAMP.csv)')
    
    args = parser.parse_args()
    
    # Use provided output file or generate one with timestamp
    output_file = args.output_file or f'sales_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    convert_to_csv(args.input_file, output_file)

if __name__ == "__main__":
    main() 