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

#ifndef MINDX_SDK_SAMPLE_VIDEODECODER_H
#define MINDX_SDK_SAMPLE_VIDEODECODER_H

#include <memory>
#include "acl/acl.h"
#include "MxBase/E2eInfer/VideoDecoder/VideoDecoder.h"
#include "MxBase/E2eInfer/ImageProcessor/ImageProcessor.h"
#include "../ConfigParser/ConfigParser.h"
#include "../BlockingQueue/BlockingQueue.h"

using namespace MxBase;

namespace ascendVideoDecoder {
struct FrameImage {
    MxBase::Image image;                 // Video Image Class
    uint32_t frameId = 0;        // Video Frame Index
    uint32_t channelId = 0;      // Video Channel Index
};

class VideoDecoder {
public:
    VideoDecoder();

    ~VideoDecoder();

    APP_ERROR Init(const ConfigParser &configParser, const uint32_t streamWidthMax, const uint32_t streamHeightMax);

    APP_ERROR DeInit(void);

    void SetInstanceId(int instanceId);

    APP_ERROR Process(std::shared_ptr<FrameImage> frameImage, std::shared_ptr<BlockingQueue<std::shared_ptr<void>>>& output);

private:
    APP_ERROR ParseConfig(const ConfigParser &configParser);

    static APP_ERROR VideoDecoderCallback(MxBase::Image &decodedImage, uint32_t channelId, uint32_t frameId,
                                          void *userData);

private:
    uint32_t streamWidthMax_ = 1920;
    uint32_t streamHeightMax_ = 1080;
    uint32_t skipInterval_ = 3;
    int32_t deviceId_ = -1;
    int instanceId_ = -1;
    std::string videoFormat_ = "H264";
    struct timeval vdecStartTime = {0};
    struct timeval vdecEndTime = {0};
    MxBase::StreamFormat videoType_ = MxBase::StreamFormat::H264_MAIN_LEVEL;
    std::shared_ptr<MxBase::VideoDecoder> videoDecoder_ = nullptr;
};
}
#endif
