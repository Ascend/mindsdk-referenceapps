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
#include "MxBase/DeviceManager/DeviceManager.h"

enum tokenType {
    CHINESE, ENGLISH, ALPHA
};

APP_ERROR CaptionImpl::init(const std::string &inputFont, const std::string &fontSize,
                            const std::string &inputFont2, const std::string &fontSize2, int32_t deviceId) {
    APP_ERROR ret = MxBase::DeviceManager::GetInstance()->CheckDeviceId(deviceId);
    if (ret != APP_ERR_OK) {
        LogError << "Device id is out of range, current deviceId is " << deviceId << "." << GetErrorInfo(ret);
        return APP_ERR_COMM_FAILURE;
    }
    deviceId_ = deviceId;
    // 初始化CaptionGenerator
    ret = captionGenerator_.init(inputFont, fontSize, inputFont2, fontSize2, deviceId);
    if (ret != 0) {
        LogError << "Fail to init captionGenerator";
        return APP_ERR_COMM_FAILURE;
    }
    int font1Height = CaptionGenManager::getInstance().FindHeight(inputFont, fontSize);
    int font2Height = CaptionGenManager::getInstance().FindHeight(inputFont2, fontSize2);
    if (font1Height < font2Height) {
        height_ = font2Height;
    } else {
        height_ = font1Height;
    }
    font_ = inputFont;
    font2_ = inputFont2;
    fontSizeMap_[inputFont] = fontSize;
    fontSizeMap_[inputFont2] = fontSize2;
    return APP_ERR_OK;
}

APP_ERROR CaptionImpl::initRectAndColor(cv::Scalar textColor, cv::Scalar backgroundColor, double fontScale, int width) {
    const int EXTRA_MARGIN_SIZE = 64;
    const int WIDTH_MIN_VALUE = 20;
    const int LINE_NUMBER = 2;
    if (width < WIDTH_MIN_VALUE) {
        LogError << "The width of backgroundSize or the height of backgroundSize should be >= 64.";
    }
    width_ = width;
    textColor_ = textColor;
    backgroundColor_ = backgroundColor;
    fontScale_ = fontScale;
    dstBackgroundWidth_ = int(fontScale * (width_ + EXTRA_MARGIN_SIZE));
    dstBackgroundHeight_ = int(fontScale * (height_ * LINE_NUMBER + EXTRA_MARGIN_SIZE));

    // 初始化captionGenerator
    cv::Size backgroundSize(width + EXTRA_MARGIN_SIZE, height_ * LINE_NUMBER + EXTRA_MARGIN_SIZE);
    APP_ERROR ret = captionGenerator_.initRectAndTextColor(backgroundSize, textColor);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to init captionGenerator";
        return APP_ERR_COMM_FAILURE;
    }

    // 分配保存字幕结果的Tensor
    caption_ = MxBase::Tensor(std::vector<uint32_t>{uint32_t(dstBackgroundHeight_), uint32_t(dstBackgroundWidth_), 3},
                              MxBase::TensorDType::UINT8, deviceId_);
    ret = MxBase::Tensor::TensorMalloc(caption_);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to malloc caption tensor.";
        return APP_ERR_COMM_FAILURE;
    }

    // 字幕背景生成
    coloredTensor_ = MxBase::Tensor(std::vector<uint32_t>{caption_.GetShape()[0], caption_.GetShape()[1], 3},
                                    MxBase::TensorDType::UINT8, deviceId_);
    MxBase::Tensor color_r = MxBase::Tensor(std::vector<uint32_t>{caption_.GetShape()[0], caption_.GetShape()[1], 1},
                                            MxBase::TensorDType::UINT8, deviceId_);
    MxBase::Tensor::TensorMalloc(color_r);

    ret = color_r.SetTensorValue((uint8_t) backgroundColor[2]);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to set the value of red color for caption background.";
        return APP_ERR_COMM_FAILURE;
    }
    MxBase::Tensor color_g = MxBase::Tensor(std::vector<uint32_t>{caption_.GetShape()[0], caption_.GetShape()[1], 1},
                                            MxBase::TensorDType::UINT8, deviceId_);
    MxBase::Tensor::TensorMalloc(color_g);
    ret = color_g.SetTensorValue((uint8_t) backgroundColor[1]);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to set the value of green color for caption background.";
        return APP_ERR_COMM_FAILURE;
    }
    MxBase::Tensor color_b = MxBase::Tensor(std::vector<uint32_t>{caption_.GetShape()[0], caption_.GetShape()[1], 1},
                                            MxBase::TensorDType::UINT8, deviceId_);
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

