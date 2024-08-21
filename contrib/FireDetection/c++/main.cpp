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

#include <ctime>
#include <cstdio>
#include <csignal>
#include <iostream>
#include <map>
#include <fstream>
#include <memory>
#include <queue>
#include <thread>
#include <algorithm>
#include "unistd.h"
#include "acl/acl.h"
#include "acl/acl_rt.h"
#include "MxBase/DeviceManager/DeviceManager.h"
#include "MxBase/DvppWrapper/DvppWrapper.h"
#include "MxBase/MemoryHelper/MemoryHelper.h"
#include "boost/filesystem.hpp"
#include "MxBase/E2eInfer/VideoDecoder/VideoDecoder.h"
#include "MxBase/E2eInfer/VideoEncoder/VideoEncoder.h"
#include "MxBase/MxBase.h"
#include "MxBase/Maths/FastMath.h"
#include "MxBase/postprocess/include/ObjectPostProcessors/Yolov3PostProcess.h"
#include "MxBase/E2eInfer/DataType.h"
#include "VideoDecoder/VideoDecoder.h"
#include "ConfigParser/ConfigParser.h"
#include "BlockingQueue/BlockingQueue.h"
#include "FrameAnalyzer/rameAnalyzer.h"

extern "C" {
#include <libavformat/avformat.h>
}

static bool g_sendSignial = false;
static bool g_readVideoEnded = false;;
const int QUEUE_SIZE = 1000;
const int TIME_OUT = 3000;
const int FRAME_WAIT_TIME = 10;
static std::string g_videoSavedPath = "";
const std::string CONFIG_FILE_NAME = "./config/setup.config";
const int SIGNAL_CHECK_TIMESTEP = 10000;
const uint32_t REF_MIN_VDEC_LENGTH = 128;
const uint32_t REF_MAX_VDEC_LENGTH = 4096;
const int DEFAULT_SRC_RATE = 60;
const int DEFAULT_MAX_BIT_RATE = 6000;
std::shared_ptr<BlockingQueue<std::shared_ptr<void>>> inputQueue = std::make_shared<BlockingQueue<std::shared_ptr<void>>>(QUEUE_SIZE);
std::shared_ptr<BlockingQueue<std::shared_ptr<void>>> outputQueue = std::make_shared<BlockingQueue<std::shared_ptr<void>>>(QUEUE_SIZE);

using namespace std;
using namespace MxBase;
using namespace ascendVideoDecoder;

static void SigHandler(int signal)
{
    if (signal == SIGINT) {
        g_sendSignial = true;
    }
}

struct FrameInfo {
    int height;
    int width;
    std::string videoSavedPath;
};

AVFormatContext* CreateFormatContext(const std::string &filePath)
{
    LogInfo << "Start to CreateFormatContext!";
    // create message for stream pull
    AVFormatContext *formatContext = nullptr;
    AVDictionary *options = nullptr;
    int ret = avformat_open_input(&formatContext, filePath.c_str(), nullptr, nullptr);
    if (options != nullptr) {
        av_dict_free(&options);
    }
    if (ret != 0) {
        LogError << "Couldn't open input stream " << filePath.c_str() << " ret=" << ret;
        return nullptr;
    }
    ret = avformat_find_stream_info(formatContext, nullptr);
    if (ret != 0) {
        LogError << "Couldn't find stream information";
        return nullptr;
    }
    return formatContext;
}

void GetFrame(AVPacket& pkt, FrameImage& frameImage, AVFormatContext* pFormatCtx, bool &isEnded)
{
    av_init_packet(&pkt);
    int ret = av_read_frame(pFormatCtx, &pkt);
    if (ret != 0) {
        LogInfo << "[StreamPuller] Channel read frame failed, continue!";
        if (ret == AVERROR_EOF) {
            LogInfo << "[StreamPuller] Channel streamPuller is EOF, over!";
            isEnded = true;
        }
        return;
    } else {
        if (pkt.size <= 0) {
            LogError << "Invalid pkt.size: " << pkt.size;
            return;
        }
        // sent to the device
        const auto hostDeleter = [](void *dataPtr) -> void {aclrtFreeHost(dataPtr);};
        MemoryData data(pkt.size, MemoryData::MEMORY_HOST);
        MemoryData src((void *)(pkt.data), pkt.size, MemoryData::MEMORY_HOST_MALLOC);
        APP_ERROR ret = MemoryHelper::MxbsMallocAndCopy(data, src);
        if (ret != APP_ERR_OK) {
            LogError << "MxbsMallocAndCopy failed!";
        }
        std::shared_ptr<uint8_t> imageData((uint8_t*)data.ptrData, hostDeleter);
        Image subImage(imageData, pkt.size);
        frameImage.image = subImage;
        LogDebug << "channelId = " << frameImage.channelId << ", frameId = " << frameImage.frameId
        << ", dataSize = " << frameImage.image.GetDataSize();
        av_packet_unref(&pkt);
    }
}

