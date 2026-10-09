#!/bin/bash
# usage: ./crab_report_lumi.sh 12p31 MET_V12
#
# crab_report_lumi.sh -- luminosity sections processed by one production, copied to lxplus
#
# For every project directory crab_projects/*CodeV<version>, the script runs
# `crab report`, copies the results/processedLumis.json it writes to
# lumis_<version>/<project>.json, then sends these JSON files to lxplus with scp. They
# are the input of the luminosity computation done there.
#
# Usage
# -----
#     ./crab_report_lumi.sh <version> <lxplus directory>
#
#     <version>            version tag of the production, as given to the
#                          submitCrabJobs*.py scripts, without the leading "V"
#                          (e.g. 12p31)
#     <lxplus directory>   directory that receives the JSON files, below
#                          ComputeLumi/ on lxplus (e.g. MET_V12). It must exist.
#
# Before launching
# ----------------
# Launch the script from the directory that contains crab_projects/ (the one from
# which the submitCrabJobs*.py scripts were launched), with the CMSSW environment set
# and a grid proxy:
#         cmsenv
#         voms-proxy-init --rfc --voms cms -valid 192:00
# scp asks for the CERN password unless a Kerberos ticket is available
# (kinit gcoulon@CERN.CH).
#
# What the script writes
# ----------------------
#     crab_projects/<project>/results/
#         files written by `crab report`, among them processedLumis.json
#     lumis_<version>/<project>.json
#         copy of processedLumis.json, one file per task
#     gcoulon@lxplus9.cern.ch:/afs/cern.ch/user/g/gcoulon/ComputeLumi/<lxplus directory>/
#         the same JSON files
#
# Things to know
# --------------
# - Meant for data. processedLumis.json lists the luminosity sections processed by the
#   jobs that finished successfully: run the script once all the jobs are done,
#   otherwise the list is incomplete.
# - The version must match exactly: only the project names that end with
#   CodeV<version> are taken (12p3 does not select 12p31). StatusCrabJobs.py and
#   ResubmitCrabJobs.py select the tasks in the same way.
# - The account and the parent directory on lxplus are set in REMOTE below: change it
#   to send the files to another account.
# - The JSON files of lumis_<version>/ are deleted at the start, so that only the files
#   of this run are sent. Files already on lxplus are not removed: a task that is no
#   longer in crab_projects/ keeps its old JSON file there.
# - A task whose `crab report` fails, or gives no processedLumis.json, is reported with
#   a line starting with "!!" and skipped; the script goes on. If no JSON file was
#   collected at all, nothing is sent and the script exits with code 1.

# Version of the production and destination directory on lxplus (both required).
USAGE="usage: $0 <version> <lxplus directory>, ex: $0 12p31 MET_V12"
VERSION="${1:?$USAGE}"
DESTDIR="${2:?$USAGE}"

# CRAB work area, parent directory on lxplus, local directory for the JSON files.
CRABDIR="crab_projects"
REMOTE="gcoulon@lxplus9.cern.ch:/afs/cern.ch/user/g/gcoulon/ComputeLumi"
DEST="$REMOTE/$DESTDIR/"
OUTDIR="lumis_${VERSION}"

# Local directory, emptied of the JSON files of an earlier run.
mkdir -p "$OUTDIR"
rm -f "$OUTDIR"/*.json

# One `crab report` per task of this version.
for d in "$CRABDIR"/*CodeV${VERSION}; do
    [ -d "$d" ] || continue
    name=$(basename "$d")
    echo "=== crab report on $name ==="
    crab report -d "$d" || { echo "!! report failed for $name"; continue; }

    # Lumis processed by the finished jobs, copied under the name of the task.
    json="$d/results/processedLumis.json"
    if [ -f "$json" ]; then
        cp "$json" "$OUTDIR/${name}.json"
    else
        echo "!! no processedLumis.json for $name"
    fi
done

# Nothing collected: stop here instead of calling scp without files.
if ! ls "$OUTDIR"/*.json > /dev/null 2>&1; then
    echo "!! no JSON file collected for version $VERSION: nothing sent"
    exit 1
fi

# Send the JSON files of this run to lxplus.
echo "=== scp to $DEST ==="
scp "$OUTDIR"/*.json "$DEST"