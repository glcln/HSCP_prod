#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
transfer_prod.py -- Copy a production from dCache into the current directory with gfal-copy.

USAGE
    python3 transfer_prod.py <version> <dataType>

INPUT
    <version>  : code version without the "V" (e.g. 18p1). A task is selected when its
                 name contains exactly V<version>: 19p6 selects ..._CodeV19p6 but not
                 ..._CodeV19p60.
    <dataType> : SingleMu, MET, WJetsToLNu_0J, WJetsToLNu_1J, WJetsToLNu_2J
                 (one dataset each, see DATASETS below), or
                 signal (every dataset whose name contains "HSCP")
    dCache layout scanned:
        <BASE_URL>/<dataset>/<task>/<YYMMDD_HHMMSS>/<000N>/

OUTPUT
    Relative to the current directory. With f1, f2, f3 the "_"-separated fields of the
    task name after the first one (Analysis_SingleMuon_Run2018A_CodeV... -> f1 = SingleMuon,
    f2 = Run2018A):
        data / background : <f1>/<f1>_<f2>/
        signal            : SIGNAL/V<version>/<f2>_V<version>/<f2>_<f3>/
    All <000N> blocks of a task are copied into the same directory.
    If a task has several <YYMMDD_HHMMSS> directories (production submitted more than
    once), each one is copied into its own directory, named as above plus
    _<YYMMDD_HHMMSS>, and a WARNING is printed: nothing is mixed, nothing is dropped.
    Exit code: 0 if something was copied and nothing failed, 1 otherwise
    (the listings and copies that failed are listed at the end).
"""

import os
import re
import subprocess
import sys

BASE_URL = "davs://sbgdcache.in2p3.fr/cms/phedex/store/user/gcoulon/HSCP/"

# <dataType> -> dataset directory under BASE_URL.
# To transfer another dataset, add a line here.
DATASETS = {
    "SingleMu": "SingleMuon",
    "MET": "MET",
    "WJetsToLNu_0J": "WJetsToLNu_0J_TuneCP5_13TeV-amcatnloFXFX-pythia8",
    "WJetsToLNu_1J": "WJetsToLNu_1J_TuneCP5_13TeV-amcatnloFXFX-pythia8",
    "WJetsToLNu_2J": "WJetsToLNu_2J_TuneCP5_13TeV-amcatnloFXFX-pythia8",
}

# <dataType> "signal": every dataset whose name contains this string is scanned.
# Use "ZPrime" for the ZPrime samples (and the ZPrime naming in destination()).
SIGNAL_TAG = "HSCP"

# Listings and copies that failed, reported at the end of the run
FAILURES = []


def run_gfal_ls(url):
    """List a dCache directory. Returns [] (and records the failure) if gfal-ls fails."""
    try:
        output = subprocess.check_output(["gfal-ls", url], stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        print("gfal-ls failed for {}: {}".format(url, e.output.decode(errors="replace").strip()))
        FAILURES.append("gfal-ls {}".format(url))
        return []
    return [line for line in output.decode().splitlines() if line.strip()]


def run_gfal_copy(src, dst):
    """Copy a dCache directory recursively into dst. Returns True if gfal-copy succeeded."""
    if not os.path.exists(dst):
        os.makedirs(dst)
    command = ["gfal-copy", "-r", src, dst]
    print(" ".join(command))
    try:
        subprocess.check_call(command)
        return True
    except subprocess.CalledProcessError as e:
        print("gfal-copy failed for {}: {}".format(src, e))
        FAILURES.append("gfal-copy {} -> {}".format(src, dst))
        return False


def task_matches_version(task, version):
    """
    True if the task name contains exactly V<version>, i.e. not followed by another
    digit or letter: 19p6 matches ..._CodeV19p6 but not ..._CodeV19p60.
    """
    return re.search("V" + re.escape(version) + r"(?![0-9A-Za-z])", task) is not None


def destination(task, version, data_type):
    """Local directory, relative to the current one, into which a task is copied."""
    fields = task.split("_")

    if data_type == "signal":
        # THIS BELOW IS FOR ALL SIGNALS EXCEPT ZPRIME
        direcName = "SIGNAL/V" + version + "/" + fields[2] + "_V" + version
        direcSplit = fields[2] + "_" + fields[3]

        # THIS IS FOR ZPRIME SPECIFICALLY
        # direcName = "_".join(fields[2:6]) + "_V" + version
        # direcSplit = "_".join(fields[2:6])
    else:
        direcName = fields[1]
        direcSplit = fields[1] + "_" + fields[2]

    return os.path.join(direcName, direcSplit)


def transfer_dataset(dataset, version, data_type):
    """
    Copy every task of one dataset whose name matches the version.
    Returns the number of <000N> blocks copied.
    """
    dataset_url = BASE_URL + dataset
    n_copied = 0

    for task in run_gfal_ls(dataset_url):
        if version not in task:
            continue

        # The version must match exactly, not as a substring of a longer one
        if not task_matches_version(task, version):
            print("Ignored (other version): {}".format(task))
            continue

        print("Task: {}".format(task))

        try:
            newDir = destination(task, version, data_type)
        except IndexError:
            print("Unexpected task name, skipped: {}".format(task))
            FAILURES.append("task name {}".format(task))
            continue

        # One <YYMMDD_HHMMSS> directory per submission of the task
        task_url = dataset_url + "/" + task
        timestamps = run_gfal_ls(task_url)

        if len(timestamps) > 1:
            print("WARNING: {} was submitted {} times ({}). Each submission is copied to "
                  "its own directory {}_<YYMMDD_HHMMSS>: keep the one you want.".format(
                      task, len(timestamps), ", ".join(timestamps), newDir))

        for timestamp in timestamps:
            # Usual case, one submission: <newDir>/. Otherwise: <newDir>_<timestamp>/
            target = newDir if len(timestamps) == 1 else newDir + "_" + timestamp
            print(target)

            # All the <000N> blocks of a submission go into the same directory
            timestamp_url = task_url + "/" + timestamp
            for block in run_gfal_ls(timestamp_url):
                if run_gfal_copy(timestamp_url + "/" + block + "/", target + "/"):
                    n_copied += 1

    return n_copied


def main():
    if len(sys.argv) != 3:
        print("Usage: python3 transfer_prod.py <Version> <data type>")
        return 1

    filter_string = sys.argv[1]
    data_type = sys.argv[2]

    # Datasets to scan
    if data_type == "signal":
        # signal_paths = [s for s in all_MC if "ZPrime" in s]  -> set SIGNAL_TAG = "ZPrime"
        datasets = [s for s in run_gfal_ls(BASE_URL) if SIGNAL_TAG in s]
    elif data_type in DATASETS:
        datasets = [DATASETS[data_type]]
    else:
        print("Unknown data type: {}".format(data_type))
        print("Known data types: {}, signal".format(", ".join(sorted(DATASETS))))
        return 1

    n_copied = 0
    for dataset in datasets:
        n_copied += transfer_dataset(dataset, filter_string, data_type)

    # Summary, so that a failed listing or copy cannot go unnoticed
    print("")
    print("Done: {} block(s) copied, {} failure(s).".format(n_copied, len(FAILURES)))
    for failure in FAILURES:
        print("  FAILED: {}".format(failure))
    if n_copied == 0 and not FAILURES:
        print("No task matching V{} was found for {}.".format(filter_string, data_type))

    return 0 if n_copied > 0 and not FAILURES else 1


if __name__ == "__main__":
    sys.exit(main())