"""
submitCrabJobsData.py -- CRAB submission of the HSCP ntuplizer on collision data (MiniAOD)

For each dataset of `datasetList`, the script fills a CRAB configuration from the
template defined below, submits it with `crab submit`, and keeps the configuration in
submittedConfigs/.

Usage
-----
    python3 submitCrabJobsData.py <codeVersion>

<codeVersion> is the version tag of the ntuple production, without the leading "V"
(e.g. 18p2). It goes into the CRAB request name, Analysis_<sample>_CodeV<codeVersion>,
which is also the name of the output directory on the storage site.
Tags read by TupleAnalysis (cfg/configFile.txt) in October 2026:
JetMET V12p35, MuonEG V17p4x, Muon V18p10x.

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
    HSCPAnalysis/Ntuplizer/data/lumi/Cert_Collisions2024_378981_386951_Golden.txt
        golden JSON of 2024: used as CRAB lumi mask and shipped with the jobs
    HSCPAnalysis/Ntuplizer/data/lumi/Cert_Collisions2022_355100_362760_Golden.txt
        same for 2022 (only needed for 2022 datasets)

What the script writes
----------------------
    crab_projects/crab_Analysis_<sample>_CodeV<codeVersion>/
        CRAB project directory of each dataset (crab status / resubmit -d ...)
    submittedConfigs/<codeVersion>_<year><era>.py
        CRAB configuration that was submitted
    /store/user/gcoulon/HSCP/<primary dataset>/Analysis_<sample>_CodeV<codeVersion>/<date>/
        ntuples, on T2_FR_IPHC
    4crab_Template_Data.py, 4crab_toSubmit_Data.py
        temporary files in the launch directory, removed at the end

Dataset lists
-------------
Three lists are defined, one per primary dataset: MuonEG (block labelled EGAMMA),
JetMET0/1 (block labelled MET) and Muon0/1 (block labelled MUON), for the 2024 eras C
to I. A list is switched off by enclosing it in triple quotes. When this header was
written, the JetMET list was the active one.

Things to know
--------------
- <sample> is "<primary dataset>_Run<year><era>", e.g. JetMET0_Run2024C. Run2024I is
  listed with two processing strings, MINIv6NANOv15 and MINIv6NANOv15_v2 (JetMET and
  Muon lists; the MuonEG list has the first one only). The datasets of the second get a
  suffix so that their request names differ from the first: "0bis" when the dataset
  ends with "v2-v1", "1bis" when it ends with "v2-v2". The suffix follows the dataset
  version, not the number of the primary dataset: Muon1/...MINIv6NANOv15_v2-v1 gives
  Muon1_Run2024I0bis.
- The file kept in submittedConfigs/ is named after the version, the year and the era
  only. Datasets of the same era (JetMET0 and JetMET1, the two Run2024I processings)
  overwrite each other: 16 submissions leave 7 files, the last one submitted per era.
- Only 2022 and 2024 are handled. For another year, `year=` and the lumi mask stay
  empty in the configuration and the submission must not be trusted.
- The return code of `crab submit` is not checked: the configuration is moved to
  submittedConfigs/ even when the submission failed. Read the terminal output, or
  check with `crab status -d crab_projects/crab_<request name>`.
- 4crab_Template_Data.py is written only if it does not exist yet, and removed at the
  end. After an interrupted run (Ctrl-C, crash), delete it by hand: otherwise the next
  run silently reuses the old template, whatever was changed in this script.
- The output directory (/store/user/gcoulon/HSCP) and the storage site (T2_FR_IPHC) are
  hard-coded in the template: change both to run under another account.
- Without argument the script stops on an IndexError; the usage line is only printed
  with -h.
"""
import sys, os, time, re
import numpy as np
from optparse import OptionParser

parser = OptionParser(usage="Usage: python %prog codeVersion")
(opt,args) = parser.parse_args()

# ---------------------------------------------------------------------------
# Dataset lists: leave exactly one block uncommented (see the header).
# ---------------------------------------------------------------------------

#        EGAMMA
# NB: despite its label, this block is the MuonEG primary dataset.
'''
datasetList = [
"/MuonEG/Run2024C-MINIv6NANOv15-v1/MINIAOD",
"/MuonEG/Run2024D-MINIv6NANOv15-v1/MINIAOD",
"/MuonEG/Run2024E-MINIv6NANOv15-v1/MINIAOD",
"/MuonEG/Run2024F-MINIv6NANOv15-v2/MINIAOD",
"/MuonEG/Run2024G-MINIv6NANOv15-v3/MINIAOD",
"/MuonEG/Run2024H-MINIv6NANOv15-v2/MINIAOD",
"/MuonEG/Run2024I-MINIv6NANOv15-v2/MINIAOD",
]
'''


