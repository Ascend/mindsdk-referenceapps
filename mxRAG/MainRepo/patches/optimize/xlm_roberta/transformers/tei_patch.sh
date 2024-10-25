#!/bin/bash
set -e

PATCH_DIR=$(cd $(dirname $0); pwd)

# transformers打patch
TRANSFORMER_PACKAGE_PATH=$(python3 -c 'import transformers; import os; print(os.path.dirname(transformers.__file__))')
patch -p1 $TRANSFORMER_PACKAGE_PATH/models/xlm_roberta/modeling_xlm_roberta.py < $PATCH_DIR/transformers_xlm_roberta.patch
