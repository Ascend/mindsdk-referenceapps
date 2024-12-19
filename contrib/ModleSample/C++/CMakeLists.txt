# CMake lowest version requirement
cmake_minimum_required(VERSION 3.5.2)
# project information
project(MindX_SDK_Sample)
set(MX_SDK_HOME $ENV{MX_SDK_HOME})
if (NOT DEFINED ENV{MX_SDK_HOME})
string(REGEX REPLACE "(.*)/(.*)/(.*)/(.*)" "\\1" MX_SDK_HOME  ${CMAKE_CURRENT_SOURCE_DIR})
message(STATUS "set default MX_SDK_HOME: ${MX_SDK_HOME}")
else ()
message(STATUS "env MX_SDK_HOME: ${MX_SDK_HOME}")
endif()
# Compile options
add_definitions(-D_GLIBCXX_USE_CXX11_ABI=0)
add_definitions(-Dgoogle=mindxsdk_private)
add_compile_options(-std=c++14 -fPIC -fstack-protector-all -Wall)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_CURRENT_SOURCE_DIR})
set(CMAKE_CXX_FLAGS_DEBUG "-g")
set(CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} -Wl,-z,relro,-z,now,-z,noexecstack -s -pie")
set(CMAKE_SKIP_RPATH TRUE)
set(ASCEND_HOME_PATH $ENV{ASCEND_HOME_PATH})


include_directories(
${MX_SDK_HOME}/include/
${MX_SDK_HOME}/include/MxBase/postprocess/include/
${MX_SDK_HOME}/opensource/include/
${MX_SDK_HOME}/opensource/include/opencv4
${ASCEND_HOME_PATH}/${ARCH_PATTERN}/include
${ASCEND_HOME_PATH}/${ARCH_PATTERN}/runtime/include
)


link_directories(
${MX_SDK_HOME}/lib/
${MX_SDK_HOME}/lib/modelpostprocessors/
${MX_SDK_HOME}/opensource/lib/
${MX_SDK_HOME}/opensource/lib64/
${ASCEND_HOME_PATH}/atc/lib64
${MX_SDK_HOME}/include/MxBase/postprocess/include
)


add_executable(main main.cpp)
target_link_libraries(main ascendcl acl_dvpp mxbase glog opencv_world pthread)
install(TARGETS main DESTINATION ${CMAKE_RUNTIME_OUTPUT_DIRECTORY})