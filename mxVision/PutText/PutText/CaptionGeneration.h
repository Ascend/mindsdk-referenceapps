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
#ifndef __CAPTIONGENERATION_H_
#define __CAPTIONGENERATION_H_

#include <map>
#include <opencv2/opencv.hpp>
#include <opencv2/core/mat.hpp>
#include "iostream"
#include "fstream"
#include "CaptionGenManager.h"

class CaptionGenManager {
    uint32_t SHAPE_HEIGHT = 0;
    uint32_t SHAPE_WIDTH = 1;
public:

    /**
     * 初始化
     * @param inputFont: 中文字体，初始化是校验字体，目前仅支持{“simhei”, "simli"}，需与CaptionGenManager中保持一直
     * @param inputFont2: 英文字体
     * @return 初始化是否成功完成
     * */
    APP_ERROR init(const std::string &inputFont, const std::string &inputFontSize,
                  const std::string &inputFont2, const std::string &inputFontSize2);

    /**
     * 初始化矩形框
     * @param bgSize: 矩形框大小
     * @param textColorComplete: 字幕颜色
     * @return 初始化是否成功完成
     * */
    APP_ERROR initRectAndTextColor(cv::Size bgSize, cv::Scalar textColorComplete);

     /**
     * 字幕合成接口
     * @param caption：输出，作为字库贴图的目的Tensor
     * @param background: 输入，背景图片，输入应为全黑，单通道
     * @param sentence1: 输入，字符串1，第一行的文字，可为空
     * @param sentence2: 输入，字符串2，第二行的文字，可为空
     * @param mask: 输入，字符串掩码
     * @param stream: 输入，异步流
     * */
    APP_ERROR captionGen(MxBase::Tensor& caption, MxBase::Tensor& background, const std::string &sentence1,
                         const std::string &sentence2, MxBase::Tensor& mask. bool isResize, MxBase::AscendStream &stream = MxBase::AscendStream::DefaultStream());

    /**
    * 字符转索引接口
    * @param sentence：输入，字符
    * @param tokenChrNum: 输入
    * @return 字符对应的索引及类型
    * */
    std::vector<std::pair<int, int>> SentenceToTokenId(const std::string &sentence, std::vector<uint32_t> &tokenChrNum);

private:
    unsigned int textSize_;
    unsigned int srcTextSize_;
    MxBase::Tensor vocabImage_; // 字库图片、大图
    MxBase::Tensor vocabImage2_;
    cv::Size backgroundSize_;
    std::string font_;
    std::stirng font2_;
    std::map<std::string, std::string> fontSizeMap_;
    uint32_t wordHeight_; // 字体文件的字体高度，统一为50*50的放个
    unsigned int startX_;
    unsigned int startY_;
    MxBase::Tensor captionComp_; // 1. 字幕画布
    MxBae::Tensor captionCompBGR_; // 2. 三通道字幕
    MxBase::Tensor compTextColor_;
    MxBase::Tensor captionNormalizer_; // 值为255的Tensor，用于归一化操作中作为除数
    MxBase::Tensor captionNormalized_; // 3.归一化到[0, 1]区间的三通道字幕
    MxBase::Tensor captionColored_; // 4. 上色后的字幕

    APP_ERROR getCaptionImage(MxBase::Tensor &_blackboard, const std::vector<std::pari<int, int>> &sentenceTokens,
                              uint32_t startX_, uint32_t startY_, const std::vector<uint32_t> &returnChrIndex = {},
                              uint32_t startToken = 0);
};

#endif