# GPU path: Gemma 4 12B on a Slurm GPU node

These scripts run the observer's asynchronous suite with v2 pictures and Gemma 4 12B
on one GPU node. OpenFOAM runs in an Apptainer image. llama-server runs on the host
GPU, and the callback reaches it at 127.0.0.1.

| Script | What it does |
|---|---|
| `setup_12b.sh` | Downloads the CUDA build of llama.cpp b11429, the 12B weights and the image projector into `POD_LLM_RUNTIME`, about 8 GB, and checks their SHA-256. Records the SHA-256 of these files and of the `llama-server` there, and whether that server runs. |
| `build_llama_cuda.sh` | Builds llama.cpp b11429 from source with CUDA into the same folder. |
| `start_server.sh` | Starts `llama-server` on the node's GPU with all layers offloaded, writes `server.pid` and waits for `/health`, up to 10 minutes. |
| `stop_server.sh` | Stops the server named in `server.pid`. |
| `async_v2.slurm` | The batch job: starts the server, runs `run_demo.sh` with `POD_SUITE=async` and `LLM_IMAGE_STYLE=v2` in the image, and stops the server. |

## What is required

- `POD_LLM_RUNTIME`: the folder for the weights and `llama-server`. The job's default
  is `../llm-runtime-12b` beside the repository, like its outputs.
- The Gemma licence applies to the weights: see
  `google/gemma-4-12B-it-qat-q4_0-gguf` on Hugging Face. If `HF_TOKEN` is set, it is
  sent with the download. A public repository needs none, and neither do weights that
  are already there.
- `SIF`: an OpenFOAM image with its compilers, for example from
  `apptainer pull docker://opencfd/openfoam-dev:2212`. `OPENFOAM_BASHRC` is the bashrc
  inside the image, and `POD_OPENFOAM_VERSION` the version it reports. The defaults
  are `/usr/lib/openfoam/openfoam2212/etc/bashrc` and `v2212`. With both set, an
  earlier version of this example ran the same job on v2012 and OpenFOAM 8 images.
  `POD_REFERENCE_RUN` and `LLM_LONG_START` below must come from the image the job
  uses.
- `PYTHON`: a Python 3.10 to 3.12 with numpy and matplotlib that the image can see.
- `POD_REFERENCE_RUN`: the reference run, a passed validation run of that image.
- `LLM_LONG_START`: a numeric time directory of a developed run on the same mesh, with
  `constant/polyMesh` beside it. The five mesh files must equal the reference run's
  byte for byte, file headers included, so a mesh written by another OpenFOAM version
  may be refused. Max Courant must stay below 1 in the run. Continuing a copy of that
  validation run's `fixed-pimple` with `pimpleFoam` would give such a state, but this
  has not been tried.
- Optional: `POD_HOST_MODULES`, the host modules that a source-built `llama-server`
  needs. Without them it stops at start-up because `libcudart.so.12` is not found.

The prebuilt CUDA binaries need GLIBC_2.38 and GLIBCXX_3.4.32, that is glibc 2.38 and
the libstdc++ of GCC 13. They do not run on glibc 2.34. On such a system, build
llama.cpp with `build_llama_cuda.sh`. It needs cmake, a C++17 compiler and the CUDA
toolkit, and git and internet access unless `llama.cpp-src` is already there.

A build on a GPU node with the toolkit's `lib64/stubs` in `LDFLAGS` worked; one on a
CPU node without the stubs did not. CMake reads `LDFLAGS` only on a fresh configure.
The build that worked moved the prebuilt folder aside first, as the commands below do.
Otherwise its libraries stay on `LD_LIBRARY_PATH`. Run `setup_12b.sh` again after a
build, so that `sha256.txt` and the manifest name the built server.

When the `llama-server` in the folder does not run, `setup_12b.sh` prints the loader's
message and writes `"server_runs": false` into the manifest. The downloaded files are
still complete.

## Commands

From the repository root:

```bash
export POD_LLM_RUNTIME=$PWD/../llm-runtime-12b PYTHON=<python>
bash Solver_Examples/PODFoam/llm_demo/hpc/setup_12b.sh     # once, where there is internet

# if the prebuilt binaries do not run, in a GPU job
module load <modules>
mv "$POD_LLM_RUNTIME/llama-b11429-cuda" "$POD_LLM_RUNTIME/llama-b11429-cuda.prebuilt"
LDFLAGS="-L<cuda-toolkit>/lib64/stubs" bash Solver_Examples/PODFoam/llm_demo/hpc/build_llama_cuda.sh
bash Solver_Examples/PODFoam/llm_demo/hpc/setup_12b.sh

# the reference run, in the image, on a node with apptainer
export OPENFOAM_BASHRC=/usr/lib/openfoam/openfoam2212/etc/bashrc POD_OPENFOAM_VERSION=v2212
apptainer exec <image> bash -c 'source "$OPENFOAM_BASHRC"
    export LD_LIBRARY_PATH=$(dirname "$PYTHON")/../lib:$LD_LIBRARY_PATH
    cd Solver_Examples/PODFoam && ./validation/run.sh'

# the job
export POD_LLM_RUNTIME=$PWD/../llm-runtime-12b PYTHON=<python>
export SIF=<image> POD_HOST_MODULES="<modules>"
export POD_REFERENCE_RUN=<pod-v2212.XXXXXX> LLM_LONG_START=<developed case>/<time>
sbatch --account=<account> --partition=<partition> Solver_Examples/PODFoam/llm_demo/hpc/async_v2.slurm
```

