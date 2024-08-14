import threading
import av
from mindx.sdk import base
from mindx.sdk.base import VideoDecoder, VideoDecodeConfig,\
    VdecCallBacker, VideoEncoder, VideoEncodeConfig, VencCallBacker
from frame_analyzer import FrameAnalyzer
from utils import infer_config, logger

decoded_data_queue = []
decode_finished_flag = False


def vdec_callback_func(decoded_image, channel_id, frame_id):
    logger.debug('Video decoder output decoded image (channelId:{}, frameId:{}, image.width:{},'
                 ' image.height:{}, image.format:{})'.format(channel_id, frame_id, decoded_image.width,
                                                             decoded_image.height, decoded_image.format))
    # 解码完成的Image类存入列表中
    decoded_data_queue.append(decoded_image)


def vdec_thread_func(vdec_config, vdec_callbacker, device_id, rtsp):
    global decode_finished_flag
    with av.open(rtsp) as container:
        count = 0
        # 初始化VideoDecoder
        video_decoder = VideoDecoder(vdec_config, vdec_callbacker, device_id, 0)
        # 循环取帧解码
        for packet in container.demux():
            logger.debug("send packet:{} ".format(count))
            video_decoder.decode(packet, count)
            count += 1
        logger.info("There are {} frames in total.".format(count))
        decode_finished_flag = True


# 视频编码回调函数
def venc_callback_func(output, output_datasize, channel_id, frame_id):
    logger.debug('Video encoder output encoded_stream. (type:{}, outDataSize:{}, channelId:{}, frameId:{})'
                 .format(type(output), output_datasize, channel_id, frame_id))
    with open(infer_config["video_saved_path"], 'ab') as file:
        file.write(output)


def venc_thread_func(venc_config, venc_callbacker, device_id, model_path):
    video_encoder = VideoEncoder(venc_config, venc_callbacker, device_id)
    frame_analyzer = FrameAnalyzer(model_path, device_id)
    i = 0
    global decode_finished_flag
    while not decode_finished_flag or not decoded_data_queue:
        if not decoded_data_queue:
            continue
        frame_image = decoded_data_queue.pop(0)
        if i % infer_config["skip_frame_number"] == 0:
            results = frame_analyzer.analyze(frame_image)
            if results.size != 0:
                frame_analyzer.alarm(results, i)
        video_encoder.encode(frame_image, i)
        i += 1


if __name__ == '__main__':
    base.mx_init()
    vdec_callbacker_instance = VdecCallBacker()
    vdec_callbacker_instance.registerVdecCallBack(vdec_callback_func)
    # # 初始化VideoDecodeConfig类并设置参数
    vdec_conf = VideoDecodeConfig()
    vdec_conf.inputVideoFormat = base.h264_main_level
    vdec_conf.outputImageFormat = base.nv12
    vdec_conf.width = infer_config["width"]
    vdec_conf.height = infer_config["height"]
    # 初始化VencCallBacker类并注册回调函数
    venc_callbacker_instance = VencCallBacker()
    venc_callbacker_instance.registerVencCallBack(venc_callback_func)
    # 初始化VideoEncodeConfig
    venc_conf = VideoEncodeConfig()
    venc_conf.keyFrameInterval = 50
    venc_conf.srcRate = 30
    venc_conf.maxBitRate = 6000
    venc_conf.ipProp = 30

    # 创建线程，并传递参数
    vdec = threading.Thread(target=vdec_thread_func, kwargs={'vdec_config': vdec_conf,
                                                             'vdec_callbacker': vdec_callbacker_instance,
                                                             "device_id": infer_config["device_id"],
                                                             "rtsp": infer_config["rtsp_url"]})

    venc = threading.Thread(target=venc_thread_func, kwargs={'venc_config': venc_conf,
                                                             'venc_callbacker': venc_callbacker_instance,
                                                             "device_id": infer_config["device_id"],
                                                             "model_path": infer_config["model_path"]})
    # 启动线程
    vdec.start()
    venc.start()

    # 等待执行完毕
    vdec.join()
    venc.join()