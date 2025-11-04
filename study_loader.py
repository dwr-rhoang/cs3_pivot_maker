from collections import namedtuple

import pandas as pd
import yaml
from utils import load_data
from pathlib import Path

# Scenario management
Study = namedtuple("Scenario", ["dv_path", "sv_path", "alias", "assumptions", "climate", "color"])


with open("config/dvars.yaml", "r") as file:
    var_dict_dv = yaml.safe_load(file)
with open("config/svars.yaml", "r") as file:
    var_dict_sv = yaml.safe_load(file)
with open("config/study_ledger.yaml", "r") as file:
    study_ledger = yaml.safe_load(file)
date_map = pd.read_csv("config/date_map.csv", index_col=0, parse_dates=True)

studies = [

    Study(r"C:\dev\calsim3-dcr\DSS\output\DCR2025_DV_9.8.1_Danube_Adj_v4.0_QWEST.dss",
          r"C:\jobs\20230428_DCR23\models\9.3.1_danube_adj\DSS\input\DCR2023_SV_Danube_Adj_v1.8.dss",
          "DCR25_AdjHist_QWEST", "QWEST", "Current", 1)

]


load_data(studies, var_dict_dv, date_map, "dv", "dv_data.csv")
load_data(studies, var_dict_sv, date_map, "sv", "sv_data.csv")
