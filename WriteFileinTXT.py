#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WriteFileinTXT.py -- List one dCache directory and append its ROOT files to a .txt.

USAGE
    python3 WriteFileinTXT.py "gfal-ls davs://<host>/<path>/<000N>" <output.txt>

INPUT
    "gfal-ls davs://..." : the gfal-ls command listing one job directory, in quotes
    <output.txt>         : file list to fill; its directory must already exist

OUTPUT
    One line per .root file found, appended to <output.txt>:
        root://<host>/<path>/<000N>/<file>.root
    Entries that are not .root files (e.g. a log/ sub-directory) are skipped.
    Nothing is written if gfal-ls fails or finds no .root file.
    Lines are appended: running the same command twice duplicates them.
    Exit code: 0 if lines were written, 1 otherwise.
"""

import os
import shlex
import subprocess
import sys


def error(message):
    print("ERROR: " + message, file=sys.stderr)


def parse_command(input_command):
    """
    Split the "gfal-ls davs://..." string.
    Returns (command as a list, root:// URL of the listed directory), or None if the
    string is not of that form.
    """
    parts = shlex.split(input_command)
    if len(parts) != 2 or parts[0] != "gfal-ls" or not parts[1].startswith("davs://"):
        return None
    # Same path, read through XRootD instead of WebDAV. The trailing "/" is dropped so
    # that the lines written never contain "<000N>//<file>".
    root_url = "root" + parts[1][len("davs"):].rstrip("/")
    return parts, root_url


def main():
    if len(sys.argv) != 3:
        print('Usage: python3 WriteFileinTXT.py "gfal-ls davs://..." <output.txt>')
        return 1

    input_command = sys.argv[1]
    output_file = sys.argv[2]

    parsed = parse_command(input_command)
    if parsed is None:
        error('first argument must be "gfal-ls davs://...", got: {}'.format(input_command))
        return 1
    command, root_url = parsed

    output_dir = os.path.dirname(output_file)
    if output_dir and not os.path.isdir(output_dir):
        error("output directory does not exist: {} (create it with mkdir -p)".format(output_dir))
        return 1

    # Run gfal-ls and check its exit code: if the listing fails (expired proxy, wrong
    # path), nothing must end up in the list
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                   universal_newlines=True)
    except OSError as e:
        error("cannot run gfal-ls: {}".format(e))
        return 1
    stdout, stderr = process.communicate()

    if process.returncode != 0:
        error("gfal-ls failed (exit code {}), nothing written to {}".format(
            process.returncode, output_file))
        error("  command: {}".format(input_command))
        if stderr.strip():
            error("  " + stderr.strip())
        return 1

    # Keep the ROOT files only
    entries = [line.strip() for line in stdout.splitlines() if line.strip()]
    root_files = [entry for entry in entries if entry.endswith(".root")]
    skipped = [entry for entry in entries if not entry.endswith(".root")]

    if skipped:
        print("Skipped (not a .root file): {}".format(", ".join(skipped)))

    if not root_files:
        error("no .root file found in {}, nothing written to {}".format(root_url, output_file))
        return 1

    print("Writing {} line(s) to file: {}".format(len(root_files), output_file))

    # Append mode: the file is created if it does not exist yet
    with open(output_file, 'a') as f:
        for name in root_files:
            f.write(root_url + '/' + name + '\n')

    return 0


if __name__ == "__main__":
    sys.exit(main())