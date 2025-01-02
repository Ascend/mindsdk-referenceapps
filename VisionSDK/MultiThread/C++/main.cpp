/*
* Copyright(C) 2020. Huawei Technologies Co.,Ltd. All rights reserved.
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
*     http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
*/

#include <dirent.h>
#include <cstring>
#include <unistd.h>
#include <thread>
#include <fstream>
#include <opencv4/opencv2/opencv.hpp>
#include <opencv4/opencv2/imgproc.hpp>
#include "MxBase/Log/Log.h"
#include "MxStream/StreamManager/MxStreamManager.h"
#include "MxBase/DeviceManager/DeviceManager.h"

using namespace MxTools;
using namespace MxStream;
using namespace cv;

namespace {
    const int TIME_OUT = 15000;
    const int INPUT_UINT8 = 1;
}

std::string ReadFileContent(const std::string filePath)
{
    std::ifstream file(filePath, std::ios::binary);
    if (!file) {
        LogError << "Invalid file. filePath(" << filePath << ")";
        return "";
    }

    file.seekg(0, std::ifstream::end);
    uint32_t fileSize = file.tellg();
    file.seekg(0);
    std::vector<char> buffer = {};
    buffer.resize(fileSize);
    file.read(buffer.data(), fileSize);
    file.close();

    return std::string(buffer.data(), fileSize);
}

APP_ERROR streamCallback(MxStreamManager& mxStreamManager, std::string streamName, std::string picturePath)
{
    MxstDataInput mxstDataInput = {};
    std::string catImage = ReadFileContent("./test.jpg");
    mxstDataInput.dataPtr = (uint32_t *) catImage.c_str();
    mxstDataInput.dataSize = catImage.size();
    APP_ERROR ret = mxStreamManager.SendData(streamName, 0, mxstDataInput);
    if (ret != APP_ERR_OK) {
        LogError << "Failed to send data to stream";
    }
    MxstDataOutput *outputPtr = mxStreamManager.GetResult(streamName, 0, TIME_OUT);
    if (outputPtr == nullptr || outputPtr->errorCode != 0) {
        LogError << "Failed to get data to stream";
    }
    std::string dataStr = std::string((char *)outputPtr->dataPtr, outputPtr->dataSize);
    std::cout << "[" << streamName << "] GetResult: " << dataStr << std::endl;
    return APP_ERR_OK;
}

APP_ERROR TestMultiThread(std::string pipelinePath)
{
    LogInfo << "********case TestMultiThread********" << std::endl;
    MxStream::MxStreamManager mxStreamManager;
    APP_ERROR ret = mxStreamManager.InitManager();
    if (ret != APP_ERR_OK) {
        LogError << "Failed to init streammanager";
        return ret;
    }
    ret = mxStreamManager.CreateMultipleStreamsFromFile(pipelinePath);
    if (ret != APP_ERR_OK) {
        LogError << "Pipeline is no exit";
        return ret;
    }

    int threadCount = 3;
    std::thread threadSendData[threadCount];
    std::string streamName[threadCount];
    std::string picturePath = "../picture";
    for (int i = 0; i < threadCount; ++i) {
        streamName[i] = "detection" + std::to_string(i);
        threadSendData[i] = std::thread(streamCallback, std::ref(mxStreamManager), streamName[i], picturePath);
    }
    for (int j = 0; j < threadCount; ++j) {
        threadSendData[j].join();
    }

    ret = mxStreamManager.DestroyAllStreams();
    if (ret != APP_ERR_OK) {
        LogError << "Failed to destroy stream";
    }
    return APP_ERR_OK;
}

int main(int argc, char *argv[])
{
    struct timeval inferStartTime = { 0 };
    struct timeval inferEndTime = { 0 };
    gettimeofday(&inferStartTime, nullptr);
    APP_ERROR ret = TestMultiThread("EasyStream.pipeline");
    if (ret == APP_ERR_OK) {
        float sec2ms = 1000.0;
        gettimeofday(&inferEndTime, nullptr);
        double inferCostTime = sec2ms * (inferEndTime.tv_sec - inferStartTime.tv_sec) +
                               (inferEndTime.tv_usec - inferStartTime.tv_usec) / sec2ms;
        LogInfo << "Total time: " << inferCostTime / sec2ms;
    }
    return 0;
}
