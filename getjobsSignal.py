#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
getjobsSignal.py -- Copy all signal samples of a code version from dCache with gfal-copy.

USAGE
    python3 getjobsSignal.py <version>

INPUT
    <version> : code version without the "V" (e.g. 21p0)
    dCache layout scanned:
        <BASE_URL>/<dataset containing "HSCP">/<task>/<YYMMDD_HHMMSS>/<000N>/
    A task is selected when its name contains exactly V<version>:
    19p6 selects ..._CodeV19p6 but not ..._CodeV19p60.

OUTPUT
    One directory per production (dataset + submission timestamp):
        <OUTPUT_BASE_DIR>/V<version>/<Model>_<Par-M-mass>_<YYMMDD_HHMMSS>/output_N.root
    where <Model>_<Par-M-mass> is the first two "_"-separated fields of the dataset name.
    All <000N> blocks of a production are copied into the same directory.
    Files already present locally are not overwritten (gfal-copy is run without --force).
    Exit code: 0 if something was copied and nothing failed, 1 otherwise
    (the listings and copies that failed are listed at the end).
"""

import argparse
import os
import re
import subprocess
import sys

OUTPUT_BASE_DIR = "/scratch/ui3_1/gcoulon/HSCP_prod/SIGNAL/"
BASE_URL = 'davs://sbgdcache.in2p3.fr/cms/phedex/store/user/gcoulon/HSCP/'

# Listings and copies that failed, reported at the end of the run
FAILURES = []


def run_gfal_ls(path):
    """List a dCache directory. Returns [] (and records the failure) if gfal-ls fails."""
    try:
        output = subprocess.check_output(['gfal-ls', path], stderr=subprocess.STDOUT)
        return [line.decode() if isinstance(line, bytes) else line for line in output.splitlines()]
    except subprocess.CalledProcessError as e:
        print("Command failed with error: {}".format(e.output))
        FAILURES.append("gfal-ls {}".format(path))
        return []


def run_gfal_copy(src, dst):
    """Copy a dCache directory recursively into dst. Returns True if gfal-copy succeeded."""
    os.makedirs(dst, exist_ok=True)
    try:
        print("Copying {} -> {}".format(src, dst))
        subprocess.check_call(['gfal-copy', '-r', src, dst])
        return True
    except subprocess.CalledProcessError as e:
        print("gfal-copy failed for {}: {}".format(src, e))
        FAILURES.append("gfal-copy {} -> {}".format(src, dst))
        return False


def extract_signal(name):
    """HSCP-Gluino_Par-M-1100_TuneCP5_... -> HSCP-Gluino_Par-M-1100"""
    parts = name.split('_')
    return parts[0] + "_" + parts[1]


def task_matches_version(task, version):
    """
    True if the task name contains exactly V<version>, i.e. not followed by another
    digit or letter: 19p6 matches ..._CodeV19p6 but not ..._CodeV19p60.
    """
    return re.search("V" + re.escape(version) + r"(?![0-9A-Za-z])", task) is not None


def main(search_string):

    version_dir = os.path.join(OUTPUT_BASE_DIR, 'V' + search_string)

    print("Search string for version is {}".format(search_string))

    # 1 : Run the initial gfal-ls command
    initial_output = run_gfal_ls(BASE_URL)

    # 2 : Filter the lines that contain 'HSCP'
    filtered_lines = [line for line in initial_output if 'HSCP' in line]

    print("Filtered lines with substring:")
    print(filtered_lines)

    n_copied = 0

    # 3 : Iterate over each signal hypothesis directory
    for line in filtered_lines:
        second_path = BASE_URL + line
        second_output = run_gfal_ls(second_path)
        signalHypothesis = extract_signal(line)

        for tline in second_output:
            if search_string not in tline:
                continue

            # The version must match exactly, not as a substring of a longer one
            if not task_matches_version(tline, search_string):
                print("Ignored (other version): {}".format(tline))
                continue

            print("Found version match: {}".format(tline))
            third_path = second_path + '/' + tline
            third_output = run_gfal_ls(third_path)

            # 4 : Each sub_item is an individual production for this version
            for sub_item in third_output:
                fourth_path = third_path + '/' + sub_item
                fourth_output = run_gfal_ls(fourth_path)

                for last_item in fourth_output:
                    final_path = fourth_path + '/' + last_item
                    src_path = final_path.replace('davs', 'root')

                    # Production name = signalHypothesis + sub_item for uniqueness
                    prod_name = "{}_{}".format(signalHypothesis, sub_item)
                    dst_path = os.path.join(version_dir, prod_name)

                    # 5 : Copy recursively the production directory
                    if run_gfal_copy(src_path, dst_path):
                        n_copied += 1

    # 6 : Summary, so that a failed listing or copy cannot go unnoticed
    print("")
    print("Done: {} block(s) copied to {}, {} failure(s).".format(n_copied, version_dir, len(FAILURES)))
    for failure in FAILURES:
        print("  FAILED: {}".format(failure))
    if n_copied == 0 and not FAILURES:
        print("No task matching V{} was found.".format(search_string))

    return 0 if n_copied > 0 and not FAILURES else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Copy all signal samples of a code version from dCache.')
    parser.add_argument('search_string', type=str,
                        help='code version without the "V" (e.g. 21p0)')

    args = parser.parse_args()
    sys.exit(main(args.search_string))