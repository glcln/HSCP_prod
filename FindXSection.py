"""
FindXSection.py -- cross section of a simulated sample, from its generator information

cmsRun configuration that runs GenXSecAnalyzer (GeneratorInterface/Core) on files of a
simulated sample, MiniAODSIM here. The analyzer does not look at the events: at the end
of each luminosity block it adds up the generator information stored with the block
(cross section of the LHE processes, jet-matching efficiency, filter efficiency, event
weights), and it prints a summary at the end of the job. No output file is written.

Usage
-----
    cmsRun FindXSection.py inputFiles=<file1>,<file2>,...  [maxEvents=<N>]
    cmsRun FindXSection.py inputFiles_load=<list.txt>      [maxEvents=<N>]

    inputFiles        files to read, separated by commas
    inputFiles_load   text file with one file name per line ('#' starts a comment)
    maxEvents         number of events to process; default -1, all events of the files
    filePrepend       string put in front of every file name, e.g.
                      filePrepend=root://cms-xrd-global.cern.ch/
                      to read /store/... files through the global xrootd redirector

Without inputFiles, the configuration reads one file of the W+jets sample
WtoLNu-2Jets_Bin-1J-PTLNu-40to100 (RunIII2024Summer24MiniAODv6), set in
DEFAULT_INPUT_FILE below, and says so.

To get the file names of a dataset:
    dasgoclient --query="file dataset=<DAS name of the dataset>"

Before launching
----------------
        cmsenv
        voms-proxy-init --rfc --voms cms -valid 192:00
Nothing to build: GenXSecAnalyzer is part of the CMSSW release, and the configuration
can be launched from any directory. The proxy is needed to read /store/... files from
the grid.

Reading the output
------------------
The summary comes at the end of the job, on the standard error. To keep it:
    cmsRun FindXSection.py inputFiles=... 2>&1 | tee xsec.log

The cross section of the sample is the line
    After filter: final cross section = <value> +- <error> pb
It includes the jet-matching efficiency (MLM, FxFx) and the efficiency of the generator
filter. The lines before it give the cross section before and after matching and the
efficiencies; the lines after it give the fraction of events with negative weights and
the luminosity equivalent to one million events.

Things to know
--------------
- One file gives a rough value. For a number to use in the analysis, pass several
  files of the sample: the error printed gets smaller with the amount read.
- The value is the one computed by the generator, at the order of the generator (NLO
  for amcatnloFXFX, LO for madgraphMLM and pythia8). It is not a higher-order
  prediction.
- maxEvents only limits how much of the files is read; the earlier version of this
  configuration stopped at 1000000 events (maxEvents=1000000 gives the same).
- The other options registered by VarParsing('analysis') (outputFile, ...) are not
  used.
"""
import FWCore.ParameterSet.Config as cms
from FWCore.ParameterSet.VarParsing import VarParsing

# File read when no inputFiles is given on the command line.
DEFAULT_INPUT_FILE = '/store/mc/RunIII2024Summer24MiniAODv6/WtoLNu-2Jets_Bin-1J-PTLNu-40to100_TuneCP5_13p6TeV_amcatnloFXFX-pythia8/MINIAODSIM/150X_mcRun3_2024_realistic_v2-v3/110000/00412da6-5436-42b8-86fb-a4e89bddbad1.root'

# Command-line options: inputFiles, maxEvents, filePrepend (see the header).
options = VarParsing ('analysis')
options.parseArguments()

inputFiles = list(options.inputFiles)
if not inputFiles:
    inputFiles = [options.filePrepend + DEFAULT_INPUT_FILE]
    print("FindXSection.py: no inputFiles given, reading the default file " + inputFiles[0])

process = cms.Process('XSec')

# Number of events to process (-1: all).
process.maxEvents = cms.untracked.PSet(
    input = cms.untracked.int32(options.maxEvents)
)

# Progress line every 1000 events.
process.load('FWCore.MessageService.MessageLogger_cfi')
process.MessageLogger.cerr.FwkReport.reportEvery = 1000

# Input files; no secondary files.
secFiles = cms.untracked.vstring()
process.source = cms.Source("PoolSource",
                            fileNames = cms.untracked.vstring(inputFiles),
                            secondaryFileNames = secFiles)

# The analyzer takes no parameter: it reads the luminosity-block products of the generator.
process.xsec = cms.EDAnalyzer("GenXSecAnalyzer")

process.ana = cms.Path(process.xsec)
process.schedule = cms.Schedule(process.ana)