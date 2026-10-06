#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MergeJobs.py -- Merge the ROOT files produced by HSCP jobs with hadd.

USAGE
    python3 MergeJobs.py data   <inputDir>
    python3 MergeJobs.py signal <version>

INPUT
    data mode
        <inputDir> : production directory, relative to
                     /opt/sbg/cms/ui3_data1/gcoulon/HSCP_prod (or an absolute path)
        Expected layout:
            <inputDir>/<subDir>/Histos*.root

    signal mode
        <version>  : version without the "V" (e.g. 12 -> directory V12), looked up in
                     /scratch/ui3_1/gcoulon/HSCP_prod/SIGNAL
        Expected layout:
            V<version>/<prod>_<date>_<time>/*.root

OUTPUT
    One merged file per sub-directory, written next to the sub-directories:
        data   : <inputDir>/<subDir>_merged.root
                 (histograms only: TTrees are not merged, -T option)
        signal : V<version>/<prod>_merged.root
                 (date and time stripped from the sub-directory name)
    An existing *_merged.root is deleted and recreated.
    The sub-directories are never modified.
    Exit code: 0 if everything went fine, 1 if at least one hadd failed.
"""

import argparse
import glob
import os
import shutil
import subprocess
import sys

MERGED_SUFFIX = "_merged.root"

# Settings specific to each production type:
#   base_dir        : root in which the directory given as argument is looked up
#   target_prefix   : prefix added to the argument to get the directory name
#   pattern         : files to merge in each sub-directory
#   hadd_options    : options passed to hadd
#   strip_timestamp : remove the trailing "_<date>_<time>" from the sub-directory name
MODES = {
    "data": {
        "base_dir": "/opt/sbg/cms/ui3_data1/gcoulon/HSCP_prod",
        "target_prefix": "",
        "pattern": "Histos*.root",
        # -j 16: parallel merge on 16 processes; -T: do not merge TTrees
        "hadd_options": ["-j", "16", "-T"],
        "strip_timestamp": False,
    },
    "signal": {
        "base_dir": "/scratch/ui3_1/gcoulon/HSCP_prod/SIGNAL",
        "target_prefix": "V",
        "pattern": "*.root",
        "hadd_options": [],
        "strip_timestamp": True,
    },
}


def output_name(subdir, strip_timestamp):
    """Name (without suffix) of the merged file associated with a sub-directory."""
    if strip_timestamp:
        # Drop the last 2 fields (date + time), keep the rest
        return "_".join(subdir.split("_")[:-2])
    return subdir


def merge_subdir(parent_dir, subdir, cfg):
    """
    Merge the ROOT files of parent_dir/subdir into parent_dir/<name>_merged.root.
    Returns "merged", "skipped" (nothing to merge) or "failed" (hadd failed).
    """
    sub_path = os.path.join(parent_dir, subdir)

    # Files to merge, excluding any leftover merged file
    inputs = sorted(
        os.path.basename(f)
        for f in glob.glob(os.path.join(sub_path, cfg["pattern"]))
        if not f.endswith(MERGED_SUFFIX)
    )
    if not inputs:
        print("No {} files found in {}, skipping.".format(cfg["pattern"], sub_path))
        return "skipped"

    merged_file = os.path.join(
        parent_dir, output_name(subdir, cfg["strip_timestamp"]) + MERGED_SUFFIX
    )

    print("")
    print("         >> Merging {} files from {} -> {}".format(len(inputs), subdir, merged_file))
    print("")

    if os.path.exists(merged_file):
        print("Deleting existing {} before merging.".format(merged_file))
        os.remove(merged_file)

    # hadd runs from the sub-directory (cwd): input files are given as relative paths,
    # which keeps the command line short even with many jobs.
    # The output is written directly in the parent directory (no mv needed).
    command = ["hadd"] + cfg["hadd_options"] + [merged_file] + inputs
    try:
        subprocess.check_call(command, cwd=sub_path)
    except subprocess.CalledProcessError as e:
        print("hadd failed for {}: {}".format(sub_path, e))
        # Do not leave an incomplete merged file behind
        if os.path.exists(merged_file):
            os.remove(merged_file)
        return "failed"

    return "merged"


def main():
    parser = argparse.ArgumentParser(
        description="Merge the ROOT files of HSCP jobs (data or signal) with hadd.",
        epilog="Examples:\n"
               "  python3 %(prog)s data <inputDir>\n"
               "  python3 %(prog)s signal <version>",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("mode", choices=sorted(MODES), help="production type to merge")
    parser.add_argument(
        "target",
        help="data: production directory (relative to the data base directory, or absolute); "
             "signal: version without the 'V'",
    )
    args = parser.parse_args()

    # Without ROOT in the environment there is no point going further
    if shutil.which("hadd") is None:
        sys.exit("hadd not found: set up ROOT (e.g. cmsenv) before running this script.")

    cfg = MODES[args.mode]
    parent_dir = os.path.join(cfg["base_dir"], cfg["target_prefix"] + args.target)

    if not os.path.isdir(parent_dir):
        sys.exit("Directory does not exist: {}".format(parent_dir))

    # Only sub-directories are processed: plain files (including existing
    # *_merged.root files) are ignored
    subdirs = sorted(
        d for d in os.listdir(parent_dir) if os.path.isdir(os.path.join(parent_dir, d))
    )

    # Two sub-directories giving the same output name (same prod submitted twice,
    # only date/time differ) overwrite each other: only the last one processed is kept.
    by_output = {}
    for subdir in subdirs:
        by_output.setdefault(output_name(subdir, cfg["strip_timestamp"]), []).append(subdir)
    for name, dirs in sorted(by_output.items()):
        if len(dirs) > 1:
            print("WARNING: {} all write to {}{} -> only {} will be kept.".format(
                ", ".join(dirs), name, MERGED_SUFFIX, dirs[-1]))

    n_merged = 0
    failed = []
    for subdir in subdirs:
        status = merge_subdir(parent_dir, subdir, cfg)
        if status == "merged":
            n_merged += 1
        elif status == "failed":
            failed.append(subdir)

    # Summary: failures are listed so that only what is missing needs to be rerun
    print("")
    print("Done: {} merged, {} failed.".format(n_merged, len(failed)))
    for subdir in failed:
        print("  FAILED: {}".format(subdir))

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())