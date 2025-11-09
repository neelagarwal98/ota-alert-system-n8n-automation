import pandas as pd

xl = pd.ExcelFile('data/Kasa_Living_Weekly_Conversion_Report_2025_(external).xlsx')
print("Weeks available:", xl.sheet_names)

df = pd.read_excel('data/Kasa_Living_Weekly_Conversion_Report_2025_(external).xlsx', sheet_name=0)
print(f"\nShape: {df.shape}")
print(f"\nColumns: {df.columns.tolist()}")
print(f"\nSample:\n{df.head()}")
print(f"\nStats:\n{df.describe()}")