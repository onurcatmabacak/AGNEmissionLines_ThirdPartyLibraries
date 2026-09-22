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
#      results/scores.csv                  reduced chi^2 per (object, tool)
#      results/lines.csv                   line fluxes per (object, tool)
#      results/report.html / report.md     cross-tool comparison report
#
#  Docker is used automatically; if your shell is missing the 'docker' group the
#  script re-execs itself through 'sg docker' so you never need sudo.
#
#  Config (override with environment variables):
#      INPUT_DIR  RUNS_DIR  RESULTS_DIR  AGN_DATA_DIR  PYTHON  DOCKER  JOBS
#      TOOLS  BUILD  CLEAN  VARIANTS  RUN_LABEL  TOOL_TIMEOUT
#
#  Tuning grid: VARIANTS="pyqsofit=err05,badass=fast" selects per-tool config
#  variants from configs/<tool>/<variant>/; RUN_LABEL namespaces runs/ and
#  results/ so several variants can be compared side by side.
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
FANTASY_TIMEOUT="${FANTASY_TIMEOUT:-900}"  # fantasy_agn can hang after writing its products
VARIANTS="${VARIANTS:-}"           # per-tool config variants, e.g. "pyqsofit=err05,badass=fast"
RUN_LABEL="${RUN_LABEL:-}"         # namespaces runs/ and results/ for variant grids
REPORT_ONLY=0
# BADASS3 is slow with full MCMC; the pipeline defaults to a fast OLS/basinhopping
# fit. Set BADASS_MCMC=1 to restore the full uncertainty run.
BADASS_MCMC="${BADASS_MCMC:-0}"
BADASS_NBASINHOP="${BADASS_NBASINHOP:-5}"
BADASS_MAX_LIKE_NITER="${BADASS_MAX_LIKE_NITER:-100}"   # MC bootstrap iterations (0 = fastest)
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
    --variant)  VARIANTS="${VARIANTS:+$VARIANTS,}$2"; shift 2 ;;
    --label)    RUN_LABEL="$2"; shift 2 ;;
    --report-only) REPORT_ONLY=1; shift ;;
    -h|--help)  sed -n '2,34p' "$SCRIPT" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) die "unknown argument: $1 (try --help)" ;;
  esac
done

# ---- resolve per-tool config variants (configs/<tool>/<variant>/<file>) -----
declare -A VARIANT
for kv in ${VARIANTS//,/ }; do [[ -n "$kv" ]] && VARIANT[${kv%%=*}]=${kv#*=}; done
pick() {  # $1 tool, $2 default file
  local v="${VARIANT[$1]:-}"
  local cand="$ROOT/configs/$1/$v/$(basename "$2")"
  if [[ -n "$v" && -f "$cand" ]]; then echo "$cand"; else echo "$2"; fi
}
PYQSOFIT_MAIN="$(pick pyqsofit "$ROOT/pyqsofit/main.py")"
BADASS_MAIN="$(pick badass "$ROOT/badass/main.py")"
FANTASY_MAIN="$(pick fantasy_agn "$ROOT/fantasy_agn/main.py")"
GELATO_JSON="$(pick gelato "$ROOT/Gelato/my_sdss.json")"
GLEAM_CONFIG="$(pick gleam "$ROOT/Gleam/gleamconfig.yaml")"
[[ -n "$RUN_LABEL" ]] && { RUNS_DIR="$RUNS_DIR/$RUN_LABEL"; RESULTS_DIR="$RESULTS_DIR/$RUN_LABEL"; }
[[ -n "$VARIANTS" ]] && log "variants: $VARIANTS"

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
[[ $CLEAN -eq 1 && $REPORT_ONLY -eq 0 ]] && { log "cleaning $RUNS_DIR"; rm -rf "$RUNS_DIR"; }

if [[ $REPORT_ONLY -eq 0 ]]; then

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
"$PYTHON" pipeline/prepare_inputs.py --fits "$INPUT_DIR" --out "$RUNS_DIR" \
    --gelato-json "$GELATO_JSON" --gleam-config "$GLEAM_CONFIG"

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
key_produced() {  # $1 = tool, $2 = output dir -- did the tool write its headline product?
  local tool="$1" out="$2"
  case "$tool" in
    fantasy_agn) [[ -f "$out/my_sdss_model.csv" ]] ;;
    gelato)      [[ -f "$out/my_sdss-results.fits" ]] ;;
    badass)      [[ -f "$out/spectrum.pdf" ]] || find "$out" -name 'best_model_components.fits' -print -quit 2>/dev/null | grep -q . ;;
    gleam)       find "$out" -name '*.png' -print -quit 2>/dev/null | grep -q . ;;
    *)           find "$out" -type f ! -name 'docker.log' -print -quit 2>/dev/null | grep -q . ;;
  esac
}