// The stream puller thread
void StreamPullerThread(const std::string filePath, AVFormatContext* pFormatCtx, const int frameCount,
                        const uint32_t width, const uint32_t height)
{
    uint32_t streamHeight = 0;
    uint32_t streamWidth = 0;
    AVPacket pkt;
    uint32_t frameId = 0;
    uint32_t channelId = 0;
    pFormatCtx = avformat_alloc_context();
    pFormatCtx = CreateFormatContext(filePath); // create context
    if (pFormatCtx == nullptr) {
        return;
    }
    av_dump_format(pFormatCtx, 0, filePath.c_str(), 0);
    DeviceContext context = {};
    context.devId = 0;
    DeviceManager::GetInstance()->SetDevice(context);
    // get the real width and height of the stream
    for (unsigned int i = 0; i < pFormatCtx->nb_streams; ++i) {
        AVStream *inStream = pFormatCtx->streams[i];
        if (inStream->codecpar->codec_type == AVMEDIA_TYPE_VIDEO) {
            streamHeight = inStream->codecpar->height;
            streamWidth = inStream->codecpar->width;
            if (streamHeight > height) {
                LogError << "Video height " << streamHeight << " exceeds the configuration height " << height << ".";
                g_sendSignial = true;
                g_readVideoEnded = true;
                return;
            }
            if (streamWidth > width) {
                LogError << "Video width " << streamWidth << " exceeds the configuration width " << width << ".";
                g_sendSignial = true;
                g_readVideoEnded = true;
                return;
            }
        }
    }
    while (!g_sendSignial) {
        Image subImage;
        FrameImage frame;
        frame.channelId = channelId;
        frame.frameId = frameId;
        frame.image = subImage;
        GetFrame(pkt, frame, pFormatCtx, g_readVideoEnded);
        if (g_readVideoEnded == true) {
            break;
        }
        std::shared_ptr<FrameImage> Pframe = std::make_shared<FrameImage>(frame);
        inputQueue->Push(Pframe, true);
        frameId += 1;
        std::this_thread::sleep_for(std::chrono::milliseconds(FRAME_WAIT_TIME));
    }
    std::cout << "There are " << (frameId + 1) << " frames in total." << std::endl;
}

// the video decoder thread
void VdecThread(const ConfigParser &configParser, const uint32_t width, const uint32_t height)
{
    ascendVideoDecoder::VideoDecoder videoDecoder;
    videoDecoder.SetInstanceId(0);
    APP_ERROR ret = videoDecoder.Init(configParser, width, height);
    if (ret != APP_ERR_OK) {
        LogError << "VideoDecoder[" << 0 << "]: videoDecoder init failed.";
        return;
    }
    while (!g_sendSignial && inputQueue->GetSize() != 0) {
        std::shared_ptr<void> inputData = nullptr;
        ret = inputQueue->Pop(inputData, TIME_OUT);
        if (ret != APP_ERR_OK || inputData == nullptr) {
            continue;
        }
        std::shared_ptr<FrameImage> frame = std::static_pointer_cast<FrameImage>(inputData);
        ret = videoDecoder.Process(frame, outputQueue);
        if (ret != APP_ERR_OK) {
            LogError << "VideoDecoder decode failed. Ret is: " << ret;
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(FRAME_WAIT_TIME));
    }
    ret = videoDecoder.DeInit();
    if (ret != APP_ERR_OK) {
        LogError << "VideoDecoder[" << 0 << "]: videoDecoder deinit failed.";
    }
    std::cout << "Vdec thread ended." << std::endl;
}


