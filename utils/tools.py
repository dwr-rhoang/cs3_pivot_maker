import csv
import os
from typing import Any, Iterable
from pathlib import Path

import pandas as pd
import pandss as pdss
import yaml

# pd.options.mode.chained_assignment = None


# Constants
monthfilter = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]

month_map = {
    "Jan": 1,
    "Feb": 2,
    "Mar": 3,
    "Apr": 4,
    "May": 5,
    "Jun": 6,
    "Jul": 7,
    "Aug": 8,
    "Sep": 9,
    "Oct": 10,
    "Nov": 11,
    "Dec": 12,
}

month_list = [
    "Oct",
    "Nov",
    "Dec",
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
]

wyt_map = {"Wet": 1, "Above Normal": 2, "Below Normal": 3, "Dry": 4, "Critical": 5}

wyt_list = ["Wet", "Above Normal", "Below Normal", "Dry", "Critical"]

common_pers = {
    "Full Simulation Period (1922-2021)": "1922-2021",
    "2021 DCR Simulation Period (1922-2015)": "1922-2015",
    "Single Dry Year (1977)": "1977-1977",
    "Two-Year Drought (1976-1977)": "1976-1977",
    "Single Dry Year (2014)": "2014-2014",
    "Two-Year Drought (2014-2015)": "2014-2015",
    "Six Year Drought (1987-1992)": "1987-1992",
    "Six Year Drought (1929-1934)": "1929-1934",
    "Single Wet Year (1983)": "1983-1983",
    "Single Wet Year (1998)": "1998-1998",
    "Single Wet Year (2006)": "2006-2006",
    "Two Year Wet Sequence (1982-1983)": "1982-1983",
    "Four Year Wet Sequence (1980-1983)": "1980-1983",
    "Six Year Wet Sequence (1978-1983)": "1978-1983",
    "Ten Year Wet Sequence (1978-1987)": "1978-1987",
    "Single Wet Year (2017)": "2017-2017",
}

UNIT_DESCRIPTIONS = {
        "cfs": "Cubic feet per second",
        "taf": "Thousand acre-feet",
        "ec": "µmho/cm",
        "km": "Kilometers from the Golden Gate Bridge"
}

def get_unit_descriptions(var_dict, b_part):
    if var_dict[b_part]["units"] == "cfs":
        unit_description = UNIT_DESCRIPTIONS["cfs"]
    elif var_dict[b_part]["units"] == "taf":
        unit_description = UNIT_DESCRIPTIONS["taf"]
    elif var_dict[b_part]["units"] == "ec":
        unit_description = UNIT_DESCRIPTIONS["ec"]
    elif var_dict[b_part]["units"] == "km":
        unit_description = UNIT_DESCRIPTIONS["km"]
    else:
        unit_description = ""
    return unit_description


def convert_cm_nums(monthchecklist: Iterable[str]) -> list[str]:
    """
    Converts calendar month strings to calendar month numbers
    Jan=1, etc.
    """
    monthfilter = []
    for v in monthchecklist:
        monthfilter.append(month_map[v])
    return monthfilter


def convert_wyt_nums(wytchecklist: Iterable[str]) -> list[str]:
    """
    Converts WYT strings to numbers: Wet = 1, etc.
    """
    wytfilter = []
    for v in wytchecklist:
        wytfilter.append(wyt_map[v])
    return wytfilter


from pathlib import Path
import pandas as pd

def load_data(studies, var_dict: dict, date_map, kind: str, outfile="temp.csv") -> None:
    """
    Load data from the selected DSS files into a .csv
    """
    appended_data = []

    for s in studies:
        dss_path = s.dv_path if kind == "dv" else s.sv_path
        frames = []

        with pdss.DSS(dss_path) as dss:
            for var, spec in var_dict.items():
                path_str = spec["pathname"]
                path_i = pdss.DatasetPath.from_str(path_str)
                print(path_str)

                # collect all RTS as separate columns
                for rts in dss.read_multiple_rts(path_i):
                    tmp = rts.to_frame()           # index = time
                    tmp.columns = [rts.path.b]     # name column by B-part
                    frames.append(tmp)

        if not frames:
            continue

        # concat once per study to avoid fragmentation
        dfi = pd.concat(frames, axis=1)

        # add metadata once per study
        dfi["Scenario"]   = s.alias
        dfi["Assumption"] = s.assumptions
        dfi["Climate"]    = s.climate

        appended_data.append(dfi)

    # ensure output dir exists
    Path("output").mkdir(parents=True, exist_ok=True)

    if not appended_data:
        pd.DataFrame().to_csv(f"output/{outfile}")
        return

    # --- align index types/granularity BEFORE merge ---
    # combine studies, round
    df = pd.concat(appended_data, axis=0).round(2)

    # coerce both sides to tz-naive midnight timestamps so keys match
    df.index = pd.to_datetime(df.index)
    date_map.index = pd.to_datetime(date_map.index)

    if getattr(df.index, "tz", None) is not None:
        df.index = df.index.tz_convert(None)
    if getattr(date_map.index, "tz", None) is not None:
        date_map.index = date_map.index.tz_convert(None)

    df.index = df.index.normalize()
    date_map.index = date_map.index.normalize()

    df = pd.merge(df, date_map, left_index=True, right_index=True)

    # reorder cols for better human readability
    meta_cols = ["Scenario", "Assumption", "Climate"]
    cols = [c for c in df.columns if c not in meta_cols]
    ordered_cols = meta_cols + cols
    df = df[ordered_cols]

    # keep original behavior for CSV (index included by default)
    df.to_csv(f"output/{outfile}")


