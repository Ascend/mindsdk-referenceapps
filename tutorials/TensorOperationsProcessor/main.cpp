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

namespace {

const int TENSOR1D = 1;
const int TENSOR2D = 2;
const int TENSOR3D = 3;
const int TENSOR4D = 4;

const uint demension1Dim1 = 4;

const uint demension2Dim1 = 2;
const uint demension2Dim2 = 2;

const uint demension3Dim1  = 3;
const uint demension3Dim2  = 2;
const uint demension3Dim3  = 2;

const uint demension4Dim1 = 1;
const uint demension4Dim2 = 3;
const uint demension4Dim3 = 2;
const uint demension4Dim4 = 2;

const int shapeDim1     = 1;
const int shapeDim2     = 2;
const int shapeDim4     = 4;
const int tensorOpTotal = 27;

uint8_t g_input1ForD1Unit8[demension1Dim1]  = {0, 1, 2, 3}; // 位操作 1维张量 输入示例1
uint8_t g_input2ForD1Unit8[demension1Dim1]  = {3, 2, 1, 0}; // 位操作 1维张量 输入示例2

float g_input1ForD1[demension1Dim1] = {0, -1, 2, -3}; // 常规操作(除位操作以外) 1维张量 输入示例1
float g_input2ForD1[demension1Dim1] = {3, -2, 1, 0};  // 常规操作(除位操作以外) 1维张量 输入示例2

uint8_t g_input1ForD2Unit8[demension2Dim1][demension2Dim2] = {
    {0, 1}, // 位操作 2维张量 输入示例1
    {2, 3}
};
uint8_t g_input2ForD2Unit8[demension2Dim1][demension2Dim2] = {
    {3, 2}, // 位操作 2维张量 输入示例2
    {1, 0}
};

float g_input1ForD2[demension2Dim1][demension2Dim2] = {
    {0, 1}, // 常规操作(除位操作以外) 2维张量 输入示例1
    {-2, 3}
};
float g_input2ForD2[demension2Dim1][demension2Dim2] = {
    {-3, 2}, // 常规操作(除位操作以外) 2维张量 输入示例2
    {-1, 0}
};

uint8_t g_input1ForD3Unit8[demension3Dim1][demension3Dim2][demension3Dim3] = {
    {{0, 1}, // 位操作 3维张量 输入示例1
     {2, 3}},
    {{4, 5}, {6, 7}},
    {{8, 9}, {10, 11}}
};
uint8_t g_input2ForD3Unit8[demension3Dim1][demension3Dim2][demension3Dim3] = {
    {{11, 10}, // 位操作 3维张量 输入示例2
     {9, 8}},
    {{7, 6}, {5, 4}},
    {{3, 2}, {1, 0}}
};

float g_input1ForD3[demension3Dim1][demension3Dim2][demension3Dim3] = {
    {{0, 1}, // 常规操作(除位操作以外) 3维张量 输入示例1
     {-2, 3}},
    {{-4, 5}, {-6, 7}},
    {{-8, 9}, {-10, 11}}
};
float g_input2ForD3[demension3Dim1][demension3Dim2][demension3Dim3] = {
    {{-11, 10}, // 常规操作(除位操作以外) 3维张量 输入示例2
     {-9, 8}},
    {{-7, 6}, {-5, 4}},
    {{-3, 2}, {-1, 0}}
};

uint8_t g_input1For4DUnit8[demension4Dim1][demension4Dim2][demension4Dim3][demension4Dim4] = {
    {{{0, 1}, // 位操作 4维张量 输入示例1
      {2, 3}},
     {{4, 5}, {6, 7}},
     {{8, 9}, {10, 11}}}
};
uint8_t g_input2For4DUnit8[demension4Dim1][demension4Dim2][demension4Dim3][demension4Dim4] = {
    {{{11, 10}, // 位操作 4维张量 输入示例2
      {9, 8}},
     {{7, 6}, {5, 4}},
     {{3, 2}, {1, 0}}}
};

float g_input1For4D[demension4Dim1][demension4Dim2][demension4Dim3][demension4Dim4] = {
    {{{0, 1}, // 常规操作(除位操作以外) 4维张量 输入示例1
      {-2, 3}},
     {{-4, 5}, {-6, 7}},
     {{-8, 9}, {-10, 11}}}
};
float g_input2For4D[demension4Dim1][demension4Dim2][demension4Dim3][demension4Dim4] = {
    {{{-11, 10}, // 常规操作(除位操作以外) 4维张量 输入示例2
      {-9, 8}},
     {{-7, 6}, {-5, 4}},
     {{-3, 2}, {-1, 0}}}
};

const uint32_t deviceID = 0;

// 定义部分操作额外参数的示例
const float thresh  = 2.0;
const float minVal  = 1.0;
const float maxVal  = 3.0;

const float alpha  = 1.1;
const float beta   = 1.1;
const float gamma_value  = 1.1;

const uint8_t axis     = 0;
const bool descending  = true;

const float bias   = 1.1;
const float scale  = 2.2;

const std::string commands_string[] = {
    "Abs",    "Sqr",     "Sqrt",      "Exp", "Log",      "Rescale",     "ThresholdBinary", "Threshold",  "Clip",
    "Sort",   "SortIdx", "ConvertTo", "Add", "ScaleAdd", "AddWeighted", "Subtract",        "AbsDiff",    "Multiply",
    "Divide", "Pow",     "Min",       "Max", "Compare",  "BitwiseAnd",  "BitwiseOr",       "BitwiseXor", "BitwiseNot"
};

enum class Command {
    ABS_OP,
    SQR_OP,
    SQRT_OP,
    EXP_OP,
    LOG_OP,
    RESCALE_OP,
    THRESHOLD_BINARY_OP,
    THRESHOLD_OP,
    CLIP_OP,
    SORT_OP,
    SORT_IDX_OP,
    CONVERT_TO_OP,
    ADD_OP,
    SCALE_ADD_OP,
    ADD_WEIGHTED_OP,
    SUBTRACT_OP,
    ABS_DIFF_OP,
    MULTIPLY_OP,
    DIVIDE_OP,
    POW_OP,
    MIN_OP,
    MAX_OP,
    COMPARE_OP,
    BITWISE_AND_OP,
    BITWISE_OR_OP,
    BITWISE_XOR_OP,
    BITWISE_NOT_OP
};

Command commands[] = {
    Command::ABS_OP,
    Command::SQR_OP,
    Command::SQRT_OP,
    Command::EXP_OP,
    Command::LOG_OP,
    Command::RESCALE_OP,
    Command::THRESHOLD_BINARY_OP,
    Command::THRESHOLD_OP,
    Command::CLIP_OP,
    Command::SORT_OP,
    Command::SORT_IDX_OP,
    Command::CONVERT_TO_OP,
    Command::ADD_OP,
    Command::SCALE_ADD_OP,
    Command::ADD_WEIGHTED_OP,
    Command::SUBTRACT_OP,
    Command::ABS_DIFF_OP,
    Command::MULTIPLY_OP,
    Command::DIVIDE_OP,
    Command::POW_OP,
    Command::MIN_OP,
    Command::MAX_OP,
    Command::COMPARE_OP,
    Command::BITWISE_AND_OP,
    Command::BITWISE_OR_OP,
    Command::BITWISE_XOR_OP,
    Command::BITWISE_NOT_OP
};
}

