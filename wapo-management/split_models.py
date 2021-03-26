import json
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("model_name", help="provide a django model")
args = parser.parse_args()
model_name = args.model_name

print(model_name)

with open('agency_jurisdiction.json') as f:
    data = json.load(f)
    chunk = []

    def write_file(model, raw_data):
        cleaned_model = model.replace(".", "_")
        with open(f"wapo-management/model-fixtures/fixture_{cleaned_model}.json", 'w') as outfile:
            json.dump(raw_data, outfile, indent=4)
        print(f"added file: fixture_{cleaned_model}.json with {len(raw_data)} entries")

    for index, key in enumerate(data):
        model = key.get('model')
        if (model.startswith(model_name)):
            chunk.append(key)
    write_file(model_name, chunk)
