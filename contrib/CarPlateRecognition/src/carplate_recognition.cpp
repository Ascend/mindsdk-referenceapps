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

#include "carplate_recognition.h"
#include "carplate_recognition_postprocess.h"
#include "cvx_text.h"
#include "opencv2/opencv.hpp"
#include "MxBase/DeviceManager/DeviceManager.h"
#include "MxBase/Log/Log.h"
#include "MxBase/E2eInfer/ImageProcessor/ImageProcessor.h"
#include "MxBase/E2eInfer/DataType.h"
#include "MxBase/Tensor/TensorBase/TensorBase.h"
#include <iostream>
using namespace std;
using namespace MxBase;
// 以下3个参数用于YUV图像与BGR图像之间的宽高转换
namespace {
const uint32_t YUV_BYTE_NU = 3;  // 用于图像缩放
const uint32_t YUV_BYTE_DE = 2;  // 用于图像缩放
const uint32_t DIV_TWO = 2;
constexpr uint32_t DETECTION_WIDTH = 480;
constexpr uint32_t DETECTION_HEIGHT = 640;
constexpr uint32_t RECOGNITION_WIDTH = 272;
constexpr uint32_t RECOGNITION_HEIGHT = 72;
constexpr uint32_t PUT_TEXT_OFFSET = 5;
}  // namespace

/* @brief: 初始化各类资源
   @param：initParam：初始化参数
   @retval:APP_ERROR型变量
*/
APP_ERROR car_plate_recognition::init(const InitParam &initParam)
{

    deviceId_ = initParam.deviceId;  // 初始化设备ID

    // STEP1:资源初始化
    APP_ERROR ret = MxBase::DeviceManager::GetInstance()->InitDevices();
    if (ret != APP_ERR_OK) {
        LogError << "Init devices failed, ret=" << ret << ".";
        return ret;
    }
    // STEP2:文本信息初始化
    ret = MxBase::TensorContext::GetInstance()->SetContext(initParam.deviceId);
    if (ret != APP_ERR_OK) {
        LogError << "Set context failed, ret=" << ret << ".";
        return ret;
    }
    // STEP3:载入车牌检测模型，将模型的描述信息分别写入变量detection_modelDesc_
    detection_model_ = std::make_shared<MxBase::ModelInferenceProcessor>();
    ret = detection_model_->Init(initParam.DetecModelPath, detection_modelDesc_);
    if (ret != APP_ERR_OK) {
        LogError << "Detection ModelInferenceProcessor init failed, ret=" << ret << ".";
        return ret;
    }
    // STEP4:载入车牌识别模型，将模型的描述信息分别写入变量recognition_modelDesc_
    recognition_model_ = std::make_shared<MxBase::ModelInferenceProcessor>();
    ret = recognition_model_->Init(initParam.RecogModelPath, recognition_modelDesc_);
    if (ret != APP_ERR_OK) {
        LogError << "Recognition ModelInferenceProcessor init failed, ret=" << ret << ".";
        return ret;
    }
    // STEP5:初始化车牌检测模型的后处理对象
    detection_post_ = std::make_shared<SsdVggPostProcess>();
    std::map<std::string, std::string> SsdVggPostConfig;
    SsdVggPostConfig.insert(
        std::pair<std::string, std::string>("postProcessConfigPath", "./model/car_plate_detection/car_plate_detection.cfg"));
    SsdVggPostConfig.insert(std::pair<std::string, std::string>("labelPath", "./model/car_plate_detection/car_plate_detection.names"));
    ret = detection_post_->Init(SsdVggPostConfig);
    if (ret != APP_ERR_OK) {
        LogError << "retinaface_postprocess init failed, ret=" << ret << ".";
        return ret;
    }
    // STEP6:初始化车牌识别模型的后处理对象
    recognition_post_ = std::make_shared<CarPlateRecognitionPostProcess>();
    ret = recognition_post_->Init();
    if (ret != APP_ERR_OK) {
        LogError << "lpr_postprocess init failed, ret=" << ret << ".";
        return ret;
    }

    return APP_ERR_OK;
}