void tensor_printf (Tensor outputTensor, int lens, Command command, bool bitOpFlag)
{
    // ConvertTo操作结果类型UINT8判定
    if (command == Command::CONVERT_TO_OP && outputTensor.GetDataType() == TensorDType::UINT8) {
        LogInfo << "outputTensor type: UINT8";
        std::cout << "outputTensor type: UINT8 \n";
    }

    // 获取结果数值
    auto outputTensorData = outputTensor.GetData();

    // 打印结果数值
    LogInfo << "result : ";
    for (int i = 0; i < lens; ++i) {
        if (bitOpFlag) {
            printf ("%d ", reinterpret_cast<uint8_t *> (outputTensorData)[i]); // 位操作结果打印
        } else if (command == Command::SORT_IDX_OP) {
            printf ("%d ", reinterpret_cast<int *> (outputTensorData)[i]); // 排序返回索引操作结果打印
        } else {
            printf ("%.3f ", reinterpret_cast<float *> (outputTensorData)[i]);
        }
    }
    LogInfo << "\n";
    printf ("\n");
    // 打印结果维度
    LogInfo << "outputTensor shape:";
    for (auto s : outputTensor.GetShape()) {
        LogInfo << s << " ";
    }
    LogInfo << "\n";
}

template <typename T>
APP_ERROR tensorOperationsProcessor (
    T *input1,
    T *input2,
    std::vector<uint32_t> shape,
    std::vector<uint32_t> outshape,
    int lens,
    Command command,
    AscendStream &stream,
    bool bitOpFlag,
    TensorDType tensor_dtype
)
{
    // 定义输入张量并转移到Device侧
    Tensor inputTensor1 (input1, shape, tensor_dtype);
    inputTensor1.ToDevice (deviceID);
    Tensor inputTensor2 (input2, shape, tensor_dtype);
    inputTensor2.ToDevice (deviceID);

    TensorDType output_tensor_dtype = tensor_dtype;
    if (command == Command::CONVERT_TO_OP) { // 与ConvertTo设置输出参数类型一致
        output_tensor_dtype = TensorDType::UINT8;
    }
    if (command == Command::SORT_IDX_OP) { // SortIdx输出参数类型需为INT32
        output_tensor_dtype = TensorDType::INT32;
    }

    // 定义输出张量并申请内存
    Tensor outputTensor (outshape, output_tensor_dtype, deviceID);
    Tensor::TensorMalloc (outputTensor);

    // 迭代执行27种操作
    APP_ERROR ret = APP_ERR_OK;
    switch (command) {
        case Command::ABS_OP:
            ret = Abs (inputTensor1, outputTensor, stream);
            break;
        case Command::SQR_OP:
            ret = Sqr (inputTensor1, outputTensor, stream);
            break;
        case Command::SQRT_OP:
            ret = Sqrt (inputTensor1, outputTensor, stream);
            break;
        case Command::EXP_OP:
            ret = Exp (inputTensor1, outputTensor, stream);
            break;
        case Command::LOG_OP:
            ret = Log (inputTensor1, outputTensor, stream);
            break;
        case Command::RESCALE_OP:
            ret = Rescale (inputTensor1, outputTensor, scale, bias, stream);
            break;
        case Command::THRESHOLD_BINARY_OP:
            ret = ThresholdBinary (inputTensor1, outputTensor, thresh, maxVal, stream);
            break;
        case Command::THRESHOLD_OP:
            ret = Threshold (inputTensor1, outputTensor, thresh, maxVal, ThresholdType::THRESHOLD_BINARY_INV, stream);
            break;
        case Command::CLIP_OP:
            ret = Clip (inputTensor1, outputTensor, minVal, maxVal, stream);
            break;
        case Command::SORT_OP:
            ret = Sort (inputTensor1, outputTensor, axis, descending, stream);
            break;
        case Command::SORT_IDX_OP:
            ret = SortIdx (inputTensor1, outputTensor, axis, descending, stream);
            break;
        case Command::CONVERT_TO_OP:
            ret = ConvertTo (inputTensor1, outputTensor, TensorDType::UINT8, stream);
            break;
        case Command::ADD_OP:
            ret = Add (inputTensor1, inputTensor2, outputTensor, stream);
            break;
        case Command::SCALE_ADD_OP:
            ret = ScaleAdd (inputTensor1, scale, inputTensor2, outputTensor, stream);
            break;
        case Command::ADD_WEIGHTED_OP:
            ret = AddWeighted (inputTensor1, alpha, inputTensor2, beta, gamma_value, outputTensor, stream);
            break;
        case Command::SUBTRACT_OP:
            ret = Subtract (inputTensor1, inputTensor2, outputTensor, stream);
            break;
        case Command::ABS_DIFF_OP:
            ret = AbsDiff (inputTensor1, inputTensor2, outputTensor, stream);
            break;
        case Command::MULTIPLY_OP:
            ret = Multiply (inputTensor1, inputTensor2, outputTensor, scale, stream);
            break;
        case Command::DIVIDE_OP:
            ret = Divide (inputTensor1, inputTensor2, outputTensor, scale, stream);
            break;
        case Command::POW_OP:
            ret = Pow (inputTensor1, inputTensor2, outputTensor, stream);
            break;
        case Command::MIN_OP:
            ret = Min (inputTensor1, inputTensor2, outputTensor, stream);
            break;
        case Command::MAX_OP:
            ret = Max (inputTensor1, inputTensor2, outputTensor, stream);
            break;
        case Command::COMPARE_OP:
            ret = Compare (inputTensor1, inputTensor2, outputTensor, CmpOp::CMP_LE, stream);
            break;
        case Command::BITWISE_AND_OP:
            ret = BitwiseAnd (inputTensor1, inputTensor2, outputTensor, stream);
            break;
        case Command::BITWISE_OR_OP:
            ret = BitwiseOr (inputTensor1, inputTensor2, outputTensor, stream);
            break;
        case Command::BITWISE_XOR_OP:
            ret = BitwiseXor (inputTensor1, inputTensor2, outputTensor, stream);
            break;
        case Command::BITWISE_NOT_OP:
            ret = BitwiseNot (inputTensor1, outputTensor, stream);
            break;
        default:
            break;
    }
    stream.Synchronize(); // 进行流同步以等待计算结果
    if (ret != APP_ERR_OK) {
        LogError << "TensorOperations failed.";
    } else {
        LogInfo << "TensorOperations success.";
    }

    // 结果转移到Host侧
    outputTensor.ToHost();
    tensor_printf(outputTensor, lens, command, bitOpFlag);

    return ret;
}

