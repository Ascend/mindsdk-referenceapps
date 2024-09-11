cmake_minimum_required(VERSION 3.6)
project(plugin_sample)

#从环境变量中读取MX_SDK_HOME
set(MX_SDK_HOME ENV{MX_SDK_HOME})

add_subdirectory(./mxVision/C++)
add_subdirectory(./mindx_sdk_plugin)