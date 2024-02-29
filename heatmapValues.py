import json
import numpy as np

# Load the GeoJSON data
def load_geojson(file_path):
    with open(file_path, 'r') as file:
        return json.load(file)

# Calculate and normalize heatmap values, filtering for kind == 'county'
def calculate_heatmap_values(geojson_data):
    per_capita_income_values = []
    population_values = []
    prosperity_index_values = []

    for feature in geojson_data['features']:
        properties = feature['properties']
        # Filter for 'county' kind
        if properties.get('kind') == 'county':
            # Explicitly handle None values
            population = properties.get('population') or 0
            per_capita_income = properties.get('perCapitaIncome') or 0
            area = properties.get('area') or 1  # Prevent division by zero

            # Convert to float, ensuring no None values are passed
            population = float(population)
            per_capita_income = float(per_capita_income)
            area = float(area)

            # Calculate prosperity index
            prosperity_index = (population * per_capita_income) / area if population and per_capita_income and area else 0

            # Append values for normalization
            per_capita_income_values.append(per_capita_income)
            population_values.append(population)
            prosperity_index_values.append(prosperity_index)

    # Normalize values to a 0-1 scale
    def normalize(values):
        min_val = min(values)
        max_val = max(values)
        return [(val - min_val) / (max_val - min_val) for val in values if max_val - min_val > 0]  # Avoid division by zero

    return {
        'perCapitaIncome': normalize(per_capita_income_values),
        'population': normalize(population_values),
        'prosperityIndex': normalize(prosperity_index_values)
    }

# Write heatmap values to a JSON file
def write_heatmap_values_to_file(heatmap_values, output_file_path):
    with open(output_file_path, 'w') as file:
        json.dump(heatmap_values, file, indent=4)

# Example usage
file_path = 'files/updated_usaCounties.geojson'  # Update this path with your actual file path
output_file_path = 'files/heatmap_values.json'  # This is the output file

geojson_data = load_geojson(file_path)
heatmap_values = calculate_heatmap_values(geojson_data)

# Write the output to a file
write_heatmap_values_to_file(heatmap_values, output_file_path)

print(f"Heatmap values have been written to {output_file_path}")
