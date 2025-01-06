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

#include "libavutil/imgutils.h"
#include "libavutil/avassert.h"
#include "libavutil/opt.h"
#include "avcodec.h"
#include "blockdsp.h"
#include "copy_block.h"
#include "decode.h"
#include "hwconfig.h"
#include "idctdsp.h"
#include "internal.h"
#include "jpegtables.h"
#include "mjpeg.h"
#include "mjpegdec.h"
#include "jpeglsdec.h"
#include "profiles.h"
#include "put_bits.h"
#include "tiff.h"
#include "exif.h"
#include "bytestream.h"
#include "ascend_mjpeg_dec.h"


static const uint8_t jpeg_header2[] = {
        0xff, 0xd8,                        // SOI
        0xff, 0xe0,                        // APP0
        0x00, 0x10,                        // APP0 header size
        0x4a, 0x46, 0x49, 0x46, 0x00,      // ID string 'JFIF\0'
        0x01, 0x01,                        // version
        0x00,                              // bits per type
        0x00, 0x00,                        // X density
        0x00, 0x00,                        // Y density
        0x00,                              // X thumbnail size
        0x00,                              // Y thumbnail size
};

static const int dht_segment_size2 = 420;

static const uint8_t dht_segment_head2[] = {0xFF, 0xC4, 0x01, 0xA2, 0x00};
static const uint8_t dht_segment_frag2[] = {
        0x00, 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08, 0x09,
        0x0a, 0x0b, 0x01, 0x00, 0x03, 0x01, 0x01, 0x01, 0x01, 0x01,
        0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00,
};

static uint8_t *append2(uint8_t *buf, const uint8_t *src, int size)
{
    memcpy(buf, src, size);
    return buf + size;
}

static uint8_t *append_dht_segment2(uint8_t *buf)
{
    buf = append2(buf, dht_segment_head2, sizeof(dht_segment_head2));
    buf = append2(buf, avpriv_mjpeg_bits_dc_luminance + 1, 16);
    buf = append2(buf, dht_segment_frag2, sizeof(dht_segment_frag2));
    buf = append2(buf, avpriv_mjpeg_val_dc, 12);
    *(buf++) = 0x10;
    buf = append2(buf, avpriv_mjpeg_bits_ac_luminance + 1, 16);
    buf = append2(buf, avpriv_mjpeg_val_ac_luminance, 162);
    *(buf++) = 0x11;
    buf = append2(buf, avpriv_mjpeg_bits_ac_chrominance + 1, 16);
    buf = append2(buf, avpriv_mjpeg_val_ac_chrominance, 162);
    return buf;
}

#define REF_FRAME_NUM 8
#define DISPLAY_FRAME_NUM 2
#define FFALIGNMJPEG(x, a) (((x) + (a) - 1) &~ ((a) - 1))
#define WIDTH_ALIGN 2
#define HEIGHT_ALIGN 16

