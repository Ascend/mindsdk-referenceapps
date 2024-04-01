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

#include "CaptionImpl.h"
#include "MxBase/MxBase.h"
#include "MxBase/Log/Log.h"

enum tokenType {
    CHINESE, ENGLISH, ALPHA
};

APP_ERROR CaptionImpl::init(const std::string &inputFont, const std::string &fontSize,
                            const std::string &inputFont2, const std::string &fontSize2) {
    // 初始化CaptionGenerator
    auto ret = captionGenerator_.init(inputFont, fontSize, inputFont2, fontSize2);
    if (ret != 0) {
        LogError << "Fail to init captionGenerator";
        return APP_ERR_COMM_FAILURE;
    }
    int font1Height = CaptionGenManager::getInstance().FindHeight(inputFont, fontSize);
    int font2Height = CaptionGenManager::getInstance().FindHeight(inputFont2, fontSize2);
    if (font1Height < font2Height) {
        height_ = font2Height * 2;
    } else {
        height_ = font1Height * 2;
    }
    font_ = inputFont;
    font2_ = inputFont2;
    fontSizeMap_[inputFont] = fontSize;
    fontSizeMap_[inputFont2] = fontSize2;
    return APP_ERR_OK;
}

APP_ERROR CaptionImpl::initRectAndColor(cv::Scalar textColor, cv::Scalar backgroundColor, double fontScale, int width) {
    if (width < 64) {
        LogError << "The width of backgroundSize or the height of backgroundSize should be >= 64.";
    }
    width_ = width;
    textColor_ = textColor;
    backgroundColor_ = backgroundColor;
    fontScale_ = fontScale;
    dstBackgroundWidth_ = int(fontScale * width_);
    dstBackgroundHeight_ = int(fontScale * height_);

    // 初始化captionGenerator
    cv::Size backgroundSize(width, height_);
    APP_ERROR ret = captionGenerator_.initRectAndTextColor(backgroundSize, textColor);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to init captionGenerator";
        return APP_ERR_COMM_FAILURE;
    }

    // 分配保存字幕结果的Tensor
    caption_ = MxBase::Tensor(std::vector<uint32_t>{uint32_t(dstBackgroundHeight_), uint32_t(dstBackgroundWidth_), 3},
                              MxBase::TensorDType::UINT8, 0);
    ret = MxBase::Tensor::TensorMalloc(caption_);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to malloc caption tensor.";
        return APP_ERR_COMM_FAILURE;
    }

    // 字幕背景生成
    coloredTensor_ = MxBase::Tensor(std::vector<uint32_t>{caption_.GetShape()[0], caption_.GetShape()[1], 3},
                                    MxBase::TensorDType::UINT8, 0);
    MxBase::Tensor color_r = MxBase::Tensor(std::vector<uint32_t>{caption_.GetShape()[0], caption_.GetShape()[1], 1},
                                            MxBase::TensorDType::UINT8, 0);
    MxBase::Tensor::TensorMalloc(color_r);

    ret = color_r.SetTensorValue((uint8_t) backgroundColor[2]);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to set the value of red color for caption background.";
        return APP_ERR_COMM_FAILURE;
    }
    MxBase::Tensor color_g = MxBase::Tensor(std::vector<uint32_t>{caption_.GetShape()[0], caption_.GetShape()[1], 1},
                                            MxBase::TensorDType::UINT8, 0);
    MxBase::Tensor::TensorMalloc(color_g);
    ret = color_g.SetTensorValue((uint8_t) backgroundColor[1]);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to set the value of green color for caption background.";
        return APP_ERR_COMM_FAILURE;
    }
    MxBase::Tensor color_b = MxBase::Tensor(std::vector<uint32_t>{caption_.GetShape()[0], caption_.GetShape()[1], 1},
                                            MxBase::TensorDType::UINT8, 0);
    MxBase::Tensor::TensorMalloc(color_b);
    ret = color_b.SetTensorValue((uint8_t) backgroundColor[0]);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to set the value of blue color for caption background.";
        return APP_ERR_COMM_FAILURE;
    }
    std::vector<MxBase::Tensor> color_vec{color_r, color_g, color_b};
    ret = MxBase::Merge(color_vec, coloredTensor_);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to merge RGB color for caption background.";
        return APP_ERR_COMM_FAILURE;
    }
    return APP_ERR_OK;
}

APP_ERROR CaptionImpl::putText(MxBase::Tensor &img, const std::string text1, const std::string text2, cv::Point org, float opacity) {
    // Step0: 校验字幕贴字位置
    int rightBottomX = org.x + dstBackgroundWidth_;
    int rightBottomY = org.y + dstBackgroundHeight_;
    if (rightBottomY > img.GetShape()[0]) {
        LogWarn << "The y part of right bottom point (" << rightBottomY << ") exceed image width ("
                << img.GetShape()[0] << ". The text is automatically putted in the margin.";
        org.y = img.GetShape()[0] - dstBackgroundHeight_;
    }
    if (rightBottomX > img.GetShape()[1]) {
        LogWarn << "The x part of right bottom point (" << rightBottomX << ") exceed image height ("
                << img.GetShape()[1] << ". The text is automatically putted in the margin.";
        org.x = img.GetShape()[1] - dstBackgroundWidth_;
    }

    // Step1: 字幕生成
    MxBase::Tensor mask;
    bool isResize = true;
    if (fontScale_ == 1) {
        isResize = false;
    }
    APP_ERROR ret = captionGenerator_.captionGen(caption_, coloredTensor_, text1, text2, mask, isResize);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to generate caption.";
        return APP_ERR_COMM_FAILURE;
    }

    // step2: 图片+字幕+字幕背景叠加
    MxBase::Rect dstRect(org.x, org.y, org.x + dstBackgroundWidth_, org.y + dstBackgroundHeight_);
    MxBase::Rect srcRect(0, 0, dstBackgroundWidth_, dstBackgroundHeight_);
    ret = img.SetReferRect(dstRect);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to set referRect for image.";
        return APP_ERR_COMM_FAILURE;
    }
    ret = mask.SetReferRect(srcRect);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to set referRect for mask.";
        return APP_ERR_COMM_FAILURE;
    }
    ret = coloredTensor_.SetReferRect(srcRect);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to set referRect for coloredTensor.";
        return APP_ERR_COMM_FAILURE;
    }
    ret = caption_.SetReferRect(srcRect);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to set referRect for caption.";
        return APP_ERR_COMM_FAILURE;
    }
    int blendRet = MxBase::BlendImageCaption(img, caption_, mask, coloredTensor_, opacity);
    if (blendRet != APP_ERR_OK) {
        LogError << "Fail to conduct blendImageCaption operator.";
        return APP_ERR_COMM_FAILURE;
    }
    return APP_ERR_OK;
}

int CaptionImpl::getLength(const std::string text) {
    std::vector<uint32_t> compChrNum;
    std::vector<std::pair<int, int>> tokens = captionGenerator_.SentenceToTokensId(text, compChrNum);
    int totalWidth = 0;
    for (const auto& token : tokens) {
        std::string font = "";
        if (token.second == CHINESE) {
            font = font_;
        } else {
            font = font2_;
        }
        totalWidth += CaptionGenManager::getInstance().FindWidth(font, fontSizeMap_[font], token.first);
    }
    return totalWidth;
}