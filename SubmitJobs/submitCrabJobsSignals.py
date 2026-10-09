"""
submitCrabJobsSignals.py -- CRAB submission of the HSCP ntuplizer on signal simulation (MiniAODSIM)

For each dataset of `datasetList`, the script fills a CRAB configuration from the
template defined below, submits it with `crab submit`, and keeps the configuration in
submittedConfigs/.

Usage
-----
    python3 submitCrabJobsSignals.py <codeVersion>

<codeVersion> is the version tag of the ntuple production, without the leading "V"
(e.g. 21p0). It goes into the CRAB request name, Analysis_<sample>_CodeV<codeVersion>,
which is also the name of the output directory on the storage site.
Tags read by TupleAnalysis (cfg/configFile.txt) in October 2026:
Run 2 gluino V13p2, Run 3 gluino V19p0 and V19p12, stau V20p0, stop V21p0.

Before launching
----------------
Launch the script from the directory that contains HSCPAnalysis/ (the src/ directory
of the CMSSW release), after these steps, in this order:

 1. Move the limit-setting packages out of the release BEFORE building, so that they
    are not compiled with it nor packed into the CRAB sandbox:
        mv HiggsAnalysis ../.. && mv CombineHarvester ../..
    (they end up next to the CMSSW_X_Y_Z directory; move them back and rebuild to
    compute limits again)
 2. Set up and build the release:
        cmsenv
        scram b -j 8
 3. Get a grid proxy, valid 8 days:
        voms-proxy-init --rfc --voms cms -valid 192:00
 4. Leave exactly one `datasetList` block uncommented below (see "Dataset lists").
 5. For the Run 2 list only, switch the template to 2018 (see "Things to know").

Files read by the script
------------------------
All paths are relative to the launch directory, so all of them must be reachable from
the place where this script sits.

    ntuplizer_cfg.py
        cmsRun configuration of the ntuplizer; read next to this script, not inside
        HSCPAnalysis/
    HSCPAnalysis/Ntuplizer/data/template/template_Run3.root
        dE/dx templates, shipped with the jobs
    HSCPAnalysis/Ntuplizer/data/template/SF_dEdx_Run3.txt
        dE/dx scale factors, shipped with the jobs
    HSCPAnalysis/Ntuplizer/data/pileup/mix_2024_25ns_RunIII2024Summer24_PoissonOOTPU_cfi-100bins.root
        pileup profile of the Summer24 simulation
    HSCPAnalysis/Ntuplizer/data/pileup/dataPileupHistogram-2024BCDEFGHI-69200ub.root
    HSCPAnalysis/Ntuplizer/data/pileup/dataPileupHistogram-2024BCDEFGHI-72400ub.root
    HSCPAnalysis/Ntuplizer/data/pileup/dataPileupHistogram-2024BCDEFGHI-66000ub.root
        pileup profiles of the 2024 data for a minimum-bias cross section of
        69.2 mb (nominal), 72.4 mb and 66.0 mb (variations)

For the Run 2 list, the commented `inputFiles` line of the template is used instead:

    HSCPAnalysis/Ntuplizer/data/template/template_Run2_MC.root
    HSCPAnalysis/Ntuplizer/data/template/SF_dEdx_Run3.txt
    HSCPAnalysis/Ntuplizer/data/pileup/mix_2018_25ns_UltraLegacy_PoissonOOTPU_cfi-99bins.root
    HSCPAnalysis/Ntuplizer/data/pileup/PileupHistogram-goldenJSON-13tev-2018-69200ub-99bins.root
    HSCPAnalysis/Ntuplizer/data/pileup/PileupHistogram-goldenJSON-13tev-2018-72400ub-99bins.root
    HSCPAnalysis/Ntuplizer/data/pileup/PileupHistogram-goldenJSON-13tev-2018-66000ub-99bins.root

What the script writes
----------------------
    crab_projects/crab_Analysis_<sample>_CodeV<codeVersion>/
        CRAB project directory of each dataset (crab status / resubmit -d ...)
    submittedConfigs/4crab_Signal_toSubmit.py
        CRAB configuration of the last dataset submitted
    /store/user/gcoulon/HSCP/<primary dataset>/Analysis_<sample>_CodeV<codeVersion>/<date>/
        ntuples, on T2_FR_IPHC
    4crab_Signal_Template.py, 4crab_Signal_toSubmit.py
        temporary files in the launch directory, removed at the end

Dataset lists
-------------
Five lists are defined: Run 2 gluino (UL18, 13 TeV, madgraph; 12 mass points), Run 3
gluino generated with pythia8 (9), Run 3 gluino generated with madgraphMLM (10), Run 3
pair-produced stau (11) and Run 3 stop (12). The Run 3 lists belong to the
RunIII2024Summer24MiniAODv6 campaign. A list is switched off by enclosing it in triple
quotes. When this header was written, the stop list was the active one.

Things to know
--------------
- <sample> is the name of the primary dataset up to "_TuneCP5", e.g.
  HSCP-Stop_Par-M-1000. For samples of another tune, use the commented
  `shortSampleName` line (TuneCP2) instead.
- The generator is not part of <sample>: the pythia8 and madgraphMLM gluino datasets of
  the same mass (1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600 GeV) get the same
  request name. Submit the two lists with different <codeVersion>, otherwise
  `crab submit` refuses the second one (project directory already exists).
- The template is set for Run 3 (year=2024, 2024 pileup, template_Run3.root). For the
  Run 2 list, comment the active `inputFiles` and `pyCfgParams` lines of the template
  and uncomment the two below them (year=2018). Nothing checks that the template
  matches the list: left as is, Run 2 samples are submitted with year=2024.
- One file per job (unitsPerJob = 1).
- The configuration is always moved to submittedConfigs/4crab_Signal_toSubmit.py: each
  dataset overwrites the previous one, and so does the next run. Only the last
  configuration submitted is kept, and its file name does not carry the version.
- The return code of `crab submit` is not checked: the configuration is moved to
  submittedConfigs/ even when the submission failed. Read the terminal output, or
  check with `crab status -d crab_projects/crab_<request name>`.
- 4crab_Signal_Template.py is written only if it does not exist yet, and removed at the
  end. After an interrupted run (Ctrl-C, crash), delete it by hand: otherwise the next
  run silently reuses the old template, whatever was changed in this script.
- The output directory (/store/user/gcoulon/HSCP) and the storage site (T2_FR_IPHC) are
  hard-coded in the template: change both to run under another account.
- Without argument the script stops on an IndexError; the usage line is only printed
  with -h.
"""
import sys, os, time, re
import numpy as np
#from common_functions import *
from optparse import OptionParser
parser = OptionParser(usage="Usage: python %prog codeVersion")
(opt,args) = parser.parse_args()