The job sets these values:

| Setting | Job value |
|---|---|
| Steps | 6000 steps of 5e-6 s, written every 250 steps |
| `describe` request | step 250 |
| Sequence frames | steps 3000, 3250 and 3750 |
| Picture window | x 0 to 0.12 m, y 0 to 0.04 m |
| Server context | 4096 |
| Batch and ubatch | 512 |
| `LLM_TIMEOUT_S`, `LLM_MAX_TOKENS` | 120, 320 |
| `LLM_IMAGE_STYLE`, `POD_SUITE` | `v2`, `async` |
| Endpoint | from `POD_LLM_PORT` |
| `LLM_KILL_JOIN_S` | 0.2 unless given |

`LLM_LONG_*`, `LLM_IMAGE_XRANGE` and `LLM_IMAGE_YRANGE` change the first four rows. The
job fixes the others, except `LLM_KILL_JOIN_S`.

A shorter run needs its own frames. With `LLM_LONG_STEPS=1000`, set
`LLM_LONG_SEQUENCE_STEPS=250,500,750`: the default frames lie beyond step 1000, and the
sequence request would never be sent.

`start_server.sh` also reads `LLM_MODEL_FILE`, `LLM_PROJECTOR_FILE`, `LLM_PARALLEL`,
`LLM_THREADS`, `LLM_GPU_LAYERS`, `LLM_IMAGE_TOKENS` and `LLM_IMAGE_MIN_TOKENS`. When it
is called directly rather than from the job, it also reads `LLM_CTX`, `LLM_BATCH` and
`LLM_UBATCH`. `setup_12b.sh` reads `LLAMA_CUDA` and `GEMMA_12B_REVISION`. It checks the
SHA-256 of the pinned revision's weights and projector and of the CUDA 12.8 archives.
For any other revision or CUDA build it only records the hashes.
`build_llama_cuda.sh` reads `CMAKE_CUDA_ARCHITECTURES` and `BUILD_JOBS`.

## What comes out

Everything goes to `POD_ASYNC_OUT`, by default `../pod-async-v2/run-<job>` beside the
repository:

- `pod-llm-async.XXXXXX/`: the five cases, `async-verification.json`, `summary.json`
  and `run-archive.tar.gz`, which is about 500 MB at 1000 steps.
  [The observer's README](../README.md) describes them.
- `suite.log`, `site.txt` with the image, Python and modules, `nvidia-smi.txt` and
  `gpu-samples.csv`. Slurm's own output is `pod-async-v2-<job>.out` in `llm_demo/`,
  where git ignores it.
- `server/`: the server's log and command line.
- `git/`: HEAD, status and diff of the checkout. `llm-demo-work/`: the build.

### Tested runs

`async_v2.slurm` ran with 12B and a source-built server on an A30, and every check
passed:

| Run | Code | Versions | Time |
|---|---|---|---|
| `LLM_LONG_STEPS=1000`, frames 250, 500 and 750, from a developed state | this code | v2212 | |
| The same | an earlier version of this example | v2012, OpenFOAM 8 | |
| The default 6000 steps, once | an earlier version of this example | v2212 | 31 minutes, 333 s per case |

The three `bash` commands of the first two groups above ran as written on 2026-11-01,
without `HF_TOKEN`, with an earlier version of the scripts:

| Step | Result |
|---|---|
| `setup_12b.sh` on a login node | 47 s, about 25 s of it for the four downloads of 7.9 GB; all four files have the same SHA-256 as the runtime of October 19 |
| Prebuilt server without its soname links | stops with `libllama-common.so.0: cannot open shared object file`; `setup_12b.sh` keeps the links |
| Prebuilt server with the links, GLIBC 2.34 node | stops with `GLIBC_2.38' not found` |
| `build_llama_cuda.sh` on an A30 node | 335 s; the built server loaded the model in 5 s and answered a text request in 0.8 s |

Two things have not run: the prebuilt CUDA binaries on a system with GLIBC 2.38, and
`LLAMA_CUDA=13.4`.