av_cold int ff_mjpeg_ascend_decode_init(AvCodecContext* avctx)
{
    AscendMjpegDecodeContext *s = avctx->priv_data;
    int ret;

    enum AVPixelFormat pix_fmts[3] = { AV_PIX_FMT_ASCEND, AV_PIX_FMT_NV12, AV_PIX_FMT_NONE };
    avctx->pix_fmt = ff_get_format(avctx, pix_fmts);
    if (avctx->pix_fmt != AV_PIX_FMT_ASCEND) {
        av_log(avctx, AV_LOG_ERROR, "Perhaps the command \"-hwaccel ascend\" is missing. Please check it.\n");
        return AVERROR(EINVAL);
    }

    if (avctx->width < 128 || avctx->height < 128 || avctx->width > 4096 || avctx->height > 4096) {
        av_log(avctx, AV_LOG_ERROR, "MJPEG decoder only support resolution: 128x128 ~ 4096x4096, now: %dx%d.\n",
               avctx->width, avctx->height);
        return AVERROR(EINVAL);
    }

    char device_id[sizeof(int)];
    sprintf(device_id, "%d", s->device_id);

    AVASCENDDeviceContext* hw_device_ctx;
    AVHWFramesContext* hw_frame_ctx;
    if (avctx->hw_frame_ctx) {
        av_buffer_unref(&s->hw_frame_ref);
        s->hw_frame_ref = av_buffer_ref(avctx->hw_frame_ctx);
        if (!s->hw_frame_ref) {
            ret = AVERROR(EINVAL);
            goto error;
        }

        hw_frame_ctx = (AVHWFramesContext*)s->hw_frame_ref->data;
        if (!hw_frame_ctx->pool || (avctx->width != hw_frame_ctx->width)) {
            if (hw_frame_ctx->pool) {
                av_buffer_pool_uninit(&hw_frame_ctx->pool);
            }
            hw_frame_ctx->width                    = avctx->width;
            hw_frame_ctx->height                   = avctx->height;
            hw_frame_ctx->initial_pool_size        = 2;
            hw_frame_ctx->format                   = AV_PIX_FMT_ASCEND;
            hw_frame_ctx->sw_format                = AV_PIX_FMT_NV12;

            ret = av_hwframe_ctx_init(s->hw_frame_ref);
            if (ret < 0) {
                av_log(avctx, AV_LOG_ERROR, "HWFrame context init failed, ret is %d.\n", ret);
                return AVERROR(ENAVAIL);
            }
        }
        s->hw_device_ref = av_buffer_ref(hw_frame_ctx->device_ref);
        if (!s->hw_device_ref) {
            av_log(avctx, AV_LOG_ERROR, "Get hw_device_ref failed.\n");
            ret = AVERROR(EINVAL);
            goto error;
        }
    } else {
        if (avctx->hw_device_ctx) {
            s->hw_device_ref = av_buffer_ref(avctx->hw_device_ctx);
            if (!s->hw_device_ref) {
                av_log(avctx, AV_LOG_ERROR, "ref hwdevice failed.\n");
                ret = AVERROR(EINVAL);
                goto error;
            }
        } else {
            ret = av_hwdevice_ctx_create(&s->hw_device_ref, AV_HWDEVICE_TYPE_ASCEND, device_id, NULL, 0);
            if (ret < 0) {
                av_log(avctx, AV_LOG_ERROR, "hwdevice context create failed. ret is %d.\n", ret);
                goto error;
            }
        }
        s->hw_frame_ref = av_hwframe_ctx_alloc(s->hw_device_ref);
        if (!s->hw_frame_ref) {
            av_log(avctx, AV_LOG_ERROR, "hwframe ctx alloc falied.\n");
            ret = AVERROR(EINVAL);
            goto error;
        }
        hw_frame_ctx = (AVHWFramesContext*)s->hw_frame_ref->data;
        if (!hw_frame_ctx->pool) {
            hw_frame_ctx->width                  = avctx_width;
            hw_frame_ctx->height                 = avctx->height;
            hw_frame_ctx->initial_pool_size      = 2;
            hw_frame_ctx->format                 = AV_PIX_FMT_ASCEND;
            hw_frame_ctx->sw_format              = AV_PIX_FMT_NV12;
            ret = av_hwframe_ctx_init(s->hw_frame_ref);
            if (ret < 0) {
                av_log(avctx, AV_LOG_ERROR, "hwframe ctx init error, ret is %d.\n", ret);
                ret = AVERROR(EINVAL);
                goto error;
            }
        }
    }

    hw_device_ctx = ((AVHWDeviceContext*)s->hw_device_ref->data)->hwctx;
    s->hw_device_ctx = hw_device_ctx;
    s->hw_frame_ctx = hw_frame_ctx;
    s->ascend_ctx = s->hw_device_ctx->ascend_ctx;

    ret = aclrtSetCurrentContext(s->ascend_ctx->context);
    if (ret != 0) {
        av_log(avctx, AV_LOG_ERROR, "Set context failed at line(%d) in func(%s), ret is %d.\n", __LINE__, __func__, ret);
        return ret;
    }

    ret = hi_mpi_sys_init();
    if (ret != 0) {
        av_log(avctx, AV_LOG_ERROR, "HiMpi sys init failed, ret is %d.\n", ret);
        return ret;
    }

    hi_vdec_chn_attr chn_attr_;
    chn_attr_.type                                              = HI_PT_JPEG;
    chn_attr_.mode                                              = HI_VDEC_SEND_MODE_FRAME;
    chn_attr_.pic_width                                         = avctx->width;
    chn_attr_.pic_height                                        = avctx->height;
    chn_attr_.stream_buf_size                                   = chn_attr_.pic_width * chn_attr_.height * 3 / 2;
    chn_attr_.frame_buf_cnt                                     = REF_FRAME_NUM + DISPLAY_FRAME_NUM + 1;

    hi_pic_buf_attr buf_attr_;
    buf_attr_.width                                             = chn_attr_.pic_width;
    buf_attr_.height                                            = chn_attr_.pic_height;
    buf_attr_.align                                             = 0;
    buf_attr_.bit_width                                         = HI_DATA_BIT_WIDTH_8;
    buf_attr_.pixel_format                                      = HI_PIXEL_FORMAT_YUV_SEMIPLANAR_420;
    buf_attr_.compress_mode                                     = HI_COMPRESS_MODE_NONE;

    chn_attr_.frame_buf_size                                    = hi_vdec_get_pic_buf_size(chn_attr_.type, &buf_attr_);
    chn_attr_.video_attr.ref_frame_num                          = REF_FRAME_NUM;
    chn_attr_.video_attr.temporal_mvp_en                        = HI_TRUE;
    chn_attr_.video_attr.tmv_buf_size                           = hi_vdec_get_tmv_buf_size(chn_attr_.type,
                                                                                           chn_attr_.pic_width,
                                                                                           chn_attr_.pic_height);
    uint32_t channel_id = s->channel_id;
    ret = hi_mpi_vdec_create_chn(channel_id, &chn_attr_);
    if (ret != 0) {
        av_log(avctx, AV_LOG_ERROR, "HiMpi create vdec channel failed, ret is %d.\n", ret);
        return ret;
    }

    hi_vdec_chn_param chn_param_;
    ret = hi_mpi_vdec_get_chn_param(channel_id, &chn_param_);
    if (ret != 0) {
        av_log(avctx, AV_LOG_ERROR, "HiMpi vdec get channel param failed, ret is %d.\n", ret);
        return ret;
    }

    chn_param_.video_param.dec_mode                              = HI_VIDEO_DEC_MODE_IPB;
    chn_param_.video_param.compress_mode                         = HI_COMPRESS_MODE_HFBC;
    chn_param_.video_param.video_format                          = HI_VIDEO_FORMAT_TILE_64x16;
    chn_param_.display_frame_num                                 = DISPLAY_FRAME_NUM;
    chn_param_.video_param.out_order                             = HI_VIDEO_OUT_ORDER_DISPLAY;

    ret = hi_mpi_vdec_set_chn_param(channel_id, &chn_param_);
    if (ret != 0) {
        av_log(avctx, AV_LOG_ERROR, "HiMpi vdec set channel param failed, ret is %d.\n", ret);
        return ret;
    }

    ret = hi_mpi_vdec_start_recv_stream(channel_id);
    if (ret != 0) {
        av_log(avctx, AV_LOG_ERROR, "HiMpi vdec start receive stream failed, ret is %d.\n", ret);
        return ret;
    }

    s->pkt = av_packet_alloc();
    if (!s->pkt)
        return AVERROR(ENOMEM);
    s->avctx = avctx;
    return 0;
    error:
    ff_mjpeg_ascend_decode_end(avctx);
    return ret;
}