/* @brief: 释放各类资源
   @param：none
   @retval:APP_ERROR型变量
*/
APP_ERROR car_plate_recognition::deinit()
{
    detection_model_->DeInit();
    detection_post_->DeInit();
    recognition_model_->DeInit();
    recognition_post_->DeInit();
    MxBase::DeviceManager::GetInstance()->DestroyDevices();
    return APP_ERR_OK;
}

/* @brief: 读取图片
   @param：imgPath：图片的存放路径
   @param：tensor：存储读取到的图片tensor
   @param：decodedImage：存储读取到的图片
   @retval:APP_ERROR型变量
*/
APP_ERROR car_plate_recognition::readimage(
    const std::string &imgPath, MxBase::TensorBase &tensor, MxBase::Image &decodedImage)
{
    MxBase::ImageProcessor imageProcessor(0);
    APP_ERROR ret = imageProcessor.Decode(imgPath, decodedImage);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to decode the image.";
        return ret;
    }
    MxBase::Tensor decodeImageTensor = decodedImage.ConvertToTensor(false, false);
    MemoryData decodememorydata;
    decodememorydata.ptrData = decodeImageTensor.GetData();
    decodememorydata.size = decodeImageTensor.GetByteSize();
    decodememorydata.deviceId = decodeImageTensor.GetDeviceId();
    decodememorydata.type = decodeImageTensor.GetMemoryType();
    tensor = TensorBase(decodememorydata, true, decodeImageTensor.GetShape(), TensorDataType::TENSOR_DTYPE_UINT8);
    return ret;
}

/* @brief: 图像缩放，用在车牌检测推理前
   @param：decodedImage：原始的图像数据
   @param：outputTensor:缩放后的图像数据
   @retval:APP_ERROR型变量
*/
APP_ERROR car_plate_recognition::resize(const MxBase::Image &decodedImage, MxBase::TensorBase &outputTensor)
{
    MxBase::ImageProcessor imageProcessor(0);
    MxBase::Size size(DETECTION_WIDTH, DETECTION_HEIGHT);
    MxBase::Image outputImage;
    APP_ERROR ret = imageProcessor.Resize(decodedImage, size, outputImage, Interpolation::BILINEAR_SIMILAR_OPENCV);
    if (ret != APP_ERR_OK) {
        LogError << "Dvpp resize failed." << GetErrorInfo(ret);
        return ret;
    }
    MxBase::Tensor imageTensor = outputImage.ConvertToTensor(false, false);
    auto shape = imageTensor.GetShape();
    MemoryData memorydata;
    memorydata.ptrData = imageTensor.GetData();
    memorydata.size = imageTensor.GetByteSize();
    memorydata.deviceId = imageTensor.GetDeviceId();
    memorydata.type = imageTensor.GetMemoryType();
    outputTensor = TensorBase(memorydata, true, imageTensor.GetShape(), TensorDataType::TENSOR_DTYPE_UINT8);
    return ret;
}

/* @brief: 抠图缩放函数，用在车牌识别推理前
   @param：inputImage：原始的图像数据
   @param：outputTensors:抠图缩放后的图像数据
   @param：objInfos:目标框信息
   @retval:APP_ERROR型变量
*/
APP_ERROR car_plate_recognition::crop_resize(const MxBase::Image &inputImage,
    std::vector<MxBase::TensorBase> &outputTensors, std::vector<MxBase::ObjectInfo> objInfos)
{
    MxBase::ImageProcessor imageProcessor(0);
    std::vector<Rect> cropRectVec = {};
    MxBase::Size size = {RECOGNITION_WIDTH, RECOGNITION_HEIGHT};
    auto originWidth = inputImage.GetSize().width;
    auto originHeight = inputImage.GetSize().height;
    for (int i = 0; i < int(objInfos.size()); i++)  // 遍历检测出来的所有目标框信息(因为在一幅图中可能检测出多个车牌)
    {
        if (objInfos[i].x1 > originWidth || objInfos[i].y1 > originHeight) {
            continue;
        }
        cropRectVec.push_back({static_cast<uint32_t>(objInfos[i].x0),
            static_cast<uint32_t>(objInfos[i].y0),
            static_cast<uint32_t>(objInfos[i].x1),
            static_cast<uint32_t>(objInfos[i].y1)});
    }
    std::vector<Image> outputImageVec(cropRectVec.size());
    APP_ERROR ret = imageProcessor.CropResize(inputImage, cropRectVec, size, outputImageVec);
    if (ret != APP_ERR_OK) {
        LogError << "CropResize failed, ret=" << ret << ".";
    }
    for (auto &outputImage : outputImageVec) {
        MxBase::Tensor imageTensor = outputImage.ConvertToTensor(false, false);
        auto shape = imageTensor.GetShape();
        MemoryData memorydata;
        memorydata.ptrData = imageTensor.GetData();
        memorydata.size = imageTensor.GetByteSize();
        memorydata.deviceId = imageTensor.GetDeviceId();
        memorydata.type = imageTensor.GetMemoryType();
        outputTensors.push_back(
            TensorBase(memorydata, true, imageTensor.GetShape(), TensorDataType::TENSOR_DTYPE_UINT8));
    }
    return ret;
}

