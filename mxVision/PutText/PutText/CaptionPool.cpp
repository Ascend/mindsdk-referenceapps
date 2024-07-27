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

APP_ERROR CaptionPool::putCaptionAndMask(std::string text1, std::string text2, MxBase::Tensor caption,
                                         MxBase::Tensor mask) {
    std::string textMark = text1 + "_" + text2;
    text2CaptionMap_.put(textMark, caption);
    text2MaskMap_.put(textMark, mask);
}

APP_ERROR CaptionPool::getCaptionAndMask(std::string text1, std::string text2, MxBase::Tensor& caption,
                                         MxBase::Tensor& mask) {
    std::string textMark = text1 + "_" + text2;
    if (text2CaptionMap_.get(textMark, caption) && text2MaskMap_.get(textMark, mask)) {
        return APP_ERR_OK;
    }
    return APP_ERR_COMM_FAILURE;
}

bool CaptionPool::isCaptionExist(std::string text1, std::string text2) {
    std::string textMark = text1 + "_" + text2;
    if (text2MaskMap_.isExist(textMark) && text2CaptionMap_.isExist(textMark)) {
        return true;
    }
    return false;
}

APP_ERROR CaptionPool::putCaptionLength(std::string text, int length) {
    text2Lenghth_.put(text, length);
    return APP_ERR_OK;
}


APP_ERROR CaptionPool::getCaptionLength(std::string text, int& length) {
    if (text2Lenghth_.get(text, length)) {
        return APP_ERR_OK;
    }
    return APP_ERR_COMM_FAILURE;
}

bool CaptionPool::isCaptionLengthExist(std::string text) {
    if (text2Lenghth_.isExist(text)) {
        return true;
    }
    return false;
}