#!/usr/bin/env bash
# =============================================================================
#  run_pipeline.sh -- the ONE command for the AGN emission-line pipeline
# =============================================================================
#
#      bash run_pipeline.sh                 # process everything in input/
#      bash run_pipeline.sh --fetch 10      # download 10 eFEDS spectra first
#
#  Tidy layout it produces:
#
#      input/                              raw .fits you drop in
#      runs/<object>/
#          inputs/<tool>/...               spectrum adapted to each tool
#          outputs/<tool>/...              that tool's raw results
#          manifest.json                   redshift / SID / paths
#      results/<tool>/<object>/...         collected, ready to compare
#      results/index.csv                   one row per (object, tool)
#
#  Docker is used automatically; if your shell is missing the 'docker' group the
#  script re-execs itself through 'sg docker' so you never need sudo.
#
#  Config (override with environment variables):
#      INPUT_DIR  RUNS_DIR  RESULTS_DIR  AGN_DATA_DIR  PYTHON  DOCKER  JOBS
#      TOOLS  BUILD  CLEAN
# =============================================================================
set -euo pipefail

SCRIPT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/$(basename "${BASH_SOURCE[0]}")"
ROOT="$(dirname "$SCRIPT")"
cd "$ROOT"

# ---- re-exec with the docker group if this shell is missing it --------------
if command -v docker >/dev/null 2>&1 && ! docker info >/dev/null 2>&1; then
  if command -v sg >/dev/null 2>&1 && sg docker -c "docker info" >/dev/null 2>&1; then
    if [[ $# -gt 0 ]]; then
      exec sg docker -c "bash $(printf '%q' "$SCRIPT") $(printf '%q ' "$@")"
    else
      exec sg docker -c "bash $(printf '%q' "$SCRIPT")"
    fi
  fi
fi

# ------------------------------- CONFIG --------------------------------------
INPUT_DIR="${INPUT_DIR:-$ROOT/input}"
RUNS_DIR="${RUNS_DIR:-$ROOT/runs}"
RESULTS_DIR="${RESULTS_DIR:-$ROOT/results}"
AGN_DATA_DIR="${AGN_DATA_DIR:-$HOME/agn_data}"
PYTHON="${PYTHON:-$ROOT/.venv/bin/python}"
DOCKER="${DOCKER:-docker}"
JOBS="${JOBS:-4}"
TOOLS="${TOOLS:-pyqsofit badass fantasy_agn gelato gleam}"   # sculptor is GUI-only
BUILD="${BUILD:-1}"
CLEAN="${CLEAN:-0}"
TOOL_TIMEOUT="${TOOL_TIMEOUT:-}"   # optional per-tool wall-clock limit, seconds (e.g. 3600)
# BADASS3 is slow with full MCMC; the pipeline defaults to a fast OLS/basinhopping
# fit. Set BADASS_MCMC=1 to restore the full uncertainty run.
BADASS_MCMC="${BADASS_MCMC:-0}"
BADASS_NBASINHOP="${BADASS_NBASINHOP:-5}"
DOCKER_TOOLS="badass fantasy_agn gelato gleam"
FETCH_N=""

log()  { printf '\033[1;34m[%s]\033[0m %s\n' "$(date +%H:%M:%S)" "$*"; }
warn() { printf '\033[1;33m[warn]\033[0m %s\n' "$*" >&2; }
die()  { printf '\033[1;31m[error]\033[0m %s\n' "$*" >&2; exit 1; }

# ------------------------------- ARGS ----------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    --fetch)    FETCH_N="${2:-10}"; shift 2 ;;
    --no-build) BUILD=0; shift ;;
    --clean)    CLEAN=1; shift ;;
    --jobs)     JOBS="$2"; shift 2 ;;
    --tools)    TOOLS="$2"; shift 2 ;;
    -h|--help)  sed -n '2,30p' "$SCRIPT" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) die "unknown argument: $1 (try --help)" ;;
  esac
done