/* @brief: 进行车牌检测推理
   @param：inputs：输入数据
   @param：outputs:模型推理的输出数据
   @retval:APP_ERROR型变量
*/
APP_ERROR car_plate_recognition::detection_inference(
    const std::vector<MxBase::TensorBase> inputs, std::vector<MxBase::TensorBase> &outputs)
{

    // STEP1:根据模型的输出创建空的TensorBase变量
    auto dtypes = detection_model_->GetOutputDataType();
    for (size_t i = 0; i < detection_modelDesc_.outputTensors.size(); ++i) {
        std::vector<uint32_t> shape = {};
        for (size_t j = 0; j < detection_modelDesc_.outputTensors[i].tensorDims.size(); ++j) {
            shape.push_back((uint32_t)detection_modelDesc_.outputTensors[i].tensorDims[j]);
        }
        MxBase::TensorBase tensor(shape, dtypes[i], MxBase::MemoryData::MemoryType::MEMORY_DEVICE, deviceId_);
        APP_ERROR ret = MxBase::TensorBase::TensorBaseMalloc(tensor);
        if (ret != APP_ERR_OK) {
            LogError << "TensorBaseMalloc failed, ret=" << ret << ".";
            return ret;
        }
        outputs.push_back(tensor);
    }
    // STEP2:进行模型推理，结果存入outputs
    MxBase::DynamicInfo dynamicInfo = {};
    dynamicInfo.dynamicType = MxBase::DynamicType::STATIC_BATCH;  // 设置类型为静态batch
    APP_ERROR ret = detection_model_->ModelInference(inputs, outputs, dynamicInfo);
    if (ret != APP_ERR_OK) {
        LogError << "ModelInference failed, ret=" << ret << ".";
        return ret;
    }

    return APP_ERR_OK;
}

/* @brief: 车牌检测模型后处理
   @param：origin_image：原始图像数据
   @param：detect_outputs:模型的推理输出
   @param：objInfos:目标检测类任务的目标框信息
   @retval:APP_ERROR型变量
*/
APP_ERROR car_plate_recognition::detection_postprocess(const MxBase::Image &origin_image,
    std::vector<MxBase::TensorBase> detect_outputs, std::vector<MxBase::ObjectInfo> &objectInfos)
{

    APP_ERROR ret = detection_post_->Process(origin_image, detect_outputs, objectInfos);
    if (ret != APP_ERR_OK) {
        LogError << "retinaface_postprocess failed, ret=" << ret << ".";
        return ret;
    }
    // STEP3:后处理完成，将资源释放
    ret = detection_post_->DeInit();
    if (ret != APP_ERR_OK) {
        LogError << "retinaface_postprocess DeInit failed";
        return ret;
    }
    return APP_ERR_OK;
}

