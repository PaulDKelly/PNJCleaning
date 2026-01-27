import pandas as pd
import os

file_path = "e:/Code/Projects/PNJCleaning/All Stores Spreadsheet.xlsx"

try:
    xl = pd.ExcelFile(file_path)
    df = pd.read_excel(file_path, sheet_name='Sheet1')
    
    # Analyze rows 160 to 170 precisely
    print("\n--- Precise Mapping (Rows 160-170) ---")
    for idx in range(160, 171):
        row = df.iloc[idx]
        print(f"\nRow {idx}:")
        for col_idx, val in enumerate(row):
            if pd.notna(val):
                print(f"  Col {col_idx}: {val}")
            
except Exception as e:
    print(f"Error: {e}")
