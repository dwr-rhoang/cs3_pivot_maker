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

    Study(r"C:\jobs\20251020_Alt5\_models\DCR_9.8.0_SDR_Off\DSS\output\DCR2025_DV_9.8.0_Danube_Adj_v4.0_OMRbase2.dss",
          r"C:\jobs\20251020_Alt5\_models\DCR_9.8.0_SDR_Off\DSS\input\DCR2025_SV_Danube_Adj_v4.0.dss",
          "DCR25_AdjHist_noSDR", "DCR25", "Current", 1)
    Study(r"C:\jobs\20251020_Alt5\_models\Alt5_1.3.2\DSS\output\Alt5_1.3.2_adjHist.dss",
          r"C:\jobs\20251020_Alt5\_models\Alt5_1.3.2\DSS\input\DCR2025_SV_Danube_Adj_v4.0.dss",
          "Alt5_1.3.2", "Alt5", "Current", 1)


]


load_data(studies, var_dict_dv, date_map, "dv", "dv_data.csv")
load_data(studies, var_dict_sv, date_map, "sv", "sv_data.csv")
