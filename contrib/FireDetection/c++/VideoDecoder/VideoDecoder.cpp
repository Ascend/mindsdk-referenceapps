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
#include <sys/time.h>
#include <iostream>
#include <sstream>
#include "./VideoDecoder.h"

using namespace std;
using namespace MxBase;

namespace ascendVideoDecoder {
namespace {
    const double ONE_SCECOND = 1000.;
}

VideoDecoder::VideoDecoder() {}

VideoDecoder::~VideoDecoder() {}

APP_ERROR VideoDecoder::ParseConfig(const ConfigParser &configParser)
{
    std::string itemCfgStr = {};
    itemCfgStr = std::string("deviceId");
    APP_ERROR ret = configParser.GetIntValue(itemCfgStr, deviceId_);
    if (ret != APP_ERR_OK) {
        LogError << "Get deviceId from config file fail.";
        return APP_ERR_COMM_FAILURE;
    }
    LogDebug << "deviceId=" << deviceId_;
    return ret;
}

APP_ERROR VideoDecoder::Init(const ConfigParser &configParser, const uint32_t streamWidthMax,
                             const uint32_t streamHeightMax)
                             {
    LogDebug << "VideoDecoder[" << instanceId_ << "]: Begin to init instance.";
    APP_ERROR ret = ParseConfig(configParser);
    if (ret != APP_ERR_OK) {
        LogError << "VideoDecoder[" << instanceId_ << "]: Fail to parse config params." << GetAppErrCodeInfo(ret) <<
                 ".";
        return ret;
    }
    // Init the vdec
    streamWidthMax_ = streamWidthMax;
    streamHeightMax_ = streamHeightMax;
    MxBase::VideoDecodeConfig config;
    MxBase::VideoDecodeCallBack callbackFunc = VideoDecoderCallback;
    config.callbackFunc = callbackFunc;
    config.height = streamHeightMax_;
    config.width = streamWidthMax_;
    config.inputVideoFormat = videoType_;
    config.outputImageFormat = MxBase::ImageFormat::YUV_SP_420;
    try {
        videoDecoder_ = std::make_shared<MxBase::VideoDecoder>(config, deviceId_, instanceId_);
    } catch (const std::runtime_error &e) {
        LogError << "VideoDecoder[" << instanceId_ << "]: mxbs videoDecoder init failed.";
        return APP_ERR_COMM_FAILURE;
    }

    LogDebug << "VideoDecoder[" << instanceId_ << "]: VideoDecoder Init OK.";
    return APP_ERR_OK;
}

void VideoDecoder::SetInstanceId(int instanceId)
{
    instanceId_ = instanceId;
}

APP_ERROR VideoDecoder::Process(std::shared_ptr<FrameImage> frameImage, std::shared_ptr<BlockingQueue<std::shared_ptr<void>>>& output)
{
    LogDebug << "VideoDecoder[" << instanceId_ << "]: VideoDecoder: process start.";
    gettimeofday(&vdecStartTime, nullptr);
    APP_ERROR ret = videoDecoder_->Decode(frameImage->image.GetData(), frameImage->image.GetDataSize(),
                                          frameImage->frameId, output.get());
    gettimeofday(&vdecEndTime, nullptr);
    double costMs = (vdecEndTime.tv_sec - vdecStartTime.tv_sec) * ONE_SCECOND +
            (vdecEndTime.tv_usec - vdecStartTime.tv_usec) / ONE_SCECOND;
    LogDebug << "VideoDecoder[" << instanceId_ << "]: VideoDecoder: Decode " << costMs << "ms";
    if (ret != APP_ERR_OK) {
        LogError << "VideoDecoder[" << instanceId_ << "]: mxbs videoDecode failed, ret=" << ret;
    }
    return APP_ERR_OK;
}

APP_ERROR VideoDecoder::VideoDecoderCallback(MxBase::Image &decodedImage, uint32_t channelId, uint32_t frameId,
                                             void *userData)
                                             {
    LogDebug << "VideoDecoder[" << channelId << "]: VideoDecoderCallback end, frameId:" << frameId;
    
    FrameImage frameImage;
    frameImage.image = decodedImage;
    frameImage.channelId = channelId;
    frameImage.frameId = frameId;

    std::shared_ptr<FrameImage> pFrame = std::make_shared<FrameImage>(frameImage);

    BlockingQueue<std::shared_ptr<FrameImage>>* decodedVec = static_cast<BlockingQueue<std::shared_ptr<FrameImage>>*>(userData);
    if (decodedVec == nullptr) {
        LogError << "VideoDecoderCallback: decodedVec has been released.";
        return APP_ERR_DVPP_INVALID_FORMAT;
    }

    decodedVec->Push(pFrame, true);
    return APP_ERR_OK;
}

APP_ERROR VideoDecoder::DeInit(void)
{
    LogDebug << "VideoDecoder [" << instanceId_ << "]: Begin to deinit";
    videoDecoder_.reset();
    LogDebug << "VideoDecoder [" << instanceId_ << "]: Deinit success.";
    return APP_ERR_OK;
}
}