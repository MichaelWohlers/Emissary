#cleans raw csv data from overature maps query
import pandas as pd
import json

def extract_json_field(json_str, field):
    try:
        json_obj = json.loads(json_str)
        if field == 'common':
            # Extract the 'common' field value
            return ' '.join([item['value'] for item in json_obj[field] if item.get('value')]) if json_obj.get(field) else ''
        else:
            return json_obj.get(field, "")
    except:
        return ""

def extract_address_components(address_json):
    try:
        addresses = json.loads(address_json)
        street, city, postcode, state, country = '', '', '', '', ''
        if addresses and isinstance(addresses, list):
            address = addresses[0]
            street = address.get('freeform', '')
            city = address.get('locality', '')
            postcode = address.get('postcode', '')
            state = address.get('region', '')
            country = address.get('country', '')
        return street, city, postcode, state, country
    except:
        return '', '', '', '', ''

def main():
    df = pd.read_csv('files/base.csv')

    # Extract address components
    df[['street', 'city', 'postcode', 'state', 'country']] = df.apply(
        lambda row: extract_address_components(row['addresses']), axis=1, result_type='expand')

    # Extract categories and altCategories
    df['categories'] = df['categories'].apply(lambda x: extract_json_field(x, 'main'))
    df['altCategories'] = df['categories'].apply(lambda x: extract_json_field(x, 'alternate'))

    # Clean 'names'
    df['names'] = df['names'].apply(lambda x: extract_json_field(x, 'common'))

    output_columns = ['id', 'names', 'categories', 'altCategories', 'websites', 'socials', 'phones', 'brand', 'street', 'city', 'postcode', 'state', 'country']
    final_df = df[output_columns]

    final_df.to_csv('files/cleaned_data.csv', index=False)

if __name__ == "__main__":
    main()
