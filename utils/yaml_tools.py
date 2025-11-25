import yaml

def remove_duplicates_from_yaml(filename: str) -> None:
    """
    Remove duplicate entries from a YAML file.

    Args:
    - filename: Name of the YAML file to process.
    """
    with open(filename, "r") as file:
        data = yaml.safe_load(file)

    # Remove duplicates
    unique_data = remove_duplicates(data)

    # Write unique data back to the YAML file
    with open(filename, "w") as file:
        yaml.dump(unique_data, file)


def remove_duplicates(data: dict) -> dict:
    """
    Remove duplicate entries with the same top-level keys from a nested dictionary.

    Args:
    - data: Nested dictionary to process.

    Returns:
    - Unique data (nested dictionary) without duplicates.
    """
    seen = {}
    unique_data = {}
    for key, value in data.items():
        if isinstance(value, dict):
            # Recursively process nested dictionaries
            unique_data[key] = remove_duplicates(value)
        elif key not in seen:
            # Add the first occurrence of the key
            seen[key] = value
            unique_data[key] = value
    return unique_data  # TODO: 2024-07-15 explore if this is the fastest implementation

def generate_yaml_file(varlist: list, filename: str) -> None:
    """
    Generate a YAML file with given data.

    Args:
    - data: Dictionary containing the data to be written to the YAML file.
    - filename: Name of the YAML file to be generated.
    """
    data = {}

    for var in varlist:
        data[var[0]] = {
            "bpart": var[0],
            "pathname": f"/CALSIM/{var[0]}/.*//.*/.*/",
            "alias": var[1],
            "table_convert": "cfs_taf",
            "table_display": "wy",
            "type": "Channel",
        }

    with open(filename, "w") as file:
        yaml.dump(data, file)
    print(f"YAML file '{filename}' generated successfully.")
    

def clean_yaml(infile, outfile=None):
    """
    Remove `bpart` and `pathname` keys from each entry in a YAML file.
    """
    with open(infile, "r") as f:
        data = yaml.safe_load(f)

    for key, entry in data.items():
        entry.pop("bpart", None)
        entry.pop("pathname", None)

    outfile = outfile or infile  # overwrite if no outfile given

    with open(outfile, "w") as f:
        yaml.safe_dump(data, f, sort_keys=False)

    print(f"Cleaned YAML written to {outfile}")

clean_yaml("config/svars.yaml")