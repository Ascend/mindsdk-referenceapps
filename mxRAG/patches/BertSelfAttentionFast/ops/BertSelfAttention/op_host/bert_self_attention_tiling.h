/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2024. All rights reserved.
 */



#ifndef BERT_SELF_ATTENTION_TILING_H
#define BERT_SELF_ATTENTION_TILING_H

#include "register/tilingdata_base.h"
#include "tiling/tiling_api.h"

namespace optiling {
    BEGIN_TILING_DATA_DEF(BertSelfAttentionTilingData)
    TILING_DATA_FIELD_DEF(uint32_t, usedAivCoreNum);
    TILING_DATA_FIELD_DEF(uint32_t, aicNum);
    TILING_DATA_FIELD_DEF(uint32_t, aivNum);
    TILING_DATA_FIELD_DEF(uint32_t, batchSize);
    TILING_DATA_FIELD_DEF(uint32_t, sequenceLength);
    TILING_DATA_FIELD_DEF(uint32_t, featuresSize);
    TILING_DATA_FIELD_DEF(uint32_t, headNum);
    TILING_DATA_FIELD_DEF(uint32_t, headSize);
    TILING_DATA_FIELD_DEF(uint32_t, fomerBatchNum);
    TILING_DATA_FIELD_DEF(uint32_t, perBlockBatchFormer);
    TILING_DATA_FIELD_DEF(uint32_t, perBlockBatchLatter);

    TILING_DATA_FIELD_DEF(uint32_t, baseSeqLength);
    TILING_DATA_FIELD_DEF(uint32_t, tailSeqLength);
    TILING_DATA_FIELD_DEF(uint32_t, softMaxWorkSpaceSize);
    TILING_DATA_FIELD_DEF(float, sqrtHeadSize);
    TILING_DATA_FIELD_DEF(float, dropOutKeepProb);

    TILING_DATA_FIELD_DEF_STRUCT(TCubeTiling, projectionTiling);
    TILING_DATA_FIELD_DEF_STRUCT(TCubeTiling, scoresCubeTiling);
    TILING_DATA_FIELD_DEF_STRUCT(TCubeTiling, probsCubeTiling);
    TILING_DATA_FIELD_DEF_STRUCT(SoftMaxTiling, softMaxTilingData);
    END_TILING_DATA_SEF;

    REGISTER_TILING_DATA_CLASS(BertSelfAttention, BertSelfAttentionTilingData)
}

#endif