APP_ERROR tensor1DCase(AscendStream &stream, Command command, bool bitOpFlag)
{
    // 一维
    std::vector<uint32_t> shape {demension1Dim1};
    std::vector<uint32_t> outshape {demension1Dim1};
    int lens                 = demension1Dim1;
    TensorDType tensor_dtype = TensorDType::FLOAT32; // 定义并张量类型
    if (bitOpFlag) {
        TensorDType tensor_dtype       = TensorDType::UINT8; // 位操作张量输入类型为UINT8
        return tensorOperationsProcessor (
            g_input1ForD1Unit8, g_input2ForD1Unit8, shape, outshape, lens, command, stream, bitOpFlag, tensor_dtype
        );
    } else {

        return tensorOperationsProcessor (
            g_input1ForD1, g_input2ForD1, shape, outshape, lens, command, stream, bitOpFlag, tensor_dtype
        );
    }
}

APP_ERROR tensor2DCase(AscendStream &stream, Command command, bool bitOpFlag)
{
    // 二维
    std::vector<uint32_t> shape {demension2Dim1, demension2Dim2};
    std::vector<uint32_t> outshape {demension2Dim1, demension2Dim2};
    int lens                 = demension2Dim1 * demension2Dim2;
    TensorDType tensor_dtype = TensorDType::FLOAT32; // 定义并张量类型
    if (bitOpFlag) {
        TensorDType tensor_dtype                       = TensorDType::UINT8; // 位操作张量输入类型为UINT8
        return tensorOperationsProcessor (
            g_input1ForD2Unit8, g_input2ForD2Unit8, shape, outshape, lens, command, stream, bitOpFlag, tensor_dtype
        );
    } else {
        return tensorOperationsProcessor (
            g_input1ForD2, g_input2ForD2, shape, outshape, lens, command, stream, bitOpFlag, tensor_dtype
        );
    }
}

