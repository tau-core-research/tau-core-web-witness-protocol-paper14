#!/usr/bin/env bash
set -euo pipefail

# TC-RUNBOOK-003
# End-to-end DESI + lensing + optional velocity/CMB Tau-web v3 workflow.

TRACER="${TRACER:-LRG}"
REGION="${REGION:-NGC}"
RANDOM_INDICES="${RANDOM_INDICES:-0}"
MAX_ROWS="${MAX_ROWS:-200000}"
MAX_PAIRS="${MAX_PAIRS:-300000}"

ROOT="${ROOT:-tau_web_run}"
SCRIPT_DIR="${SCRIPT_DIR:-${ROOT}/scripts}"
DESI_DIR="${DESI_DIR:-${ROOT}/data/desi}"
LENSING_INPUT="${LENSING_INPUT:-${ROOT}/data/lensing/lensing_input.csv}"
LENSING_REDUCED="${LENSING_REDUCED:-${ROOT}/data/lensing/lensing_reduced.csv}"
VELOCITY_INPUT="${VELOCITY_INPUT:-}"
CMB_KAPPA_INPUT="${CMB_KAPPA_INPUT:-}"
MOCK_GLOB="${MOCK_GLOB:-${ROOT}/data/mocks/mock_*.csv}"
RESULTS_DIR="${RESULTS_DIR:-${ROOT}/results}"

mkdir -p "${DESI_DIR}" "$(dirname "${LENSING_REDUCED}")" "${RESULTS_DIR}"

echo "== TC-RUNBOOK-003 =="
echo "TRACER=${TRACER}"
echo "REGION=${REGION}"
echo "ROOT=${ROOT}"

echo
echo "1) Planning DESI files..."
python "${SCRIPT_DIR}/tc_desi_connector.py" \
  --tracer "${TRACER}" \
  --region "${REGION}" \
  --random-indices ${RANDOM_INDICES} \
  --out-dir "${DESI_DIR}" \
  --plan

echo
echo "2) Downloading and reducing DESI files..."
python "${SCRIPT_DIR}/tc_desi_connector.py" \
  --tracer "${TRACER}" \
  --region "${REGION}" \
  --random-indices ${RANDOM_INDICES} \
  --out-dir "${DESI_DIR}" \
  --download \
  --prepare-csv \
  --max-rows "${MAX_ROWS}"

GALAXY_CSV="${DESI_DIR}/${TRACER}_${REGION}_clustering.reduced.csv"
RANDOM_CSV="${DESI_DIR}/${TRACER}_${REGION}_randoms.reduced.csv"

if [[ ! -f "${GALAXY_CSV}" ]]; then
  echo "Missing galaxy CSV: ${GALAXY_CSV}" >&2
  exit 1
fi

echo
echo "3) Preparing lensing reduced CSV..."
if [[ -f "${LENSING_INPUT}" ]]; then
  python "${SCRIPT_DIR}/tc_lensing_connector.py" \
    --mode kappa-table \
    --input "${LENSING_INPUT}" \
    --out "${LENSING_REDUCED}" \
    --redshift-proxy 1.0
else
  echo "Lensing input not found: ${LENSING_INPUT}"
  echo "Skipping lensing prep and cross-readout."
fi

echo
echo "4) Galaxy-lensing cross-readout..."
if [[ -f "${LENSING_REDUCED}" ]]; then
  python "${SCRIPT_DIR}/tc_obs_pipeline.py" \
    --galaxy "${GALAXY_CSV}" \
    --lensing "${LENSING_REDUCED}" \
    --n-nulls 100 \
    --out "${RESULTS_DIR}/obs_result.json" \
    --null-out "${RESULTS_DIR}/obs_nulls.csv" \
    --max-pairs "${MAX_PAIRS}"
else
  echo "Lensing reduced CSV not found; skipping cross-readout."
fi

echo
echo "5) Plain z-stability..."
python "${SCRIPT_DIR}/tc_zstab_pipeline.py" \
  --catalog "${GALAXY_CSV}" \
  --n-bins 5 \
  --min-per-bin 500 \
  --out "${RESULTS_DIR}/zstab_result.json" \
  --bins-out "${RESULTS_DIR}/zstab_bins.csv" \
  --max-pairs "${MAX_PAIRS}"

echo
echo "6) Z-stability diagnostic..."
python "${SCRIPT_DIR}/tc_zstab_diag.py" \
  --zstab-result "${RESULTS_DIR}/zstab_result.json" \
  --out "${RESULTS_DIR}/zstab_diag.json" \
  --tensor-matrix-out "${RESULTS_DIR}/zstab_tensor_matrix.csv" \
  --axis-matrix-out "${RESULTS_DIR}/zstab_axis_matrix.csv"

