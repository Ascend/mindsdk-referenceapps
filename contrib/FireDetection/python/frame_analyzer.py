import numpy as np
from mindx.sdk import base
from mindx.sdk.base import Tensor, Model, Size, Rect, log, ImageProcessor, post, Point
from utils import file_base_check
import os
from utils import logger


MODEL_INPUT_HEIGHT = 640
MODEL_INPUT_WIDTH = 640
MODEL_SHAPE = Size(MODEL_INPUT_HEIGHT, MODEL_INPUT_WIDTH)
ANCHORS_SIZE = [[[10, 13], [16, 30], [33, 23]], [[30, 61], [62, 45], [59, 119]], [[116, 90], [156, 198], [373, 326]]]
NMS_THRESHOLD = 0.6
INDEX_TO_CLASS = {0: "Fire", 1: "Smoke"}


def sigmoid(x):
    return 1 / (1 + np.exp(-x))


def nms(dets, thresh):
    x1 = dets[:, 0]  # xmin
    y1 = dets[:, 1]  # ymin
    x2 = dets[:, 2]  # xmax
    y2 = dets[:, 3]  # ymax
    scores = dets[:, 4]  # confidence

    areas = (x2 - x1 + 1) * (y2 - y1 + 1)  # 每个bounding box的面积
    order = scores.argsort()[::-1]  # 按置信度降序排序

    keep = []  # 用来保存最后留下来的bounding box
    while order.size > 0:
        i = order[0]  # 置信度最高的bounding box的index
        keep.append(i)  # 添加本次置信度最高的bounding box的index

        # 当前bbox和剩下bbox之间的交叉区域
        xx1 = np.maximum(x1[i], x1[order[1:]])
        yy1 = np.maximum(y1[i], y1[order[1:]])
        xx2 = np.minimum(x2[i], x2[order[1:]])
        yy2 = np.minimum(y2[i], y2[order[1:]])

        # 计算交叉区域的面积
        w = np.maximum(0.0, xx2 - xx1 + 1)
        h = np.maximum(0.0, yy2 - yy1 + 1)
        inter = w * h

        # 交叉区域面积 / (bbox + 某区域面积 - 交叉区域面积)
        ovr = inter / (areas[i] + areas[order[1:]] - inter)

        # 保留交集小于一定阈值的bounding box
        inds = np.where(ovr <= thresh)[0]
        order = order[inds + 1]
    return keep


class FrameAnalyzeModel:
    def __init__(self, model_path, device_id):
        file_base_check(os.path.realpath(model_path))
        self.model = Model(os.path.realpath(model_path), device_id)
        self.image_processor = ImageProcessor(device_id)

    def infer(self, image):
        height_ratio = image.original_height / MODEL_INPUT_HEIGHT
        width_ratio = image.original_width / MODEL_INPUT_WIDTH
        if image.height != MODEL_INPUT_HEIGHT or image.width != MODEL_INPUT_WIDTH:
            image = self.image_processor.resize(image, MODEL_SHAPE, base.huaweiu_high_order_filter)
        # model inference
        image_tensor = [image.to_tensor()]
        output_tensors = self.model.infer(image_tensor)
        # decode output results
        bounding_box_array = self.__decode_output(output_tensors)
        # conduct non max suppression
        if bounding_box_array.size != 0:
            keep_idx = nms(bounding_box_array, NMS_THRESHOLD)
            # correct bounding box bias due to resize operation
            bounding_box_array = bounding_box_array[keep_idx, :]
            bounding_box_array[:, [0, 2]] *= width_ratio
            bounding_box_array[:, [1, 3]] *= height_ratio
        return bounding_box_array

    def __decode_output(self, output_tensors):
        output_np_tensors = []
        for tensor in output_tensors:
            tensor.to_host()
            output_np_tensors.append(np.array(tensor))
        bounding_box_array = []
        for layer_idx, tensor in enumerate(output_np_tensors):
            batch, anchor_num, height, width, box_para = tensor.shape
            for height_idx in range(height):
                for width_idx in range(width):
                    for anchor_idx in range(anchor_num):
                        # Filter unimportant anchor and determine the class of anchor according to the given threshold
                        objectness = sigmoid(tensor[0, anchor_idx, height_idx, width_idx, 4])
                        if objectness < 0.1:
                            continue

                        class_score1 = sigmoid(tensor[0, anchor_idx, height_idx, width_idx, 5]) * objectness
                        class_score2 = sigmoid(tensor[0, anchor_idx, height_idx, width_idx, 6]) * objectness
                        if class_score1 < 0.4 and class_score2 < 0.4:
                            continue

                        temp_score = -1
                        temp_class_id = -1
                        if class_score1 < class_score2:
                            temp_score = class_score2
                            temp_class_id = 1
                        else:
                            temp_score = class_score1
                            temp_class_id = 0

                        # Convert relative box info into absolute box info according to prior anchors
                        temp_x = width_idx + sigmoid(tensor[0, anchor_idx, height_idx, width_idx, 0]) * 2 - 0.5
                        temp_y = height_idx + sigmoid(tensor[0, anchor_idx, height_idx, width_idx, 1]) * 2 - 0.5
                        temp_width = sigmoid(tensor[0, anchor_idx, height_idx, width_idx, 2]) * \
                                     sigmoid(tensor[0, anchor_idx, height_idx, width_idx, 2]) * 4 * \
                                     ANCHORS_SIZE[layer_idx][anchor_idx][0]
                        temp_height = sigmoid(tensor[0, anchor_idx, height_idx, width_idx, 3]) * \
                                      sigmoid(tensor[0, anchor_idx, height_idx, width_idx, 3]) * 4 * \
                                      ANCHORS_SIZE[layer_idx][anchor_idx][1]

                        # Convert (x, y, h, w) format into (x0, y0, x1, y1) format
                        x0 = max(temp_x / width * MODEL_INPUT_WIDTH - temp_width / 2, 0)
                        y0 = max(temp_y / height * MODEL_INPUT_HEIGHT - temp_height / 2, 0)
                        x1 = min(temp_x / width * MODEL_INPUT_WIDTH + temp_width / 2, MODEL_INPUT_WIDTH)
                        y1 = min(temp_y / width * MODEL_INPUT_HEIGHT + temp_height / 2, MODEL_INPUT_HEIGHT)
                        bounding_box_array.append([x0, y0, x1, y1, temp_score, temp_class_id])
        return np.array(bounding_box_array)


class FrameAnalyzer:
    def __init__(self, model_path, device_id):
        self.frame_analyze_model = FrameAnalyzeModel(model_path, device_id)

    def analyze(self, image):
        return self.frame_analyze_model.infer(image)

    @staticmethod
    def alarm(analysis_info, frame_id):
        for bounding_box in analysis_info:
            left_top_point, right_button_point = (int(bounding_box[0]), int(bounding_box[1])),\
                                                 (int(bounding_box[2]), int(bounding_box[3]))
            logger.warning("Frame {} detect {}! Confidence: {:.2f}, x0: {:.2f}, y0: {:.2f}, x1: {:.2f}, y1: {:.2f},"
                           .format(frame_id, INDEX_TO_CLASS[bounding_box[5]], bounding_box[4], left_top_point[0],
                                   left_top_point[1], right_button_point[0], right_button_point[1]))