#        MET

datasetList = [
"/JetMET0/Run2024C-MINIv6NANOv15-v1/MINIAOD",
"/JetMET1/Run2024C-MINIv6NANOv15-v1/MINIAOD",
"/JetMET0/Run2024D-MINIv6NANOv15-v1/MINIAOD",
"/JetMET1/Run2024D-MINIv6NANOv15-v1/MINIAOD",
"/JetMET0/Run2024E-MINIv6NANOv15-v1/MINIAOD",
"/JetMET1/Run2024E-MINIv6NANOv15-v1/MINIAOD",
"/JetMET0/Run2024F-MINIv6NANOv15-v2/MINIAOD",
"/JetMET1/Run2024F-MINIv6NANOv15-v2/MINIAOD",
"/JetMET0/Run2024G-MINIv6NANOv15-v2/MINIAOD",
"/JetMET1/Run2024G-MINIv6NANOv15-v2/MINIAOD",
"/JetMET0/Run2024H-MINIv6NANOv15-v2/MINIAOD",
"/JetMET1/Run2024H-MINIv6NANOv15-v2/MINIAOD",
"/JetMET0/Run2024I-MINIv6NANOv15-v2/MINIAOD",
"/JetMET0/Run2024I-MINIv6NANOv15_v2-v1/MINIAOD",
"/JetMET1/Run2024I-MINIv6NANOv15-v1/MINIAOD",
"/JetMET1/Run2024I-MINIv6NANOv15_v2-v2/MINIAOD"
]


#        MUON
'''
datasetList = [
"/Muon0/Run2024C-MINIv6NANOv15-v1/MINIAOD",
"/Muon1/Run2024C-MINIv6NANOv15-v1/MINIAOD",
"/Muon0/Run2024D-MINIv6NANOv15-v1/MINIAOD",
"/Muon1/Run2024D-MINIv6NANOv15-v1/MINIAOD",
"/Muon0/Run2024E-MINIv6NANOv15-v1/MINIAOD",
"/Muon1/Run2024E-MINIv6NANOv15-v1/MINIAOD",
"/Muon0/Run2024F-MINIv6NANOv15-v1/MINIAOD",
"/Muon1/Run2024F-MINIv6NANOv15-v1/MINIAOD",
"/Muon0/Run2024G-MINIv6NANOv15-v1/MINIAOD",
"/Muon1/Run2024G-MINIv6NANOv15-v2/MINIAOD",
"/Muon0/Run2024H-MINIv6NANOv15-v1/MINIAOD",
"/Muon1/Run2024H-MINIv6NANOv15-v2/MINIAOD",
"/Muon0/Run2024I-MINIv6NANOv15-v1/MINIAOD",
"/Muon1/Run2024I-MINIv6NANOv15-v1/MINIAOD",
"/Muon0/Run2024I-MINIv6NANOv15_v2-v1/MINIAOD",
"/Muon1/Run2024I-MINIv6NANOv15_v2-v1/MINIAOD"
]
'''




# ---------------------------------------------------------------------------
# Production version tag: first command-line argument, without the leading "V".
# ---------------------------------------------------------------------------
codeVersion = sys.argv[1]
#just the number, like 18p2


# Directory where the submitted CRAB configurations are kept.
if not os.path.exists("submittedConfigs"): os.makedirs("submittedConfigs")


# ---------------------------------------------------------------------------
# CRAB configuration template, written to 4crab_Template_Data.py.
#
# Placeholders replaced with sed for each dataset, in this order:
#   VERSION  -> codeVersion
#   NAME     -> short sample name (primary dataset + run period)
#   DATASET  -> full DAS name of the dataset
#   YEAR_    -> data-taking year, passed to ntuplizer_cfg.py as year=
#   CERT_    -> file name of the golden JSON (in inputFiles and in lumiMask)
#   ERA_     -> era letter, passed to ntuplizer_cfg.py as era=
#
# Main settings:
#   psetName          ntuplizer_cfg.py, taken from the launch directory
#   pyCfgParams       options given to ntuplizer_cfg.py (MiniAOD input, data, CRAB mode)
#   inputFiles        files shipped with every job
#   splitting         LumiBased, 15 luminosity sections per job
#   lumiMask          golden JSON: only certified luminosity sections are processed
#   outLFNDirBase     /store/user/gcoulon/HSCP, on storageSite T2_FR_IPHC
#   publication       False: the output is not published in DBS
# ---------------------------------------------------------------------------
if not os.path.exists("4crab_Template_Data.py"):
  TEMPLATE = '''
from CRABClient.UserUtilities import config, getUsername
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
config.JobType.inputFiles = ['HSCPAnalysis/Ntuplizer/data/template/template_Run3.root','HSCPAnalysis/Ntuplizer/data/template/SF_dEdx_Run3.txt', 'HSCPAnalysis/Ntuplizer/data/lumi/CERT_']
config.JobType.pyCfgParams = ['isAOD=False','isData=True','year=YEAR_','era=ERA_','doCrab=True']

config.section_('Data')
config.Data.inputDataset = 'DATASET'
config.Data.splitting = 'LumiBased'
config.Data.unitsPerJob = 15
#NJOBS = 200
#config.Data.totalUnits = config.Data.unitsPerJob * NJOBS
config.Data.outputDatasetTag = config.General.requestName
config.Data.outLFNDirBase = '/store/user/gcoulon/HSCP'
config.Data.lumiMask = 'HSCPAnalysis/Ntuplizer/data/lumi/CERT_' #
config.Data.ignoreLocality = False
config.Data.partialDataset = False
config.Data.publication = False

config.section_('Site')
config.Site.whitelist = ['T1_*','T2_*','T3_*']
config.Site.storageSite = 'T2_FR_IPHC'
'''

  with open("4crab_Template_Data.py", "w") as text_file:
      text_file.write(TEMPLATE)