echo
echo "7) Weighted z-stability..."
python "${SCRIPT_DIR}/tc_zstab_weighted.py" \
  --zstab-result "${RESULTS_DIR}/zstab_result.json" \
  --out "${RESULTS_DIR}/zstab_weighted.json" \
  --pairs-out "${RESULTS_DIR}/zstab_weighted_pairs.csv" \
  --amp-relative-floor 0.35 \
  --weight-power 1.0

echo
echo "8) Systematics projector..."
if [[ -f "${RANDOM_CSV}" ]]; then
  python "${SCRIPT_DIR}/tc_sys_projector.py" \
    --observed "${GALAXY_CSV}" \
    --systematics "${RANDOM_CSV}" \
    --out "${RESULTS_DIR}/sys_result.json" \
    --max-pairs "${MAX_PAIRS}"
else
  echo "Random CSV not found: ${RANDOM_CSV}; skipping systematics projector."
fi

echo
echo "9) Mock covariance..."
shopt -s nullglob
MOCKS=( ${MOCK_GLOB} )
shopt -u nullglob
if (( ${#MOCKS[@]} > 0 )); then
  MOCK_CMD=(
    python "${SCRIPT_DIR}/tc_mock_cov.py"
    --observed "${GALAXY_CSV}"
    --mock-glob "${MOCK_GLOB}"
    --out "${RESULTS_DIR}/mock_cov_result.json"
    --mock-out "${RESULTS_DIR}/mock_cov_rows.csv"
    --max-pairs "${MAX_PAIRS}"
  )
  if [[ -f "${RANDOM_CSV}" ]]; then
    MOCK_CMD+=( --systematics "${RANDOM_CSV}" )
  fi
  "${MOCK_CMD[@]}"
else
  echo "No mocks found at ${MOCK_GLOB}; skipping mock covariance."
fi

echo
echo "10) Optional third readout..."
EXTRA_CMD=( python "${SCRIPT_DIR}/tc_extra_readout.py" --out "${RESULTS_DIR}/extra_result.json" )

if [[ -f "${RESULTS_DIR}/obs_result.json" ]]; then
  EXTRA_CMD+=( --obs-result "${RESULTS_DIR}/obs_result.json" )
else
  echo "No obs_result.json; skipping extra readout."
  EXTRA_CMD=()
fi

if [[ -n "${VELOCITY_INPUT}" && -f "${VELOCITY_INPUT}" ]]; then
  EXTRA_CMD+=( --velocity-catalog "${VELOCITY_INPUT}" )
fi

if [[ -n "${CMB_KAPPA_INPUT}" && -f "${CMB_KAPPA_INPUT}" ]]; then
  EXTRA_CMD+=( --cmb-kappa-catalog "${CMB_KAPPA_INPUT}" )
fi

if (( ${#EXTRA_CMD[@]} > 0 )) && { [[ -n "${VELOCITY_INPUT}" && -f "${VELOCITY_INPUT}" ]] || [[ -n "${CMB_KAPPA_INPUT}" && -f "${CMB_KAPPA_INPUT}" ]]; }; then
  "${EXTRA_CMD[@]}"
else
  echo "No velocity/CMB extra input supplied; skipping extra readout."
fi

echo
echo "11) Final verdict v3..."
VERDICT_CMD=( python "${SCRIPT_DIR}/tc_verdict_engine_v3.py" --out "${RESULTS_DIR}/final_verdict_v3.json" --allow-weighted-z-rescue )

if [[ -f "${RESULTS_DIR}/obs_result.json" ]]; then
  VERDICT_CMD+=( --obs-result "${RESULTS_DIR}/obs_result.json" )
fi

if [[ -f "${RESULTS_DIR}/zstab_result.json" ]]; then
  VERDICT_CMD+=( --zstab-result "${RESULTS_DIR}/zstab_result.json" )
fi

if [[ -f "${RESULTS_DIR}/zstab_diag.json" ]]; then
  VERDICT_CMD+=( --zdiag-result "${RESULTS_DIR}/zstab_diag.json" )
fi

if [[ -f "${RESULTS_DIR}/zstab_weighted.json" ]]; then
  VERDICT_CMD+=( --zweighted-result "${RESULTS_DIR}/zstab_weighted.json" )
fi

if [[ -f "${RESULTS_DIR}/sys_result.json" ]]; then
  VERDICT_CMD+=( --sys-result "${RESULTS_DIR}/sys_result.json" )
fi

if [[ -f "${RESULTS_DIR}/mock_cov_result.json" ]]; then
  VERDICT_CMD+=( --mock-result "${RESULTS_DIR}/mock_cov_result.json" )
fi

if [[ -f "${RESULTS_DIR}/extra_result.json" ]]; then
  VERDICT_CMD+=( --extra-result "${RESULTS_DIR}/extra_result.json" )
fi

"${VERDICT_CMD[@]}"

echo
echo "Done. Final v3 verdict:"
cat "${RESULTS_DIR}/final_verdict_v3.json"