run_pyqsofit() {   # $1 = object tag
  local tag="$1" base="$RUNS_DIR/$tag"
  local out="$base/outputs/pyqsofit" tmp="$base/.tmp/pyqsofit"
  local -a tmo=(); [[ -n "$TOOL_TIMEOUT" ]] && tmo=(timeout "$TOOL_TIMEOUT")
  mkdir -p "$out" "$tmp"
  cp "$PYQSOFIT_MAIN" "$tmp/main.py"
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
  local wait_s=""
  if [[ -n "$TOOL_TIMEOUT" ]]; then wait_s="$TOOL_TIMEOUT"
  elif [[ "$tool" == fantasy_agn && -n "$FANTASY_TIMEOUT" ]]; then wait_s="$FANTASY_TIMEOUT"; fi
  mkdir -p "$out"
  local -a mounts=()
  case "$tool" in
    badass)
      mounts=(
        -v "$in/my_sdss.fits:/app/BADASS3/example_spectra/2-onur/my_sdss.fits:ro"
        -v "$BADASS_MAIN:/app/BADASS3/example_notebooks/main.py:ro"
        -e "BADASS_MCMC=$BADASS_MCMC"
        -e "BADASS_NBASINHOP=$BADASS_NBASINHOP"
        -e "BADASS_MAX_LIKE_NITER=$BADASS_MAX_LIKE_NITER"
      ) ;;
    fantasy_agn)
      mounts=(-v "$in/my_sdss.fits:/app/my_sdss.fits:ro"
              -v "$FANTASY_MAIN:/app/main.py:ro") ;;
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
  # Run detached and wait with a timeout: killing a foreground `docker run`
  # client does NOT stop the container, so a hung tool would linger forever.
  local cname="pipe_${tool}_${tag}_${RUN_LABEL:-default}_$$"
  if ! $DOCKER run -d --name "$cname" "${mounts[@]}" -v "$out:/app/output" "$tool" >/dev/null 2>&1; then
    warn "$tool container failed to start for $tag"
    $DOCKER rm -f "$cname" >/dev/null 2>&1 || true
    return 1
  fi
  local container_rc="" wrc=0 timed_out=0
  if [[ -n "$wait_s" ]]; then
    # -k: SIGKILL if the `docker wait` client ignores SIGTERM
    container_rc=$(timeout -k 10 "$wait_s" $DOCKER wait "$cname" 2>/dev/null); wrc=$?
    [[ $wrc -eq 124 || $wrc -eq 137 ]] && timed_out=1
  else
    container_rc=$($DOCKER wait "$cname" 2>/dev/null)
  fi
  container_rc="${container_rc//[[:space:]]/}"
  if [[ $timed_out -eq 1 ]]; then
    $DOCKER kill "$cname" >/dev/null 2>&1 || true
    $DOCKER wait "$cname" >/dev/null 2>&1 || true
  fi
  $DOCKER logs "$cname" > "$out/docker.log" 2>&1 || true
  $DOCKER rm -f "$cname" >/dev/null 2>&1 || true
  # containers run as root; give the products back to the host user so that
  # work/ and results/ stay writable (and cleanable) from the host.
  $DOCKER run --rm -v "$out:/o" --entrypoint sh "$tool" \
    -c "chown -R $(id -u):$(id -g) /o" >/dev/null 2>&1 || true
  local rc=0
  if [[ $timed_out -eq 1 ]]; then rc=124
  elif [[ -n "$container_rc" && "$container_rc" != "0" ]]; then rc=1; fi
  if [[ $rc -ne 0 ]]; then
    # A tool can hang after writing its headline product; keep the product
    # instead of discarding a usable run. Require the tool's *key* output so we
    # are not fooled by the early pre-fit line-list CSVs some tools write.
    if [[ $rc -eq 124 ]] && key_produced "$tool" "$out"; then
      warn "$tool timed out for $tag but produced its key outputs -- keeping them"
      chmod -R u+rwX "$out" 2>/dev/null || true
      return 0
    fi
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
fi   # end REPORT_ONLY==0

# ------------------------------ COLLECT --------------------------------------
[[ $REPORT_ONLY -eq 1 ]] || {
  log "collecting results -> $RESULTS_DIR"
  "$PYTHON" pipeline/collect_results.py --runs "$RUNS_DIR" --results "$RESULTS_DIR" \
    || warn "collector reported an error"
}

# --------------------------- SCORE + REPORT ----------------------------------
"$PYTHON" pipeline/score_fits.py --runs "$RUNS_DIR" --results "$RESULTS_DIR" \
  || warn "scorer reported an error"
"$PYTHON" pipeline/make_report.py --runs "$RUNS_DIR" --results "$RESULTS_DIR" \
  || warn "report step reported an error"
log "done.  raw runs: $RUNS_DIR   collected: $RESULTS_DIR   report: $RESULTS_DIR/report.html"
