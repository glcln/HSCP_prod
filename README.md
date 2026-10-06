# HSCP_prod

Bookkeeping directory for the HSCP analysis productions (CMS, 2024 data, IPHC Strasbourg).
The ROOT files produced by the CRAB jobs stay on the Strasbourg dCache; this directory holds
what is needed to use them:

- **file lists** (`.txt`, one XRootD URL per line) for the data and background productions,
  which are read remotely;
- **local copies** of the signal productions, merged into one ROOT file per mass point;
- the **scripts** that produce both.

Location: `/scratch/ui3_1/gcoulon/HSCP_prod` (sbgui machines).
The tree is described as of 2026-10-06.

Sections:

1. What is in the directory
2. Before you start
3. How to list a production in a .txt
4. How to transfer and merge a signal production
5. How to transfer and merge a data or background production
6. Script reference
7. Productions currently recorded
8. Using the scripts from another account
9. Pitfalls

---

## 1. What is in the directory

### Scripts

| File                     | Role                                                                  |
|--------------------------|-----------------------------------------------------------------------|
| `WriteFileinTXT.py` | Lists one dCache directory and appends its content to a `.txt`        |
| `ScriptWrite.sh`         | Calls `WriteFileinTXT.py` for each production; record of every `.txt` |
| `getjobsSignal.py`       | Copies all signal samples of a code version to `SIGNAL/V<version>/`   |
| `MergeJobs.py`           | Merges the copied ROOT files with `hadd` (modes `signal` and `data`)  |
| `transfer_prod.py`       | Older transfer script for data/background (Run 2 dataset names)       |

### Sub-directories

| Directory     | Content                                                                  |
|---------------|--------------------------------------------------------------------------|
| `Mu2024/`     | File lists, Muon0 + Muon1 2024 data                                      |
| `MuonEG2024/` | File lists, MuonEG 2024 data                                             |
| `JetMET2024/` | File lists, JetMET0 + JetMET1 2024 data                                  |
| `BKG/`        | File lists, simulated backgrounds, in `QCD2024/`, `Wjets2024/`, `TTbar2024/`, `TTbar1L1Nu2024/` |
| `SIGNAL/`     | Local signal productions (per-job and merged files), plus older merged files |
| `AOD2024/`    | Not filled by any script here and absent from `ScriptWrite.sh` |

The `.txt` files and the signal productions are detailed in section 7.

### Where the productions are on dCache

    davs://sbgdcache.in2p3.fr/cms/phedex/store/user/gcoulon/HSCP/<Dataset>/<Task>/<YYMMDD_HHMMSS>/<000N>/<file>.root

| Level             | Meaning                                  | Example                             |
|-------------------|------------------------------------------|-------------------------------------|
| `<Dataset>`       | Primary dataset or MC sample             | `Muon0`, `HSCP-Stop_Par-M-1000_...` |
| `<Task>`          | CRAB task, ends with the code version    | `Analysis_Muon0_Run2024C_CodeV18p1` |
| `<YYMMDD_HHMMSS>` | CRAB submission timestamp                | `260610_180305`                     |
| `<000N>`          | Block of 1000 jobs (`0000`, `0001`, ...) | `0000`                              |

The **code version** (`V18p1`, `V21p0`, ...) is what identifies a production everywhere in
this directory.

---

## 2. Before you start

| Needed for                               | What                                                  |
|------------------------------------------|-------------------------------------------------------|
| Any access to dCache (listing, transfer) | A valid CMS grid proxy: `voms-proxy-init --voms cms`  |
| Listing and transfer                     | The `gfal-ls` and `gfal-copy` commands                |
| Merging                                  | ROOT in the environment (`hadd`), e.g. after `cmsenv` |
| All the scripts                          | Python 3                                              |

Write access: the `SIGNAL/` tree belongs to `gcoulon` and is not group-writable. To produce
new lists or transfers from another account, see section 8.

---

## 3. How to list a production in a .txt

Goal: one `.txt` containing the XRootD URL of every file of a production, to read it remotely.