APP_ERROR SetAnalyzeConfigValue(const ConfigParser &configParser, std::string &modelPath, int &deviceId,
                                int &skipFrameNumber)
{
    // check the stream width and height
    std::string itemCfgStr = {};
    itemCfgStr = std::string("modelPath");
    APP_ERROR ret = configParser.GetStringValue(itemCfgStr, modelPath);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to get config variable named " << itemCfgStr << ".";
        return APP_ERR_COMM_FAILURE;
    }
    std::ifstream modelFile(modelPath);
    if (!modelFile.good()) {
        LogError << "Model path is not valid.";
        return APP_ERR_COMM_FAILURE;
    }
    itemCfgStr = std::string("deviceId");
    ret = configParser.GetIntValue(itemCfgStr, deviceId);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to get config variable named " << itemCfgStr << ".";
        return APP_ERR_COMM_FAILURE;
    }

    itemCfgStr = std::string("skipFrameNumber");
    ret = configParser.GetIntValue("skipFrameNumber", skipFrameNumber);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to get config variable named " << itemCfgStr << ".";
        return APP_ERR_COMM_FAILURE;
    }
    if (skipFrameNumber <= 0) {
        LogError << "skipFrameNumber must >= 1.";
        return APP_ERR_COMM_FAILURE;
    }
}

APP_ERROR SetVideoConfigValue(const ConfigParser &configParser, int &width, int &height,
                              std::string &videoPath, std::string &videoSavedPath)
{
    // check the stream width and height
    std::string itemCfgStr = {};
    itemCfgStr = std::string("width");
    APP_ERROR ret = configParser.GetIntValue(itemCfgStr, width);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to get config variable named " << itemCfgStr << ".";
        return APP_ERR_COMM_FAILURE;
    }

    itemCfgStr = std::string("height");
    ret = configParser.GetIntValue(itemCfgStr, height);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to get config variable named " << itemCfgStr << ".";
        return APP_ERR_COMM_FAILURE;
    }
    if (width > REF_MAX_VDEC_LENGTH || height > REF_MAX_VDEC_LENGTH || width < REF_MIN_VDEC_LENGTH ||
        height < REF_MIN_VDEC_LENGTH) {
        LogError << "Width or Height of config file is out of range [128, 4096], [128, 4096]. "
                 << "width: " << width << ". height:" << height << ".";
        return APP_ERR_COMM_FAILURE;
    }

    itemCfgStr = std::string("videoPath");
    ret = configParser.GetStringValue("videoPath", videoPath);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to get config variable named " << itemCfgStr << ".";
        return APP_ERR_COMM_FAILURE;
    }
    std::ifstream videoFile(videoPath);
    if (!videoFile.good()) {
        LogError << "VideoPath dose not exist.";
        return APP_ERR_COMM_FAILURE;
    }
    itemCfgStr = std::string("videoSavedPath");
    ret = configParser.GetStringValue("videoSavedPath", videoSavedPath);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to get config variable named " << itemCfgStr << ".";
        return APP_ERR_COMM_FAILURE;
    }
    std::ifstream videoSavedfile(videoSavedPath);
    if (videoSavedfile.good()) {
        std::remove(videoSavedPath.c_str());
    }
    return APP_ERR_OK;
}

APP_ERROR CallBackVenc(std::shared_ptr<uint8_t>& outDataPtr, uint32_t& outDataSize, 
                       uint32_t& channelId, uint32_t& frameId, void* userData)
{
    FrameInfo* frameInfo = static_cast<FrameInfo*>(userData);
    Image image(outDataPtr, outDataSize, -1, Size(frameInfo->width,frameInfo->height));
    FrameImage frameImage;
    frameImage.image = image;
    frameImage.channelId = channelId;
    frameImage.frameId = frameId;
    FILE *fp = fopen(frameInfo->videoSavedPath.c_str(), "ab");
    if (fp == nullptr) {
        LogError << "Failed to open file." << std::endl;
        fclose(fp);
        return APP_ERR_COMM_FAILURE;
    }
    // write frame to file
    if (fwrite(frameImage.image.GetData().get(), frameImage.image.GetDataSize(), 1, fp) != 1) {
        LogError << "Write frame << f to file fail."<< std::endl;
        fclose(fp);
        return APP_ERR_COMM_FAILURE;
    }
    fclose(fp);
    return APP_ERR_OK;
}