def make_ressum_df(
    scenlist: Iterable[int],
    df: pd.DataFrame,
    var_dict,
    start_yr=1922,
    end_yr=2021,
    monthfilter=monthfilter,
) -> pd.DataFrame:
    df1 = df.loc[
        (df["icm"].isin(monthfilter)) & (df["iwy"] >= start_yr) & (df["iwy"] <= end_yr)
    ]

    for i in df1:
        try:
            f = var_dict[i]["table_display"]
            if f == "wy":
                df1 = df1.drop(columns=i)

        except KeyError:
            continue

    df_tbl = round(df1.groupby(["Scenario"]).sum(numeric_only=True) / (end_yr - start_yr + 1))

    # Drop the index columns
    df_tbl.drop(["icy", "icm", "iwy", "iwm", "cfs_taf"], axis=1, inplace=True)

    df_tbl = df_tbl.T
    df_tbl["diff"] = df_tbl[scenlist[1]] - df_tbl[scenlist[0]]
    df_tbl["perdiff"] = (
        round((df_tbl[scenlist[1]] - df_tbl[scenlist[0]]) / df_tbl[scenlist[0]], 2)
        * 100
    )
    df_tbl.reset_index(inplace=True)
    return df_tbl


def cfs_taf(df: pd.DataFrame, var_dict: dict) -> pd.DataFrame:
    df_convert = pd.DataFrame(df)
    for var in var_dict:
        b = var
        if var_dict[var]["table_convert"] == "cfs_taf":
            if var not in df.columns:
                # print(f"Warning: '{var}' not found in DataFrame. Skipping.")
                continue
            df_convert[b] = df_convert[b] * df["cfs_taf"]
        else:
            continue
    return df_convert


def make_summary_df(
    scenlist: list[int],
    df: pd.DataFrame,
    var_dict: dict,
    yrkind: str = 'iwy',
    start_yr: int = 1922,
    end_yr: int = 2021,
    monthfilter: Iterable[int] = monthfilter,
    bparts=None,
) -> pd.DataFrame:

    df1 = df.loc[
        (df["icm"].isin(monthfilter)) &
        (df[yrkind] >= start_yr) &
        (df[yrkind] <= end_yr)
    ]
    columns_to_drop = [col for col in df1.columns if "S_" in col]
    df1 = df1.drop(columns=columns_to_drop)
    # Do Conversions
    df1 = cfs_taf(df1, var_dict)
    df1 = cfs_taf(df1, var_dict)

    # Annual Average
    df_tbl = round(df1.groupby(["Scenario"]).sum(numeric_only=True) / (end_yr - start_yr + 1))

    # Time slicing is done; drop the index columns
    df_tbl.drop(["icy", "icm", "iwy", "iwm", "cfs_taf"], axis=1, inplace=True)

    # Filter B-Parts, if user-specified
    if bparts is not None:
        df1 = df_tbl.loc[:, bparts]
        df_tbl = df1

    # Make a dictionary of just aliases to map to the dataframe
    alias_dict = {}
    type_dict = {}
    convert_dict = {}
    for key in var_dict:
        alias_dict[key] = var_dict[key]["alias"]
        type_dict[key] = var_dict[key]["type"]
        convert_dict[key] = "TAF/Yr" \
            if var_dict[key]["table_convert"] == 'cfs_taf' else ''

    df_tbl = df_tbl.T
    # Add index columns
    df_tbl["description"] = df_tbl.index.map(alias_dict)
    df_tbl["type"] = df_tbl.index.map(type_dict)
    df_tbl["convert"] = df_tbl.index.map(convert_dict)
    # Calculate tables
    df_tbl["diff"] = df_tbl[scenlist[1]].sub(
        df_tbl[scenlist[0]],
        fill_value=0,
    )
    df_tbl["perdiff"] = (
        round(
            df_tbl[scenlist[1]]
            .sub(
                df_tbl[scenlist[0]],
                fill_value=0,
            )
            .div(
                df_tbl[scenlist[0]],
                fill_value=0,
            ),
            2,
        )
        * 100
    )
    df_tbl.reset_index(inplace=True, names="bpart")

    return df_tbl


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


def read_csv_into_list(filename: str) -> list[list[str]]:
    data = []
    with open(filename, "r", newline="") as file:
        reader = csv.reader(file, delimiter=",")
        for row in reader:
            data.append(row)
    return data


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


def list_files(directory_path):
    """
    List all the pathnames of files in the specified directory.

    Parameters:
    directory_path (str): The path to the directory.

    Returns:
    list: A list of full pathnames of the files in the directory.
    """
    try:
        # Convert the directory path to a Path object
        directory = Path(directory_path)
        
        if not directory.exists():
            print(f"The directory '{directory_path}' does not exist.")
            return []

        if not directory.is_dir():
            print(f"The path '{directory_path}' is not a directory.")
            return []

        # Get all file paths in the directory
        files = [str(file) for file in directory.iterdir() if file.is_file()]
        return files
    except PermissionError:
        print(f"Permission denied to access the directory '{directory_path}'.")
        return []

