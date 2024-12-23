#!/bin/bash
# 检查目录是否存在
dir_name="build"
if [ -d "$dir_name" ]; then
  # 删除目录及其内容
  rm -rf "$dir_name"
fi

mkdir build
cd build
# 执行编译
cmake ..
make