/* @brief: 进行车牌识别推理
   @param：inputs：输入数据
   @param：outputs:模型推理的输出数据
   @retval:APP_ERROR型变量
*/
APP_ERROR car_plate_recognition::recognition_inference(
    const std::vector<MxBase::TensorBase> inputs, std::vector<std::vector<MxBase::TensorBase>> &outputs)
{
    MxBase::DynamicInfo dynamicInfo = {};
    dynamicInfo.dynamicType = MxBase::DynamicType::STATIC_BATCH;  // 设置类型为静态batch

    std::vector<MxBase::TensorBase> k_inputs;
    std::vector<MxBase::TensorBase> k_outputs;
    auto dtypes = recognition_model_->GetOutputDataType();
    for (int k = 0; k < int(inputs.size()); k++) {
        // STEP1:根据模型的输出创建空的TensorBase变量
        for (size_t i = 0; i < recognition_modelDesc_.outputTensors.size(); ++i) {
            std::vector<uint32_t> shape = {};
            for (size_t j = 0; j < recognition_modelDesc_.outputTensors[i].tensorDims.size(); ++j) {
                shape.push_back((uint32_t)recognition_modelDesc_.outputTensors[i].tensorDims[j]);
            }
            MxBase::TensorBase tensor(shape, dtypes[i], MxBase::MemoryData::MemoryType::MEMORY_DEVICE, deviceId_);
            APP_ERROR ret = MxBase::TensorBase::TensorBaseMalloc(tensor);
            if (ret != APP_ERR_OK) {
                LogError << "TensorBaseMalloc failed, ret=" << ret << ".";
                return ret;
            }
            k_outputs.push_back(tensor);
        }
        // STEP2:进行车牌识别推理
        k_inputs.push_back(inputs[k]);
        APP_ERROR ret = recognition_model_->ModelInference(k_inputs, k_outputs, dynamicInfo);
        if (ret != APP_ERR_OK) {
            LogError << "ModelInference failed, ret=" << ret << ".";
            return ret;
        }
        outputs.push_back(k_outputs);
        k_inputs.clear();
        k_outputs.clear();
    }
    return APP_ERR_OK;
}

/* @brief: 车牌识别模型后处理
   @param：recog_outputs：模型推理的输出数据
   @param：objInfos:其成员className用于存放所识别出来的车牌字符
   @retval:APP_ERROR型变量
*/
APP_ERROR car_plate_recognition::recognition_postprocess(
    std::vector<std::vector<MxBase::TensorBase>> recog_outputs, std::vector<MxBase::ObjectInfo> &objectInfos)
{

    for (int i = 0; i < int(objectInfos.size()); i++) {
        // STEP1:进行模型后处理
        APP_ERROR ret = recognition_post_->Process(recog_outputs[i], objectInfos[i]);
        if (ret != APP_ERR_OK) {
            LogError << "lpr_postprocess failed, ret=" << ret << ".";
            return ret;
        }
        // STEP2:后处理完成，将资源释放
        ret = recognition_post_->DeInit();
        if (ret != APP_ERR_OK) {
            LogError << "lpr_postprocess DeInit failed";
            return ret;
        }
    }

    return APP_ERR_OK;
}

/* @brief: 车牌检测结果可视化
   @param：image：原始图像数据
   @param：objInfos：经模型后处理获得的目标框信息
   @retval:APP_ERROR型变量
*/
APP_ERROR car_plate_recognition::write_result(MxBase::Image &image, std::vector<MxBase::ObjectInfo> objectInfos)
{

    // STEP1:数据从DEVICE侧转到HOST侧（ReadImage的STEP2和Resize的STEP3将数据转到了DEVICE侧）
    APP_ERROR ret = image.ToHost();
    if (ret != APP_ERR_OK) {
        LogError << "ToHost faile";
        return ret;
    }
    // STEP2:初始化OpenCV图像信息矩阵,并进行颜色空间转换:YUV->BGR
    auto size = image.GetSize();
    cv::Mat imgYuv = cv::Mat(size.height * YUV_BYTE_NU / YUV_BYTE_DE, size.width, CV_8UC1, image.GetData().get());
    cv::Mat imgBgr = cv::Mat(size.height, size.width, CV_8UC3);
    cv::cvtColor(imgYuv, imgBgr, cv::COLOR_YUV2BGR_NV12);
    // STEP3:对识别结果进行画框
    int baseline = 0;                   // 使用cv::getTextSize所必须传入的参数，但实际上未用到
    cvx_text text("./simhei.ttf");      // 指定字体
    cv::Scalar size1{40, 0.5, 0.1, 0};  // (字体大小, 无效的, 字符间距, 无效的 }
    text.set_font(nullptr, &size1, nullptr, 0);
    for (int j = 0; j < int(objectInfos.size()); ++j) {
        const char *str1 = objectInfos[j].className.data();  // 将std::string转为const char*
        char *str = (char *)(str1);  // 将const char*转为char*（因为ToWchar只支持将char*转为wchar_t*）
        wchar_t *w_str = nullptr;
        text.to_wchar(str, w_str);
        // 写车牌号
        cv::Size text_size = cv::getTextSize(objectInfos[j].className, cv::FONT_HERSHEY_SIMPLEX, 1, 2, &baseline);
        text.put_text(imgBgr,
            w_str,
            cv::Point(objectInfos[j].x0 + (objectInfos[j].x1 - objectInfos[j].x0) / DIV_TWO -
                          text_size.width / DIV_TWO + PUT_TEXT_OFFSET,
                objectInfos[j].y0 - PUT_TEXT_OFFSET),
            cv::Scalar(0, 0, 255));
        // 画目标框
        cv::Rect rect(objectInfos[j].x0,
            objectInfos[j].y0,
            objectInfos[j].x1 - objectInfos[j].x0,
            objectInfos[j].y1 - objectInfos[j].y0);
        cv::rectangle(imgBgr, rect, cv::Scalar(0, 0, 255), 1, 8, 0);
        cout << "CarPlate " + to_string(j) << ": " << objectInfos[j].className << endl;
    }
    // STEP4:将结果保存为图片
    cv::imwrite("./result.jpg", imgBgr);

    return APP_ERR_OK;
}

