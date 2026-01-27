import pandas as pd
import os

file_path = "e:/Code/Projects/PNJCleaning/All Stores Spreadsheet.xlsx"

print(f"--- Deep Analysis: All Stores Spreadsheet.xlsx ---")
try:
    xl = pd.ExcelFile(file_path)
    for sheet in xl.sheet_names:
        print(f"\nSheet: {sheet}")
        df = pd.read_excel(file_path, sheet_name=sheet)
        print(f"Total Rows: {len(df)}")
        
        # User mentioned row 164. In 0-indexed pandas, this is row 162 or 163 depending on headers.
        # Let's show 10 rows around 164.
        print("\n--- Rows around 164 (Target Area) ---")
        target_area = df.iloc[160:175]
        print(target_area)
        
        print("\n--- Rows with 'KFC' ---")
        kfc_rows = df[df.apply(lambda row: row.astype(str).str.contains('KFC', case=False).any(), axis=1)].head(10)
        print(kfc_rows)
        
        # Identify columns with data
        print("\n--- Column Identification ---")
        for i, col in enumerate(df.columns):
            sample_vals = df.iloc[160:170, i].dropna().tolist()
            print(f"Column {i} ({col}): Sample values around row 164: {sample_vals}")

except Exception as e:
    print(f"Error reading {file_path}: {e}")
