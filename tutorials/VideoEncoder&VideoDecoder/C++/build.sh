#!/bin/bash
# 定义要检查的目录名
dir_name="build"

# 检查目录是否存在
if [ -d "$dir_name" ]; then
  # 删除目录及其内容
  rm -rf "$dir_name"
fi

mkdir build
cd build
# 执行编译
cmake ..
make