# ---------------------------------------------------------------------------
# Dataset lists: leave exactly one block uncommented (see the header).
# ---------------------------------------------------------------------------

# Gluino Run2 madgraph
'''
datasetList = [
#"/HSCPgluino_M-2000_TuneCP5_13TeV_madgraph-pythia8/RunIISummer20UL18RECO-106X_upgrade2018_realistic_v11_L1v1-v2/AODSIM",
"/HSCPgluino_M-1000_TuneCP5_13TeV_madgraph-pythia8/RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2/MINIAODSIM",
"/HSCPgluino_M-1100_TuneCP5_13TeV_madgraph-pythia8/RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2/MINIAODSIM",
"/HSCPgluino_M-1200_TuneCP5_13TeV_madgraph-pythia8/RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2/MINIAODSIM",
"/HSCPgluino_M-1300_TuneCP5_13TeV_madgraph-pythia8/RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2/MINIAODSIM",
"/HSCPgluino_M-1400_TuneCP5_13TeV_madgraph-pythia8/RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2/MINIAODSIM",
"/HSCPgluino_M-1500_TuneCP5_13TeV_madgraph-pythia8/RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2/MINIAODSIM",
"/HSCPgluino_M-1600_TuneCP5_13TeV_madgraph-pythia8/RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2/MINIAODSIM",
"/HSCPgluino_M-1800_TuneCP5_13TeV_madgraph-pythia8/RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2/MINIAODSIM",
"/HSCPgluino_M-2000_TuneCP5_13TeV_madgraph-pythia8/RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2/MINIAODSIM",
"/HSCPgluino_M-2200_TuneCP5_13TeV_madgraph-pythia8/RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2/MINIAODSIM",
"/HSCPgluino_M-2400_TuneCP5_13TeV_madgraph-pythia8/RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2/MINIAODSIM",
"/HSCPgluino_M-2600_TuneCP5_13TeV_madgraph-pythia8/RunIISummer20UL18MiniAODv2-106X_upgrade2018_realistic_v16_L1v1-v2/MINIAODSIM",
]
'''

# Gluino Run3 pythia
'''
datasetList = [
"/HSCP-Gluino_Par-M-1000_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/HSCP-Gluino_Par-M-1200_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/HSCP-Gluino_Par-M-1400_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/HSCP-Gluino_Par-M-1600_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/HSCP-Gluino_Par-M-1800_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/HSCP-Gluino_Par-M-2000_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/HSCP-Gluino_Par-M-2200_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/HSCP-Gluino_Par-M-2400_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/HSCP-Gluino_Par-M-2600_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM"
]
'''

