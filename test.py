import pandas as pd

# Replace 'path_to_your_parquet_file.parquet' with the actual path to your Parquet file
parquet_file_path = 'files/contacts.parquet'

# Read the Parquet file into a DataFrame
df = pd.read_parquet(parquet_file_path)

# Display the DataFrame
print(df)