**Step 1. Find the production on dCache.** Go down the levels until the `000N` directories:

    gfal-ls davs://sbgdcache.in2p3.fr/cms/phedex/store/user/gcoulon/HSCP/
    gfal-ls davs://sbgdcache.in2p3.fr/cms/phedex/store/user/gcoulon/HSCP/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/
    gfal-ls davs://sbgdcache.in2p3.fr/cms/phedex/store/user/gcoulon/HSCP/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/Analysis_TTtoLNu2Q_CodeV22p0/
    gfal-ls davs://sbgdcache.in2p3.fr/cms/phedex/store/user/gcoulon/HSCP/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/Analysis_TTtoLNu2Q_CodeV22p0/260721_185412/
    # -> 0000  0001  0002

**Step 2. Add a block to `ScriptWrite.sh`**, one line per `000N` directory, all writing to
the same `.txt`:

    # TTbar 1L1NU 2024
    python3 WriteFileinTXT.py "gfal-ls davs://sbgdcache.in2p3.fr/cms/phedex//store/user/gcoulon/HSCP/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/Analysis_TTtoLNu2Q_CodeV22p0/260721_185412/0000" BKG/TTbar1L1Nu2024/V22p0.txt
    python3 WriteFileinTXT.py "gfal-ls davs://sbgdcache.in2p3.fr/cms/phedex//store/user/gcoulon/HSCP/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/Analysis_TTtoLNu2Q_CodeV22p0/260721_185412/0001" BKG/TTbar1L1Nu2024/V22p0.txt
    python3 WriteFileinTXT.py "gfal-ls davs://sbgdcache.in2p3.fr/cms/phedex//store/user/gcoulon/HSCP/TTtoLNu2Q_TuneCP5_13p6TeV_powheg-pythia8/Analysis_TTtoLNu2Q_CodeV22p0/260721_185412/0002" BKG/TTbar1L1Nu2024/V22p0.txt

- The first argument is the whole command in quotes, of the form `gfal-ls davs://...`. The
  script runs it and writes the same paths with `root://` instead of `davs://`.
- To put several datasets in one list (e.g. Muon0 and Muon1 of the same era), give them the
  same `.txt`.
- `.txt` naming used so far: `V<code version><index>.txt`, the index numbering the eras or
  the bins (see section 7).

**Step 3. Comment out every other block.** Each uncommented line is executed again and
*appends* to its `.txt`, which would duplicate the entries of the older lists.

**Step 4. Create the output directory if it is new**, and delete the `.txt` if you are
regenerating it (the script appends, it never overwrites):

    mkdir -p BKG/TTbar1L1Nu2024
    rm -f BKG/TTbar1L1Nu2024/V22p0.txt

**Step 5. Run from this directory** (the `.txt` paths are relative):

    cd /scratch/ui3_1/gcoulon/HSCP_prod
    voms-proxy-init --voms cms
    bash ScriptWrite.sh

**Step 6. Check the result.** Each line of `ScriptWrite.sh` must answer
`Writing <n> line(s) to file: ...`. An `ERROR:` means that this directory was not listed and
that nothing was written for it (see section 9). Then:

    wc -l BKG/TTbar1L1Nu2024/V22p0.txt                 # number of files
    sort BKG/TTbar1L1Nu2024/V22p0.txt | uniq -d        # must print nothing (no duplicate)

Each line looks like:

    root://sbgdcache.in2p3.fr/cms/phedex//store/user/gcoulon/HSCP/<Dataset>/<Task>/<YYMMDD_HHMMSS>/0000/<file>.root

Leave the block in `ScriptWrite.sh` (commented) once done: the file is the only record of
which dCache directories each `.txt` was built from.

---

## 4. How to transfer and merge a signal production

Goal: `SIGNAL/V<version>/<sample>_merged.root`, one file per mass point.

**Step 1. Transfer.** The argument is the code version *without* the `V`:

    voms-proxy-init --voms cms
    python3 getjobsSignal.py 21p0

Every dCache dataset whose name contains `HSCP` is scanned, and every task of that version
(exact match: `19p6` does not take `CodeV19p60`) is copied to:

    SIGNAL/V21p0/<Model>_<Par-M-mass>_<YYMMDD_HHMMSS>/output_N.root
    e.g. SIGNAL/V21p0/HSCP-Stop_Par-M-1000_260717_081327/output_1.root