# Gluino Run3 madgraph
'''
datasetList = [
"/HSCP-Gluino_Par-M-1100_TuneCP5_13p6TeV_madgraphMLM-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v4/MINIAODSIM",
"/HSCP-Gluino_Par-M-1200_TuneCP5_13p6TeV_madgraphMLM-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v4/MINIAODSIM",
"/HSCP-Gluino_Par-M-1300_TuneCP5_13p6TeV_madgraphMLM-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v4/MINIAODSIM",
"/HSCP-Gluino_Par-M-1400_TuneCP5_13p6TeV_madgraphMLM-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v4/MINIAODSIM",
"/HSCP-Gluino_Par-M-1600_TuneCP5_13p6TeV_madgraphMLM-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v4/MINIAODSIM",
"/HSCP-Gluino_Par-M-1800_TuneCP5_13p6TeV_madgraphMLM-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v4/MINIAODSIM",
"/HSCP-Gluino_Par-M-2000_TuneCP5_13p6TeV_madgraphMLM-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v4/MINIAODSIM",
"/HSCP-Gluino_Par-M-2200_TuneCP5_13p6TeV_madgraphMLM-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v4/MINIAODSIM",
"/HSCP-Gluino_Par-M-2400_TuneCP5_13p6TeV_madgraphMLM-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v4/MINIAODSIM",
"/HSCP-Gluino_Par-M-2600_TuneCP5_13p6TeV_madgraphMLM-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v4/MINIAODSIM",
]
'''


# Pair-Stau Run3
'''
datasetList = [
"/HSCP-Pair-Stau_Par-M-1029_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/HSCP-Pair-Stau_Par-M-1218_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/HSCP-Pair-Stau_Par-M-1409_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/HSCP-Pair-Stau_Par-M-1599_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/HSCP-Pair-Stau_Par-M-247_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/HSCP-Pair-Stau_Par-M-308_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/HSCP-Pair-Stau_Par-M-432_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/HSCP-Pair-Stau_Par-M-557_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/HSCP-Pair-Stau_Par-M-651_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/HSCP-Pair-Stau_Par-M-745_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/HSCP-Pair-Stau_Par-M-871_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
]
'''

# Stop Run3

datasetList = [
"/HSCP-Stop_Par-M-700_TuneCP5_13p6TeV_madgraphMLM-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v4/MINIAODSIM",
"/HSCP-Stop_Par-M-800_TuneCP5_13p6TeV_madgraphMLM-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v4/MINIAODSIM",
"/HSCP-Stop_Par-M-900_TuneCP5_13p6TeV_madgraphMLM-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v4/MINIAODSIM",
"/HSCP-Stop_Par-M-1000_TuneCP5_13p6TeV_madgraphMLM-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v4/MINIAODSIM",
"/HSCP-Stop_Par-M-1200_TuneCP5_13p6TeV_madgraphMLM-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v4/MINIAODSIM",
"/HSCP-Stop_Par-M-1400_TuneCP5_13p6TeV_madgraphMLM-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v4/MINIAODSIM",
"/HSCP-Stop_Par-M-1600_TuneCP5_13p6TeV_madgraphMLM-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v4/MINIAODSIM",
"/HSCP-Stop_Par-M-1800_TuneCP5_13p6TeV_madgraphMLM-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v4/MINIAODSIM",
"/HSCP-Stop_Par-M-2000_TuneCP5_13p6TeV_madgraphMLM-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v4/MINIAODSIM",
"/HSCP-Stop_Par-M-2200_TuneCP5_13p6TeV_madgraphMLM-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v4/MINIAODSIM",
"/HSCP-Stop_Par-M-2400_TuneCP5_13p6TeV_madgraphMLM-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v4/MINIAODSIM",
"/HSCP-Stop_Par-M-2600_TuneCP5_13p6TeV_madgraphMLM-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v4/MINIAODSIM",
]


# ---------------------------------------------------------------------------
# Production version tag: first command-line argument, without the leading "V".
# ---------------------------------------------------------------------------
codeVersion = sys.argv[1]
#just the number, like 18p2


# Directory where the submitted CRAB configuration is kept.
if not os.path.exists("submittedConfigs"): os.makedirs("submittedConfigs")


