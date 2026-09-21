# Per-problem image: the shared tools base plus this problem's data, already
# extracted under data/. Built once per problem by build_and_push.sh.
#
#   docker build -f Dockerfile --build-arg BASE=<base-image> \
#     -t <prefix><id> <dir-holding-this-problem's-data>
ARG BASE
FROM ${BASE}

# The build context is the problem's own extracted data directory.
COPY . /workspace/data/

WORKDIR /workspace
