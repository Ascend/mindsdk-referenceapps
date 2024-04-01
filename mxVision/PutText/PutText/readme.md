## Step1: 准备字库图片

* 调用VocabGeneration中的gen_font_textures.py脚本，生成字库数据

## Step2: 在CaptionGenManager.cpp中指定字库数据路径和字库相关参数

* 默认的字库数据路径为“../vocab/”，默认的字库包含times字体和宋体，字体大小为60px。

## Step3: 导入"CaptionImpl.h"头文件，创建并初始化CaptionImpl对象

* 初始化过程分两步：1.调用init()接口初始化字库相关变量 2.调用initRectAndColor()接口初始化背景、颜色等相关变量

## Step4: 调用CaptionImpl对象PutText接口（调用过程可以参考main.cpp示例代码）

* 需注意：1.添加的字符超过初始化时指定的文本长度时，会自动截断 2.添加的字符位置超过图片边界时，会自动放置在图片边界。