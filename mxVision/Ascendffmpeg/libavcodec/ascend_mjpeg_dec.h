/*
 * MJPEG Ascend decoder
 * Copyright (c) 2000, 2001 Fabrice Bellard
 * Copyright (c) 2003 Alex Beregszaszi
 * Copyright (c) 2003-2004 Michael Niedermayer
 *
 * This file is part of FFmpeg.
 *
 * FFmpeg is free software; you can redistribute it and/or
 * modify it under the terms of the GNU Lesser General Public
 * License as published by the Free Software Foundation; either
 * version 2.1 of the License, or (at your option) any later version.
 *
 * FFmpeg is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
 * Lesser General Public License for more details.
 *
 * You should have received a copy of the GNU Lesser General Public
 * License along with FFmpeg; if not, write to the Free Software
 * Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
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
