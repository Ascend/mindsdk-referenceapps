cmake_minimum_required(VERSION 3.10)
project(MultiChannelVideoDetection)

add_compile_options(-fPIC -fstack-protector-all -g -Wl,-z,relro,-z,now,-z -pie -Wall)
add_definitions(-D_GLIBCXX_USE_CXX11_ABI=0 -Dgoogle=mindxsdk_private)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}/")
set(OUTPUT_NAME "videoGestureRecognition")

set(MX_SDK_HOME "$ENV{MX_SDK_HOME}")
set(FFMPEG_PATH "$ENV{FFMPEG_PATH}")

include_directories(
        ${CMAKE_CURRENT_SOURCE_DIR}
        ${MX_SDK_HOME}/include
        ${MX_SDK_HOME}/opensource/include
        ${MX_SDK_HOME}/opensource/include/opencv4
        ${MX_SDK_HOME}/include/MxBase/postprocess/include
        ${FFMPEG_PATH}/include
)

link_directories(
        ${MX_SDK_HOME}/lib
        ${MX_SDK_HOME}/opensource/lib
        ${MX_SDK_HOME}/lib/modelpostprocessors
        ${FFMPEG_PATH}/lib
)

add_executable(${OUTPUT_NAME} main.cpp
        Util/Util.cpp
        StreamPuller/StreamPuller.cpp
        VideoDecoder/VideoDecoder.cpp
        ImageResizer/ImageResizer.cpp
        ResnetDetector/ResnetDetector.cpp
        VideoGestureReasoner/VideoGestureReasoner.cpp
        FrameSkippingSampling/FrameSkippingSampling.cpp
        VideoGestureReasoner/VideoGestureReasoner.cpp)

set(cpprest_DIR ${MX_SDK_HOME}/opensource/lib/libcpprest.so)
if(EXISTS ${cpprest_DIR})
        target_link_libraries(${OUTPUT_NAME} cpprest)
        add_definitions(-DMX_VERSION_5)
endif()

target_link_libraries(${OUTPUT_NAME}
        avcodec
        avdevice
        avfilter
        avformat
        avcodec
        avutil
        swscale
        swresample
        glog
        mxbase
        opencv_world
        pthread m
        resnet50postprocess
        )