**Step 2. Check the transfer.** The last lines must read
`Done: <n> block(s) copied to ..., 0 failure(s).` A listing or a copy that failed is listed
as `FAILED:` and the exit code is 1; in that case delete the sub-directories concerned and
rerun the command. Then compare with what is expected:

    ls SIGNAL/V21p0            # one sub-directory per mass point
    ls SIGNAL/V21p0/*/ | head  # output_N.root files inside

**Step 3. Merge** (ROOT needed):

    python3 MergeJobs.py signal 21p0

Result, next to the sub-directories:

    SIGNAL/V21p0/<Model>_<Par-M-mass>_merged.root
    e.g. SIGNAL/V21p0/HSCP-Stop_Par-M-1000_merged.root

**Step 4. Check the merge.** The last lines must read `Done: <n> merged, 0 failed.` with
`<n>` equal to the number of mass points. Failed sub-directories are listed and the exit
code is 1.

Both scripts work on absolute paths, so the current directory does not matter. Rerunning the
merge is safe: existing `*_merged.root` files are deleted and rebuilt, the sub-directories
are not touched.

---

## 5. How to transfer and merge a data or background production

Data and background productions are normally read through the `.txt` lists (section 3).
For the cases where a local copy is needed there is `transfer_prod.py`, but it only knows
Run 2 dataset names.

**Step 1. Transfer**, from the directory where the copy must land (output paths are relative):

    cd /scratch/ui3_1/gcoulon/HSCP_prod
    voms-proxy-init --voms cms
    python3 transfer_prod.py <version> <dataType>

`<version>` is the code version without the `V`. `<dataType>` is one of:

| `<dataType>`    | dCache dataset scanned                                              |
|-----------------|---------------------------------------------------------------------|
| `SingleMu`      | `SingleMuon`                                                        |
| `MET`           | `MET`                                                               |
| `WJetsToLNu_0J` | `WJetsToLNu_0J_TuneCP5_13TeV-amcatnloFXFX-pythia8`                  |
| `WJetsToLNu_1J` | `WJetsToLNu_1J_TuneCP5_13TeV-amcatnloFXFX-pythia8`                  |
| `WJetsToLNu_2J` | `WJetsToLNu_2J_TuneCP5_13TeV-amcatnloFXFX-pythia8`                  |
| `signal`        | every dataset containing `HSCP` (old layout, use section 4 instead) |

The 2024 datasets (`Muon0`, `JetMET0`, `MuonEG`, `QCD_...`, ...) are not in the list. To
transfer one, add a line to the `DATASETS` dictionary at the top of the script. An unknown
`<dataType>` stops with the list of the known ones.

Output, with `<f1>` and `<f2>` the 2nd and 3rd `_`-separated fields of the task name:

    <f1>/<f1>_<f2>/<files>.root
    e.g. task Analysis_SingleMuon_Run2018A_CodeV... -> SingleMuon/SingleMuon_Run2018A/

If a task was submitted more than once (several `<YYMMDD_HHMMSS>` directories on dCache),
each submission goes to its own directory `<f1>/<f1>_<f2>_<YYMMDD_HHMMSS>/` and a `WARNING`
is printed. Remove the one you do not want before merging.

The last lines must read `Done: <n> block(s) copied, 0 failure(s).` A listing or a copy that
failed is listed as `FAILED:` and the exit code is 1.

**Step 2. Merge**, giving the absolute path of the dataset directory:

    python3 MergeJobs.py data "$PWD/SingleMuon"

Result:

    SingleMuon/SingleMuon_Run2018A_merged.root
    SingleMuon/SingleMuon_Run2018B_merged.root

In `data` mode only the files named `Histos*.root` are merged, and only their histograms
(`hadd -T`: the trees are dropped). If the job outputs have another name, change `pattern`
in the `MODES` dictionary at the top of `MergeJobs.py`.

---

## 6. Script reference

### WriteFileinTXT.py

    python3 WriteFileinTXT.py "<gfal-ls command>" <output.txt>

- **Input**: `<gfal-ls command>`, a `gfal-ls davs://...` on one `000N` directory, in quotes;
  `<output.txt>`, the list to fill (its directory must exist).
- **Output**: one line `root://<same path>/<file>.root` appended to `<output.txt>` for each
  `.root` file returned by `gfal-ls`. Exit code 0 if lines were written, 1 otherwise.

Behaviour to know:

- It appends: running the same command twice duplicates the lines.
- Entries that are not `.root` files (a `log/` sub-directory for instance) are skipped and
  printed as `Skipped`.
- If `gfal-ls` fails (expired proxy, wrong path) or finds no `.root` file, nothing is
  written and an `ERROR:` is printed.

### ScriptWrite.sh

    bash ScriptWrite.sh

- **Input**: none; edit the file to choose which blocks are uncommented.
- **Output**: the `.txt` files named on the uncommented lines, relative to the current
  directory.

Currently uncommented: the `BKG/TTbar1L1Nu2024/V22p0.txt` block.

### getjobsSignal.py

    python3 getjobsSignal.py <version>

- **Input**: `<version>`, the code version without the `V` (e.g. `21p0`).
- **Output**:
  `/scratch/ui3_1/gcoulon/HSCP_prod/SIGNAL/V<version>/<Model>_<Par-M-mass>_<YYMMDD_HHMMSS>/output_N.root`.
  Exit code 0 if something was copied and nothing failed, 1 otherwise.

Behaviour to know:

- `<Model>_<Par-M-mass>` is the first two `_`-separated fields of the dCache dataset name.
- All `000N` blocks of a task are copied into the same sub-directory.
- All signal samples of that version are taken; there is no option to select one model.
- A task is selected when its name contains exactly `V<version>`: `19p6` takes `CodeV19p6`
  but not `CodeV19p60`. Tasks of a longer version are printed as `Ignored (other version)`.
- A summary is printed at the end, with every listing or copy that failed as `FAILED:`.
- `gfal-copy` is called without `--force`: files already present locally are not overwritten.

### MergeJobs.py

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
- `signal` mode: two sub-directories of the same sample (same name, different timestamp)
  write to the same merged file. A `WARNING` is printed and only the most recent is kept.
- The settings of both modes are in the `MODES` dictionary at the top of the script.

### transfer_prod.py

    python3 transfer_prod.py <version> <dataType>

- **Input**: `<version>`, the code version without the `V`; `<dataType>`, see section 5.
- **Output**, relative to the current directory:
  - data/background: `<f1>/<f1>_<f2>/`
  - `signal`: `SIGNAL/V<version>/<Par-M-mass>_V<version>/<Par-M-mass>_CodeV<version>/`

  Exit code 0 if something was copied and nothing failed, 1 otherwise.

Behaviour to know:

- The `signal` layout is the old one, not the one `MergeJobs.py signal` expects. The naming
  for ZPrime samples is kept as comments in the code.
- Tasks are selected as in `getjobsSignal.py`: exact `V<version>`, longer versions ignored.
- A task with several timestamp directories (submitted more than once) is copied once per
  submission, each into its own directory suffixed with `_<YYMMDD_HHMMSS>`, with a `WARNING`.
- A summary is printed at the end, with every listing or copy that failed as `FAILED:`.
- The datasets behind each `<dataType>` are in the `DATASETS` dictionary at the top of the
  script.

---

## 7. Productions currently recorded

### File lists (from ScriptWrite.sh)

Data, one `.txt` per era; the last digit(s) of the name are the era index:

| Directory     | Files                           | Datasets          | Code   | Submitted  | Eras (index order)  |
|---------------|---------------------------------|-------------------|--------|------------|---------------------|
| `MuonEG2024/` | `V17p40.txt` ... `V17p46.txt`   | MuonEG            | V17p4  | 2026-03-10 | C, D, E, F, G, H, I |
| `Mu2024/`     | `V18p100.txt` ... `V18p106.txt` | Muon0 + Muon1     | V18p1  | 2026-06-10 | C, D, E, F, G, H, I |
| `JetMET2024/` | `V12p310.txt` ... `V12p316.txt` | JetMET0 + JetMET1 | V12p31 | 2026-06-30 | C, D, E, F, G, H, I |

In `Mu2024/` and `JetMET2024/`, the era I list also contains the `bis` tasks
(`Run2024I0bis`, and `Run2024I1bis` for JetMET1).

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

- `BKG/Wjets2024/V14p604.txt`, `V14p605.txt`, `V14p609.txt`, `V14p6010.txt` (PTLNu 400to600
  and 600 bins) come from `CodeV14p7` tasks.
- `BKG/TTbar2024/V15p9.txt` comes from the task `Analysis_TTto2L2Nu_CodeV14p13`.

### SIGNAL/

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

`SIGNAL/` takes about 38 GB in total.

---

## 8. Using the scripts from another account

Everything points to the `gcoulon` areas. To run the scripts for your own productions, copy
them and change:

| Script             | Where                                          | Current value                                                   |
|--------------------|------------------------------------------------|-----------------------------------------------------------------|
| `ScriptWrite.sh`   | each line                                      | dCache path `.../store/user/gcoulon/HSCP/...`                   |
| `getjobsSignal.py` | `OUTPUT_BASE_DIR` (top of file)                | `/scratch/ui3_1/gcoulon/HSCP_prod/SIGNAL/`                      |
| `getjobsSignal.py` | `BASE_URL` (top of file)                       | `davs://sbgdcache.in2p3.fr/cms/phedex/store/user/gcoulon/HSCP/` |
| `MergeJobs.py`     | `MODES["signal"]["base_dir"]`                  | `/scratch/ui3_1/gcoulon/HSCP_prod/SIGNAL`                       |
| `MergeJobs.py`     | `MODES["data"]["base_dir"]`                    | `/opt/sbg/cms/ui3_data1/gcoulon/HSCP_prod`                      |
| `transfer_prod.py` | `BASE_URL` (top of file)                       | `davs://sbgdcache.in2p3.fr/cms/phedex/store/user/gcoulon/HSCP/` |

`WriteFileinTXT.py` has no hard-coded path. `ScriptWrite.sh` and `transfer_prod.py`
write relative to the current directory.

To only *read* the existing productions, nothing needs changing: use the `.txt` lists and
the `SIGNAL/V<version>/*_merged.root` files directly.

---

## 9. Pitfalls

**A `.txt` has duplicated lines.**
`ScriptWrite.sh` was run with old blocks uncommented, or run twice. Delete the `.txt` and
regenerate it.

**`ERROR: gfal-ls failed ...` or `ERROR: no .root file found ...` from `WriteFileinTXT.py`.**
That directory was not listed (proxy, path) and nothing was written for it. The other lines
of the block did write theirs, so delete the `.txt`, fix the cause and rerun the block.

**`ERROR: output directory does not exist` from `WriteFileinTXT.py`.**
`mkdir -p` the directory of the `.txt` first.

**An older `.txt` has lines not ending with `.root`, or ending with `/`.**
The lists written before October 2026 come from an earlier version of the script, which
wrote every entry of the directory, and a bogus line when the listing failed. To check a
list: `grep -v '\.root$' <list>.txt` must print nothing.

**`FAILED:` lines at the end of `getjobsSignal.py` or `transfer_prod.py`.**
A listing or a copy failed (proxy, network). Delete the sub-directories concerned (files
already present are not overwritten, so a partial copy would stay), rerun the command, then
check that the number of sub-directories is the expected one.

**`WARNING: ... was submitted 2 times` from `transfer_prod.py`.**
The task has several timestamp directories on dCache. Each one was copied to its own
directory; remove the one you do not want before merging.

**`WARNING: ... all write to ..._merged.root` from `MergeJobs.py`.**
The same sample is present twice under that version. Remove the sub-directory you do not
want and merge again.

**`hadd not found`.**
ROOT is not set up in the shell.

**`Directory does not exist: /opt/sbg/cms/ui3_data1/...`.**
`MergeJobs.py data` got a relative path, resolved against its hard-coded base. Give an
absolute path.

**`gfal-ls` / `gfal-copy` fail with Python or library errors.**
Possible clash with a CMSSW environment: run the transfer in a shell without `cmsenv`, then
merge in a shell with ROOT.