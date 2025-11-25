from pathlib import Path

import yaml

from study_loader import load_studies_from_ledger


def test_load_studies_from_ledger(tmp_path):
    ledger = {
        "studies": [
            {
                "dv_path": "C:/temp/a.dss",
                "sv_path": "C:/temp/a_sv.dss",
                "alias": "A",
                "assumptions": "Test",
                "climate": "Current",
                "color": 1,
            },
            {
                "dv_path": "C:/temp/b.dss",
                "sv_path": "C:/temp/b_sv.dss",
                "alias": "B",
                "assumptions": "Alt",
                "climate": "Future",
                "color": 2,
            },
        ]
    }
    ledger_file = tmp_path / "ledger.yaml"
    ledger_file.write_text(yaml.safe_dump(ledger))

    studies = load_studies_from_ledger(str(ledger_file))
    assert len(studies) == 2
    assert studies[0].alias == "A"
    assert studies[1].dv_path == "C:/temp/b.dss"