APP_ERROR CaptionImpl::setTensorsReferRect(MxBase::Tensor &img, MxBase::Rect srcRect, MxBase::Rect dstRect) {
    APP_ERROR ret = img.SetReferRect(dstRect);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to set referRect for image.";
        return APP_ERR_COMM_FAILURE;
    }
    ret = mask_.SetReferRect(srcRect);
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
    return APP_ERR_OK;
}
APP_ERROR CaptionImpl::checkPutText(MxBase::Tensor &img, const std::string text1, const std::string text2, cv::Point &org) {
    if (img.GetDeviceId() != deviceId_) {
        LogError << "The deviceId of img is not equal to that of CaptionImpl. Please check.";
        return APP_ERR_COMM_FAILURE;
    }
    // Step0: 校验字幕贴字位置
    int roiLength1 = getLength(text1) * fontScale_;
    int roiLength2 = getLength(text2) * fontScale_;
    if (roiLength1 > dstBackgroundWidth_ || roiLength2 > dstBackgroundWidth_) {
        LogError << "The text length exceeds the maximum length of initialized temp tensor. Please initialize again.";
        return APP_ERR_COMM_FAILURE;
    }
    int maxLength = (roiLength1 > roiLength2) ? roiLength1 : roiLength2;
    if (maxLength > img.GetShape()[1]) {
        LogError << "The text length exceeds the maximum length of image.";
        return APP_ERR_COMM_FAILURE;
    }
    int rightBottomX = org.x + maxLength;
    int rightBottomY = org.y + dstBackgroundHeight_;
    if (rightBottomY > img.GetShape()[0]) {
        LogWarn << "The y part of right bottom point (" << rightBottomY << ") exceed image width ("
                << img.GetShape()[0] << ". The text is automatically putted in the margin.";
        org.y = img.GetShape()[0] - dstBackgroundHeight_;
    }
    if (rightBottomX > img.GetShape()[1]) {
        LogWarn << "The x part of right bottom point (" << rightBottomX << ") exceed image height ("
                << img.GetShape()[1] << ". The text is automatically putted in the margin.";
        org.x = img.GetShape()[1] - maxLength;
    }
    return APP_ERR_OK;
}
APP_ERROR CaptionImpl::putText(MxBase::Tensor &img, const std::string text1, const std::string text2, cv::Point org, float opacity) {
    const int LINE_NUMBER = 2;
    if (checkPutText(img, text1, text2, org) != APP_ERR_OK) {
        LogError << "The requirements of putText are not met.";
        return APP_ERR_COMM_FAILURE;
    }

    // Step1: 字幕生成
    bool isResize = true;
    if (fontScale_ == 1) {
        isResize = false;
    }
    if (text1 != formerText1_ || text2 != formerText2_) {
        mask_ = MxBase::Tensor();
        APP_ERROR ret = captionGenerator_.captionGen(caption_, coloredTensor_, text1, text2, mask_, isResize);
        if (ret != APP_ERR_OK) {
            LogError << "Fail to generate caption for putText function.";
            return APP_ERR_COMM_FAILURE;
        }
    }
    // step2: 图片+字幕+字幕背景叠加
    int roiHeight = height_ * fontScale_;
    if (text1 != "") {
        int roiLength = getLength(text1) * fontScale_;
        MxBase::Rect dstRect(org.x, org.y, org.x + roiLength, org.y + roiHeight);
        MxBase::Rect srcRect(0, 0, roiLength, roiHeight);
        setTensorsReferRect(img, srcRect, dstRect);
        APP_ERROR ret = MxBase::BlendImageCaption(img, caption_, mask_, coloredTensor_, opacity);
        if (ret != APP_ERR_OK) {
            LogError << "Fail to conduct blendImageCaption operator.";
            return APP_ERR_COMM_FAILURE;
        }
        formerText1_ = text1;
    }

    if (text2 != "") {
        int roiLength = getLength(text2) * fontScale_;
        MxBase::Rect dstRect(org.x, org.y + roiHeight, org.x + roiLength, org.y + roiHeight * LINE_NUMBER);
        MxBase::Rect srcRect(0, roiHeight, roiLength, roiHeight * LINE_NUMBER);
        setTensorsReferRect(img, srcRect, dstRect);
        APP_ERROR ret = MxBase::BlendImageCaption(img, caption_, mask_, coloredTensor_, opacity);
        if (ret != APP_ERR_OK) {
            LogError << "Fail to conduct blendImageCaption operator.";
            return APP_ERR_COMM_FAILURE;
        }
        formerText2_ = text2;
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