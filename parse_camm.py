def parse_camm_data(filename):
    with open(filename, 'r') as f:
        lines = f.readlines()

    data = []
    current_sample = {}

    for line in lines:
        if 'AngularVelocity' in line or 'Acceleration' in line:
            identifier, values = line.strip().split(' = ')
            values = list(map(float, values.split(' ')))
            current_sample[identifier] = values
            if 'Acceleration' in line:
                # Once we have both AngularVelocity and Acceleration, consider the sample complete
                data.append(current_sample)
                current_sample = {}

    return data

camm_data = parse_camm_data('R0013304_0.txt')

# Convert to JSON-like format
import json
camm_data_json = json.dumps(camm_data, indent=4)


# Specify the file path where you want to save the JSON data
file_path = "camm_data.json"

# Open the file for writing and write the JSON data
with open(file_path, "w") as json_file:
    json_file.write(camm_data_json)