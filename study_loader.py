from collections import namedtuple
from pathlib import Path

import pandas as pd
import yaml

# Scenario management
Study = namedtuple("Scenario", ["dv_path", "sv_path", "alias", "assumptions", "climate", "color"])

def load_studies_from_ledger(ledger_path: Path | str = "config/study_ledger.yaml") -> list[Study]:
    with open(ledger_path, "r") as fh:
        ledger = yaml.safe_load(fh) or {}
    studies_raw = ledger.get("studies", [])
    studies = []
    for s in studies_raw:
        studies.append(
            Study(
                dv_path=s["dv_path"],
                sv_path=s["sv_path"],
                alias=s.get("alias"),
                assumptions=s.get("assumptions"),
                climate=s.get("climate"),
                color=s.get("color", None),
            )
        )
    return studies

def load_config(config_dir: Path | str = "config"):
    config_dir = Path(config_dir)
    with open(config_dir / "dvars.yaml", "r") as file:
        var_dict_dv = yaml.safe_load(file)
    with open(config_dir / "svars.yaml", "r") as file:
        var_dict_sv = yaml.safe_load(file)
    date_map = pd.read_csv(config_dir / "date_map.csv", index_col=0, parse_dates=True)
    return var_dict_dv, var_dict_sv, date_map

def main(ledger_path="config/study_ledger.yaml", config_dir="config", append: bool = False):
    # import here so tests that import study_loader won't require pandss
    from utils import load_data

    studies = load_studies_from_ledger(ledger_path)
    var_dict_dv, var_dict_sv, date_map = load_config(config_dir)

    load_data(studies, var_dict_dv, date_map, "dv", "dv_data.csv", append=append)
    load_data(studies, var_dict_sv, date_map, "sv", "sv_data.csv", append=append)

if __name__ == "__main__":
    # default: do not append to existing CSVs; set append=True to merge
    main(append=False)
