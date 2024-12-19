import cv2  
import numpy as np
import torch

# from mindx.sdk.base import Tensor  # mxVision 中的 Tensor 数据结构
from mindx.sdk import Tensor 
from mindx.sdk import base  # mxVision 推理接口
from mindx.sdk.base import Model  # mxVision 推理接口


def process():

    DEVICE_ID = 0  # 设备id
    model_path = '../model/yolov4_detection.om'  # 模型路径

    # 模型加载的两种方式
    # 方式一
    model = base.model(modelPath=model_path, deviceId=DEVICE_ID)  # 函数返回参数为Model对象

    # 方式二
    # model = Model(model_path,0) # 直接使用Model类构造对象

    print("input_num:",model.input_num) # 获得模型的输入个数。
    print("output_num:",model.output_num) # 获得模型的输出个数。

    input_shape_vector  = model.input_shape(0) # 获得模型输入的对应Tensor的数据shape信息。
    input_shape_list = list(input_shape_vector)
    print("input_shape_list:",input_shape_list)

    output_shape_vector  = model.output_shape(0) # 获得模型输出的对应Tensor的数据shape信息。
    output_shape_list = list(output_shape_vector)
    print("output0_shape_list:",output_shape_list)

    output_shape_vector  = model.output_shape(1) # 获得模型输出的对应Tensor的数据shape信息。
    output_shape_list = list(output_shape_vector)
    print("output1_shape_list:",output_shape_list)

    input_dtype = model.input_dtype(0)
    print("Input dtype:", input_dtype)


    # 使用numpy生成输入数据 真实情况下读入图片进行推理也可以通过numpy转换为Tensor类型
    img = np.random.randint(0, 255, size=(input_shape_list[0], input_shape_list[1], input_shape_list[2], input_shape_list[3]), dtype=np.uint8).astype(np.uint8) #这里的size根据模型输入的要求确定
    img = Tensor(img) # 将numpy转为转为Tensor类
    output = model.infer([img])  # 执行推理。输入数据类型：List[base.Tensor]， 返回模型推理输出的 List[base.Tensor]

    output[0].to_host()  # 将 Tensor 数据转移到内存
    output0 = np.array(output[0])  # 将数据转为 numpy array 类型
    print("output0 shape",output0.shape)

    output[1].to_host()  # 将 Tensor 数据转移到内存
    output1 = np.array(output[1])  # 将数据转为 numpy array 类型
    print("output1 shape",output1.shape)


if __name__ == "__main__":
    # 初始化资源和变量
    base.mx_init()  # 初始化 mxVision 资源
    process()
    base.mx_deinit()