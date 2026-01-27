import pandas as pd
import os

file_path = "e:/Code/Projects/PNJCleaning/All Stores Spreadsheet.xlsx"

try:
    xl = pd.ExcelFile(file_path)
    for sheet in xl.sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet)
        
        # Search for CM Resturants or CM Restaurants
        mask = df.apply(lambda row: row.astype(str).str.contains('CM Resturant', case=False).any(), axis=1)
        matches = df[mask]
        
        if not matches.empty:
            print(f"\n--- Matches found in Sheet: {sheet} ---")
            pd.set_option('display.max_columns', None)
            pd.set_option('display.width', 1000)
            print(matches)
            
            # Print column headers for these matches
            print("\nRow indexes where CM Resturants was found:", matches.index.tolist())
            
except Exception as e:
    print(f"Error reading {file_path}: {e}")
