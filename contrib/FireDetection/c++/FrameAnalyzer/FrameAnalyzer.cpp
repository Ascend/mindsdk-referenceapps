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
#include <algorithm>
#include <map>
#include <iostream>
#include <string>
#include <ctime>
#include <chrono>
#include "./FrameAnalyzer.h"
using namespace std;
using namespace MxBase;

const int ANCHOR_DIM = 3;
const std::vector<int> STRIDE_LIST = {80*80, 40*40, 20*20};
const std::vector<int> LAYER_SIZE_LIST = {80, 40, 20};
const std::map<int, std::string> INDEX_TO_CLASS = {{0, "Fire"}, {1, "Smoke"}};
const int INFO_NUMBER_PER_BOX = 7;
const int BBOX_INFO_NUMBER_PER_BOX = 4;
const float OBJECT_THRESHOLD = 0.1;
const float CLASS_THRESHOLD = 0.4;
const float NMS_THRESHOLD = 0.6;
const int CLASS_NUMBER = 2;
const int MODEL_LENGTH = 640;
const int DECODE_NUMBER = 2;
MxBase::Size modelSize(MODEL_LENGTH, MODEL_LENGTH);
std::vector<std::vector<std::vector<int>>> ANCHORS_SIZE =
        {{{10, 13}, {16, 30}, {33, 23}}, {{30, 61}, {62, 45}, {59, 119}}, {{116, 90}, {156, 198}, {373, 326}}};


FrameAnalyzeModel::FrameAnalyzeModel(std::string modelPath, int deviceId) {
    model_ = std::make_shared<Model>(modelPath, deviceId);
    imageProcessor_ = std::make_shared<ImageProcessor>(deviceId);
}


APP_ERROR FrameAnalyzeModel::DecodeBox(std::vector<MxBase::Tensor>& outputs, std::vector<MxBase::ObjectInfo>& detBoxes) {
    for (int layer = 0; layer < outputs.size(); layer++) {
        int anchorNumber = outputs[layer].GetShape()[1];
        int tensorHeight = outputs[layer].GetShape()[2];
        int tensorWidth = outputs[layer].GetShape()[3];
        float *tensor = static_cast<float *>(outputs[layer].GetData());
        for (int heightIndex = 0; heightIndex < tensorHeight; ++heightIndex) {
            for (int widthIndex = 0; widthIndex < tensorWidth; ++widthIndex) {
                for (int anchorIndex = 0; anchorIndex < anchorNumber; ++anchorIndex) {
                    int bIdx = anchorIndex * tensorWidth * tensorHeight * INFO_NUMBER_PER_BOX + heightIndex *
                            tensorWidth * INFO_NUMBER_PER_BOX + widthIndex * INFO_NUMBER_PER_BOX;
                    int oIdx = bIdx + BBOX_INFO_NUMBER_PER_BOX;
                    int cIdx = bIdx + BBOX_INFO_NUMBER_PER_BOX + 1;
                    // 取目标框得分和分类得分
                    float objectness = fastmath::sigmoid(tensor[oIdx]);
                    if (objectness <= OBJECT_THRESHOLD) {
                        continue;
                    }
                    float classScore1 = fastmath::sigmoid(tensor[cIdx]) * objectness;
                    float classScore2 = fastmath::sigmoid(tensor[cIdx+1]) * objectness;
                    if (classScore1 < CLASS_THRESHOLD && classScore2 < CLASS_THRESHOLD) {
                        continue;
                    }
                    float tempScore = classScore1;
                    int tempClassId = 0;
                    if (classScore1 < classScore2) {
                        tempScore = classScore2;
                        tempClassId = 1;
                    }
                    float x = (widthIndex + fastmath::sigmoid(tensor[bIdx]) * DECODE_NUMBER - 0.5);
                    float y = (heightIndex + fastmath::sigmoid(tensor[bIdx + 1]) * DECODE_NUMBER - 0.5);
                    auto widthTempValue = fastmath::sigmoid(tensor[bIdx + 2]);
                    float width = widthTempValue * widthTempValue * 4 * ANCHORS_SIZE[layer][anchorIndex][0];
                    auto heightTempValue = fastmath::sigmoid(tensor[bIdx + 3]);
                    float height = heightTempValue * heightTempValue * 4 * ANCHORS_SIZE[layer][anchorIndex][1];
                    MxBase::ObjectInfo objInfo;
                    objInfo.x0 = max(x / LAYER_SIZE_LIST[layer] * modelSize.width - width / DECODE_NUMBER, 0.0f);
                    objInfo.y0 = max(y / LAYER_SIZE_LIST[layer] * modelSize.height - height / DECODE_NUMBER, 0.0f);
                    objInfo.x1 = min(x / LAYER_SIZE_LIST[layer] * modelSize.width + width /DECODE_NUMBER, static_cast<float>(modelSize.width));
                    objInfo.y1 = min(y / LAYER_SIZE_LIST[layer] * modelSize.height + height / DECODE_NUMBER, static_cast<float>(modelSize.height));
                    objInfo.confidence = tempScore;
                    objInfo.classId = tempClassId;
                    objInfo.className = INDEX_TO_CLASS[tempClassId];
                    detBoxes.emplace_back(objInfo);
                }
            }
        }
    }
    if (detBoxes.size() > 0){
        MxBase::NmsSort(detBoxes,NMS_THRESHOLD);
    }
    return APP_ERR_OK;
}

