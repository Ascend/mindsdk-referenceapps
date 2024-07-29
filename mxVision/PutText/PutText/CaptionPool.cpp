/*
 * Copyright(C) 2024. Huawei Technologies Co.,Ltd. All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
#include "CaptionPool.h"

CaptionPool::CaptionPool(size_t max_size) {
    text2Lenghth_ = std::make_shared<LimitedSizeMap<std::string, int>>(max_size);
    text2CaptionMap_ = std::make_shared<LimitedSizeMap<std::string, MxBase::Tensor>>(max_size);
    text2MaskMap_ = std::make_shared<LimitedSizeMap<std::string, MxBase::Tensor>>(max_size);
}

APP_ERROR CaptionPool::putCaptionAndMask(std::string text1, std::string text2, MxBase::Tensor caption,
                                         MxBase::Tensor mask) {
    std::string textMark = text1 + "_" + text2;
    if(text2MaskMap_ != nullptr && text2CaptionMap_ != nullptr) {
        text2CaptionMap_->put(textMark, caption);
        text2MaskMap_->put(textMark, mask);
        return APP_ERR_OK;
    }
    return APP_ERR_COMM_FAILURE;
}

APP_ERROR CaptionPool::getCaptionAndMask(std::string text1, std::string text2, MxBase::Tensor& caption,
                                         MxBase::Tensor& mask) {
    std::string textMark = text1 + "_" + text2;
    if (text2MaskMap_ != nullptr && text2CaptionMap_ != nullptr &&
        text2CaptionMap_->get(textMark, caption) && text2MaskMap_->get(textMark, mask)) {
        return APP_ERR_OK;
    }
    return APP_ERR_COMM_FAILURE;
}

bool CaptionPool::isCaptionExist(std::string text1, std::string text2) {
    std::string textMark = text1 + "_" + text2;
    if (text2MaskMap_ != nullptr && text2CaptionMap_ != nullptr &&
        text2MaskMap_->isExist(textMark) && text2CaptionMap_->isExist(textMark)) {
        return true;
    }
    return false;
}

APP_ERROR CaptionPool::putCaptionLength(std::string text, int length) {
    if (text2Lenghth_ != nullptr) {
        text2Lenghth_->put(text, length);
        return APP_ERR_OK;
    }
    return APP_ERR_COMM_FAILURE;
}


APP_ERROR CaptionPool::getCaptionLength(std::string text, int& length) {
    if (text2Lenghth_ != nullptr && text2Lenghth_->get(text, length)) {
        return APP_ERR_OK;
    }
    return APP_ERR_COMM_FAILURE;
}

bool CaptionPool::isCaptionLengthExist(std::string text) {
    if (text2Lenghth_ != nullptr && text2Lenghth_->isExist(text)) {
        return true;
    }
    return false;
}