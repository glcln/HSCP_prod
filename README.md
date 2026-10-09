# HSCP_prod

Production tools of the CMS Run 3 search for heavy stable charged particles (HSCP) at IPHC
Strasbourg, 2024 data: from the CRAB submission of the ntuplizer to the file lists and merged
signal files read by the analysis.

The ntuples stay on the IPHC dCache (T2_FR_IPHC). This repository holds:

- the **CRAB scripts** that produce them (`SubmitJobs/`, `crab_report_lumi.sh`,
  `FindXSection.py`), used from the CMSSW release that contains the analysis code;
- the **bookkeeping scripts** that make them usable by the analysis: file lists (`.txt`, one
  XRootD URL per line) for data and background, local merged copies for the signal;
- the **directory tree** where these lists and copies are kept. Only its skeleton is
  versioned; the content stays on the IPHC UI (see [section 2](#2-repository-layout)).

Where each part runs:

| Where                                                                  | What                                                              |
|------------------------------------------------------------------------|-------------------------------------------------------------------|
| `CMSSW_X_Y_Z/src/`, the directory that contains `HSCPAnalysis/` and `ntuplizer_cfg.py` | `SubmitJobs/*.py`, `crab_report_lumi.sh`, `FindXSection.py`; then the analysis itself (histograms, background prediction, limits) |
| The clone of this repository on the IPHC UI, `/scratch/ui3_1/gcoulon/HSCP_prod` | `ScriptWrite.sh`, `WriteFileinTXT.py`, `getjobsSignal.py`, `MergeJobs.py`, `transfer_prod.py` |

Contents:

1. [Production chain](#1-production-chain)
2. [Repository layout](#2-repository-layout)
3. [Before you start](#3-before-you-start)
4. [Producing ntuples with CRAB](#4-producing-ntuples-with-crab)
5. [Listing a data or background production in a .txt](#5-listing-a-data-or-background-production-in-a-txt)
6. [Transferring and merging a signal production](#6-transferring-and-merging-a-signal-production)
7. [Transferring and merging a data or background production](#7-transferring-and-merging-a-data-or-background-production)
8. [Script reference](#8-script-reference)
9. [Productions](#9-productions)
10. [Using the scripts from another account](#10-using-the-scripts-from-another-account)
11. [Pitfalls](#11-pitfalls)

---

## 0. Disclaimer

I wrote all the code in this project myself. However, this README and the comments in the scripts were generated using Claude.


## 1. Production chain

```
CMSSW_X_Y_Z/src/   (HSCPAnalysis/, ntuplizer_cfg.py)
  1. submitCrabJobs{Data,MC,Signals}.py <version>   -> one CRAB task per dataset
  2. StatusCrabJobs.py / ResubmitCrabJobs.py <version>
  3. crab_report_lumi.sh <version> <dir>            data: processed lumis, sent to lxplus
     FindXSection.py                                simulation: generator cross section
        |
        v   ntuples on the IPHC dCache (T2_FR_IPHC)
/store/user/gcoulon/HSCP/<Dataset>/Analysis_<sample>_CodeV<version>/<YYMMDD_HHMMSS>/<000N>/
        |
        v
HSCP_prod/   (this repository, on the IPHC UI)
  4a. data, background: ScriptWrite.sh -> WriteFileinTXT.py  ->  <dir>/V<version><index>.txt
  4b. signal: getjobsSignal.py -> MergeJobs.py signal        ->  SIGNAL/V<version>/<sample>_merged.root
        |
        v
CMSSW_X_Y_Z/src/   analysis: TupleAnalysis (versions chosen in cfg/configFile.txt),
                   histograms, background prediction, limits
```

The **code version** (`18p1`, `21p0`, ...) given at submission identifies a production
everywhere: CRAB request names, dCache directories, list names, `SIGNAL/V<version>/`. All the
scripts take it without the leading `V`, and those that select tasks by version do it on an
exact match: `18p1` does not take `18p10`.

### Where the ntuples are on dCache

    davs://sbgdcache.in2p3.fr/cms/phedex/store/user/gcoulon/HSCP/<Dataset>/<Task>/<YYMMDD_HHMMSS>/<000N>/output_N.root

| Level             | Meaning                                         | Example                                      |
|-------------------|-------------------------------------------------|----------------------------------------------|
| `<Dataset>`       | Primary dataset (data) or sample name (simulation) | `Muon0`, `TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8` |
| `<Task>`          | CRAB request name, `Analysis_<sample>_CodeV<version>` | `Analysis_Muon0_Run2024C_CodeV18p1`, `Analysis_HSCP-Stop_Par-M-1000_CodeV21p0` |
| `<YYMMDD_HHMMSS>` | CRAB submission time                            | `260610_180305`                              |
| `<000N>`          | Block of 1000 jobs                              | `0000`, `0001`                               |

`<sample>` is `<primary dataset>_Run<year><era>` for data (plus `0bis` or `1bis` for the second
processing of Run2024I), and the dataset name up to `_TuneCP5` for simulation.

---

## 2. Repository layout

### Scripts

| File                                  | Role                                                                  | Run from     |
|---------------------------------------|-----------------------------------------------------------------------|--------------|
| `SubmitJobs/submitCrabJobsData.py`    | Submits the ntuplizer on 2024 data (MuonEG, JetMET0/1, Muon0/1)       | `src/`       |
| `SubmitJobs/submitCrabJobsMC.py`      | Same on the background simulation (W+jets, QCD, TTbar)               | `src/`       |
| `SubmitJobs/submitCrabJobsSignals.py` | Same on the signal simulation (gluino, stau, stop)                    | `src/`       |
| `SubmitJobs/StatusCrabJobs.py`        | `crab status` on every task of a version                              | `src/`       |
| `SubmitJobs/ResubmitCrabJobs.py`      | `crab resubmit` on every task of a version, optionally every hour     | `src/`       |
| `crab_report_lumi.sh`                 | Luminosity sections processed by a data production, sent to lxplus    | `src/`       |
| `FindXSection.py`                     | cmsRun configuration printing the cross section of a simulated sample | anywhere     |
| `ScriptWrite.sh`                      | Calls `WriteFileinTXT.py` for each production; record of every `.txt` | this clone   |
| `WriteFileinTXT.py`                   | Lists one dCache directory and appends its ROOT files to a `.txt`     | this clone   |
| `getjobsSignal.py`                    | Copies all signal samples of a version to `SIGNAL/V<version>/`        | this clone   |
| `MergeJobs.py`                        | Merges the copied ROOT files with `hadd` (modes `signal` and `data`)  | this clone   |
| `transfer_prod.py`                    | Older transfer script for data/background (Run 2 dataset names)       | this clone   |

`src/` stands for `CMSSW_X_Y_Z/src/`. The scripts that run from there read and write
everything relative to the current directory: they can be copied next to `HSCPAnalysis/` or
called by their path from this clone, what matters is to launch them from `src/`. They write
`crab_projects/`, `submittedConfigs/` and `lumis_<version>/` there, not in this repository.
Each one documents itself in its header (usage, files read and written, things to know).

### Directories

| Directory     | Content, on the UI                                                     | In git                     |
|---------------|------------------------------------------------------------------------|----------------------------|
| `Mu2024/`     | File lists, Muon0 + Muon1 2024 data                                    | the lists (section 9)      |
| `MuonEG2024/` | File lists, MuonEG 2024 data                                           | empty directory            |
| `JetMET2024/` | File lists, JetMET0 + JetMET1 2024 data                                | empty directory            |
| `BKG/`        | File lists, background simulation, in `QCD2024/`, `Wjets2024/`, `TTbar2024/`, `TTbar1L1Nu2024/` | empty directories |
| `SIGNAL/`     | Local signal productions (per-job and merged files), older merged files | empty directories, per-job ones included |
| `AOD2024/`    | Not filled by any script here and absent from `ScriptWrite.sh`         | empty directory            |

`.gitignore` excludes everything inside these directories except the `.gitkeep` files that
keep the tree. The `Mu2024/` lists are an exception: they are tracked, so changes to them show
up in git, but a new list there is ignored like anywhere else unless added with `git add -f`.

---

## 3. Before you start

| Needed for                                | What                                                                  |
|-------------------------------------------|-----------------------------------------------------------------------|
| CRAB submission                           | A CMSSW release with `HSCPAnalysis/` and `ntuplizer_cfg.py` in `src/`, built after moving the limit packages out (section 4) |
| Any grid access (CRAB, dCache)            | A CMS proxy: `voms-proxy-init --rfc --voms cms -valid 192:00` (8 days) |
| CRAB commands, `cmsRun`, merging          | The CMSSW environment (`cmsenv`), which also provides ROOT and `hadd` |
| Listing and transfer                      | `gfal-ls` and `gfal-copy`                                             |
| Luminosity report                         | An lxplus account; `kinit gcoulon@CERN.CH` avoids the password prompt of `scp` |
| All the Python scripts                    | Python 3                                                              |

The bookkeeping scripts expect this repository to be cloned at
`/scratch/ui3_1/gcoulon/HSCP_prod`:

    git clone https://github.com/glcln/HSCP_prod.git /scratch/ui3_1/gcoulon/HSCP_prod

Anywhere else, or from another account, change the paths listed in section 10.

---

## 4. Producing ntuples with CRAB

Goal: one CRAB task per dataset, writing the ntuples to
`/store/user/gcoulon/HSCP/<Dataset>/Analysis_<sample>_CodeV<version>/` on T2_FR_IPHC.
All the commands of this section are run from `CMSSW_X_Y_Z/src/`.

**Step 1. Prepare the release.** Move the limit-setting packages out *before* building, so
that they are neither compiled with the release nor packed into the CRAB sandbox:

    cd CMSSW_X_Y_Z/src
    mv HiggsAnalysis ../.. && mv CombineHarvester ../..
    cmsenv
    scram b -j 8
    voms-proxy-init --rfc --voms cms -valid 192:00

**Step 2. Choose the datasets.** Each submission script defines several `datasetList` blocks;
leave exactly one active and enclose the others in `'''`:

| Script                     | Lists                                                          | Also set by hand                       |
|----------------------------|----------------------------------------------------------------|----------------------------------------|
| `submitCrabJobsData.py`    | MuonEG, JetMET0/1, Muon0/1, eras 2024C to 2024I                | nothing                                |
| `submitCrabJobsMC.py`      | W+jets (10 bins), W to mu nu + jets, QCD MuEnriched (12 bins), TTbar | `config.Data.unitsPerJob` in the template: 5 for TTbar and QCD, 2 for W+jets |
| `submitCrabJobsSignals.py` | Run 2 gluino, Run 3 gluino (pythia8, madgraphMLM), pair stau, stop | for the Run 2 list, swap the `inputFiles` and `pyCfgParams` lines of the template for the commented 2018 ones |

**Step 3. Submit**, with a version never used before:

    python3 submitCrabJobsData.py 18p2

For each dataset this creates the CRAB task `Analysis_<sample>_CodeV18p2`, its project
directory `crab_projects/crab_Analysis_<sample>_CodeV18p2/`, and a copy of the configuration in
`submittedConfigs/`. The script does not check the return code of `crab submit`: read its
output.

**Step 4. Follow the jobs and resubmit the failed ones:**

    python3 StatusCrabJobs.py 18p2 2>&1 | tee status_18p2.log
    python3 ResubmitCrabJobs.py 18p2         # one pass
    python3 ResubmitCrabJobs.py 18p2 48      # 48 passes, one per hour: run it in screen or tmux

The proxy must stay valid until the last pass.

**Step 5. Data only: processed luminosity.** Once all the jobs are finished:

    ./crab_report_lumi.sh 12p31 MET_V12

The second argument is a directory that must already exist under `ComputeLumi/` on lxplus. The
script runs `crab report` on every task of the version, keeps each `processedLumis.json` in
`lumis_<version>/`, and sends them with `scp` to
`gcoulon@lxplus9.cern.ch:/afs/cern.ch/user/g/gcoulon/ComputeLumi/<dir>/`, where the luminosity
is computed.

**Step 6. Simulation, if needed: cross section.** `FindXSection.py` runs `GenXSecAnalyzer` on
files of the sample:

    dasgoclient --query="file dataset=<DAS name of the dataset>" > files.txt
    cmsRun FindXSection.py inputFiles_load=files.txt 2>&1 | tee xsec.log

The value is on the line `After filter: final cross section = <value> +- <error> pb`. It is the
generator cross section, at the order of the generator. Add
`filePrepend=root://cms-xrd-global.cern.ch/` to read the files through the global redirector,
and `maxEvents=<N>` to stop earlier.

**Step 7. Move the limit packages back** when the production is done:

    mv ../../HiggsAnalysis ../../CombineHarvester . && scram b -j 8

The ntuples are then ready for section 5 (data, background) or section 6 (signal).

---

## 5. Listing a data or background production in a .txt

Goal: one `.txt` containing the XRootD URL of every file of a production, to read it remotely.
All the commands of this section are run from this clone.

**Step 1. Find the production on dCache.** Go down the levels until the `000N` directories:

    gfal-ls davs://sbgdcache.in2p3.fr/cms/phedex/store/user/gcoulon/HSCP/
    gfal-ls davs://sbgdcache.in2p3.fr/cms/phedex/store/user/gcoulon/HSCP/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/
    gfal-ls davs://sbgdcache.in2p3.fr/cms/phedex/store/user/gcoulon/HSCP/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/Analysis_TTtoLNu2Q_CodeV22p0/
    gfal-ls davs://sbgdcache.in2p3.fr/cms/phedex/store/user/gcoulon/HSCP/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/Analysis_TTtoLNu2Q_CodeV22p0/260721_185412/
    # -> 0000  0001  0002

**Step 2. Add a block to `ScriptWrite.sh`**, one line per `000N` directory, all writing to the
same `.txt`:

    # TTbar 1L1NU 2024
    python3 WriteFileinTXT.py "gfal-ls davs://sbgdcache.in2p3.fr/cms/phedex//store/user/gcoulon/HSCP/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/Analysis_TTtoLNu2Q_CodeV22p0/260721_185412/0000" BKG/TTbar1L1Nu2024/V22p0.txt
    python3 WriteFileinTXT.py "gfal-ls davs://sbgdcache.in2p3.fr/cms/phedex//store/user/gcoulon/HSCP/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/Analysis_TTtoLNu2Q_CodeV22p0/260721_185412/0001" BKG/TTbar1L1Nu2024/V22p0.txt
    python3 WriteFileinTXT.py "gfal-ls davs://sbgdcache.in2p3.fr/cms/phedex//store/user/gcoulon/HSCP/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/Analysis_TTtoLNu2Q_CodeV22p0/260721_185412/0002" BKG/TTbar1L1Nu2024/V22p0.txt

- The first argument is the whole command in quotes, of the form `gfal-ls davs://...`. The
  script runs it and writes the same paths with `root://` instead of `davs://`.
- To put several datasets in one list (e.g. Muon0 and Muon1 of the same era), give them the
  same `.txt`.
- `.txt` naming used so far: `V<code version><index>.txt`, the index numbering the eras or the
  bins (see section 9).

**Step 3. Comment out every other block.** Each uncommented line is executed again and
*appends* to its `.txt`, which would duplicate the entries of the older lists.

**Step 4. Create the output directory if it is new**, and delete the `.txt` if you are
regenerating it (the script appends, it never overwrites):

    mkdir -p BKG/TTbar1L1Nu2024
    rm -f BKG/TTbar1L1Nu2024/V22p0.txt

**Step 5. Run from this clone** (the `.txt` paths are relative):

    cd /scratch/ui3_1/gcoulon/HSCP_prod
    voms-proxy-init --rfc --voms cms -valid 192:00
    ./ScriptWrite.sh

**Step 6. Check the result.** Each line of `ScriptWrite.sh` must answer
`Writing <n> line(s) to file: ...`. An `ERROR:` means that this directory was not listed and
that nothing was written for it (see section 11). Then:

    wc -l BKG/TTbar1L1Nu2024/V22p0.txt                 # number of files
    sort BKG/TTbar1L1Nu2024/V22p0.txt | uniq -d        # must print nothing (no duplicate)

Each line looks like:

    root://sbgdcache.in2p3.fr/cms/phedex//store/user/gcoulon/HSCP/<Dataset>/<Task>/<YYMMDD_HHMMSS>/0000/output_N.root

Leave the block in `ScriptWrite.sh` (commented) once done and commit it: the file is the only
record of which dCache directories each `.txt` was built from. The `.txt` itself stays on the
UI (section 2).

---

## 6. Transferring and merging a signal production

Goal: `SIGNAL/V<version>/<sample>_merged.root`, one file per mass point. Both scripts work on
absolute paths, so the current directory does not matter.

**Step 1. Transfer.** The argument is the code version without the `V`:

    voms-proxy-init --rfc --voms cms -valid 192:00
    python3 getjobsSignal.py 21p0

Every dCache dataset whose name contains `HSCP` is scanned, and every task of that version
(exact match: `19p6` does not take `CodeV19p60`) is copied to:

    SIGNAL/V21p0/<Model>_<Par-M-mass>_<YYMMDD_HHMMSS>/output_N.root
    e.g. SIGNAL/V21p0/HSCP-Stop_Par-M-1000_260717_081327/output_1.root

**Step 2. Check the transfer.** The last lines must read
`Done: <n> block(s) copied to ..., 0 failure(s).` A listing or a copy that failed is listed as
`FAILED:` and the exit code is 1; in that case delete the sub-directories concerned and rerun
the command. Then compare with what is expected:

    ls SIGNAL/V21p0            # one sub-directory per mass point
    ls SIGNAL/V21p0/*/ | head  # output_N.root files inside

**Step 3. Merge** (ROOT needed):

    python3 MergeJobs.py signal 21p0

Result, next to the sub-directories:

    SIGNAL/V21p0/<Model>_<Par-M-mass>_merged.root
    e.g. SIGNAL/V21p0/HSCP-Stop_Par-M-1000_merged.root

**Step 4. Check the merge.** The last lines must read `Done: <n> merged, 0 failed.` with `<n>`
equal to the number of mass points. Failed sub-directories are listed and the exit code is 1.

Rerunning the merge is safe: existing `*_merged.root` files are deleted and rebuilt, the
sub-directories are not touched.

---

## 7. Transferring and merging a data or background production

Data and background productions are normally read through the `.txt` lists (section 5). For the
cases where a local copy is needed there is `transfer_prod.py`, but it only knows Run 2 dataset
names.

**Step 1. Transfer**, from the directory where the copy must land (output paths are relative):

    cd /scratch/ui3_1/gcoulon/HSCP_prod
    voms-proxy-init --rfc --voms cms -valid 192:00
    python3 transfer_prod.py <version> <dataType>

`<version>` is the code version without the `V`. `<dataType>` is one of:

| `<dataType>`    | dCache dataset scanned                                              |
|-----------------|---------------------------------------------------------------------|
| `SingleMu`      | `SingleMuon`                                                        |
| `MET`           | `MET`                                                               |
| `WJetsToLNu_0J` | `WJetsToLNu_0J_TuneCP5_13TeV-amcatnloFXFX-pythia8`                  |
| `WJetsToLNu_1J` | `WJetsToLNu_1J_TuneCP5_13TeV-amcatnloFXFX-pythia8`                  |
| `WJetsToLNu_2J` | `WJetsToLNu_2J_TuneCP5_13TeV-amcatnloFXFX-pythia8`                  |
| `signal`        | every dataset containing `HSCP` (old layout, use section 6 instead) |

The 2024 datasets (`Muon0`, `JetMET0`, `MuonEG`, `QCD_...`, ...) are not in the list. To
transfer one, add a line to the `DATASETS` dictionary at the top of the script. An unknown
`<dataType>` stops with the list of the known ones.

Output, with `<f1>` and `<f2>` the 2nd and 3rd `_`-separated fields of the task name:

    <f1>/<f1>_<f2>/<files>.root
    e.g. task Analysis_SingleMuon_Run2018A_CodeV... -> SingleMuon/SingleMuon_Run2018A/

If a task was submitted more than once (several `<YYMMDD_HHMMSS>` directories on dCache), each
submission goes to its own directory `<f1>/<f1>_<f2>_<YYMMDD_HHMMSS>/` and a `WARNING` is
printed. Remove the one you do not want before merging.

The last lines must read `Done: <n> block(s) copied, 0 failure(s).` A listing or a copy that
failed is listed as `FAILED:` and the exit code is 1.

**Step 2. Merge**, giving the absolute path of the dataset directory:

    python3 MergeJobs.py data "$PWD/SingleMuon"

Result:

    SingleMuon/SingleMuon_Run2018A_merged.root
    SingleMuon/SingleMuon_Run2018B_merged.root

In `data` mode only the files named `Histos*.root` are merged, and only their histograms
(`hadd -T`: the trees are dropped). The 2024 jobs write `output_N.root` ntuples, which this
mode does not take: to merge them, both `pattern` and `hadd_options` of the `data` entry of
`MODES`, at the top of `MergeJobs.py`, need changing.

---

## 8. Script reference

### CRAB side (run from `CMSSW_X_Y_Z/src/`)

The headers of these scripts give the full details; the points below are the ones that matter
most.

#### submitCrabJobsData.py, submitCrabJobsMC.py, submitCrabJobsSignals.py

    python3 submitCrabJobsData.py <version>
    python3 submitCrabJobsMC.py <version>
    python3 submitCrabJobsSignals.py <version>

- **Input**: `<version>` without the `V`; the active `datasetList` block of the script; from
  the current directory, `ntuplizer_cfg.py` and the dE/dx, pileup and golden JSON files of
  `HSCPAnalysis/Ntuplizer/data/` shipped with the jobs.
- **Output**: one CRAB task per dataset, `Analysis_<sample>_CodeV<version>`;
  `crab_projects/crab_Analysis_<sample>_CodeV<version>/`; the configuration submitted in
  `submittedConfigs/`; the ntuples on dCache.

Behaviour to know:

- The CRAB configuration is a template written to `4crab_*_Template.py` and removed at the
  end. It is written only if it does not exist yet: after an interrupted run, delete it by
  hand, or the next run silently reuses the old one.
- `submittedConfigs/` keeps one file per era for data, and only the last configuration for
  MC and signal: the others are overwritten.
- Data: `LumiBased`, 15 luminosity sections per job, golden JSON as lumi mask (2022 and 2024
  only). MC: `FileBased`, files per job set by hand (step 2 of section 4). Signal: one file per
  job.
- Signal: the gluino pythia8 and madgraphMLM samples of the same mass get the same request
  name. Submit the two lists with different versions.

#### StatusCrabJobs.py, ResubmitCrabJobs.py

    python3 StatusCrabJobs.py <version>
    python3 ResubmitCrabJobs.py <version> [<hours>]

- **Input**: the project directories `crab_projects/*CodeV<version>` of the current directory.
- **Output**: `crab status --verboseErrors` for each task; `crab resubmit --maxmemory 2500`
  for each task, once, or once per hour for `<hours>` passes.

`ResubmitCrabJobs.py` reads `crab_projects/` again at each pass and checks for `crab` before
starting. Neither script checks the return code of the `crab` commands.

#### crab_report_lumi.sh

    ./crab_report_lumi.sh <version> <lxplus directory>

- **Input**: the project directories `crab_projects/*CodeV<version>`; `<lxplus directory>`,
  an existing directory under `ComputeLumi/` on lxplus.
- **Output**: `lumis_<version>/<project>.json` (copy of each `processedLumis.json`), sent to
  `gcoulon@lxplus9.cern.ch:/afs/cern.ch/user/g/gcoulon/ComputeLumi/<lxplus directory>/`.

For data. A task whose report fails is flagged with `!!` and skipped; exit code 1 if no JSON
file at all was collected. The JSON files of an earlier run are removed locally, not on lxplus.

#### FindXSection.py

    cmsRun FindXSection.py inputFiles=<file1>,<file2>,... [maxEvents=<N>] [filePrepend=<prefix>]
    cmsRun FindXSection.py inputFiles_load=<list.txt>      [maxEvents=<N>] [filePrepend=<prefix>]

- **Input**: files of a simulated sample (MiniAODSIM); without `inputFiles`, one W+jets file
  set in `DEFAULT_INPUT_FILE`.
- **Output**: a summary on the standard error, ending with
  `After filter: final cross section = <value> +- <error> pb`. No file is written.

One file gives a rough value: pass several for a number to use in the analysis.

### Bookkeeping side (run from this clone)

#### WriteFileinTXT.py

    python3 WriteFileinTXT.py "<gfal-ls command>" <output.txt>

- **Input**: `<gfal-ls command>`, a `gfal-ls davs://...` on one `000N` directory, in quotes;
  `<output.txt>`, the list to fill (its directory must exist).
- **Output**: one line `root://<same path>/<file>.root` appended to `<output.txt>` for each
  `.root` file returned by `gfal-ls`. Exit code 0 if lines were written, 1 otherwise.

Behaviour to know:

- It appends: running the same command twice duplicates the lines.
- Entries that are not `.root` files (a `log/` sub-directory for instance) are skipped and
  printed as `Skipped`.
- If `gfal-ls` fails (expired proxy, wrong path) or finds no `.root` file, nothing is written
  and an `ERROR:` is printed.

#### ScriptWrite.sh

    ./ScriptWrite.sh

- **Input**: none; edit the file to choose which blocks are uncommented.
- **Output**: the `.txt` files named on the uncommented lines, relative to the current
  directory.

Currently uncommented: the `BKG/TTbar1L1Nu2024/V22p0.txt` block.

#### getjobsSignal.py

    python3 getjobsSignal.py <version>

- **Input**: `<version>`, the code version without the `V` (e.g. `21p0`).
- **Output**:
  `/scratch/ui3_1/gcoulon/HSCP_prod/SIGNAL/V<version>/<Model>_<Par-M-mass>_<YYMMDD_HHMMSS>/output_N.root`.
  Exit code 0 if something was copied and nothing failed, 1 otherwise.

Behaviour to know:

- `<Model>_<Par-M-mass>` is the first two `_`-separated fields of the dCache dataset name.
- All `000N` blocks of a task are copied into the same sub-directory.
- All signal samples of that version are taken; there is no option to select one model.
- A task is selected when its name contains exactly `V<version>`: `19p6` takes `CodeV19p6` but
  not `CodeV19p60`. Tasks of a longer version are printed as `Ignored (other version)`.
- A summary is printed at the end, with every listing or copy that failed as `FAILED:`.
- `gfal-copy` is called without `--force`: files already present locally are not overwritten.

#### MergeJobs.py

    python3 MergeJobs.py signal <version>
    python3 MergeJobs.py data   <inputDir>
    python3 MergeJobs.py -h

|                | `signal`                                              | `data`                                     |
|----------------|-------------------------------------------------------|--------------------------------------------|
| Input          | `<version>` without the `V`                           | `<inputDir>`, absolute, or relative to `/opt/sbg/cms/ui3_data1/gcoulon/HSCP_prod` |
| Directory read | `/scratch/ui3_1/gcoulon/HSCP_prod/SIGNAL/V<version>/` | `<inputDir>/`                              |
| Files merged   | `<subDir>/*.root`                                     | `<subDir>/Histos*.root`                    |
| `hadd` options | none (trees and histograms)                           | `-j 16 -T` (16 processes, histograms only) |
| Output         | `V<version>/<subDir without _date_time>_merged.root`  | `<inputDir>/<subDir>_merged.root`          |

Behaviour to know:

- Only sub-directories are processed; an existing `*_merged.root` is deleted and rebuilt.
- A sub-directory without matching files is skipped.
- If `hadd` fails, the incomplete merged file is removed, the sub-directory is listed as
  `FAILED` in the summary, and the exit code is 1.
- `signal` mode: two sub-directories of the same sample (same name, different timestamp) write
  to the same merged file. A `WARNING` is printed and only the most recent is kept.
- The settings of both modes are in the `MODES` dictionary at the top of the script.

#### transfer_prod.py

    python3 transfer_prod.py <version> <dataType>

- **Input**: `<version>`, the code version without the `V`; `<dataType>`, see section 7.
- **Output**, relative to the current directory:
  - data/background: `<f1>/<f1>_<f2>/`
  - `signal`: `SIGNAL/V<version>/<Par-M-mass>_V<version>/<Par-M-mass>_CodeV<version>/`

  Exit code 0 if something was copied and nothing failed, 1 otherwise.

Behaviour to know:

- The `signal` layout is the old one, not the one `MergeJobs.py signal` expects. The naming for
  ZPrime samples is kept as comments in the code.
- Tasks are selected as in `getjobsSignal.py`: exact `V<version>`, longer versions ignored.
- A task with several timestamp directories (submitted more than once) is copied once per
  submission, each into its own directory suffixed with `_<YYMMDD_HHMMSS>`, with a `WARNING`.
- A summary is printed at the end, with every listing or copy that failed as `FAILED:`.
- The datasets behind each `<dataType>` are in the `DATASETS` dictionary at the top of the
  script.

---

## 9. Productions

### Versions read by the analysis

As given in the headers of the submission scripts (versions read by TupleAnalysis,
`cfg/configFile.txt`, in October 2026), with what this directory holds for each:

| Production            | Versions        | Here                                                                 |
|-----------------------|-----------------|----------------------------------------------------------------------|
| JetMET data           | V12p35          | -                                                                    |
| MuonEG data           | V17p4x          | `MuonEG2024/V17p40.txt` ... `V17p46.txt` (`ScriptWrite.sh`)          |
| Muon data             | V18p10x         | `Mu2024/V18p100.txt` ... `V18p106.txt` (`ScriptWrite.sh`, in git)    |
| W+jets                | V14p14, V14p60x | `BKG/Wjets2024/V14p601.txt` ... `V14p6010.txt` (`ScriptWrite.sh`); V14p14: - |
| TTbar                 | V15p10          | -                                                                    |
| QCD                   | V16p3x          | -                                                                    |
| Semi-leptonic TTbar   | V22p1           | -                                                                    |
| Run 2 gluino          | V13p2           | -                                                                    |
| Run 3 gluino          | V19p0, V19p12   | V19p0: `SIGNAL/Gluino_Run3_pythia/`; V19p12: -                       |
| Pair-produced stau    | V20p0           | `SIGNAL/V20p0/`                                                      |
| Stop                  | V21p0           | `SIGNAL/V21p0/`                                                      |

`-`: no listing command in `ScriptWrite.sh` and nothing of that version in `SIGNAL/`.

### File lists in git (`Mu2024/`)

| Files                           | Content                                                   | Code   | Submitted  |
|---------------------------------|-----------------------------------------------------------|--------|------------|
| `V18p100.txt` ... `V18p106.txt` | Muon0 + Muon1, one file per era, C to I                   | V18p1  | 2026-06-10 |
| `V18p00.txt` ... `V18p06.txt`   | Muon1 only, one file per era, C to I (I: `Run2024I0bis`); one `000N` block each | V18p0  | 2026-02-16 |
| `V12p22.txt`                    | Muon0 Run2024G                                            | V12p22 | 2026-01-29 |
| `testMu2024.txt`                | 23 files of Muon0 Run2024E                                | V18p1  | 2026-06-10 |

Only `V18p10x` is recorded in `ScriptWrite.sh`.

### File lists recorded in ScriptWrite.sh (on the UI)

Data, one `.txt` per era; the last digit(s) of the name are the era index:

| Directory     | Files                           | Datasets          | Code   | Submitted  | Eras (index order)  |
|---------------|---------------------------------|-------------------|--------|------------|---------------------|
| `MuonEG2024/` | `V17p40.txt` ... `V17p46.txt`   | MuonEG            | V17p4  | 2026-03-10 | C, D, E, F, G, H, I |
| `Mu2024/`     | `V18p100.txt` ... `V18p106.txt` | Muon0 + Muon1     | V18p1  | 2026-06-10 | C, D, E, F, G, H, I |
| `JetMET2024/` | `V12p310.txt` ... `V12p316.txt` | JetMET0 + JetMET1 | V12p31 | 2026-06-30 | C, D, E, F, G, H, I |

In `Mu2024/` and `JetMET2024/`, the era I list also contains the `bis` tasks (`Run2024I0bis`,
and `Run2024I1bis` for JetMET1).

Simulated backgrounds, one `.txt` per sample or bin:

| Directory             | Files                            | Sample                                     | Code           | Submitted       |
|-----------------------|----------------------------------|--------------------------------------------|----------------|-----------------|
| `BKG/QCD2024/`        | `V16p21.txt` ... `V16p212.txt`   | QCD MuEnriched, 12 PT bins                 | V16p2          | 2026-07-10      |
| `BKG/Wjets2024/`      | `V14p601.txt` ... `V14p6010.txt` | WtoLNu-2Jets, 1J and 2J, 5 PTLNu bins each | V14p6, V14p7 * | 2026-02-13 / 14 |
| `BKG/Wjets2024/`      | `V14p13.txt`                     | WtoMuNu-2Jets                              | V14p13         | 2026-07-09      |
| `BKG/TTbar2024/`      | `V15p9.txt`                      | TTto2L2Nu                                  | V14p13 *       | 2026-07-09      |
| `BKG/TTbar1L1Nu2024/` | `V22p0.txt`                      | TTtoLNu2Q                                  | V22p0          | 2026-07-21      |

Bin order:

- QCD, index 1 to 12: PT 15to20, 20to30, 30to50, 50to80, 80to120, 120to170, 170to300,
  300to470, 470to600, 600to800, 800to1000, 1000.
- Wjets, index 01 to 05: 1J, PTLNu 40to100, 100to200, 200to400, 400to600, 600;
  index 06 to 010: 2J, same bins.

(*) Names that do not match the code version of the task they list:

- `BKG/Wjets2024/V14p604.txt`, `V14p605.txt`, `V14p609.txt`, `V14p6010.txt` (PTLNu 400to600 and
  600 bins) come from `CodeV14p7` tasks.
- `BKG/TTbar2024/V15p9.txt` comes from the task `Analysis_TTto2L2Nu_CodeV14p13`.

### SIGNAL/ (on the UI)

Productions made with `getjobsSignal.py` + `MergeJobs.py signal`. Each contains one per-job
sub-directory and one merged file per mass point:

| Directory | Sample         | Submitted  | Mass points (GeV)                                                   | Size   |
|-----------|----------------|------------|---------------------------------------------------------------------|--------|
| `V19p2/`  | HSCP-Gluino    | 2026-04-16 | 1100, 1200, 1300, 1400, 1600, 1800, 2000, 2200, 2400, 2600          | 3.7 GB |
| `V19p3/`  | HSCP-Gluino    | 2026-04-17 | same                                                                | 3.7 GB |
| `V19p4/`  | HSCP-Gluino    | 2026-06-12 | same                                                                | 4.8 GB |
| `V19p5/`  | HSCP-Gluino    | 2026-06-21 | same                                                                | 4.8 GB |
| `V19p6/`  | HSCP-Gluino    | 2026-06-26 | same                                                                | 4.8 GB |
| `V20p0/`  | HSCP-Pair-Stau | 2026-06-29 | 247, 308, 432, 557, 651, 745, 871, 1029, 1218, 1409, 1599           | 5.6 GB |
| `V21p0/`  | HSCP-Stop      | 2026-07-17 | 700, 800, 900, 1000, 1200, 1400, 1600, 1800, 2000, 2200, 2400, 2600 | 6.0 GB |

    SIGNAL/V21p0/
        HSCP-Stop_Par-M-1000_260717_081327/output_1.root ...   <- per-job files (copy of dCache)
        HSCP-Stop_Par-M-1000_merged.root                       <- file to use

About half of each size is the per-job files, the other half the merged files.

Older files, merged only (no per-job sub-directories):

| Directory               | Files                                                                        | Size    |
|-------------------------|------------------------------------------------------------------------------|---------|
| `Gluino_Run3_pythia/`   | `Par-M-<mass>_CodeV19p0_merged.root`, 9 masses: 1000 to 2600 in steps of 200 | 1.7 GB  |
| `Gluino_Run3_madgraph/` | `Par-M-<mass>_CodeV19p1_merged.root`, the 10 gluino masses listed above      | 1.8 GB  |
| `Gluino_Run2_madgraph/` | `Gluino_Run2_MET_madgraph_2000.root`                                         | 0.15 GB |
| `Gluino2000_AOD/`       | `nt_run3_skim_1.root` ... `nt_run3_skim_5.root`                              | 0.8 GB  |

`SIGNAL/` takes about 38 GB in total (October 2026).

---

## 10. Using the scripts from another account

Everything points to the `gcoulon` areas. To run the scripts for your own productions, change:

| Script                     | Where                                              | Current value                                                   |
|----------------------------|----------------------------------------------------|-----------------------------------------------------------------|
| `submitCrabJobs*.py`       | template: `config.Data.outLFNDirBase`, `config.Site.storageSite` | `/store/user/gcoulon/HSCP`, `T2_FR_IPHC`          |
| `crab_report_lumi.sh`      | `REMOTE`                                           | `gcoulon@lxplus9.cern.ch:/afs/cern.ch/user/g/gcoulon/ComputeLumi` |
| `ScriptWrite.sh`           | each line                                          | dCache path `.../store/user/gcoulon/HSCP/...`                   |
| `getjobsSignal.py`         | `OUTPUT_BASE_DIR` (top of file)                    | `/scratch/ui3_1/gcoulon/HSCP_prod/SIGNAL/`                      |
| `getjobsSignal.py`         | `BASE_URL` (top of file)                           | `davs://sbgdcache.in2p3.fr/cms/phedex/store/user/gcoulon/HSCP/` |
| `MergeJobs.py`             | `MODES["signal"]["base_dir"]`                      | `/scratch/ui3_1/gcoulon/HSCP_prod/SIGNAL`                       |
| `MergeJobs.py`             | `MODES["data"]["base_dir"]`                        | `/opt/sbg/cms/ui3_data1/gcoulon/HSCP_prod`                      |
| `transfer_prod.py`         | `BASE_URL` (top of file)                           | `davs://sbgdcache.in2p3.fr/cms/phedex/store/user/gcoulon/HSCP/` |

`WriteFileinTXT.py`, `StatusCrabJobs.py`, `ResubmitCrabJobs.py` and `FindXSection.py` have no
account-specific path. `ScriptWrite.sh` and `transfer_prod.py` write relative to the current
directory.

To only *read* the existing productions, nothing needs changing: use the `.txt` lists and the
`SIGNAL/V<version>/*_merged.root` files of the UI directly. The `SIGNAL/` tree there belongs to
`gcoulon` and is not group-writable.

---

## 11. Pitfalls

### CRAB side

**`crab submit` refuses: the project directory already exists.**
The version was already used for this sample. Pick a new version. For the signal, this also
happens when the gluino pythia8 and madgraphMLM lists are submitted with the same version.

**A change in a submission script has no effect.**
A `4crab_*_Template.py` left by an interrupted run is reused. Delete it and submit again.

**W+jets jobs read 5 files each, or Run 2 signal is submitted with `year=2024`.**
The template was not adapted to the list (step 2 of section 4).

**The build or the CRAB sandbox includes `HiggsAnalysis/` and `CombineHarvester/`.**
They were not moved out of `src/` before `scram b` (step 1 of section 4).

**`!! report failed` or `!! no processedLumis.json` from `crab_report_lumi.sh`.**
The jobs of that task are not finished, or `crab report` failed: run the script again once all
the jobs are done.

### Bookkeeping side

**A `.txt` has duplicated lines.**
`ScriptWrite.sh` was run with old blocks uncommented, or run twice. Delete the `.txt` and
regenerate it.

**`ERROR: gfal-ls failed ...` or `ERROR: no .root file found ...` from `WriteFileinTXT.py`.**
That directory was not listed (proxy, path) and nothing was written for it. The other lines of
the block did write theirs, so delete the `.txt`, fix the cause and rerun the block.

**`ERROR: output directory does not exist` from `WriteFileinTXT.py`.**
`mkdir -p` the directory of the `.txt` first.

**An older `.txt` has lines not ending with `.root`, or ending with `/`.**
The lists written before October 2026 come from an earlier version of the script, which wrote
every entry of the directory, and a bogus line when the listing failed. To check a list:
`grep -v '\.root$' <list>.txt` must print nothing.

**`FAILED:` lines at the end of `getjobsSignal.py` or `transfer_prod.py`.**
A listing or a copy failed (proxy, network). Delete the sub-directories concerned (files
already present are not overwritten, so a partial copy would stay), rerun the command, then
check that the number of sub-directories is the expected one.

**`WARNING: ... was submitted 2 times` from `transfer_prod.py`.**
The task has several timestamp directories on dCache. Each one was copied to its own
directory; remove the one you do not want before merging.

**`WARNING: ... all write to ..._merged.root` from `MergeJobs.py`.**
The same sample is present twice under that version. Remove the sub-directory you do not want
and merge again.

**`hadd not found`.**
ROOT is not set up in the shell.

**`Directory does not exist: /opt/sbg/cms/ui3_data1/...`.**
`MergeJobs.py data` got a relative path, resolved against its hard-coded base. Give an absolute
path.

**`gfal-ls` / `gfal-copy` fail with Python or library errors.**
Possible clash with a CMSSW environment: run the transfer in a shell without `cmsenv`, then
merge in a shell with ROOT.