#!/usr/bin/env bash
#
# Build and push the LAB-Bench code-tools sandbox image from the Dockerfile in
# this directory. When running an eval with this image, set LABBENCH_SANDBOX_IMAGE
# to the same image reference; the task records it in task and sample metadata.
#
# Requires: docker (linux/amd64) and push credentials for the registry
# (e.g. `aws ecr get-login-password | docker login`).
#
#   LABBENCH_SANDBOX_IMAGE=<acct>.dkr.ecr.<region>.amazonaws.com/prd/inspect-tasks:labbench-bio-v2 \
#   ./build_and_push.sh
#
# Options (env):
#   LABBENCH_PLATFORM=linux/amd64   build platform (default linux/amd64)
set -euo pipefail

: "${LABBENCH_SANDBOX_IMAGE:?set LABBENCH_SANDBOX_IMAGE to the target image reference, e.g. <acct>.dkr.ecr.<region>.amazonaws.com/prd/inspect-tasks:labbench-bio-vN}"
PLATFORM="${LABBENCH_PLATFORM:-linux/amd64}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

docker build --platform "$PLATFORM" -t "$LABBENCH_SANDBOX_IMAGE" "$SCRIPT_DIR"
docker push "$LABBENCH_SANDBOX_IMAGE"

echo "==> Done. Run the eval with:"
echo "    LABBENCH_SANDBOX_IMAGE=$LABBENCH_SANDBOX_IMAGE inspect eval inspect_evals/lab_bench_seqqa_codetools"
