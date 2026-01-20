import pandas as pd

# 1. Load the physical Parquet file you downloaded
# Replace with your actual filename
parquet_file = "train-00001-of-00002-09ac6bd45d6b3658.parquet" 
df = pd.read_parquet(parquet_file)

# Optional: If the file is huge (50k rows) and you only want your 10k POC

#print(df.count())
# get the count of distinct Case_Type
print(df['Case_Type'].nunique())
# for val in df['Case_Type'].unique():
#     print(val)

print(df[df['Case_Type'].unique()])

# 2. Convert to JSON
# orient='records' is CRITICAL. 
# It creates the format: [{"id": 1, "text": "..."}, {"id": 2, "text": "..."}]
# lines=False with indent=4 makes it a valid, readable JSON array.
# df.to_json("legal_data_10k.json", orient="records", lines=False, indent=4)

# print(f"Success! Converted {len(df)} records to 'legal_data_10k.json'")