#include <iostream>
#include <ctime>
#include "CaptionGenManager.h"
#include "CaptionGeneration.h"
#include "CaptionImpl.h"

APP_ERROR DrawCaption(MxBase::Tensor img) {
    //Step1: 初始化CaptionImpl的字体资源
    CaptionImpl captionImpl1;
    APP_ERROR ret = captionImpl1.init("simsun", "60px", "times", "60px", 0);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to init captionImpl1.";
        return APP_ERR_COMM_FAILURE;
    }
    CaptionImpl captionImpl2;
    ret = captionImpl2.init("simsun", "60px", "times", "60px", 0);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to init captionImpl2.";
        return APP_ERR_COMM_FAILURE;
    }
    float textStandardSize = 60;

    //Step2: 初始化CaptionImpl的中间变量资源
    float fontScale = 1;
    auto length1 = captionImpl1.getLength("K56 350-5-上行-北            ");
    auto length2 = captionImpl2.getLength("2023-08-20 15：21：06        ");
    ret = captionImpl1.initRectAndColor(cv::Scalar(255, 255, 255), cv::Scalar(0, 0, 0), fontScale, length1);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to init the intermediate tensor of captionImpl1.";
        return APP_ERR_COMM_FAILURE;
    }
    ret = captionImpl2.initRectAndColor(cv::Scalar(255, 255, 255), cv::Scalar(0, 0, 0), fontScale, length2);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to init the intermediate tensor of captionImpl2.";
        return APP_ERR_COMM_FAILURE;
    }

    //Step3: 调用putText添加文本
    int W = img.GetShape()[1];
    int H = img.GetShape()[0];
    int textRealSize = int(textStandardSize * fontScale);
    // 在图片左上角添加位置信息
    ret = captionImpl1.putText(img, "安徽-G5011合巢高速-ETC门架S", "K56 350-5-上行-北",
                               cv::Point(textRealSize, textRealSize), 0.3);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to put the address text in the top left corner.";
        return APP_ERR_COMM_FAILURE;
    }
    // 在图片右上角添加时间信息
    ret = captionImpl2.putText(img, "2023-08-20 15：21：06", "",
                               cv::Point(W - length2 * fontScale - textRealSize, textRealSize), 0.3);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to put the time text in the top right corner.";
        return APP_ERR_COMM_FAILURE;
    }
    // 在图片右上角添加时间信息
    ret = captionImpl2.putText(img, "", "预留信息：分辨率xxxx", cv::Point(textRealSize, H - 3 * textRealSize), 0.3);
    if (ret != APP_ERR_OK) {
        LogError << "Fail to put the reserved text in the left bottom corner.";
        return APP_ERR_COMM_FAILURE;
    }
    return APP_ERR_OK;
}


int main() {
    MxBase::MxInit();
    {
        // 读取图片到Image对象
        MxBase::ImageProcessor imageProcessor(0);
        MxBase::Image decodedImage;
        std::string imgPath = "../img.jpg";
        APP_ERROR ret = imageProcessor.Decode(imgPath, decodedImage, MxBase::ImageFormat::BGR_888);
        if (ret != APP_ERR_OK) {
            LogError << "Fail to decode the image.";
            return -1;
        }

        // Image对象转Tensor对象(第一个参数为true，代表image对象与tensor对象共享内存)
        MxBase::Tensor imgTensor = decodedImage.ConvertToTensor(true, false);

        // 字符叠加
        ret = DrawCaption(imgTensor);
        if (ret != APP_ERR_OK) {
            LogError << "Fail to put the caption to image.";
            return -1;
        }

        // Tensor对象转Image对象
        ret = MxBase::Image::TensorToImage(imgTensor, decodedImage, MxBase::ImageFormat::BGR_888);
        if (ret != APP_ERR_OK) {
            LogError << "Fail to convert the tensor to image.";
            return -1;
        }

        // 保存Image对象
        ret = imageProcessor.Encode(decodedImage, "./output.jpg");
        if (ret != APP_ERR_OK) {
            LogError << "Fail to encode the image.";
            return -1;
        }
    }
    MxBase::MxDeInit();
    return 0;
}