# ---------------------------------------------------------------------------
# CRAB configuration template, written to 4crab_Signal_Template.py.
#
# Placeholders replaced with sed for each dataset, in this order:
#   VERSION  -> codeVersion
#   NAME     -> short sample name (primary dataset up to "_TuneCP5")
#   DATASET  -> full DAS name of the dataset
#
# Main settings:
#   psetName          ntuplizer_cfg.py, taken from the launch directory
#   pyCfgParams       options given to ntuplizer_cfg.py (MiniAOD input, simulation,
#                     year 2024, CRAB mode)
#   inputFiles        files shipped with every job (dE/dx and pileup)
#   The two commented lines under them are the Run 2 (2018) versions of inputFiles
#   and pyCfgParams: swap them in for the Run 2 gluino list.
#   splitting         FileBased, 1 file per job
#   outLFNDirBase     /store/user/gcoulon/HSCP, on storageSite T2_FR_IPHC
#   publication       False: the output is not published in DBS
# ---------------------------------------------------------------------------
if not os.path.exists("4crab_Signal_Template.py"):
  TEMPLATE = '''
from CRABClient.UserUtilities import config
config = config()

config.section_('General')
config.General.requestName = 'Analysis_NAME_CodeVVERSION'
config.General.workArea = 'crab_projects'
config.General.transferOutputs = True

config.section_('JobType')
config.JobType.pluginName = 'Analysis'
config.JobType.psetName = 'ntuplizer_cfg.py'
config.JobType.allowUndistributedCMSSW = True
config.JobType.maxMemoryMB = 2500
config.JobType.numCores = 1
config.JobType.inputFiles = ['HSCPAnalysis/Ntuplizer/data/template/template_Run3.root','HSCPAnalysis/Ntuplizer/data/template/SF_dEdx_Run3.txt', 'HSCPAnalysis/Ntuplizer/data/pileup/mix_2024_25ns_RunIII2024Summer24_PoissonOOTPU_cfi-100bins.root', 'HSCPAnalysis/Ntuplizer/data/pileup/dataPileupHistogram-2024BCDEFGHI-69200ub.root', 'HSCPAnalysis/Ntuplizer/data/pileup/dataPileupHistogram-2024BCDEFGHI-72400ub.root', 'HSCPAnalysis/Ntuplizer/data/pileup/dataPileupHistogram-2024BCDEFGHI-66000ub.root']
config.JobType.pyCfgParams = ['isAOD=False','isData=False','year=2024','doCrab=True']
#config.JobType.inputFiles = ['HSCPAnalysis/Ntuplizer/data/template/template_Run2_MC.root','HSCPAnalysis/Ntuplizer/data/template/SF_dEdx_Run3.txt', 'HSCPAnalysis/Ntuplizer/data/pileup/mix_2018_25ns_UltraLegacy_PoissonOOTPU_cfi-99bins.root', 'HSCPAnalysis/Ntuplizer/data/pileup/PileupHistogram-goldenJSON-13tev-2018-69200ub-99bins.root', 'HSCPAnalysis/Ntuplizer/data/pileup/PileupHistogram-goldenJSON-13tev-2018-72400ub-99bins.root', 'HSCPAnalysis/Ntuplizer/data/pileup/PileupHistogram-goldenJSON-13tev-2018-66000ub-99bins.root']
#config.JobType.pyCfgParams = ['isAOD=False','isData=False','year=2018','doCrab=True']

config.section_('Data')
config.Data.inputDataset = 'DATASET'
config.Data.splitting = 'FileBased'
#config.Data.splitting = 'Automatic'
config.Data.unitsPerJob = 1
config.Data.outputDatasetTag = config.General.requestName
config.Data.outLFNDirBase = '/store/user/gcoulon/HSCP'
config.Data.ignoreLocality = False
config.Data.partialDataset = False
config.Data.publication = False

config.section_('Site')
config.Site.whitelist = ['T1_*','T2_*','T3_*']
config.Site.storageSite = 'T2_FR_IPHC'
'''

  with open("4crab_Signal_Template.py", "w") as text_file:
      text_file.write(TEMPLATE)

# ---------------------------------------------------------------------------
# One CRAB task per dataset.
# ---------------------------------------------------------------------------
for i in datasetList:
  print("Submit for sample "+i)
  # Fresh copy of the template, then VERSION.
  os.system("cp 4crab_Signal_Template.py 4crab_Signal_toSubmit.py")

  replaceVERSION_ = "sed -i 's/VERSION/"+codeVersion+"/g' 4crab_Signal_toSubmit.py"
  os.system(replaceVERSION_)

  # NAME: "/HSCP-Stop_Par-M-1000_TuneCP5_13p6TeV_madgraphMLM-pythia8/..." -> "HSCP-Stop_Par-M-1000".
  shortSampleName = i[1:(i.find('TuneCP5'))-1]
  #shortSampleName = i[1:(i.find('TuneCP2'))-1]

  replaceNAME_ = "sed -i 's/NAME/"+shortSampleName+"/g' 4crab_Signal_toSubmit.py"
  os.system(replaceNAME_)

  # DATASET: the slashes of the DAS name are escaped for sed.
  replaceDATASET_ = "sed -i 's/DATASET/"+i.replace("/","\/")+"/g' 4crab_Signal_toSubmit.py"
  os.system(replaceDATASET_)

  # Submit, then keep the configuration (same file name for every dataset).
  os.system("crab submit -c 4crab_Signal_toSubmit.py")
  os.system("mv 4crab_Signal_toSubmit.py submittedConfigs/.")

# Remove the template: it is rewritten at the next run.
os.system("rm 4crab_Signal_Template.py")