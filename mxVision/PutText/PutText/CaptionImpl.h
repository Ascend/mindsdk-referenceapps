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

#ifndef CAPTIONIMPL_H
#define CAPTIONIMPL_H
#include "CaptionGenManager.h"
#include "CaptionGeneration.h"

class CaptionImpl {
public；
    /**
    * 初始化字体
    * @param inputFont: 中文字体
    * @param inputFont2: 英文字体
    * @return 初始化是否成功完成
    * */
    APP_ERROR init(const std::string &inputFont, const std::string &fontSize,
                   const std::string &inputFont2, const std::string &fontSize2);

    /**
    * 初始化字体颜色和文本背景宽度
    * @param textColor: 字体颜色
    * @param backgroundColor: 背景颜色
    * @param fontScale: 字体的比例因子
    * @param width: 文本宽度，该数值可由getLength接口辅助确定
    * @return 初始化是否成功完成
    * */
    APP_ERROR initRectAndColor(cv::Scalar textColor, cv::Scalar backgroundColor, double fontScale, int width);

    /**
    * 在图中绘制文本
    * @param img: 要绘制的文本图片
    * @param text1: 第一行文本
    * @param text2: 第二行文本
    * @param org：文本的左上角坐标点
    * @param opacity: 不透明度
    * @return 绘制文本是否成功
    * */
    APP_ERROR putText(MxBase::Tensor &img, const std::string text1, const std::string text2, cv::Point org, float opacity);

    /**
    * 获取文本所占宽度
    * @param text: 文本
    * @return 文本宽度
    * */
    int getLength(const std::string text);

private:
    CaptionGeneration captionGenerator_;
    MxBase::Tensor coloredTensor_;
    MxBase::Tensor caption_;
    std::string font_;
    std::string font2_;
    std::map<std::string, std::string> fontSizeMap_;
    cv::Scalar textColor_;
    cv::Scalar backgroundColor_;
    int width_;
    int height_;
    double fontScale_;
    int dstBackgroundWidth_;
    int dstBackgroundHeight_;
};

#endif