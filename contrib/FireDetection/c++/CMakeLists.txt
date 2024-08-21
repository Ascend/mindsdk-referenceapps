# Copyright (c) Huawei Technologies Co., Ltd. 2024-2024. All rights reserved.

# CMake lowest version requirement
cmake_minimum_required(VERSION 3.5.2)

# project information
project(MindX_SDK_Fire_Detection)

set(MX_SDK_HOME $ENV{MX_SDK_HOME})
set(FFMPEG_PATH $ENV{FFMPEG_PATH})
set(ASCEND_TOOLKIT_HOME $ENV{ASCEND_TOOLKIT_HOME})

set(PROJECT_SRC_ROOT ${CMAKE_CURRENT_LIST_DIR})
set(CMAKE_MODULE_PATH ${PROJECT_SRC_ROOT}/CMake)
set(CMAKE_SKIP_BUILD_RPATH True)

if (NOT DEFINED ENV{MX_SDK_HOME})
    string(REGEX REPLACE "(.*)/(.*)/(.*)/(.*)" "\\1" MX_SDK_HOME  ${CMAKE_CURRENT_SOURCE_DIR})
    message(STATUS "set default MX_SDK_HOME: ${MX_SDK_HOME}")
else ()
    message(STATUS "env MX_SDK_HOME: ${MX_SDK_HOME}")
endif()

# Compile options
add_definitions(-D_GLIBCXX_USE_CXX11_ABI=0)
add_definitions(-Dgoogle=mindxsdk_private)
add_compile_options(-std=c++11 -fPIC -fstack-protector-all -Wall -g -O0)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})
set(CMAKE_CXX_FLAGS_DEBUG "-g")
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -Wl,-z,relro,-z,now,-z,noexecstack -pie")
set(CMAKE_SKIP_RPATH TRUE)

# Header path
include_directories(
        ${ASCEND_TOOLKIT_HOME}/aarch64-linux/include/
        ${MX_SDK_HOME}/include/
        ${MX_SDK_HOME}/opensource/include/
        ${MX_SDK_HOME}/opensource/include/opencv4
        ${FFMPEG_PATH}/include/
)

set(OPENSOURCE_DIR ${MX_SDK_HOME}/opensource)

include_directories(
        ${OPENSOURCE_DIR}/include
)
link_directories(${OPENSOURCE_DIR}/lib)

# add host lib path
link_directories(
        ${ASCEND_TOOLKIT_HOME}/aarch64-linux/lib64/
        ${MX_SDK_HOME}/lib/
        ${MX_SDK_HOME}/opensource/lib/
        ${MX_SDK_HOME}/opensource/lib64/
        ${FFMPEG_PATH}/lib/
)

add_executable(main main.cpp ConfigParser/ConfigParser.h ConfigParser/ConfigParser.cpp VideoDecoder/VideoDecoder.h
               VideoDecoder/VideoDecoder.cpp FrameAnalyzer/FrameAnalyzer.h FrameAnalyzer/FrameAnalyzer.cpp )

#target_link_libraries(main glog mxbase gstrtp-1.0 -lpthread -lm avformat avcodec avdevice avutil swresample opencv_world ascendcl)
target_link_libraries(main glog mxbase  -lpthread -lm avformat avcodec avdevice avutil ascendcl)
install(TARGETS main DESTINATION ${CMAKE_RUNTIME_OUTPUT_DIRECTORY})