# ---------------------------------------------------------------------------
# One CRAB task per dataset.
# ---------------------------------------------------------------------------
for i in datasetList:
  print("Submit for sample "+i)


  # Fresh copy of the template, then VERSION.
  os.system("cp 4crab_Template_Data.py 4crab_toSubmit_Data.py")
  replaceVERSION_ = "sed -i 's/VERSION/"+codeVersion+"/g' 4crab_toSubmit_Data.py"
  os.system(replaceVERSION_)


  # NAME: "/JetMET0/Run2024C-MINIv6NANOv15-v1/MINIAOD" -> "JetMET0_Run2024C".
  # Suffix for the second processing of Run2024I (dataset version v2-v1 or v2-v2).
  shortSampleName = i[1:(i.find('-'))].replace("/","_")
  if ("I-" in i and "v2-v1" in i):
    shortSampleName = shortSampleName + "0bis"
  elif ("I-" in i and "v2-v2" in i):
    shortSampleName = shortSampleName + "1bis"
  replaceNAME_ = "sed -i 's/NAME/"+shortSampleName+"/g' 4crab_toSubmit_Data.py"
  os.system(replaceNAME_)


  # DATASET: the slashes of the DAS name are escaped for sed.
  replaceDATASET_ = "sed -i 's/DATASET/"+i.replace("/","\/")+"/g' 4crab_toSubmit_Data.py"
  os.system(replaceDATASET_)


  # YEAR_ and CERT_: year and golden JSON, read from the dataset name (2022 or 2024).
  CERT_ = ""
  YEAR_ = ""
  if ("2024" in i) :
    YEAR_ = "2024"
    CERT_ = "Cert_Collisions2024_378981_386951_Golden.txt"
  elif ("2022" in i) :
    YEAR_ = "2022"
    CERT_ = "Cert_Collisions2022_355100_362760_Golden.txt"
  replaceYEAR_  = "sed -i 's/YEAR_/"+YEAR_+"/g' 4crab_toSubmit_Data.py"
  os.system(replaceYEAR_)
  replaceCERT_  = "sed -i 's/CERT_/"+CERT_+"/g' 4crab_toSubmit_Data.py"
  os.system(replaceCERT_)
  print ("Using cert file: "+CERT_)


  # ERA_: letter in front of the first "-" of the dataset name (Run2024C-... -> C).
  ERA_ = ""
  if ("A-" in i) :
  	ERA_ = "A"
  elif ("B-" in i) :
  	ERA_ = "B"
  elif ("C-" in i) :
  	ERA_ = "C"
  elif ("D-" in i) :
  	ERA_ = "D"
  elif ("E-" in i) :
  	ERA_ = "E"
  elif ("F-" in i) :
    ERA_ = "F"
  elif ("G-" in i) :
  	ERA_ = "G"
  elif ("H-" in i) :
  	ERA_ = "H"
  elif ("I-" in i) :
    ERA_ = "I"
  replaceERA_  = "sed -i 's/ERA_/"+ERA_+"/g' 4crab_toSubmit_Data.py"
  os.system(replaceERA_)
  	

  # Submit, then keep the configuration as submittedConfigs/<version>_<year><era>.py.
  os.system("crab submit -c 4crab_toSubmit_Data.py")
  os.system("mv 4crab_toSubmit_Data.py submittedConfigs/"+codeVersion+"_"+YEAR_+ERA_+".py")

# Remove the template: it is rewritten at the next run.
os.system("rm 4crab_Template_Data.py")