APP_ERROR FrameAnalyzeModel::Infer(MxBase::Image &image, std::vector<ObjectInfo>& detBoxes) {
    Size imageSize = image.GetOriginalSize();
    float heightRatio = imageSize.height / modelSize.height;
    float widthRatio = imageSize.width / modelSize.width;
    if (imageSize.height != modelSize.height or imageSize.width != modelSize.width) {
        APP_ERROR ret = imageProcessor_->Resize(image, modelSize, modelInputImage_);
        if (ret != APP_ERR_OK) {
            LogError << "Fail to resize the image";
            return ret;
        }
    } else {
        modelInputImage_ = image;
    }
    // Model infer
    Tensor imageTensor = modelInputImage_.ConvertToTensor(true, false);
    std::vector<uint32_t> newShape = imageTensor.GetShape();
    newShape.insert(newShape.begin(), 1);
    imageTensor.SetShape(newShape);
    std::vector<Tensor> inferInputs = {};
    inferInputs.push_back(imageTensor);
    std::vector<Tensor> inferOutputs = model_->Infer(inferInputs);
    // Move tensor form host to device
    std::vector<Tensor> outputs = {};
    for (Tensor tensor: inferOutputs) {
        APP_ERROR ret = tensor.ToHost();
        if (ret != APP_ERR_OK) {
            LogError << "Fail to move tensor to host";
        }
        outputs.push_back(tensor);
    }
    APP_ERROR ret = DecodeBox(outputs, detBoxes);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to decode bounding box.";
        return ret;
    }
    if (detBoxes.size() > 0){
        MxBase::NmsSort(detBoxes,NMS_THRESHOLD);
    }
    for (int i = 0; i < detBoxes.size(); ++i) {
        detBoxes[i].x1 = detBoxes[i].x1 * widthRatio;
        detBoxes[i].x0 = detBoxes[i].x0 * widthRatio;
        detBoxes[i].y1 = detBoxes[i].y1 * heightRatio;
        detBoxes[i].y0 = detBoxes[i].y0 * heightRatio;
    }
    return APP_ERR_OK;
}


APP_ERROR FrameAnalyzer::Alarm(std::vector<ObjectInfo>& detBoxes, int frameId) {
    for (int i = 0; i < detBoxes.size(); ++i) {
        std::cout << "Frame " << frameId << " detect " << detBoxes[i].className << "! Confidence: "
                << detBoxes[i].confidence << ", x0: " << detBoxes[i].x0 << ", y0: " << detBoxes[i].y0
                << ", x1: " << detBoxes[i].x1 << ", y1: " << detBoxes[i].y1 << std::endl;
    }
    return APP_ERR_OK;
}


APP_ERROR FrameAnalyzer::Analyze(Image &image, std::vector<ObjectInfo>& detBoxes) {
    return frameAnalyzeModel_.Infer(image, detBoxes);
}