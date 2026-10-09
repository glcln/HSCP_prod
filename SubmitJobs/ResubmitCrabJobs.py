#!/usr/bin/env python3
"""
ResubmitCrabJobs.py -- resubmit the failed jobs of the CRAB tasks of one production

Replaces the former pair ResubmitCrabJobs.py (one pass) and AutoResubmitCrabJobs.sh
(one pass per hour).

For every CRAB project directory of crab_projects/ whose name ends with
CodeV<codeVersion>, the script runs `crab resubmit --maxmemory 2500 <project>`. With
<hours>, it does so once per hour.

Usage
-----
    python3 ResubmitCrabJobs.py <codeVersion> [<hours>]

    <codeVersion>   version tag of the production, as given to the submitCrabJobs*.py
                    scripts, without the leading "V" (e.g. 18p2)
    <hours>         number of passes, one per hour (default 1: a single pass, no wait)

    python3 ResubmitCrabJobs.py 18p2         one pass
    python3 ResubmitCrabJobs.py 18p2 48      48 passes, one per hour

Note that the version comes first: the old AutoResubmitCrabJobs.sh took
<hours> <codeVersion>.

Before launching
----------------
Launch the script from the directory that contains crab_projects/ (the one from which
the submitCrabJobs*.py scripts were launched), with the CMSSW environment set and a
grid proxy:
        cmsenv
        voms-proxy-init --rfc --voms cms -valid 192:00
The proxy must stay valid until the last pass. For a long loop, run the script in
screen or tmux so that it survives the end of the terminal session.

Things to know
--------------
- The version must match exactly: only the project names that end with
  CodeV<codeVersion> are taken (18p1 does not select 18p10). StatusCrabJobs.py and
  crab_report_lumi.sh select the tasks in the same way. The old script searched the
  version anywhere in the name.
- The projects selected are listed at the start of each pass.
- crab_projects/ is read again at each pass, so tasks submitted in the meantime are
  picked up.
- <hours> passes are separated by <hours>-1 waits of one hour. The time taken by the
  passes themselves comes on top: the passes drift, and the script ends a bit after
  <hours>-1 hours.
- --maxmemory 2500 is the value of maxMemoryMB in the submission templates.
- The return code of `crab resubmit` is not checked: read the output.
- Ctrl-C stops the script, also during a `crab resubmit`.
"""
import argparse
import os
import shutil
import subprocess
import sys
import time

WORK_AREA = "crab_projects"   # config.General.workArea of the submission templates
MAX_MEMORY_MB = "2500"        # same as config.JobType.maxMemoryMB in the templates
WAIT_SECONDS = 3600           # time between two passes


def say(text=""):
    """print, flushed at once so that the lines stay in order with the output of crab."""
    print(text, flush=True)


def find_projects(code_version):
    """Project directories of WORK_AREA whose name ends with CodeV<code_version>, in alphabetical order."""
    projects = []
    for name in sorted(os.listdir(WORK_AREA)):
        if not os.path.isdir(os.path.join(WORK_AREA, name)):
            continue
        if name.endswith("CodeV" + code_version):
            projects.append(os.path.join(WORK_AREA, name))
    return projects


def resubmit(projects):
    """One `crab resubmit` per project directory."""
    for project in projects:
        say()
        say("   Resubmitting: " + project)
        subprocess.call(["crab", "resubmit", "--maxmemory", MAX_MEMORY_MB, project])


def main():
    parser = argparse.ArgumentParser(
        description="Resubmit the failed jobs of the CRAB tasks of one production.")
    parser.add_argument("codeVersion",
                        help="version tag of the production, without the leading V (e.g. 18p2)")
    parser.add_argument("hours", nargs="?", type=int, default=1,
                        help="number of passes, one per hour (default: 1, a single pass)")
    args = parser.parse_args()

    if args.hours < 1:
        parser.error("<hours> must be at least 1")
    if not os.path.isdir(WORK_AREA):
        sys.exit("No " + WORK_AREA + "/ here: launch the script from the directory that contains it.")
    if shutil.which("crab") is None:
        sys.exit("crab not found: set the CMSSW environment first (cmsenv).")

    for i in range(args.hours):
        projects = find_projects(args.codeVersion)
        say()
        say("Pass {}/{} at {}: {} project(s) for version '{}'".format(
            i + 1, args.hours, time.strftime("%H:%M:%S"), len(projects), args.codeVersion))
        for project in projects:
            say("   " + project)
        resubmit(projects)

        if i + 1 < args.hours:
            say()
            say("Waiting one hour for the next pass, " + time.strftime("%H:%M:%S"))
            time.sleep(WAIT_SECONDS)

    say()
    say("Done: {} pass(es).".format(args.hours))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        say()
        say("Interrupted.")
        sys.exit(130)