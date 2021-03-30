import json
with open('agency_jurisdiction.json') as f:
    data = json.load(f)
    chunk = []
    file_index = 1

    def write_file(index, directory, raw_data):
        with open(f"{directory}/fixture_{index}.json", 'w') as outfile:
            json.dump(raw_data, outfile, indent=4)
        print(f"added file: fixture_{index}.json with {len(raw_data)} entries")

    for index, key in enumerate(data):
        file_index += 1
        if len(chunk) < 10001:
            chunk.append(key)
        else:
            write_file(file_index, "agency-jurisdiction", chunk)
            chunk = []
            file_index += 1
    # handle leftover chunk
    if len(chunk) > 0:
        write_file(file_index, "agency-jurisdiction", chunk)
