cmake_minimum_required(VERSION 3.6)
project(plugin_sample)

#从环境变量中读取MX_SDK_HOME
set(MX_SDK_HOME $ENV{MX_SDK_HOME})
# 设置c++编译版本
execute_process(
    COMMAND awk "/MindX SDK mxVision:/ {print \$NF}" ${MX_SDK_HOME}/version.info
    OUTPUT_VARIABLE MXVISION_VERSION
    OUTPUT_STRIP_TRAILING_WHITESPACE
)

if("${MXVISION_VERSION}" STREQUAL "mxVision:6.0.RC3")
    set(CMAKE_CXX_STANDARD 14)
    message(STATUS "C++14 standard is set.")
else()
    set(CMAKE_CXX_STANDARD 11)
    message(STATUS "C++11 standard is set.")
endif()

add_subdirectory(./mindx_sdk_plugin)