int ff_mjpeg_ascend_receive_frame(AvCodecContext* avctx, AVFrame* frame)
{
    AscendMjpegDecodeContext *s = avctx->priv_data;
    int ret = 0;
    ret = mjpeg_get_packet(avctx);
    if (ret < 0) {
        return ret;
    }

    /* GET JPEG */
    AVPacket *out = av_packet_alloc();
    uint8_t* output;
    int input_skip, output_size;
    AVPacket *in = s->pkt;

    if (in->size < 12) {
        av_log(avctx, AV_LOG_ERROR, "Input is truncate.\n");
        return AVERROR_INVALIDDATA;
    }

    if (AV_RB16(int->data) != 0xffd8) {
        av_log(avctx, AV_LOG_ERROR, "Input is not MJPEG.\n");
        return AVERROR_INVALIDDATA;
    }

    if (in->data[2] == 0xff && in->data[3] == APP0) {
        input_skip = (in->data[4] << 8) + in->data[5] + 4;
    } else {
        input_skip = 2;
    }

    if (in->size < input_skip) {
        av_log(avctx, AV_LOG_ERROR, "Input is truncate.\n");
        return AVERROR_INVALIDDATA;
    }

    output_size = in->size - input_skip + sizeof(jpeg_header2) + dht_segment_size2;
    ret = av_new_packet(out, output_size);
    if (ret < 0)
        return AVERROR_INVALIDDATA;
    output = out->data;
    output = append2(output, jpeg_header2, sizeof(jpeg_header2));
    output = append_dht_segment2(output);
    output = append2(output, in->data + input_skip, in->size - input_skip);

    /* JPEG to YUV420 By Ascend */
    ret = aclrtSetCurrentContext(s->ascend_ctx->context);
    if (ret != 0) {
        av_log(avctx, AV_LOG_ERROR, "Set context failed, ret is %d.\n", ret);
        return ret;
    }

    uint8_t* streamBuffer = NULL;
    int device_id = 0;
    ret = hi_mpi_dvpp_malloc(device_id, &streamBuffer, output_size);
    if (ret != 0) {
        av_log(avctx, AV_LOG_ERROR, "HiMpi malloc packet failed, ret is %d.\n", ret);
        return ret;
    }

    ret = aclrtMemcpy(streamBuffer, output_size, output_size, out->data, output_size, ACL_MEMCPY_HOST_TO_DEVICE);
    if (ret != 0) {
        av_log(avctx, AV_LOG_ERROR, "Mem copy H2D failed. ret is %d.\n", ret);
        return ret;
    }

    hi_vdec_stream stream;
    stream.pts                                         = 0;
    stream.addr                                        = streamBuffer;
    stream.len                                         = output_size;
    stream.end_of_frame                                = HI_TRUE;
    stream.end_of_stream                               = HI_FALSE;
    stream.need_display                                = HI_TRUE;

    hi_vdec_pic_info pic_info;
    pic_info.width                                     = s->avctx->width;
    pic_info.height                                    = s->avctx->height;
    pic_info.width_stride                              = FFALIGNMJPEG(pic_info.width, WIDTH_ALIGN);
    pic_info.height_stride                             = FFALIGNMJPEG(pic_info.height, HEIGHT_ALIGN);
    pic_info.offset_top                                = 0;
    pic_info.offset_bottom                             = 0;
    pic_info.offset_left                               = 0;
    pic_info.offset_right                              = 0;

    uint32_t size = pic_info.width_stride * pic_info.height_stride * 3 / 2;
    pic_info.buffer_size = size;
    pic_info.pixel_format = HI_PIXEL_FORMAT_YUV_SEMIPLANAR_420;

    void* picBuffer = NULL;
    ret = hi_mpi_dvpp_malloc(device_id, &picBuffer, size);
    if (ret != 0) {
        av_log(avctx, AV_LOG_ERROR, "HiMpi malloc falied, ret is %d.\n", ret);
        return ret;
    }

    pic_info.vir_addr = (uint64_t)picBuffer;

    ret = hi_mpi_vdec_send_stream(s->channel_id, &stream, &pic_info, 1000);
    if (ret != 0) {
        hi_mpi_dvpp_free(picBuffer);
        av_log(avctx, AV_LOG_ERROR, "Send stream failed, ret is %d.\n", ret);
        return ret;
    }

    hi_video_frame_info got_frame;
    hi_vdec_stream got_stream;
    hi_vdec_supplement_info stSupplement;
    ret = hi_mpi_vdec_get_frame(s->channel_id, &got_frame, &stSupplement, &got_stream, 100);
    if (ret != 0) {
        hi_mpi_dvpp_free(picBuffer);
        av_log(avctx, AV_LOG_ERROR, "Get frame failed, ret is %d.\n", ret);
        return ret;
    }
    size_t decResult = got_frame.v_frame.frame_flag;
    hi_mpi_dvpp_free(got_stream.addr);
    if (decResult != 0 && got_frame.v_frame.virt_addr[0] != NULL) {
        hi_mpi_dvpp_free(got_frame.v_frame.virt_addr[0]);
        return ret;
    }
    if (decResult != 0 || got_frame.v_frame.virt_addr[0] == NULL || got_stream.need_display = HI_FALSE) {
        ret = hi_mpi_vdec_release_frame(s->channel_id, &got_frame);
        if (ret != 0) {
            av_log(avctx, AV_LOG_ERROR, "HiMpi release frame failed, ret is %d.\n", ret);
            return ret;
        }
        return -1;
    }
    ret = hi_mpi_vdec_release_frame(s->channel_id, &got_frame);
    if (ret != 0) {
        av_log(avctx, AV_LOG_ERROR, "HiMpi release frame failed, ret is %d.\n", ret);
        return ret;
    }

    ret = av_hwframe_get_buffer(s->hw_frame_ref, frame, 0);
    if (ret < 0) {
        av_log(avctx, AV_LOG_ERROR, "Frame get buffer failed, ret is %d.\n", ret);
        return AVERROR(EINVAL);
    }
    ret = ff_deocde_frame_props(avctx, frame);
    if (ret < 0) {
        av_log(avctx, AV_LOG_ERROR, "Fill frame properties failed. ret is %d.\n", ret);
        return AVERROR(EINVAL);
    }

    frame->pkt_pos = -1;
    frame->pkt_duration = 0;
    frame->pkt_size = pic_info.buffer_size;
    frame->width = got_frame.v_frame.width_stride[0];
    frame->height = got_frame.v_frame.height_stride[0];
    frame->format = (int)AV_PIX_FMT_NV12;
//    frame->pts = got_frame.v_frame.pts;
//    frame->pkt_pts = frame->pts;
//    frame->pkt_dts = out->dts;

    uint32_t offset = 0;
    for (int i = 0; i < 2; i++) {
        size_t dstBytes = got_frame.v_frame.width_stride[0] * got_frame.v_frame.height_stride[0] * (i ? 1.0 / 2 : 1);
        ret = aclrtMemcpy(frame->data[i], dstBytes, got_frame.v_frame.virt_addr[0] + offset, dstBytes,
                          ACL_MEMCPY_DEVICE_TO_DEVICE);
        if (ret != 0) {
            av_log(avctx, AV_LOG_ERROR, "Mem copy D2D failed, ret is %d.\n", ret);
            hi_mpi_dvpp_free(got_frame.v_frame.virt_addr[0]);
            return ret;
        }
        offset += dstBytes;
    }
    hi_mpi_dvpp_free(got_frame.v_frame.virt_addr[0]);
    error:
    av_packet_free(&out);
    return ret;
}