void VencThread(VideoEncodeConfig vEncodeConfig, std::string modelPath, int deviceId, int skipFrameNumber,
                FrameInfo frameInfo)
{
    VideoEncoder videoEncoder(vEncodeConfig, deviceId, 0);
    FrameAnalyzer frameAnalyzer(modelPath, deviceId);
    uint32_t frameId = 0;
    while(!g_sendSignial && outputQueue->GetSize() != 0) {
        std::shared_ptr<void> outputData = nullptr;
        APP_ERROR ret = outputQueue->Pop(outputData, TIME_OUT);
        if (ret != APP_ERR_OK || outputData == nullptr) {
            continue;
        }
        std::shared_ptr<FrameImage> frame = std::static_pointer_cast<FrameImage>(outputData);
        if (frameId % skipFrameNumber ==0) {
            std::vector<ObjectInfo> detBoxes;
            frameAnalyzer.Analyze(frame->image, detBoxes);
            if (detBoxes.size() != 0) {
                frameAnalyzer.Alarm(detBoxes, frameId);
            }
        }
        ret = videoEncoder.Encode(frame->image, frame->frameId, &frameInfo);
        if (ret != APP_ERR_OK) {
            LogError << "Encode failed.";
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(FRAME_WAIT_TIME));
        frameId += 1;
    }
    std::cout << "Venc thread ended." << std::endl;
}


int main(int argc, char *argv[])
{
    if (signal(SIGINT, SigHandler) == SIG_ERR) {
        LogError << " Cannot catch SIGINT.";
    }
    // the global init
    APP_ERROR ret = MxInit();
    if (ret != APP_ERR_OK) {
        LogError << "MxInit error.";
        return ret;
    }
    std::string videoPath;
    std::string modelPath;
    int deviceId = -1;
    int skipFrameNumber = -1;
    std::string videoSavedPath;
    int height = 0;
    int width = 0;
    int frameCount = 0;

    // parse the config file
    ConfigParser configParser;
    std::string itemCfgStr = {};
    ret = configParser.ParseConfig(CONFIG_FILE_NAME);
    if (ret != APP_ERR_OK) {
        LogError << "Cannot parse file.";
        return APP_ERR_COMM_FAILURE;
    }
    ret = SetVideoConfigValue(configParser, width, height, videoPath, videoSavedPath);
    if (ret != APP_ERR_OK) {
        LogError << "Set the width, height, videoPath, videoSavedPath fail.";
        return APP_ERR_COMM_FAILURE;
    }
    ret = SetAnalyzeConfigValue(configParser, modelPath, deviceId, skipFrameNumber);
    if (ret != APP_ERR_OK) {
        LogError << "Set the modelPath, deviceId, skipFrameNumber fail.";
        return APP_ERR_COMM_FAILURE;
    }
    FrameInfo frameInfo = {height, width, videoSavedPath};

    // start thread
    AVFormatContext * pFormatCtxs = nullptr;
    avformat_network_init();
    VideoEncodeConfig vEncodeConfig;
    MxBase::VideoEncodeCallBack cPtr2 = CallBackVenc;
    vEncodeConfig.callbackFunc = cPtr2;
    vEncodeConfig.height = height;
    vEncodeConfig.width = width;
    vEncodeConfig.keyFrameInterval = 1;
    vEncodeConfig.srcRate = DEFAULT_SRC_RATE;
    vEncodeConfig.maxBitRate = DEFAULT_MAX_BIT_RATE;
    std::thread threadStreamPuller = std::thread(StreamPullerThread, videoPath, pFormatCtxs, frameCount, width, height);
    std::thread threadVdec = std::thread(VdecThread, configParser, width, height);
    std::thread threadVenc = std::thread(VencThread, vEncodeConfig, modelPath, deviceId, skipFrameNumber, frameInfo);

    while (!g_sendSignial && !g_readVideoEnded) {
        usleep(SIGNAL_CHECK_TIMESTEP);
    }

    // join the thread
    threadStreamPuller.join();
    threadVdec.join();
    threadVenc.join();
    std::cout << "Fire detection task ended." << std::endl;

    return 0;
}
