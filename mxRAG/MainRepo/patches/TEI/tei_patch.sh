#!/bin/bash
set -e

PATCH_DIR=$(cd $(dirname $0); pwd)

# TEI打patch
cd $1
patch -p1 < $PATCH_DIR/tei.patch