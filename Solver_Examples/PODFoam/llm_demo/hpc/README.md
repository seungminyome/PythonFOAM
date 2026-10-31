# GPU path: Gemma 4 12B on a Slurm GPU node

These scripts run the observer's asynchronous suite with v2 pictures and Gemma 4 12B
on one GPU node. OpenFOAM runs in an Apptainer image. llama-server runs on the host
GPU, and the callback reaches it at 127.0.0.1.

| Script | What it does |
|---|---|
| `setup_12b.sh` | Downloads llama.cpp b11429 (CUDA build) and the 12B weights and image projector into `POD_LLM_RUNTIME`, about 8 GB. Records SHA-256 of these and of the `llama-server` there when it runs. |
| `build_llama_cuda.sh` | Builds llama.cpp b11429 from source with CUDA into the same folder. |
| `start_server.sh` | Starts `llama-server` on the node's GPU with all layers offloaded, writes `server.pid` and waits for `/health`, up to 10 minutes. |
| `stop_server.sh` | Stops the server named in `server.pid`. |
| `async_v2.slurm` | The batch job: starts the server, runs `run_demo.sh` with `POD_SUITE=async` and `LLM_IMAGE_STYLE=v2` in the image, and stops the server. |

## What is required

- `POD_LLM_RUNTIME`: the folder for the weights and `llama-server`. The job's default is
  `llm-runtime-12b` in the repository.
- The Gemma licence applies to the weights: see
  `google/gemma-4-12B-it-qat-q4_0-gguf` on Hugging Face. If `HF_TOKEN` is set, it is sent
  with the download. A public repository needs none, and neither do weights already there.
- `SIF`: an OpenFOAM v2212 image with its compilers, for example from
  `apptainer pull docker://opencfd/openfoam-dev:2212`. The job runs v2212 only: it sets
  `POD_OPENFOAM_VERSION=v2212` with no override. `OPENFOAM_BASHRC` is the bashrc inside
  the image; its default is `/usr/lib/openfoam/openfoam2212/etc/bashrc`.
- `PYTHON`: a Python 3.10 to 3.12 with numpy and matplotlib that the image can see.
- `POD_REFERENCE_RUN`: a passed validation run of that image.
- `LLM_LONG_START`: a numeric time directory of a developed run on the same mesh, with
  `constant/polyMesh` beside it. The five mesh files must equal the reference run's byte
  for byte, file headers included, so a mesh written by another OpenFOAM version may be
  refused. Max Courant must stay below 1 in the run. Continuing a copy of that validation
  run's `fixed-pimple` with `pimpleFoam` should give such a state; this was not tried.
- Optional: `POD_HOST_MODULES`, the host modules that a source-built `llama-server`
  needs. Without them it stops at start-up (`libcudart.so.12` not found).

The prebuilt CUDA binaries need GLIBC_2.38. On an older system use
`build_llama_cuda.sh`, which needs cmake, a C++17 compiler, the CUDA toolkit, and git and
internet unless `llama.cpp-src` is already there. A build on a GPU node with the toolkit's
`lib64/stubs` in `LDFLAGS` worked; one on a CPU node without the stubs did not. CMake
reads `LDFLAGS` only on a fresh configure. The build that worked moved the prebuilt folder
aside first, because its libraries stay on `LD_LIBRARY_PATH` otherwise. Run `setup_12b.sh`
again after a build, so that `sha256.txt` and the manifest name the built server.

## Commands

From the repository root:

```bash
export POD_LLM_RUNTIME=$PWD/llm-runtime-12b PYTHON=<python>
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
    cd Solver_Examples/PODFoam && ./validation/run_v2106.sh'

# the job
export POD_LLM_RUNTIME=$PWD/llm-runtime-12b PYTHON=<python>
export SIF=<image> POD_HOST_MODULES="<modules>"
export POD_REFERENCE_RUN=<pod-v2212.XXXXXX> LLM_LONG_START=<developed case>/<time>
sbatch --account=<account> --partition=<partition> Solver_Examples/PODFoam/llm_demo/hpc/async_v2.slurm
```

The job's defaults are 6000 steps of 5e-6 s, written every 250 steps, the `describe`
request at step 250, sequence frames at 3000, 3250 and 3750, and the window x 0 to
0.12 m, y 0 to 0.04 m. `LLM_LONG_*`, `LLM_IMAGE_XRANGE` and `LLM_IMAGE_YRANGE` change them.
The job fixes context 4096, batch and ubatch 512, `LLM_TIMEOUT_S=120`, `LLM_MAX_TOKENS=320`,
`LLM_IMAGE_STYLE=v2`, `POD_SUITE=async`, and the endpoint from `POD_LLM_PORT`. It sets
`LLM_KILL_JOIN_S` to 0.2 unless given.

`start_server.sh` also reads `LLM_MODEL_FILE`, `LLM_PROJECTOR_FILE`, `LLM_PARALLEL`,
`LLM_THREADS`, `LLM_GPU_LAYERS`, `LLM_IMAGE_TOKENS` and `LLM_IMAGE_MIN_TOKENS`, and, when
called directly rather than from the job, `LLM_CTX`, `LLM_BATCH` and `LLM_UBATCH`.
`setup_12b.sh` reads `LLAMA_CUDA` and `GEMMA_12B_REVISION`, and `build_llama_cuda.sh`
reads `CMAKE_CUDA_ARCHITECTURES` and `BUILD_JOBS`.

## What comes out

Everything goes to `POD_ASYNC_OUT`, by default `../pod-async-v2/run-<job>` beside the
repository:

- `pod-llm-async.XXXXXX/`: the five cases, `async-verification.json`, `summary.json`
  and `run-archive.tar.gz` (about 500 MB at 1000 steps), described in
  [the observer's README](../README.md).
- `suite.log`, `site.txt` (image, Python, modules), `nvidia-smi.txt`, `gpu-samples.csv`.
  Slurm's own output is `pod-async-v2-<job>.out` in the submit folder.
- `server/`: the server's log and command line.
- `git/`: HEAD, status and diff of the checkout. `llm-demo-work/`: the build.

`async_v2.slurm` ran unedited on a GPU with 12B and a source-built server, with
`LLM_LONG_STEPS=1000` from a developed state, and its check passed. Not run: the default
6000 steps, `setup_12b.sh` and `build_llama_cuda.sh` as written above, the prebuilt CUDA
binaries, and `LLAMA_CUDA=13.4`.
