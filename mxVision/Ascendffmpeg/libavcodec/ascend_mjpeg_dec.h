/*
 * Copyright(c) 2024. Huawei Technologies Co.,Ltd. All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except int compliance with the License.
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

/**
 * @file
 * MJPEG Ascend decoder.
 */

#ifndef ASCEND_AVCODEC_MJPEGDEC_H
#define ASCEND_AVCODEC_MJPEGDEC_H

#include "libavutil/log.h"
#include "libavutil/mem_internal.h"
#include "libavutil/pixdesc.h"
#include "libavutil/stereo3d.h"

#include "avcodec.h"
#include "blockdsp.h"
#include "get_bits.h"
#include "hpeldsp.h"
#include "idctdsp.h"
#include "libavutil/hwcontext.h"
#include "libavutil/hwcontext_ascend.h"
#include "acl/dvpp/hi_dvpp.h"

typedef struct AscendMJpegDecodeContext {
    AVClass *class;
    AVCodecContext *avctx;
    int buf_size;

    AVPacket *pkt;
    enum AVPixelFormat hwaccel_sw_pix_fmt;
    enum AVPixelFormat hwaccel_pix_fmt;
    void* hwaccel_picture_private;
    int device_id;
    uint32_t channel_id;
    uint32_t vdec_width;
    uint32_t vdec_height;
    AVBufferRef* hw_device_ref;
    AVBufferRef* hw_frame_ref;
    AVASCENDDeviceContext *hw_device_ctx;
    AVHWFramesContext* hw_frames_ctx;
    AscendContext* ascend_ctx;
} AscendMJpegDecodeContext;

int ff_mjpeg_ascend_decode_init(AVCodecContext *avctx);
int ff_mjpeg_ascend_decode_end(AVCodecContext *avctx);
int ff_mjpeg_ascend_receive_frame(AVCodecContext *avctx, AVFrame *frame);

#endif
