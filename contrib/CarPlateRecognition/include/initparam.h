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

#ifndef Init_Param_H
#define Init_Param_H

// 结构体中定义了程序所需的所有参数
struct InitParam {
    
    // 系统参数
    bool checkTensor; // 判断是否检测输入至模型后处理的Tensor形状
    uint32_t deviceId; // 设备ID
    std::string DetecModelPath; // 车牌检测模型的存放路径
    std::string RecogModelPath; // 车牌识别模型的存放路径
};

#endif