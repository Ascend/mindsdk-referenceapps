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

const int TENSOR1D = 1;
const int TENSOR2D = 2;
const int TENSOR3D = 3;
const int TENSOR4D = 4;

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

template <template T>
APP_ERROR TensorOperationsProcessor (
    T *input1,
    T *input2,
    std::vector<uint32_t> shape,
    std::vector<uint32_t> outshape,
    int lens,
    Command command,
    AscendStream &stream,
    bool bit_op_flag,
    TensorDType tensor_dtype
)
{
    // 定义输入张量并转移到Device侧
    const uint32_t deviceID = 0;
    Tensor inputTensor1 (input1, shape, tensor_dtype);
    inputTensor1.ToDevice (deviceID);
    Tensor inputTensor2 (input2, shape, tensor_dtype);
    inputTensor2.ToDevice (deviceID);

    TensorDType output_tensor_dtype = tensor_dtype;
    if (command == Command::ConvertToOp) { // 与ConvertTo设置输出参数类型一致
        output_tensor_dtype = TensorDType::UINT8;
    }
    if (command == Command::SortIdxOp) { // SortIdx输出参数类型需为INT32
        output_tensor_dtype = TensorDType::INT32;
    }

    // 定义输出张量并申请内存
    Tensor outputTensor (outshape, output_tensor_dtype, deviceID);
    Tensor::TensorMalloc (outputTensor);

    // 定义部分操作额外参数的示例
    static float thresh = 2.0;
    static float minVal = 1.0;
    static float maxVal = 3.0;

    static float alpha = 1.1;
    static float beta  = 1.1;
    static float gamma = 1.1;

    static uint8_t axis    = 0;
    static bool descending = true;

    static float bias  = 1.1;
    static float scale = 2.2;

    // 迭代执行27种操作
    APP_ERROR ret;
    switch (command) {
        case Command::AbsOp:
            ret = Abs (inputTensor1, outputTensor, stream);
            break;
        case Command::SqrOp:
            ret = Sqr (inputTensor1, outputTensor, stream);
            break;
        case Command::SqrtOp:
            ret = Sqrt (inputTensor1, outputTensor, stream);
            break;
        case Command::ExpOp:
            ret = Exp (inputTensor1, outputTensor, stream);
            break;
        case Command::LogOp:
            ret = Log (inputTensor1, outputTensor, stream);
            break;
        case Command::RescaleOp:
            ret = Rescale (inputTensor1, outputTensor, scale, bias, stream);
            break;
        case Command::ThresholdBinaryOp:
            ret = ThresholdBinary (inputTensor1, outputTensor, thresh, maxVal, stream);
            break;
        case Command::ThresholdOp:
            ret = Threshold (inputTensor1, outputTensor, thresh, maxVal, ThresholdType::THRESHOLD_BINARY_INV, stream);
            break;
        case Command::ClipOp:
            ret = Clip (inputTensor1, outputTensor, minVal, maxVal, stream);
            break;
        case Command::SortOp:
            ret = Sort (inputTensor1, outputTensor, axis, descending, stream);
            break;
        case Command::SortIdxOp:
            ret = SortIdx (inputTensor1, outputTensor, axis, descending, stream);
            break;
        case Command::ConvertToOp:
            ret = ConvertTo (inputTensor1, outputTensor, TensorDType::UINT8, stream);
            break;
        case Command::AddOp:
            ret = Add (inputTensor1, inputTensor2, outputTensor, stream);
            break;
        case Command::ScaleAddOp:
            ret = ScaleAdd (inputTensor1, scale, inputTensor2, outputTensor, stream);
            break;
        case Command::AddWeightedOp:
            ret = AddWeighted (inputTensor1, alpha, inputTensor2, beta, gamma, outputTensor, stream);
            break;
        case Command::SubtractOp:
            ret = Subtract (inputTensor1, inputTensor2, outputTensor, stream);
            break;
        case Command::AbsDiffOp:
            ret = AbsDiff (inputTensor1, inputTensor2, outputTensor, stream);
            break;
        case Command::MultiplyOp:
            ret = Multiply (inputTensor1, inputTensor2, outputTensor, scale, stream);
            break;
        case Command::DivideOp:
            ret = Divide (inputTensor1, inputTensor2, outputTensor, scale, stream);
            break;
        case Command::PowOp:
            ret = Pow (inputTensor1, inputTensor2, outputTensor, stream);
            break;
        case Command::MinOp:
            ret = Min (inputTensor1, inputTensor2, outputTensor, stream);
            break;
        case Command::MaxOp:
            ret = Max (inputTensor1, inputTensor2, outputTensor, stream);
            break;
        case Command::CompareOp:
            ret = Compare (inputTensor1, inputTensor2, outputTensor, CmpOp::CMP_LE, stream);
            break;
        case Command::BitwiseAndOp:
            ret = BitwiseAnd (inputTensor1, inputTensor2, outputTensor);
            break;
        case Command::BitwiseOrOp:
            ret = BitwiseOr (inputTensor1, inputTensor2, outputTensor);
            break;
        case Command::BitwiseXorOp:
            ret = BitwiseXor (inputTensor1, inputTensor2, outputTensor);
            break;
        case Command::BitwiseNotOp:
            ret = BitwiseNot (inputTensor1, outputTensor);
            break;
        default:
            break;
    }

    if (ret != APP_ERR_OK) {
        LogError << "TensorOperations failed.";
    } else {
        LogInfo << "TensorOperations success.";
    }

    // 结果转移到Host侧
    outputTensor.ToHost();

    // ConvertTo操作结果类型UINT8判定
    if (command == Command::ConvertToOp && outputTensor.GetDataType() == TensorDType::UINT8) {
        LogInfo << "outputTensor type: UINT8";
        std::cout << "outputTensor type: UINT8";
        return ret;
    }

    // 获取结果数值
    auto outputTensorData = outputTensor.GetData();

    // 打印结果数值
    LogInfo << "result : ";
    for (int i = 0; i < lens; ++i) {
        if (bit_op_flag) {
            printf ("%d ", reinterpret_cast<uint8_t *> (outputTensorData)[i]); // 位操作结果打印
        } else if (command == Command::SortIdxOp) {
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
    return ret;
}

APP_ERROR Tensor1DCase (AscendStream &stream, Command command, bool bit_op_flag)
{
    // 一维
    uint demension_1dim = 4;
    std::vector<uint32_t> shape {demension_1dim};
    std::vector<uint32_t> outshape {demension_1dim};
    int lens                 = demension_1dim;
    TensorDType tensor_dtype = TensorDType::FLOAT32; // 定义并张量类型
    if (bit_op_flag) {
        TensorDType tensor_dtype       = TensorDType::UINT8; // 位操作张量输入类型为UINT8
        uint8_t input1[demension_1dim] = {0, 1, 2, 3};       // 位操作 1维张量 输入示例1
        uint8_t input2[demension_1dim] = {3, 2, 1, 0};       // 位操作 1维张量 输入示例2
        return TensorOperationsProcessor (
            input1, input2, shape, outshape, lens, command, stream, bit_op_flag, tensor_dtype
        );
    } else {
        float input1[demension_1dim] = {0, -1, 2, -3}; // 常规操作(除位操作以外) 1维张量 输入示例1
        float input2[demension_1dim] = {3, -2, 1, 0};  // 常规操作(除位操作以外) 1维张量 输入示例2
        return TensorOperationsProcessor (
            input1, input2, shape, outshape, lens, command, stream, bit_op_flag, tensor_dtype
        );
    }
}

APP_ERROR Tensor2DCase (AscendStream &stream, Command command, bool bit_op_flag)
{
    // 二维
    uint demension_1dim = 2;
    uint demension_2dim = 2;
    std::vector<uint32_t> shape {demension_1dim, demension_2dim};
    std::vector<uint32_t> outshape {demension_1dim, demension_2dim};
    int lens                 = demension_1dim * demension_2dim;
    TensorDType tensor_dtype = TensorDType::FLOAT32; // 定义并张量类型
    if (bit_op_flag) {
        TensorDType tensor_dtype                       = TensorDType::UINT8; // 位操作张量输入类型为UINT8
        uint8_t input1[demension_1dim][demension_2dim] = {
            {0, 1}, // 位操作 2维张量 输入示例1
            {2, 3}
        };
        uint8_t input2[demension_1dim][demension_2dim] = {
            {3, 2}, // 位操作 2维张量 输入示例2
            {1, 0}
        };
        return TensorOperationsProcessor (
            input1, input2, shape, outshape, lens, command, stream, bit_op_flag, tensor_dtype
        );
    } else {
        float input1[demension_1dim][demension_2dim] = {
            {0, 1}, // 常规操作(除位操作以外) 2维张量 输入示例1
            {-2, 3}
        };
        float input2[demension_1dim][demension_2dim] = {
            {-3, 2}, // 常规操作(除位操作以外) 2维张量 输入示例2
            {-1, 0}
        };
        return TensorOperationsProcessor (
            input1, input2, shape, outshape, lens, command, stream, bit_op_flag, tensor_dtype
        );
    }
}

APP_ERROR Tensor3DCase (AscendStream &stream, Command command, bool bit_op_flag)
{
    // 三维
    uint demension_1dim = 3;
    uint demension_2dim = 2;
    uint demension_3dim = 2;
    std::vector<uint32_t> shape {demension_1dim, demension_2dim, demension_3dim};
    std::vector<uint32_t> outshape {demension_1dim, demension_2dim, demension_3dim};
    int lens                 = demension_1dim * demension_2dim * demension_3dim;
    TensorDType tensor_dtype = TensorDType::FLOAT32; // 定义并张量类型
    if (bit_op_flag) {
        TensorDType tensor_dtype = TensorDType::UINT8; // 位操作张量输入类型为UINT8
        uint8_t input1[demension_1dim][demension_2dim][demension_3dim] = {
            {{0, 1}, // 位操作 3维张量 输入示例1
             {2, 3}},
            {{4, 5}, {6, 7}},
            {{8, 9}, {10, 11}}
        };
        uint8_t input2[demension_1dim][demension_2dim][demension_3dim] = {
            {{11, 10}, // 位操作 3维张量 输入示例2
             {9, 8}},
            {{7, 6}, {5, 4}},
            {{3, 2}, {1, 0}}
        };
        return TensorOperationsProcessor (
            input1, input2, shape, outshape, lens, command, stream, bit_op_flag, tensor_dtype
        );
    } else {
        float input1[demension_1dim][demension_2dim][demension_3dim] = {
            {{0, 1}, // 常规操作(除位操作以外) 3维张量 输入示例1
             {-2, 3}},
            {{-4, 5}, {-6, 7}},
            {{-8, 9}, {-10, 11}}
        };
        float input2[demension_1dim][demension_2dim][demension_3dim] = {
            {{-11, 10}, // 常规操作(除位操作以外) 3维张量 输入示例2
             {-9, 8}},
            {{-7, 6}, {-5, 4}},
            {{-3, 2}, {-1, 0}}
        };
        return TensorOperationsProcessor (
            input1, input2, shape, outshape, lens, command, stream, bit_op_flag, tensor_dtype
        );
    }
}

APP_ERROR Tensor4DCase (AscendStream &stream, Command command, bool bit_op_flag)
{
    // 四维
    uint demension_1dim = 1;
    uint demension_2dim = 3;
    uint demension_3dim = 2;
    uint demension_4dim = 2;
    std::vector<uint32_t> shape {demension_1dim, demension_2dim, demension_3dim, demension_4dim};
    std::vector<uint32_t> outshape {demension_1dim, demension_2dim, demension_3dim, demension_4dim};
    int lens                 = demension_1dim * demension_2dim * demension_3dim * demension_4dim;
    TensorDType tensor_dtype = TensorDType::FLOAT32; // 定义并张量类型
    if (bit_op_flag) {
        TensorDType tensor_dtype = TensorDType::UINT8; // 位操作张量输入类型为UINT8
        uint8_t input1[demension_1dim][demension_2dim][demension_3dim][demension_4dim] = {
            {{{0, 1}, // 位操作 4维张量 输入示例1
              {2, 3}},
             {{4, 5}, {6, 7}},
             {{8, 9}, {10, 11}}}
        };
        uint8_t input2[demension_1dim][demension_2dim][demension_3dim][demension_4dim] = {
            {{{11, 10}, // 位操作 4维张量 输入示例2
              {9, 8}},
             {{7, 6}, {5, 4}},
             {{3, 2}, {1, 0}}}
        };
        return TensorOperationsProcessor (
            input1, input2, shape, outshape, lens, command, stream, bit_op_flag, tensor_dtype
        );
    } else {
        float input1[demension_1dim][demension_2dim][demension_3dim][demension_4dim] = {
            {{{0, 1}, // 常规操作(除位操作以外) 4维张量 输入示例1
              {-2, 3}},
             {{-4, 5}, {-6, 7}},
             {{-8, 9}, {-10, 11}}}
        };
        float input2[demension_1dim][demension_2dim][demension_3dim][demension_4dim] = {
            {{{-11, 10}, // 常规操作(除位操作以外) 4维张量 输入示例2
              {-9, 8}},
             {{-7, 6}, {-5, 4}},
             {{-3, 2}, {-1, 0}}}
        };
        return TensorOperationsProcessor (
            input1, input2, shape, outshape, lens, command, stream, bit_op_flag, tensor_dtype
        );
    }
}

APP_ERROR main ()
{
    APP_ERROR ret = MxInit();
    if (ret != APP_ERR_OK) {
        LogError << "MxVision failed to initialize, error code:" << ret;
        return ret;
    }

    AscendStream stream (0);
    stream.CreateAscendStream();

    std::string commands_string[] = {
        "Abs",         "Sqr",      "Sqrt",       "Exp",       "Log",        "Rescale",   "ThresholdBinary",
        "Threshold",   "Clip",     "Sort",       "SortIdx",   "ConvertTo",  "Add",       "ScaleAdd",
        "AddWeighted", "Subtract", "AbsDiff",    "Multiply",  "Divide",     "Pow",       "Min",
        "Max",         "Compare",  "BitwiseAnd", "BitwiseOr", "BitwiseXor", "BitwiseNot"
    };
    Command commands[] = {
        Command::AbsOp,
        Command::SqrOp,
        Command::SqrtOp,
        Command::ExpOp,
        Command::LogOp,
        Command::RescaleOp,
        Command::ThresholdBinaryOp,
        Command::ThresholdOp,
        Command::ClipOp,
        Command::SortOp,
        Command::SortIdxOp,
        Command::ConvertToOp,
        Command::AddOp,
        Command::ScaleAddOp,
        Command::AddWeightedOp,
        Command::SubtractOp,
        Command::AbsDiffOp,
        Command::MultiplyOp,
        Command::DivideOp,
        Command::PowOp,
        Command::MinOp,
        Command::MaxOp,
        Command::CompareOp,
        Command::BitwiseAndOp,
        Command::BitwiseOrOp,
        Command::BitwiseXorOp,
        Command::BitwiseNotOp
    };

    int min_shape;
    int max_shape;
    static int tensor_op_total = 27;
    for (int case_id = 0; case_id < tensor_op_total; ++case_id) { // 遍历27种操作
        Command command                    = commands[case_id];
        std::string commands_string_single = commands_string[case_id];
        LogInfo << "\n ########## TensorOperations " << commands_string_single << " Start ########## \n ";
        printf ("\n ########## TensorOperations %s Start ########## \n ", commands_string_single.c_str());
        if (command == Command::SortOp || command == Command::SortIdxOp) { // Sort 系列操作仅支持最多2维的张量
            min_shape = 2;
            max_shape = 2;
        } else {
            min_shape = 1;
            max_shape = 4;
        }
        for (int set_tensor_shape = min_shape; set_tensor_shape <= max_shape; ++set_tensor_shape) {
            bool bit_op_flag = false;
            if (command == Command::BitwiseAndOp || command == Command::BitwiseOrOp ||
                command == Command::BitwiseXorOp ||
                command == Command::BitwiseNotOp) { // 位系列操作输入类型定义为uint8_t
                bit_op_flag = true;
            }

            switch (set_tensor_shape) { // 选择输入张量维度
                case TENSOR1D:
                    LogInfo << "Test1D Data";
                    ret = Tensor1DCase (stream, command, bit_op_flag);
                    break;
                case TENSOR2D:
                    LogInfo << "Test2D Data";
                    ret = Tensor2DCase (stream, command, bit_op_flag);
                    break;
                case TENSOR3D:
                    LogInfo << "Test3D Data";
                    ret = Tensor3DCase (stream, command, bit_op_flag);
                    break;
                case TENSOR4D:
                    LogInfo << "Test4D Data";
                    ret = Tensor4DCase (stream, command, bit_op_flag);
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
    stream.Synchronize();
    stream.DestroyAscendStream();
    MxDeInit();
}