APP_ERROR tensor3DCase(AscendStream &stream, Command command, bool bitOpFlag)
{
    // 三维
    std::vector<uint32_t> shape {demension3Dim1, demension3Dim2, demension3Dim3};
    std::vector<uint32_t> outshape {demension3Dim1, demension3Dim2, demension3Dim3};
    int lens                 = demension3Dim1 * demension3Dim2 * demension3Dim3;
    TensorDType tensor_dtype = TensorDType::FLOAT32; // 定义并张量类型
    if (bitOpFlag) {
        TensorDType tensor_dtype = TensorDType::UINT8; // 位操作张量输入类型为UINT8
        return tensorOperationsProcessor (
            g_input1ForD3Unit8, g_input2ForD3Unit8, shape, outshape, lens, command, stream, bitOpFlag, tensor_dtype
        );
    } else {
        return tensorOperationsProcessor (
            g_input1ForD3, g_input2ForD3, shape, outshape, lens, command, stream, bitOpFlag, tensor_dtype
        );
    }
}

APP_ERROR tensor4DCase(AscendStream &stream, Command command, bool bitOpFlag)
{
    // 四维

    std::vector<uint32_t> shape {demension4Dim1, demension4Dim2, demension4Dim3, demension4Dim4};
    std::vector<uint32_t> outshape {demension4Dim1, demension4Dim2, demension4Dim3, demension4Dim4};
    int lens                 = demension4Dim1 * demension4Dim2 * demension4Dim3 * demension4Dim4;
    TensorDType tensor_dtype = TensorDType::FLOAT32; // 定义并张量类型
    if (bitOpFlag) {
        TensorDType tensor_dtype = TensorDType::UINT8; // 位操作张量输入类型为UINT8
        return tensorOperationsProcessor (
            g_input1For4DUnit8, g_input2For4DUnit8, shape, outshape, lens, command, stream, bitOpFlag, tensor_dtype
        );
    } else {
        return tensorOperationsProcessor (
            g_input1For4D, g_input2For4D, shape, outshape, lens, command, stream, bitOpFlag, tensor_dtype);
    }
}

