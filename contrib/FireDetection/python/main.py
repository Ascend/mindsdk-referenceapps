import threading
import signal
import time
import av
from mindx.sdk import base
from mindx.sdk.base import VideoDecoder, VideoDecodeConfig,\
    VdecCallBacker, VideoEncoder, VideoEncodeConfig, VencCallBacker
from frame_analyzer import FrameAnalyzer
from utils import infer_config, logger

decoded_data_queue = []
analyzed_data_queue = []
decode_finished_flag = False
SIGNAL_RECEIVED = False


class Frame:
    def __init__(self, image, frame_id):
        self.image = image
        self.frame_id = frame_id


def stop_handler(signum, frame):
    global SIGNAL_RECEIVED
    SIGNAL_RECEIVED = True


def vdec_callback_func(decoded_image, channel_id, frame_id):
    logger.debug('Video decoder output decoded image (channelId:{}, frameId:{}, image.width:{},'
                 ' image.height:{}, image.format:{})'.format(channel_id, frame_id, decoded_image.width,
                                                             decoded_image.height, decoded_image.format))
    # 解码完成的Image类存入列表中
    decoded_data_queue.append(decoded_image)


def vdec_thread_func(vdec_config, vdec_callbacker, device_id, rtsp):
    global decode_finished_flag
    global SIGNAL_RECEIVED
    with av.open(rtsp) as container:
        count = 0
        # 初始化VideoDecoder
        video_decoder = VideoDecoder(vdec_config, vdec_callbacker, device_id, 0)
        # 校验视频宽高是否符合编码器要求
        video_stream = next(s for s in container.streams if s.type == 'video')
        if video_stream.height > infer_config["height"]:
            logger.error("Video height {} exceeds the configuration height {} in config file. Please adjust config."
                         .format(video_stream.height, infer_config["height"]))
            SIGNAL_RECEIVED = True
            return
        if video_stream.width > infer_config["width"]:
            logger.error("Video width {} exceeds the configuration width {} in config file. Please adjust config."
                         .format(video_stream.width, infer_config["width"]))
            SIGNAL_RECEIVED = True
            return
        # 循环取帧解码
        for packet in container.demux():
            if SIGNAL_RECEIVED:
                break
            if packet.size == 0:
                logger.info("Finish to pull rtsp stream.")
                SIGNAL_RECEIVED = True
                break
            logger.debug("send packet:{} ".format(count))
            video_decoder.decode(packet, count)
            time.sleep(0.02)
            count += 1
        logger.info("There are {} frames in total.".format(count))


# 视频编码回调函数
def venc_callback_func(output, output_datasize, channel_id, frame_id):
    logger.debug('Video encoder output encoded_stream. (type:{}, outDataSize:{}, channelId:{}, frameId:{})'
                 .format(type(output), output_datasize, channel_id, frame_id))
    with open(infer_config["video_saved_path"], 'ab') as file:
        file.write(output)


def venc_thread_func(venc_config, venc_callbacker, device_id):
    video_encoder = VideoEncoder(venc_config, venc_callbacker, device_id)
    i = 0
    global SIGNAL_RECEIVED
    while not (SIGNAL_RECEIVED and not decoded_data_queue):
        if not decoded_data_queue:
            continue
        frame_image = decoded_data_queue.pop(0)
        if i % infer_config["skip_frame_number"] == 0:
            analyzed_data_queue.append(Frame(frame_image, i))
        video_encoder.encode(frame_image, i)
        time.sleep(0.02)
        i += 1
    logger.info("Venc thread ended.")


def analyze_thread_func(model_path, device_id):
    frame_analyzer = FrameAnalyzer(model_path, device_id)
    global SIGNAL_RECEIVED
    while not (SIGNAL_RECEIVED and not analyzed_data_queue):
        if not analyzed_data_queue:
            continue
        frame = analyzed_data_queue.pop(0)
        results = frame_analyzer.analyze(frame.image)
        if results.size != 0:
            frame_analyzer.alarm(results, frame.frame_id)
    logger.info("Analyze thread ended.")


signal.signal(signal.SIGINT, stop_handler)
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
                                                             "rtsp": infer_config["video_path"]})

    venc = threading.Thread(target=venc_thread_func, kwargs={'venc_config': venc_conf,
                                                             'venc_callbacker': venc_callbacker_instance,
                                                             "device_id": infer_config["device_id"]})

    analyze = threading.Thread(target=analyze_thread_func, kwargs={"model_path": infer_config["model_path"],
                                                                   "device_id": infer_config["device_id"]})

    # 启动线程
    vdec.start()
    venc.start()
    analyze.start()

    # 等待执行完毕
    vdec.join()
    venc.join()
    analyze.join()

    logger.info("Fire detection task ended.")