/* @brief: 串联整体流程
   @param：imgPath：图片路径
   @retval:APP_ERROR型变量
*/
APP_ERROR car_plate_recognition::process(const std::string &imgPath)
{
    // STEP1:读取图片
    MxBase::TensorBase orign_Tensor;
    MxBase::Image orign_image;
    APP_ERROR ret = readimage(imgPath, orign_Tensor, orign_image);
    if (ret != APP_ERR_OK) {
        LogError << "readimage failed, ret=" << ret << ".";
        return ret;
    }
    // STEP2:图片缩放为640*480
    MxBase::TensorBase resize_Tensor;
    ret = resize(orign_image, resize_Tensor);
    if (ret != APP_ERR_OK) {
        LogError << "resize failed, ret=" << ret << ".";
        return ret;
    }
    // STEP3:车牌检测模型推理
    std::vector<MxBase::TensorBase> detect_inputs = {};
    std::vector<MxBase::TensorBase> detect_outputs = {};
    detect_inputs.push_back(resize_Tensor);
    ret = detection_inference(detect_inputs, detect_outputs);
    if (ret != APP_ERR_OK) {
        LogError << "detection_inference failed, ret=" << ret << ".";
        return ret;
    }
    // STEP4:车牌检测模型后处理
    std::vector<MxBase::ObjectInfo> objInfos;
    ret = detection_postprocess(orign_image, detect_outputs, objInfos);
    if (ret != APP_ERR_OK) {
        LogError << "detection_postprocess failed, ret=" << ret << ".";
        return ret;
    }
    if (objInfos.empty()) {
        LogError << "No carplate detected.";
        return APP_ERR_COMM_FAILURE;
    }
    // STEP5:将检测到的车牌抠图，并缩放至72*272
    std::vector<MxBase::TensorBase> cropresize_Tensors = {};
    ret = crop_resize(orign_image, cropresize_Tensors, objInfos);
    if (ret != APP_ERR_OK) {
        LogError << "crop_resize failed, ret=" << ret << ".";
        return ret;
    }
    // STEP6:车牌识别模型推理
    std::vector<MxBase::TensorBase> recog_inputs = {};
    std::vector<std::vector<MxBase::TensorBase>> recog_outputs = {};
    recog_inputs = cropresize_Tensors;
    ret = recognition_inference(recog_inputs, recog_outputs);
    if (ret != APP_ERR_OK) {
        LogError << "recognition_inference failed, ret=" << ret << ".";
        return ret;
    }
    if (recog_outputs.empty()) {
        LogError << "No carplate recognized.";
        return APP_ERR_COMM_FAILURE;
    }
    // STEP7:车牌识别模型后处理
    ret = recognition_postprocess(recog_outputs, objInfos);
    if (ret != APP_ERR_OK) {
        LogError << "recognition_postprocess failed, ret=" << ret << ".";
        return ret;
    }
    // STEP8:结果可视化
    write_result(orign_image, objInfos);

    return APP_ERR_OK;
}