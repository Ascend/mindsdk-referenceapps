/*
 * Copyright(C) 2021. Huawei Technologies Co.,Ltd. All rights reserved.
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

#include "MxBase/Log/Log.h"
#include "MxBase/MxBase.h"


using namespace MxBase;

enum class Command {
    AbsOp,
    SqrOp,
    SqrtOp,
    ExpOp,
    LogOp,
    RescaleOp,
    ThresholdBinaryOp,
    ThresholdOp,
    ClipOp,
    SortOp,
    SortIdxOp,
    ConvertToOp,
    AddOp,
    ScaleAddOp,
    AddWeightedOp,
    SubtractOp,
    AbsDiffOp,
    MultiplyOp,
    DivideOp,
    PowOp,
    MinOp,
    MaxOp,
    CompareOp,
    BitwiseAndOp,
    BitwiseOrOp,
    BitwiseXorOp,
    BitwiseNotOp
};


void TensorOperationsProcessor(void* input1, void* input2, std::vector<uint32_t> shape, std::vector<uint32_t> outshape, int lens, Command command, AscendStream &stream, bool bit_op_flag, TensorDType tensor_dtype) {
    //定义输入张量并转移到Device侧
    const uint32_t deviceID = 0;
    Tensor inputTensor1(input1, shape, tensor_dtype);
    inputTensor1.ToDevice(deviceID);
    Tensor inputTensor2(input2, shape, tensor_dtype);
    inputTensor2.ToDevice(deviceID);

    TensorDType output_tensor_dtype = tensor_dtype;
    if (command == Command::ConvertToOp) { //与ConvertTo设置输出参数类型一致
        output_tensor_dtype = TensorDType::UINT8;
    }
    if (command == Command::SortIdxOp) { //SortIdx输出参数类型需为INT32
        output_tensor_dtype = TensorDType::INT32;
    }

    //定义输出张量并申请内存
    Tensor outputTensor(outshape, output_tensor_dtype, deviceID);
    Tensor::TensorMalloc(outputTensor);

    //定义部分操作的额外参数
    static float thresh = 2.0;
    static float minVal = 1.0;
    static float maxVal = 3.0;

    static float alpha = 1.1;
    static float beta = 1.1;
    static float gamma = 1.1;

    static uint8_t axis = 0;
    static bool descending = true;

    static float bias = 1.1;
    static float scale = 2.2;

    //迭代执行27种操作
    APP_ERROR ret;
    switch(command) {
        case Command::AbsOp:
            ret = Abs(inputTensor1, outputTensor, stream);
            break;
        case Command::SqrOp:
            ret = Sqr(inputTensor1, outputTensor, stream);
            break;
        case Command::SqrtOp:
            ret = Sqrt(inputTensor1, outputTensor, stream);
            break;
        case Command::ExpOp:
            ret = Exp(inputTensor1, outputTensor, stream);
            break;
        case Command::LogOp:
            ret = Log(inputTensor1, outputTensor, stream);
            break;
        case Command::RescaleOp:
            ret = Rescale(inputTensor1, outputTensor, scale, bias, stream);
            break;
        case Command::ThresholdBinaryOp:
            ret = ThresholdBinary(inputTensor1, outputTensor, thresh, maxVal, stream);
            break;
        case Command::ThresholdOp:
            ret = Threshold(inputTensor1, outputTensor, thresh, maxVal, ThresholdType::THRESHOLD_BINARY_INV, stream);
            break;
        case Command::ClipOp:
            ret = Clip(inputTensor1, outputTensor, minVal, maxVal, stream);
            break;
        case Command::SortOp:
            ret = Sort(inputTensor1, outputTensor, axis, descending, stream);
            break;
        case Command::SortIdxOp:
            ret = SortIdx(inputTensor1, outputTensor, axis, descending, stream);
            break;
        case Command::ConvertToOp:
            ret = ConvertTo(inputTensor1, outputTensor, TensorDType::UINT8, stream);
            break;
        case Command::AddOp:
            ret = Add(inputTensor1, inputTensor2, outputTensor, stream);
            break;
        case Command::ScaleAddOp:
            ret = ScaleAdd(inputTensor1, scale, inputTensor2, outputTensor, stream);
            break;
        case Command::AddWeightedOp:
            ret = AddWeighted(inputTensor1, alpha, inputTensor2, beta, gamma, outputTensor, stream);
            break;
        case Command::SubtractOp:
            ret = Subtract(inputTensor1, inputTensor2, outputTensor, stream);
            break;
        case Command::AbsDiffOp:
            ret = AbsDiff(inputTensor1, inputTensor2, outputTensor, stream);
            break;
        case Command::MultiplyOp:
            ret = Multiply(inputTensor1, inputTensor2, outputTensor, scale, stream);
            break;
        case Command::DivideOp:
            ret = Divide(inputTensor1, inputTensor2, outputTensor, scale, stream);
            break;
        case Command::PowOp:
            ret = Pow(inputTensor1, inputTensor2, outputTensor, stream);
            break;
        case Command::MinOp:
            ret = Min(inputTensor1, inputTensor2, outputTensor, stream);
            break;
        case Command::MaxOp:
            ret = Max(inputTensor1, inputTensor2, outputTensor, stream);
            break;
        case Command::CompareOp:
            ret = Compare(inputTensor1, inputTensor2, outputTensor, CmpOp::CMP_LE, stream);
            break;
        case Command::BitwiseAndOp:
            ret = BitwiseAnd(inputTensor1, inputTensor2, outputTensor, stream);
            break;
        case Command::BitwiseOrOp:
            ret = BitwiseOr(inputTensor1, inputTensor2, outputTensor, stream);
            break;
        case Command::BitwiseXorOp:
            ret = BitwiseXor(inputTensor1, inputTensor2, outputTensor, stream);
            break;
        case Command::BitwiseNotOp:
            ret = BitwiseNot(inputTensor1, outputTensor, stream);
            break;
        default:
            break;
    }

    if (ret != APP_ERR_OK) {
        LogError << "TensorOperations failed." ;
    }
    else {
        LogInfo << "TensorOperations success." ;
    }

    //结果转移到Host侧
    outputTensor.ToHost();

    //结果类型UINT8判定
    if (outputTensor.GetDataType() == TensorDType::UINT8) {
        LogInfo << "outputTensor type: UINT8" ;
    }

    //获取结果数值
    auto outputTensorData = outputTensor.GetData();

    //打印结果数值
    LogInfo << "result : " ;
    for (int i = 0; i < lens; ++i) {
        if (bit_op_flag) {
            printf("%d ", reinterpret_cast<uint8_t *>(outputTensorData)[i]); //位操作结果打印
        }
        else {
            printf("%.3f ", reinterpret_cast<float *>(outputTensorData)[i]);
        }
    }
    LogInfo << "\n" ;
    printf("\n");
    //打印结果维度
    LogInfo << "outputTensor shape:" ;
    for (auto s: outputTensor.GetShape()) {
        LogInfo << s << " " ;
    }
    LogInfo << "\n" ;
}

void Tensor1DCase(AscendStream &stream, Command command, bool bit_op_flag) {
    //一维
    std::vector<uint32_t> shape{4};
    std::vector<uint32_t> outshape{4};
    int lens = 4;
    TensorDType tensor_dtype = TensorDType::FLOAT32; //定义并张量类型
    if (bit_op_flag) {
        TensorDType tensor_dtype = TensorDType::UINT8; //位操作张量输入类型为UINT8
        uint8_t input1[4] = {0, 1, 2, 3}; //位操作 1维张量 输入示例1
        uint8_t input2[4] = {3, 2, 1, 0}; //位操作 1维张量 输入示例2
        TensorOperationsProcessor(input1, input2, shape, outshape, lens, command, stream, bit_op_flag, tensor_dtype);
    }
    else {
        float input1[4] = {0, -1, 2, -3}; //常规操作(除位操作以外) 1维张量 输入示例1
        float input2[4] = {3, -2, 1, 0}; //常规操作(除位操作以外) 1维张量 输入示例2
        TensorOperationsProcessor(input1, input2, shape, outshape, lens, command, stream, bit_op_flag, tensor_dtype);
    }
}

void Tensor2DCase(AscendStream &stream, Command command, bool bit_op_flag) {
    //二维
    std::vector<uint32_t> shape{2, 2};
    std::vector<uint32_t> outshape{2, 2};
    int lens = 4;
    TensorDType tensor_dtype = TensorDType::FLOAT32; //定义并张量类型
    if (bit_op_flag) {
        TensorDType tensor_dtype = TensorDType::UINT8; //位操作张量输入类型为UINT8
        uint8_t input1[2][2] = {{0, 1}, //位操作 2维张量 输入示例1
                                {2, 3}};
        uint8_t input2[2][2] = {{3, 2}, //位操作 2维张量 输入示例2
                                {1, 0}};
        TensorOperationsProcessor(input1, input2, shape, outshape, lens, command, stream, bit_op_flag, tensor_dtype);
    }
    else {
        float input1[2][2] = {{0, 1}, //常规操作(除位操作以外) 2维张量 输入示例1
                              {-2, 3}};
        float input2[2][2] = {{-3, 2},
                              {-1, 0}}; //常规操作(除位操作以外) 2维张量 输入示例2
        TensorOperationsProcessor(input1, input2, shape, outshape, lens, command, stream, bit_op_flag, tensor_dtype);
    }
}

void Tensor3DCase(AscendStream &stream, Command command, bool bit_op_flag) {
    //三维
    std::vector<uint32_t> shape{3, 2, 2};
    std::vector<uint32_t> outshape{3, 2, 2};
    int lens = 12;
    TensorDType tensor_dtype = TensorDType::FLOAT32; //定义并张量类型
    if (bit_op_flag) {
        TensorDType tensor_dtype = TensorDType::UINT8; //位操作张量输入类型为UINT8
        uint8_t input1[3][2][2] = {{{0, 1}, //位操作 3维张量 输入示例1
                                    {2, 3}},
                                   {{4, 5},
                                    {6, 7}},
                                   {{8, 9},
                                    {10, 11}}};
        uint8_t input2[3][2][2] = {{{11, 10}, //位操作 3维张量 输入示例2
                                    {9, 8}},
                                   {{7, 6},
                                    {5, 4}},
                                   {{3, 2},
                                    {1, 0}}};
        TensorOperationsProcessor(input1, input2, shape, outshape, lens, command, stream, bit_op_flag, tensor_dtype);
    }
    else {
        float input1[3][2][2] = {{{0, 1}, //常规操作(除位操作以外) 3维张量 输入示例1
                                  {-2, 3}},
                                 {{-4, 5},
                                  {-6, 7}},
                                 {{-8, 9},
                                  {-10, 11}}};
        float input2[3][2][2] = {{{-11, 10}, //常规操作(除位操作以外) 3维张量 输入示例2
                                  {-9, 8}},
                                 {{-7, 6},
                                  {-5, 4}},
                                 {{-3, 2},
                                  {-1, 0}}};
        TensorOperationsProcessor(input1, input2, shape, outshape, lens, command, stream, bit_op_flag, tensor_dtype);
    }
}

void Tensor4DCase(AscendStream &stream, Command command, bool bit_op_flag) {
    //四维
    std::vector<uint32_t> shape{1, 3, 2, 2};
    std::vector<uint32_t> outshape{1, 3, 2, 2};
    int lens = 12;
    TensorDType tensor_dtype = TensorDType::FLOAT32; //定义并张量类型
    if (bit_op_flag) {
        TensorDType tensor_dtype = TensorDType::UINT8; //位操作张量输入类型为UINT8
        uint8_t input1[1][3][2][2] = {{{{0, 1}, //位操作 4维张量 输入示例1
                                        {2, 3}},
                                       {{4, 5},
                                        {6, 7}},
                                       {{8, 9},
                                        {10, 11}}}};
        uint8_t input2[1][3][2][2] = {{{{11, 10}, //位操作 4维张量 输入示例2
                                        {9, 8}},
                                       {{7, 6},
                                        {5, 4}},
                                       {{3, 2},
                                        {1, 0}}}};
        TensorOperationsProcessor(input1, input2, shape, outshape, lens, command, stream, bit_op_flag, tensor_dtype);
    }
    else {
        float input1[1][3][2][2] = {{{{0, 1}, //常规操作(除位操作以外) 4维张量 输入示例1
                                      {-2, 3}},
                                     {{-4, 5},
                                      {-6, 7}},
                                     {{-8, 9},
                                      {-10, 11}}}};
        float input2[1][3][2][2] = {{{{-11, 10}, //常规操作(除位操作以外) 4维张量 输入示例2
                                      {-9, 8}},
                                     {{-7, 6},
                                      {-5, 4}},
                                     {{-3, 2},
                                      {-1, 0}}}};
        TensorOperationsProcessor(input1, input2, shape, outshape, lens, command, stream, bit_op_flag, tensor_dtype);
    }
}


int main() {
    APP_ERROR ret = MxInit();
    if (ret != APP_ERR_OK) {
        LogError << "MxVision failed to initialize, error code:" << ret;
        return ret;
    }

    AscendStream stream(0);
    stream.CreateAscendStream();

    std::string commands_string[] = {"Abs", "Sqr", "Sqrt", "Exp", "Log", "Rescale", "ThresholdBinary", "Threshold", "Clip", "Sort",
                                     "SortIdx", "ConvertTo", "Add", "ScaleAdd", "AddWeighted", "Subtract", "AbsDiff", "Multiply", "Divide", "Pow",
                                     "Min", "Max", "Compare", "BitwiseAnd", "BitwiseOr", "BitwiseXor", "BitwiseNot"};
    Command commands[] = {Command::AbsOp, Command::SqrOp, Command::SqrtOp, Command::ExpOp, Command::LogOp, Command::RescaleOp, Command::ThresholdBinaryOp, Command::ThresholdOp, Command::ClipOp, Command::SortOp, 
                          Command::SortIdxOp, Command::ConvertToOp, Command::AddOp, Command::ScaleAddOp, Command::AddWeightedOp, Command::SubtractOp, Command::AbsDiffOp, Command::MultiplyOp, Command::DivideOp, Command::PowOp, 
                          Command::MinOp, Command::MaxOp, Command::CompareOp, Command::BitwiseAndOp, Command::BitwiseOrOp, Command::BitwiseXorOp, Command::BitwiseNotOp};

    int min_tensor_shape;
    int max_tensor_shape;
    for (int case_id = 0; case_id < 27; ++case_id) { //遍历27种操作
        Command command = commands[case_id];
        std::string commands_string_single = commands_string[case_id];
        LogInfo << "\n ########## TensorOperations " << commands_string_single << " Start ########## \n ";
        printf("\n ########## TensorOperations %s Start ########## \n ", commands_string_single.c_str());
        if (command == Command::SortOp or command == Command::SortIdxOp) { //Sort 系列操作仅支持最多2维的张量
            min_tensor_shape = 2;
            max_tensor_shape = 2;
        }
        else {
            min_tensor_shape = 1;
            max_tensor_shape = 4;
        }
        for (int set_tensor_shape = min_tensor_shape; set_tensor_shape <= max_tensor_shape; ++set_tensor_shape) {
            bool bit_op_flag = false;
            if (command == Command::BitwiseAndOp or command == Command::BitwiseOrOp or command == Command::BitwiseXorOp or command == Command::BitwiseNotOp) { //位系列操作输入类型定义为uint8_t
                bit_op_flag = true;
            }

            switch (set_tensor_shape) { //选择输入张量维度
                case 1:
                    LogInfo << "Test1D Data" ;
                    Tensor1DCase(stream, command, bit_op_flag);
                    break;
                case 2:
                    LogInfo << "Test2D Data" ;
                    Tensor2DCase(stream, command, bit_op_flag);
                    break;
                case 3:
                    LogInfo << "Test3D Data" ;
                    Tensor3DCase(stream, command, bit_op_flag);
                    break;
                case 4:
                    LogInfo << "Test4D Data" ;
                    Tensor4DCase(stream, command, bit_op_flag);
                    break;
                default:
                    LogInfo << "Not running" ;
                    break;
            }
        }
    }
    stream.Synchronize();
    stream.DestroyAscendStream();

    MxDeInit();
}