av_cold int ff_mjpeg_ascend_decode_end(AvCodecContext* avctx)
{
    AscendMjpegDecodeContext *s = avctx->priv_data;
    int ret;
    ret = aclrtSetCurrentContext(s->ascend_ctx->context);
    if (ret != 0) {
        av_log(avctx, AV_LOG_ERROR, "Set context failed, ret is %d.\n", ret);
        return ret;
    }

    ret = hi_mpi_vdec_stop_recv_stream(s->channel_id);
    if (ret != 0) {
        av_log(avctx, AV_LOG_ERROR, "HiMpi stop receive stream failed, ret is %d.\n", ret);
        return ret;
    }

    ret = hi_mpi_vdec_destroy_chn(s->channel_id);
    if (ret != 0) {
        av_log(avctx, AV_LOG_ERROR, "HiMpi destroy channel failed, ret is %d.\n", ret);
        return ret;
    }

    ret = hi_mpi_sys_exit();
    if (ret != 0) {
        av_log(avctx, AV_LOG_ERROR, "HiMpi sys exit failed, ret is %d.\n", ret);
        return ret;
    }

    av_packet_free(&s->pkt);
    av_buffer_unref(&s->hw_device_ref);
    return 0;
}

static void ascend_decode_flush(AvCodecContext* avctx)
{
    ff_mjpeg_ascend_decode_end(avctx);
    ff_mjpeg_ascend_decode_init(avctx);
}

