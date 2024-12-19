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


#include <vector>
#include <fstream>
#include <iostream>
#include "MxBase/E2eInfer/Model/Model.h"
#include "MxBase/E2eInfer/Tensor/Tensor.h"
#include "MxBase/E2eInfer/GlobalInit/GlobalInit.h"
#include "MxBase/DeviceManager/DeviceManager.h"
#include "MxBase/Asynchron/AscendStream.h"

using namespace MxBase;
using namespace std;

std::string g_OmModelPath = "../model/IAT_lol-sim.om"; // mindir模型路径

void ModelInfer(){
    int32_t deviceId = 0; // 模型部署的芯片
    Model model(g_OmModelPath, deviceId);

    MxBase::VisionDataFormat inputFormat = model.GetInputFormat(); // 获得模型输入的数据组织形式(NHWC 或者 NCHW)。
    switch (inputFormat) {
        case MxBase::VisionDataFormat::NCHW:
            std::cout << "Input format: NCHW" << std::endl;
            break;
        case MxBase::VisionDataFormat::NHWC:
            std::cout << "Input format: NHWC" << std::endl;
            break;
        default:
            std::cout << "Unknown input format" << std::endl;
            break;
    }

    std::cout << "model input tensor num: " << model.GetInputTensorNum() << std::endl;
    std::cout << "model output tensor num: " << model.GetOutputTensorNum() << std::endl;
    
    std::vector<int64_t> inShape64 = model.GetInputTensorShape(); // 获得模型输入的对应Tensor的数据shape信息。
    std::vector<uint32_t> inShape;
    std::cout<< "inputShape:";
    for (auto s: inShape64) {
        std::cout<< " " << s ;
        inShape.push_back(static_cast<uint32_t>(s)); // 动态模型场景下对应的动态维度查询结果为-1。如果要使用查询的结果直接传入Tensor构造函数构造Tensor，需要将int64_t数据转换为uint32_t数据。
    }
    std::cout << std::endl;
    TensorDType dtype = model.GetInputTensorDataType(0); // 获得模型输入的对应Tensor的数据类型信息。
    std::vector<MxBase::Tensor> input; // 输入
    std::vector<MxBase::Tensor> output; // 输出
    for (size_t i = 0; i < model.GetOutputTensorNum(); i++) {
        std::vector<uint32_t> ouputShape = model.GetOutputTensorShape(i); // 获得模型输出的对应Tensor的数据shape信息。查询的结果可直接传入Tensor构造函数用来构造Tensor。
        std::cout << "ouputShape: " ;
        for (size_t j = 0; j < ouputShape.size(); ++j) {
            std::cout << ouputShape[j] << " ";
        }
        std::cout << std::endl;
        MxBase::TensorDType outputDType = model.GetOutputTensorDataType(i); // 获得模型输出的对应Tensor的数据类型信息。
        Tensor dst(ouputShape, outputDType);
        dst.Malloc();
        dst.ToDevice(0);
        output.push_back(dst);
    }
    Tensor src(inShape, dtype);
    src.Malloc();
    src.ToDevice(0);
    input.push_back(src);
    AscendStream stream(0);
    stream.CreateAscendStream();
    auto ret = model.Infer(input, output, stream); // Model的推理接口
    stream.Synchronize();
    stream.DestroyAscendStream();
}

int main(){
    MxBase::MxInit();
    ModelInfer();
    MxBase::MxDeInit();
}