APP_ERROR main()
{
    APP_ERROR ret = MxInit();
    if (ret != APP_ERR_OK) {
        LogError << "MxVision failed to initialize, error code:" << ret;
        return ret;
    }
    AscendStream stream (0);
    stream.CreateAscendStream();
    int minShape;
    int maxShape;
    for (int caseId = 0; caseId < tensorOpTotal; ++caseId) { // 遍历27种操作
        Command command                    = commands[caseId];
        std::string commandsStringSingle = commands_string[caseId];
        LogInfo << "\n ########## TensorOperations " << commandsStringSingle << " Start ########## \n ";
        printf ("\n ########## TensorOperations %s Start ########## \n ", commandsStringSingle.c_str());
        if (command == Command::SORT_OP || command == Command::SORT_IDX_OP) { // Sort 系列操作仅支持最多2维的张量
            minShape = shapeDim2;
            maxShape = shapeDim2;
        } else {
            minShape = shapeDim1;
            maxShape = shapeDim4;
        }
        for (int setTensorShape = minShape; setTensorShape <= maxShape; ++setTensorShape) {
            bool bitOpFlag = false;
            if (command == Command::BITWISE_AND_OP || command == Command::BITWISE_OR_OP ||
                command == Command::BITWISE_XOR_OP ||
                command == Command::BITWISE_NOT_OP) { // 位系列操作输入类型定义为uint8_t
                bitOpFlag = true;
            }
            switch (setTensorShape) { // 选择输入张量维度
                case TENSOR1D:
                    LogInfo << "Test1D Data";
                    ret = tensor1DCase (stream, command, bitOpFlag);
                    break;
                case TENSOR2D:
                    LogInfo << "Test2D Data";
                    ret = tensor2DCase (stream, command, bitOpFlag);
                    break;
                case TENSOR3D:
                    LogInfo << "Test3D Data";
                    ret = tensor3DCase (stream, command, bitOpFlag);
                    break;
                case TENSOR4D:
                    LogInfo << "Test4D Data";
                    ret = tensor4DCase (stream, command, bitOpFlag);
                    break;
                default:
                    LogInfo << "Not running";
                    break;
            }
            if (ret != APP_ERR_OK) {
                LogError << "MxVision failed to initialize, error code:" << ret;
                return ret;
            }
        }
    }
    stream.DestroyAscendStream();
    MxDeInit();
}
