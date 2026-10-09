"""
StatusCrabJobs.py -- status of the CRAB tasks of one production

For every project directory of crab_projects/ whose name ends with CodeV<codeVersion>,
the script runs `crab status --verboseErrors -d <project>`: state of the task, number of
jobs in each state and, for the failed jobs, the error messages.

Usage
-----
    python3 StatusCrabJobs.py <codeVersion>

    <codeVersion>   version tag of the production, as given to the submitCrabJobs*.py
                    scripts, without the leading "V" (e.g. 18p2)

To keep the output of all the tasks:
    python3 StatusCrabJobs.py 18p2 2>&1 | tee status_18p2.log

Before launching
----------------
Launch the script from the directory that contains crab_projects/ (the one from which
the submitCrabJobs*.py scripts were launched), with the CMSSW environment set and a
grid proxy:
        cmsenv
        voms-proxy-init --rfc --voms cms -valid 192:00

Things to know
--------------
- The version must match exactly: only the project names that end with
  CodeV<codeVersion> are taken (18p1 does not select 18p10). ResubmitCrabJobs.py and
  crab_report_lumi.sh select the tasks in the same way.
- The tasks come in the order returned by os.listdir, which is not alphabetical.
- Without argument the script stops on an IndexError; the usage line is only printed
  with -h.
- The commented `outTask` line is the short form, without the error messages.
"""
import sys, os
from optparse import OptionParser
from threading import Thread

parser = OptionParser(usage="Usage: python3 %prog codeVersion")
(opt,args) = parser.parse_args()

# Project directories of the requested version.
datasetList = []

# Production version tag: first command-line argument, without the leading "V".
codeVersion = sys.argv[1]
#just the number, like 18p2

# Keep the directories of crab_projects/ whose name ends with CodeV<codeVersion>.
for fname in os.listdir("crab_projects") :

  if (fname.endswith("CodeV"+codeVersion)):
    datasetList.append("crab_projects/"+fname)

# One `crab status` per task; --verboseErrors prints the error messages of the failed jobs.
for i in datasetList:
  outTask = "crab status --verboseErrors -d "+i
  #outTask = "crab status "+i
  os.system(outTask)