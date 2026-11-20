#!/usr/bin/env python3
"""Read the half-hourly FLUXNET data needed for Block 4."""

import re
import zipfile
from pathlib import Path

import pandas as pd


KEEP_COLUMNS = [
    "TIMESTAMP_START",
    "TIMESTAMP_END",
    "TA_F",
    "SW_IN_F",
    "VPD_F",
    "P_F",
    "NETRAD",
    "G_F_MDS",
    "H_F_MDS",
    "H_F_MDS_QC",
    "LE_F_MDS",
    "LE_F_MDS_QC",
    "NEE_VUT_REF",
    "NEE_VUT_REF_QC",
    "NEE_CUT_REF",
    "NEE_CUT_REF_QC",
    "GPP_NT_VUT_REF",
    "RECO_NT_VUT_REF",
]


def site_id_from_hh_name(hh_name: str) -> str:
    """Extract the site ID from a FLUXNET half-hourly member name."""
    match = re.search(r"^[^_]+_([^_]+)_FLUXNET_FLUXMET_HH_", hh_name)
    if not match:
        raise ValueError(f"Unrecognised FLUXMET_HH filename: {hh_name}")
    return match.group(1)


def read_hh(zip_file: str | Path) -> pd.DataFrame:
    """Read the selected half-hourly columns from one FLUXNET ZIP file."""
    zip_path = Path(zip_file)
    with zipfile.ZipFile(zip_path) as archive:
        hh_names = [name for name in archive.namelist() if "FLUXMET_HH" in name]
        if not hh_names:
            raise ValueError(f"No FLUXMET_HH file found in {zip_path.name}")
        if len(hh_names) > 1:
            raise ValueError(f"Multiple FLUXMET_HH files found in {zip_path.name}")

        hh_name = hh_names[0]
        with archive.open(hh_name) as source:
            hh = pd.read_csv(
                source,
                na_values=[-9999],
                usecols=lambda column: column in KEEP_COLUMNS,
                dtype={"TIMESTAMP_START": "string", "TIMESTAMP_END": "string"},
            )

    hh["time"] = pd.to_datetime(
        hh["TIMESTAMP_START"], format="%Y%m%d%H%M", errors="raise"
    )
    hh["site"] = site_id_from_hh_name(Path(hh_name).name)
    return hh


def read_all_hh(raw_dir: str | Path = "data/raw") -> pd.DataFrame:
    """Read all downloaded FLUXMET_HH files into one table."""
    zip_files = sorted(Path(raw_dir).glob("*.zip"))
    if not zip_files:
        raise FileNotFoundError(f"No FLUXNET ZIP files found in {raw_dir}")
    return pd.concat((read_hh(zip_file) for zip_file in zip_files), ignore_index=True)


if __name__ == "__main__":
    all_hh = read_all_hh()
    print(f"Read {len(all_hh):,} half-hours from {all_hh['site'].nunique()} sites.")
    print(all_hh.groupby("site").size().to_string())
