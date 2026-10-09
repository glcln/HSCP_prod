"""
submitCrabJobsMC.py -- CRAB submission of the HSCP ntuplizer on background simulation (MiniAODSIM)

For each dataset of `datasetList`, the script fills a CRAB configuration from the
template defined below, submits it with `crab submit`, and keeps the configuration in
submittedConfigs/.

Usage
-----
    python3 submitCrabJobsMC.py <codeVersion>

<codeVersion> is the version tag of the ntuple production, without the leading "V"
(e.g. 15p10). It goes into the CRAB request name, Analysis_<sample>_CodeV<codeVersion>,
which is also the name of the output directory on the storage site.
Tags read by TupleAnalysis (cfg/configFile.txt) in October 2026:
W+jets V14p14 and V14p60x, TTbar V15p10, QCD V16p3x, semi-leptonic TTbar V22p1.

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
 5. Set `config.Data.unitsPerJob` in the template to match the list (see "Things to know").

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

What the script writes
----------------------
    crab_projects/crab_Analysis_<sample>_CodeV<codeVersion>/
        CRAB project directory of each dataset (crab status / resubmit -d ...)
    submittedConfigs/4crab_Bkg_toSubmit.py
        CRAB configuration of the last dataset submitted
    /store/user/gcoulon/HSCP/<primary dataset>/Analysis_<sample>_CodeV<codeVersion>/<date>/
        ntuples, on T2_FR_IPHC
    4crab_Bkg_Template.py, 4crab_Bkg_toSubmit.py
        temporary files in the launch directory, removed at the end

Dataset lists
-------------
Four lists of the RunIII2024Summer24MiniAODv6 campaign are defined: W+jets in bins of
jet multiplicity and pT(l nu) (10 datasets), inclusive W to mu nu + jets (1),
muon-enriched QCD in pT-hat bins (12) and TTbar. A list is switched off by enclosing it
in triple quotes. When this header was written, the TTbar list was the active one,
with TTtoLNu2Q only (TTto2L2Nu commented out inside the list).

Things to know
--------------
- <sample> is the name of the primary dataset up to "_TuneCP5", e.g. TTtoLNu2Q or
  QCD_Bin-PT-15to20_Fil-MuEnriched. A dataset whose name does not contain "TuneCP5"
  gets a wrong sample name.
- The number of files per job is not tied to the list: the template has 5 (TTbar and
  QCD) and a commented line with 2 (W+jets). Swap the two lines by hand when changing
  list, otherwise W+jets is submitted with 5 files per job.
- The configuration is always moved to submittedConfigs/4crab_Bkg_toSubmit.py: each
  dataset overwrites the previous one, and so does the next run. Only the last
  configuration submitted is kept, and its file name does not carry the version.
- The simulation is processed with year=2024 for all lists.
- The return code of `crab submit` is not checked: the configuration is moved to
  submittedConfigs/ even when the submission failed. Read the terminal output, or
  check with `crab status -d crab_projects/crab_<request name>`.
- 4crab_Bkg_Template.py is written only if it does not exist yet, and removed at the
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

# Wjets
'''
datasetList = [
"/WtoLNu-2Jets_Bin-1J-PTLNu-40to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v3/MINIAODSIM",
"/WtoLNu-2Jets_Bin-1J-PTLNu-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v3/MINIAODSIM",
"/WtoLNu-2Jets_Bin-1J-PTLNu-200to400_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/WtoLNu-2Jets_Bin-1J-PTLNu-400to600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/WtoLNu-2Jets_Bin-1J-PTLNu-600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/WtoLNu-2Jets_Bin-2J-PTLNu-40to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v3/MINIAODSIM",
"/WtoLNu-2Jets_Bin-2J-PTLNu-100to200_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v3/MINIAODSIM",
"/WtoLNu-2Jets_Bin-2J-PTLNu-200to400_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/WtoLNu-2Jets_Bin-2J-PTLNu-400to600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/WtoLNu-2Jets_Bin-2J-PTLNu-600_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM"
]
'''

#Wjets to MuNu
'''
datasetList = [
"/WtoMuNu-2Jets_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v3/MINIAODSIM",
]
'''


# QCD MuEnriched
'''
datasetList = [
"/QCD_Bin-PT-15to20_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/QCD_Bin-PT-20to30_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/QCD_Bin-PT-30to50_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/QCD_Bin-PT-50to80_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/QCD_Bin-PT-80to120_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/QCD_Bin-PT-120to170_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/QCD_Bin-PT-170to300_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/QCD_Bin-PT-300to470_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/QCD_Bin-PT-470to600_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/QCD_Bin-PT-600to800_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/QCD_Bin-PT-800to1000_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
"/QCD_Bin-PT-1000_Fil-MuEnriched_TuneCP5_13p6TeV_pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM"
]
'''



# TTbar

datasetList = [
#"/TTto2L2Nu_TuneCP5_13p6TeV_powheg-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v3/MINIAODSIM",
"/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/RunIII2024Summer24MiniAODv6-150X_mcRun3_2024_realistic_v2-v2/MINIAODSIM",
]





# ---------------------------------------------------------------------------
# Production version tag: first command-line argument, without the leading "V".
# ---------------------------------------------------------------------------
codeVersion = sys.argv[1]
#just the number, like 18p2


# Directory where the submitted CRAB configuration is kept.
if not os.path.exists("submittedConfigs"): os.makedirs("submittedConfigs")


# ---------------------------------------------------------------------------
# CRAB configuration template, written to 4crab_Bkg_Template.py.
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
#   splitting         FileBased; unitsPerJob = files per job, to be set by hand
#                     according to the list: 5 for TTbar and QCD, 2 for W+jets
#   outLFNDirBase     /store/user/gcoulon/HSCP, on storageSite T2_FR_IPHC
#   publication       False: the output is not published in DBS
# ---------------------------------------------------------------------------
if not os.path.exists("4crab_Bkg_Template.py"):
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

config.section_('Data')
config.Data.inputDataset = 'DATASET'
config.Data.splitting = 'FileBased'
#config.Data.splitting = 'Automatic'
#config.Data.totalUnits = 10
#config.Data.unitsPerJob = 2   # Wjets
config.Data.unitsPerJob = 5  # ttbar & QCD
config.Data.outputDatasetTag = config.General.requestName
config.Data.outLFNDirBase = '/store/user/gcoulon/HSCP'
config.Data.ignoreLocality = False
config.Data.partialDataset = False
config.Data.publication = False

config.section_('Site')
config.Site.whitelist = ['T1_*','T2_*','T3_*']
config.Site.storageSite = 'T2_FR_IPHC'
'''

  with open("4crab_Bkg_Template.py", "w") as text_file:
      text_file.write(TEMPLATE)

# ---------------------------------------------------------------------------
# One CRAB task per dataset.
# ---------------------------------------------------------------------------
for i in datasetList:
  print("Submit for sample "+i)
  # Fresh copy of the template, then VERSION.
  os.system("cp 4crab_Bkg_Template.py 4crab_Bkg_toSubmit.py")

  replaceVERSION_ = "sed -i 's/VERSION/"+codeVersion+"/g' 4crab_Bkg_toSubmit.py"
  os.system(replaceVERSION_)

  # NAME: "/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/..." -> "TTtoLNu2Q".
  shortSampleName = i[1:(i.find('TuneCP5'))-1]
  replaceNAME_ = "sed -i 's/NAME/"+shortSampleName+"/g' 4crab_Bkg_toSubmit.py"
  os.system(replaceNAME_)

  # DATASET: the slashes of the DAS name are escaped for sed.
  replaceDATASET_ = "sed -i 's/DATASET/"+i.replace("/","\/")+"/g' 4crab_Bkg_toSubmit.py"
  os.system(replaceDATASET_)

  # Submit, then keep the configuration (same file name for every dataset).
  os.system("crab submit -c 4crab_Bkg_toSubmit.py")
  os.system("mv 4crab_Bkg_toSubmit.py submittedConfigs/.")

# Remove the template: it is rewritten at the next run.
os.system("rm 4crab_Bkg_Template.py")