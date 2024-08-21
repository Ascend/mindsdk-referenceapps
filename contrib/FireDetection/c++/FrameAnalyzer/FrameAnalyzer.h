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
#ifndef __FRAMEANALYZER_H
#define __FRAMEANALYZER_H
#include <vector>
#include "MxBase/MxBase.h"
#include "MxBase/E2eInfer/Image/Image.h"
#include "MxBase/Maths/FastMath.h"
#include "MxBase/PostProcessBases/PostProcessDataType.h"
#include "MxBase/CV/ObjectDetection/Nms/Nms.h"
using namespace MxBase;

class FrameAnalyzeModel {
public:
    FrameAnalyzeModel(std::string modelPath, int deviceId);

    APP_ERROR Infer(Image &image, std::vector<ObjectInfo>& detBoxes);

private:
    APP_ERROR DecodeBox(std::vector<Tensor>& outputs, std::vector<ObjectInfo>& detBoxes);
    std::shared_ptr <MxBase::Model> model_;
    std::shared_ptr <MxBase::ImageProcessor> imageProcessor_;
    Image modelInputImage_;

};

class FrameAnalyzer {
public:
    FrameAnalyzer(std::string modelPath, int deviceId) : frameAnalyzeModel_(modelPath, deviceId) {};

    APP_ERROR Analyze(Image& image, std::vector<ObjectInfo>& detBoxes);

    APP_ERROR Alarm(std::vector<ObjectInfo>& detBoxes, int frameId);

private:
    FrameAnalyzeModel frameAnalyzeModel_;

};

#endif