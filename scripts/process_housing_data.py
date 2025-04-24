import json
import argparse
from datetime import datetime
from typing import List, Dict
import requests
import PyPDF2
import io
import re
from pdf2image import convert_from_path
import pytesseract
from PIL import Image
import os

def convert_to_tmk_format(parcel_number: str) -> str:
    """Convert a 13-digit ParcelNumber to TMK format with 5 or 6 parts based on CPR."""
    if len(parcel_number) != 13 or not parcel_number.isdigit():
        return parcel_number  # Return as-is if format is unexpected

    zone = parcel_number[0]
    sec = int(parcel_number[1])
    plat = int(parcel_number[2])
    parcel = int(parcel_number[3:6])
    lot = int(parcel_number[6:9])
    cpr = int(parcel_number[9:13])

    tmk = f"{zone}-{sec}-{plat}-{parcel}-{lot}"
    if cpr != 0:
        tmk += f"-{cpr}"
    return tmk



def extract_conveyance_tax(pdf_url: str) -> str:
    try:
        response = requests.get(pdf_url)
        response.raise_for_status()

        temp_pdf = "temp.pdf"
        with open(temp_pdf, "wb") as f:
            f.write(response.content)

        pages = convert_from_path(temp_pdf, 100)
        img_filename = "temp.jpg"
        pages[0].save(img_filename, 'JPEG')

        text = str(pytesseract.image_to_string(Image.open(img_filename)))

        os.remove(temp_pdf)
        os.remove(img_filename)

        match = re.search(r'Conveyance Tax:\s*\$?\s*([\d,]+\.?\d*)', text)
        if match:
            return match.group(1)
        return "Not found"

    except Exception as e:
        return f"Error accessing PDF: {str(e)}"

def process_housing_data(input_file: str, output_file: str) -> None:
    try:
        existing_transfers = {}
        try:
            with open(output_file, 'r') as f:
                existing_data = json.load(f)
                for item in existing_data:
                    transfer_key = (
                        item.get('ParcelNumber'),
                        item.get('Date'),
                        item.get('Price'),
                        item.get('BureauOfConveyancesLink')
                    )
                    existing_transfers[transfer_key] = item
            print(f"Loaded {len(existing_transfers)} existing transfers from {output_file}")
        except (FileNotFoundError, json.JSONDecodeError):
            with open(output_file, 'w') as f:
                f.write('[\n')
            print("Starting new output file")
        
        with open(input_file, 'r') as f:
            data = json.load(f)
        
        new_transfers = {}
        first_item = len(existing_transfers) == 0
        
        for taxmapkey in data:
            parcel_number = taxmapkey.get('ParcelNumber')
            tmk = convert_to_tmk_format(parcel_number)
            
            for transfer in taxmapkey.get('Transfers', []):
                grantor = transfer.get('Grantor', {})
                transfer_key = (
                    parcel_number,
                    grantor.get('Date'),
                    grantor.get('Price'),
                    grantor.get('BureauOfConveyancesLink')
                )
                
                if transfer_key in existing_transfers:
                    continue
                
                if transfer_key not in new_transfers:
                    conveyance_tax = "ERROR"
                    pdf_url = grantor.get('BureauOfConveyancesLink')
                    if pdf_url:
                        try:
                            conveyance_tax = extract_conveyance_tax(pdf_url)
                        except Exception as e:
                            print(f"Error processing conveyance tax for parcel {parcel_number}: {str(e)}")
                            conveyance_tax = "ERROR"
                    
                    transfer_data = {
                        'ParcelNumber': parcel_number,
                        'TMK': tmk,
                        'Date': grantor.get('Date'),
                        'Price': grantor.get('Price'),
                        'BureauOfConveyancesLink': pdf_url,
                        'ConveyanceTax': conveyance_tax
                    }
                    new_transfers[transfer_key] = transfer_data
                    
                    with open(output_file, 'a') as f:
                        if not first_item:
                            f.write(',\n')
                        json.dump(transfer_data, f, indent=2)
                        first_item = False
        
        with open(output_file, 'a') as f:
            f.write('\n]')
        
        print(f"Successfully processed {len(new_transfers)} new transfers")
        print(f"Total transfers in output file: {len(existing_transfers) + len(new_transfers)}")
        print(f"Output written to {output_file}")
        
    except json.JSONDecodeError as e:
        print(f"Error reading input file: {e}")
    except Exception as e:
        print(f"Error processing data: {e}")
        try:
            with open(output_file, 'a') as f:
                f.write('\n]')
        except:
            pass

def main():
    parser = argparse.ArgumentParser(description='Process housing data and extract transfer information')
    parser.add_argument('--input-file', type=str, required=True, help='Input JSON file path')
    parser.add_argument('--output-file', type=str, help='Output JSON file path (default: processed_transfers_TIMESTAMP.json)')
    
    args = parser.parse_args()
    output_file = args.output_file or f'processed_transfers_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    process_housing_data(args.input_file, output_file)

if __name__ == "__main__":
    main()