has_tool()     { [[ " $TOOLS " == *" $1 "* ]]; }
needs_docker() { for t in $DOCKER_TOOLS; do has_tool "$t" && return 0; done; return 1; }

# ----------------------------- PREFLIGHT -------------------------------------
log "repo: $ROOT"
[[ -x "$PYTHON" ]] || die "python not found: $PYTHON (set PYTHON=... or create .venv)"
"$PYTHON" -c "import astropy, numpy" 2>/dev/null || die "astropy/numpy missing in $PYTHON"

DOCKER_OK=0
command -v "${DOCKER%% *}" >/dev/null 2>&1 && DOCKER_OK=1
if needs_docker && [[ $DOCKER_OK -eq 0 ]]; then
  warn "'${DOCKER}' not found -- Docker tools will be SKIPPED."
  warn "Install:  sudo apt-get install docker.io && sudo usermod -aG docker \$USER"
  for t in $DOCKER_TOOLS; do TOOLS="${TOOLS//$t/}"; done
fi
[[ $CLEAN -eq 1 ]] && { log "cleaning $RUNS_DIR"; rm -rf "$RUNS_DIR"; }

# ---------------------- OPTIONAL: FETCH INTO INPUT ---------------------------
if [[ -n "$FETCH_N" ]]; then
  mkdir -p "$INPUT_DIR"
  log "fetching $FETCH_N eFEDS spectra into the global dataset ($AGN_DATA_DIR)"
  AGN_DATA_DIR="$AGN_DATA_DIR" "$PYTHON" pipeline/fetch_efeds.py \
      --n "$FETCH_N" --class QSO --min-sn 8 --z-max 0.5
  n=0
  for f in "$AGN_DATA_DIR"/efeds/*.fits; do
    [[ -e "$f" ]] || continue
    b="$(basename "$f")"
    [[ -e "$INPUT_DIR/$b" ]] || ln -s "$f" "$INPUT_DIR/$b"
    n=$((n+1))
  done
  log "staged $n spectrum symlink(s) in $INPUT_DIR"
fi

# ------------------------------ PREPARE --------------------------------------
shopt -s nullglob
inputs=("$INPUT_DIR"/*.fits)
[[ ${#inputs[@]} -gt 0 ]] || die "no .fits files in $INPUT_DIR (drop spectra there or use --fetch N)"
log "preparing ${#inputs[@]} object(s) -> $RUNS_DIR"
"$PYTHON" pipeline/prepare_inputs.py --fits "$INPUT_DIR" --out "$RUNS_DIR"

# ------------------------------ BUILD IMAGES ---------------------------------
if [[ $BUILD -eq 1 && $DOCKER_OK -eq 1 ]] && needs_docker; then
  to_build=()
  for t in $DOCKER_TOOLS; do
    has_tool "$t" || continue
    $DOCKER image inspect "$t" >/dev/null 2>&1 || to_build+=("$t")
  done
  if [[ ${#to_build[@]} -gt 0 ]]; then
    log "building Docker images: ${to_build[*]}  (one-time, slow)"
    DOCKER="$DOCKER" bash pipeline/build_images.sh "${to_build[@]}"
  fi
fi

# ------------------------------ RUNNERS --------------------------------------
run_pyqsofit() {   # $1 = object tag
  local tag="$1" base="$RUNS_DIR/$tag"
  local out="$base/outputs/pyqsofit" tmp="$base/.tmp/pyqsofit"
  local -a tmo=(); [[ -n "$TOOL_TIMEOUT" ]] && tmo=(timeout "$TOOL_TIMEOUT")
  mkdir -p "$out" "$tmp"
  cp "$ROOT/pyqsofit/main.py" "$tmp/main.py"
  cp "$base/inputs/pyqsofit/spectrum.fits" "$tmp/spectrum.fits"
  ( cd "$tmp" && PYTHONPATH="$ROOT/pyqsofit/PyQSOFit/src" MPLBACKEND=Agg "${tmo[@]}" "$PYTHON" main.py ) >"$out/fit.log" 2>&1 \
    || { warn "pyqsofit failed for $tag (see $out/fit.log)"; return 1; }
  cp "$tmp"/*.fits "$tmp"/*.pdf "$out"/ 2>/dev/null || true
  rm -rf "$tmp"
}

run_docker_tool() {  # $1 = tool, $2 = object tag
  local tool="$1" tag="$2" base="$RUNS_DIR/$2"
  local out="$base/outputs/$tool"
  local in="$base/inputs/$tool"
  local -a tmo=(); [[ -n "$TOOL_TIMEOUT" ]] && tmo=(timeout "$TOOL_TIMEOUT")
  mkdir -p "$out"
  local -a mounts=()
  case "$tool" in
    badass)
      mounts=(
        -v "$in/my_sdss.fits:/app/BADASS3/example_spectra/2-onur/my_sdss.fits:ro"
        -v "$ROOT/badass/main.py:/app/BADASS3/example_notebooks/main.py:ro"
        -e "BADASS_MCMC=$BADASS_MCMC"
        -e "BADASS_NBASINHOP=$BADASS_NBASINHOP"
      ) ;;
    fantasy_agn)
      mounts=(-v "$in/my_sdss.fits:/app/my_sdss.fits:ro") ;;
    gelato)
      mounts=(-v "$in:/app/input:ro") ;;
    gleam)
      # mount files individually: the image's gleam.sh lives in /app/input
      mounts=(
        -v "$in/spec1d.sdss.sdss.fiber1.1.fits:/app/input/spec1d.sdss.sdss.fiber1.1.fits:ro"
        -v "$in/meta.dat:/app/input/meta.dat:ro"
        -v "$in/line_table.fits:/app/input/line_table.fits:ro"
        -v "$in/Sky_bands.fits:/app/input/Sky_bands.fits:ro"
        -v "$in/gleamconfig.yaml:/app/input/gleamconfig.yaml:ro"
      ) ;;
    *) warn "unknown docker tool $tool"; return 1 ;;
  esac
  local cname="pipe_${tool}_${tag}"
  "${tmo[@]}" $DOCKER run --rm --name "$cname" "${mounts[@]}" -v "$out:/app/output" "$tool" >"$out/docker.log" 2>&1
  local rc=$?
  # ensure a container killed by the timeout does not linger and clobber outputs
  $DOCKER rm -f "$cname" >/dev/null 2>&1 || true
  if [[ $rc -ne 0 ]]; then
    warn "$tool failed for $tag (rc=$rc, see $out/docker.log)"; return 1
  fi
  chmod -R u+rwX "$out" 2>/dev/null || true
}

run_one() {        # $1 = tool, $2 = tag
  case "$1" in
    pyqsofit) run_pyqsofit "$2" ;;
    sculptor) warn "sculptor is GUI-only -- skipping $2" ;;
    badass|fantasy_agn|gelato|gleam) run_docker_tool "$1" "$2" ;;
    *) warn "unknown tool: $1" ;;
  esac
}

# ------------------------------ SCHEDULE -------------------------------------
log "tools: $TOOLS | jobs: $JOBS"
started=0
for objdir in "$RUNS_DIR"/*/; do
  [[ -f "$objdir/manifest.json" ]] || continue
  tag="$(basename "$objdir")"
  for tool in $TOOLS; do
    while [[ $(jobs -rp | wc -l) -ge $JOBS ]]; do wait -n || true; done
    log "  -> $tool : $tag"
    run_one "$tool" "$tag" &
    started=$((started+1))
  done
done
wait || true
log "finished $started job(s)"

# ------------------------------ COLLECT --------------------------------------
log "collecting results -> $RESULTS_DIR"
"$PYTHON" pipeline/collect_results.py --runs "$RUNS_DIR" --results "$RESULTS_DIR" \
  || warn "collector reported an error"
log "done.  raw runs: $RUNS_DIR   collected: $RESULTS_DIR"