#define OFFSET(x) offsetof(AscendMjpegDecodeContext, x)
#define VD AV_OPT_FLAG_VIDEO_PARAM | AV_OPT_FLAG_DECODING_PARAM
static_cast const AVOption options[] = {
    { "device_id",  "Use to choose the ascend chip.",     OFFSET(device_id), AV_OPT_TYPE_INT, { .i64 = 0}, 0, 8, VD },
    { "channel_id", "Set channelId of decoder.",          OFFSET(channel_id), AV_OPT_TYPE_INT, { .i64 = 0}, 0, 255, VD },
    { NULL }
};


static const AVCodecHWConfigInternal* ascend_hw_configs[] = {
    &(const AVCodecHWConfigInternal) {
        .public = {
            .pix_fmt = AV_PIX_FMT_ASCEND,
            .methods = AV_CODEC_HW_CONFIG_METHOD_HW_DEVICE_CTX | AV_CODEC_HW_CONFIG_METHOD_HW_FRAMES_CTX |
                       AV_CODEC_HW_CONFIG_METHOD_INTERNAL,
            .device_type = AV_HWDEVICE_TYPE_ASCEND
        },
        .hwaccel = NULL,
    },
    NULL
};

#define ASCEND_DEC_CODEC(x, X) \
    static const AVClass x##_ascend_class = { \
        .class_name = #x "_ascend_dec", \
        .item_name = av_default_item_name, \
        .option = options, \
        .version = LIBAVUTIL_VERSION_INT, \
    }; \
    AVCodec ff_##x##_ascend_decoder = { \
        .name = #x "_ascend", \
        .long_name = NULL_IF_CONFIG_SMALL("Ascend HiMpi " #X " decoder"), \
        .type = AVMEDIA_TYPE_VIDEO, \
        .id = AV_CODEC_ID_MJPEG, \
        .priv_data_size = sizeof(AscendMjpegDecodeContext), \
        .priv_class = &x##_ascend_class, \
        .init = ff_mjpeg_ascend_decode_init, \
        .close = ff_mjpeg_ascend_decode_end, \
        .receive_frame = ff_mjpeg_ascend_receive_frame, \
        .flush = ascend_decode_flush, \
        .capabilities = AV_CODEC_CAP_DELAY | AV_CODEC_CAP_AVOID_PROBING | AV_CODEC_CAP_HARDWARE, \
        .pix_fmts = (const enum AVPixelFormat[]) { AV_PIX_FMT_ASCEND, \
                                                   AV_PIX_FMT_NV12, \
                                                   AV_PIX_FMT_NONE }, \
        .hw_config2 = ascend_hw_configs, \
        .wrapper_name = "ascendmjpegdec", \
    };
#if CONFIG_MJPEG_ASCEND_DECODER
ASCEND_DEC_CODEC(mjpeg, MJPEG)
##endif