#!/usr/bin/env bash
#
# Build and push the BioMysteryBench sandbox images: one shared tools base, then one
# per-problem image (base + that problem's data under data/). The eval names a sample's
# image <BP_PREFIX><id>, so pass the same BP_PREFIX as BMB_IMAGE_PREFIX at run time.
#
# Requires: docker (linux/amd64), HF_TOKEN with access to the gated dataset, and push
# creds for BP_PREFIX's registry (e.g. `aws ecr get-login-password | docker login`).
#
#   HF_TOKEN=hf_... \
#   BP_PREFIX=<acct>.dkr.ecr.<region>.amazonaws.com/prd/biomystery: \
#   ./build_and_push.sh
#
# Options (env):
#   BP_SOURCE=full|preview   dataset (default full)
#   BP_IDS="hb002 hb020"     build only these problem ids (default: all)
#   BP_MAX_GB=15             skip problems whose archive exceeds this (default: no cap)
#   BP_PLATFORM=linux/amd64  build platform (default linux/amd64)
#   BP_BASE_TAG              base image tag (default <BP_PREFIX>base)
#   BP_SKIP_EXISTING=1       skip problems whose image is already in the registry
set -euo pipefail

: "${HF_TOKEN:?set HF_TOKEN (dataset access needed to fetch the data)}"
: "${BP_PREFIX:?set BP_PREFIX to your image repo, e.g. <acct>.dkr.ecr.<region>.amazonaws.com/prd/biomystery:}"
SOURCE="${BP_SOURCE:-full}"
PLATFORM="${BP_PLATFORM:-linux/amd64}"
BASE_TAG="${BP_BASE_TAG:-${BP_PREFIX}base}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# The repo id and revision are read from the module, which is the single source of
# the pin. problems.csv is fetched at run time at that pin while data/<id>.zip is
# baked into images at build time here, and a mismatch between the two runs and
# grades normally against wrong question and data pairs, with nothing to catch it.
read -r REPO REV < <(
    cd "$REPO_ROOT" && uv run python -c "
from inspect_evals.biomysterybench.biomysterybench import (
    FULL_REPO, FULL_REVISION, PREVIEW_REPO, PREVIEW_REVISION,
)
full = '$SOURCE' == 'full'
print(FULL_REPO if full else PREVIEW_REPO, FULL_REVISION if full else PREVIEW_REVISION)
"
)

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

echo "==> Building base image $BASE_TAG"
docker build --platform "$PLATFORM" -f "$SCRIPT_DIR/Dockerfile.base" -t "$BASE_TAG" "$SCRIPT_DIR"
docker push "$BASE_TAG"

echo "==> Reading problem list from $REPO"
(cd "$REPO_ROOT" && uv run python - "$REPO" "$REV" "$work/ids.txt" \
    "$work/sizes.json" "$SOURCE") <<'PY'
import csv, json, os, sys
from huggingface_hub import HfApi

from inspect_evals.utils.huggingface import hf_hub_download

repo, rev, out, sizes_out, source = sys.argv[1:6]
token = os.environ["HF_TOKEN"]
path = hf_hub_download(repo, "problems.csv", repo_type="dataset", revision=rev,
                       token=token)
with open(path, newline="", encoding="utf-8") as f, \
     open(out, "w", encoding="utf-8") as w:
    for row in csv.DictReader(f):
        w.write(row["id"] + "\n")

# dataset_info covers the whole repo, so it is called once here and the sizes are
# written out for the per-problem step to read.
sizes = {}
if source != "preview":
    info = HfApi().dataset_info(repo, revision=rev, files_metadata=True, token=token)
    sizes = {s.rfilename: (s.size or 0) for s in info.siblings or []}
with open(sizes_out, "w", encoding="utf-8") as w:
    json.dump(sizes, w)
PY

ids="$(tr '\n' ' ' < "$work/ids.txt")"
[ -n "${BP_IDS:-}" ] && ids="$BP_IDS"

for id in $ids; do
    image="${BP_PREFIX}${id}"

    if [ "${BP_SKIP_EXISTING:-0}" = "1" ] && docker manifest inspect "$image" >/dev/null 2>&1; then
        echo "==> $id: image exists, skipping"
        continue
    fi

    echo "==> $id: fetching data"
    ctx="$work/$id"; mkdir -p "$ctx"
    rc=0
    (cd "$REPO_ROOT" && uv run python - "$REPO" "$REV" "$id" "$SOURCE" "$ctx" \
        "${BP_MAX_GB:-0}" "$work/sizes.json") <<'PY' || rc=$?
import json, os, sys, zipfile

from inspect_evals.utils.huggingface import hf_hub_download

repo, rev, pid, source, ctx, max_gb, sizes_path = sys.argv[1:8]
token = os.environ["HF_TOKEN"]
arc = "data.zip" if source == "preview" else f"data/{pid}.zip"
if float(max_gb) > 0 and source != "preview":
    with open(sizes_path, encoding="utf-8") as f:
        sizes = json.load(f)
    if arc not in sizes:
        print(f"    no archive for {pid}", file=sys.stderr); sys.exit(3)
    if sizes[arc] / 1e9 > float(max_gb):
        print(f"    {pid} archive {sizes[arc]/1e9:.1f}GB > BP_MAX_GB={max_gb}, skip",
              file=sys.stderr); sys.exit(3)
path = hf_hub_download(repo, arc, repo_type="dataset", revision=rev, token=token)
try:
    with zipfile.ZipFile(path) as z:
        if source == "preview":
            # bundled zip holds every problem under <id>/; extract only this one, flatten
            members = [m for m in z.namelist() if m.startswith(f"{pid}/")]
            if not members:
                print(f"    {pid} not in preview bundle", file=sys.stderr); sys.exit(3)
            for m in members:
                z.extract(m, ctx)
            inner = os.path.join(ctx, pid)
            for name in os.listdir(inner):
                os.rename(os.path.join(inner, name), os.path.join(ctx, name))
            os.rmdir(inner)
        else:
            z.extractall(ctx)
finally:
    # hf_hub_download caches each archive under ~/.cache/huggingface and returns a
    # symlink into it. The cache is cleared per problem because the full set is
    # 155 GB and would otherwise exhaust the runner disk.
    blob = os.path.realpath(path)
    for target in (path, blob):
        if os.path.lexists(target):
            os.unlink(target)
PY
    if [ "$rc" -ne 0 ]; then
        rm -rf "$ctx"
        # Exit 3 is a deliberate skip: the archive is over BP_MAX_GB or absent from
        # the bundle. Any other code is a real failure -- an HF 401/429, a network
        # drop, a full disk, a corrupt zip -- and aborts, because a problem with no
        # image surfaces mid-eval as a docker pull error.
        if [ "$rc" -eq 3 ]; then
            echo "    (skipped $id)"; continue
        fi
        echo "!!! $id: fetch failed with exit $rc, aborting" >&2
        exit "$rc"
    fi

    echo "==> $id: build + push $image"
    docker build --platform "$PLATFORM" -f "$SCRIPT_DIR/Dockerfile" \
        --build-arg "BASE=$BASE_TAG" -t "$image" "$ctx"
    docker push "$image"
    rm -rf "$ctx"   # reclaim disk before the next (up to ~27 GB) problem
done

echo "==> Done. Run the eval with:"
echo "    BMB_IMAGE_PREFIX=$BP_PREFIX inspect eval inspect_evals/bio_mystery_bench -T source=$SOURCE"
