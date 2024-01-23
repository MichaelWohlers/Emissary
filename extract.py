#extracts select results from cleaned_data
import pandas as pd

# Load the CSV file
df = pd.read_csv('files/cleaned_data.csv')

# List of keywords for specific categories
include_keywords = [
    'Boutique', 'Fashion', 'Apparel', 'Clothing',
    'Wear', 'Garments', 'Style', 'Chic', 'Elegant', 'Outfits', 'Wardrobe'
]

# List of keywords to exclude
exclude_keywords = ['redbox', 'JCPenny','KFC','Wingstop','chicken_restaurant','eyewear_and_optician']

# Lowercase keywords for case-insensitive comparison
include_keywords = [keyword.lower() for keyword in include_keywords]
exclude_keywords = [keyword.lower() for keyword in exclude_keywords]

# Function to filter rows based on inclusion and exclusion criteria
def filter_row(row):
    # Check for inclusion keywords in categories
    category = row['categories'].lower() if isinstance(row['categories'], str) else ''
    alt_category = row['altCategories'].lower() if isinstance(row['altCategories'], str) else ''
    name = row['names'].lower() if isinstance(row['names'], str) else ''
    website = row['websites'] if isinstance(row['websites'], str) else ''

    # Check for exclusion keywords
    exclusion = any(exclude_keyword in name or exclude_keyword in category or exclude_keyword in alt_category for exclude_keyword in exclude_keywords)
    
    # Check for inclusion keywords and non-empty website
    inclusion = (any(include_keyword in category or include_keyword in alt_category for include_keyword in include_keywords)) and website != ''

    return inclusion and not exclusion

# Apply filter function
filtered_df = df[df.apply(filter_row, axis=1)]

# Save the filtered rows to a new CSV file
filtered_df.to_csv('files/filtered_data_with_websites.csv', index=False)
