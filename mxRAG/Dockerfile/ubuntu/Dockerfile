FROM ubuntu:22.04

WORKDIR /tmp

ARG ARCH=aarch64
ARG TORCH_VERSION=2.1.0
# 请根据在服务器上执行npu-smi info 命令进行查询，将查询到的"Name"字段最后一位数字删除后值修改PLATFORM字段
ARG PLATFORM=310P
# 设置时区禁用交互式配置
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y software-properties-common && add-apt-repository -y ppa:deadsnakes/ppa && apt-get update
RUN apt-get update && apt-get install -y vim tar zip unzip git curl wget dos2unix make gcc g++ ccache gfortran libssl-dev swig ffmpeg libopenblas-dev

# 安装cmake
RUN wget https://cmake.org/files/v3.24/cmake-3.24.3.tar.gz && \
    tar -zxf cmake-3.24.3.tar.gz && \
    cd cmake-3.24.3 && \
    ./bootstrap && make -j && make install

ARG PYTHON_VERSION=python3.11

RUN apt-get update && apt-get install -y build-essential ${PYTHON_VERSION}  ${PYTHON_VERSION}-dev ${PYTHON_VERSION}-distutils ${PYTHON_VERSION}-venv 
RUN curl -k https://bootstrap.pypa.io/get-pip.py | ${PYTHON_VERSION} &&  update-alternatives --install /usr/bin/python3 python3 /usr/bin/${PYTHON_VERSION} 1

#解决blinker无法卸载的问题
RUN apt-get remove -y python3-blinker && apt-get autoremove -y

#配置 python3-config
RUN ln -sf /usr/bin/${PYTHON_VERSION}-config /usr/local/bin/python3-config

RUN pip3 install build wheel

RUN groupadd HwHiAiUser && useradd -g HwHiAiUser -d /home/HwHiAiUser -m HwHiAiUser -s /bin/bash

USER HwHiAiUser:HwHiAiUser

# 安装torch
# RUN pip3 install torch=="${TORCH_VERSION}" --index-url https://download.pytorch.org/whl/cpu 
# 安装torch-npu
# RUN pip3 install torch-npu=="${TORCH_VERSION}".post3

COPY --chown=HwHiAiUser:HwHiAiUser ./package ./

# 安装cann 依赖
RUN pip3 install --upgrade setuptools && pip3 install numpy==1.26.4 decorator==5.1.1 sympy==1.12 cffi==1.16.0 pyyaml==6.0.1 pathlib2==2.3.7.post1 protobuf==5.26.0 scipy==1.12.0 requests==2.31.0 psutil==5.9.8 absl-py==2.1.0 attrs==23.2.0


# 安装cann-toolkit和kernel
RUN bash Ascend-cann-toolkit*_linux-${ARCH}.run --install --quiet && \
    bash Ascend-cann-kernels*_linux.run --install --quiet
ENV ASCEND_HOME_PATH=/home/HwHiAiUser/Ascend/ascend-toolkit/latest
ENV TOOLCHAIN_HOME=/home/HwHiAiUser/Ascend/ascend-toolkit/latest/toolkit
ENV ASCEND_TOOLKIT_HOME=/home/HwHiAiUser/Ascend/ascend-toolkit/latest
ENV ASCEND_OPP_PATH=/home/HwHiAiUser/Ascend/ascend-toolkit/latest/opp
ENV ASCEND_AICPU_PATH=/home/HwHiAiUser/Ascend/ascend-toolkit/latest
ENV LD_LIBRARY_PATH=/usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64/common:/usr/local/Ascend/driver/lib64/driver:$LD_LIBRARY_PATH

# 安装faiss
ARG FAISS_INSTALL_PATH=/home/HwHiAiUser/faiss/faiss1.7.4 
RUN mkdir -p ${FAISS_INSTALL_PATH} && \
	wget https://github.com/facebookresearch/faiss/archive/v1.7.4.tar.gz && \
    tar -xf v1.7.4.tar.gz && \
    cd faiss-1.7.4/faiss && \
    sed -i "131 i virtual void search_with_filter (idx_t n, const float *x, idx_t k, float *distances, idx_t *lables, const void *mask = nullptr) const{}" Index.h && \
    sed -i "38 i template <typename IndexT> IndexIDMapTemplate<IndexT>::IndexIDMapTemplate (IndexT *index, std::vector<idx_t> &ids): index (index), own_fields (false) { this->is_trained = index->is_trained; this->metric_type = index->metric_type; this->verbose = index->verbose; this->d = index->d; id_map = ids; }" IndexIDMap.cpp && \
    sed -i "29 i explicit IndexIDMapTemplate (IndexT *index, std::vector<idx_t> &ids);" IndexIDMap.h && \
    sed -i "199 i utils/sorting.h" CMakeLists.txt && \
    cd .. && cmake -B build . -DFAISS_ENABLE_GPU=OFF -DPython_EXECUTABLE=/usr/bin/python3 -DBUILD_TESTING=OFF -DBUILD_SHARED_LIBS=ON -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=${FAISS_INSTALL_PATH} && \
    make -C build -j faiss && \
    make -C build -j swigfaiss && \
    cd build/faiss/python && python3 setup.py bdist_wheel && \
	cd ../../.. && make -C build install && \
	cd build/faiss/python && cp libfaiss_python_callbacks.so ${FAISS_INSTALL_PATH}/lib && \
	cd dist && \
	pip3 install faiss-1.7.4*.whl

# 安装index
RUN bash Ascend-mindxsdk-mxindex*_linux-${ARCH}.run --quiet --install --install-path=/home/HwHiAiUser/Ascend/ --platform=${PLATFORM}
ENV MX_INDEX_MODELPATH=/home/HwHiAiUser/Ascend/modelpath
RUN cd /home/HwHiAiUser/Ascend/mxIndex/ops && ./custom_opp_${ARCH}.run && mkdir -p ${MX_INDEX_MODELPATH}
ENV ASCEND_HOME=/home/HwHiAiUser/Ascend/
ENV MX_INDEX_FINALIZE=0

# 安装ascendfaiss
ARG MXINDEX_INSTALL_PATH=/home/HwHiAiUser/Ascend/mxIndex
ARG PYTHON_HEADER=/usr/include/${PYTHON_VERSION}/
ARG ASCEND_INSTALL_PATH=/home/HwHiAiUser/Ascend/ascend-toolkit/latest
ARG DRIVER_INSTALL_PATH=/tmp/

RUN wget https://gitee.com/ascend/ascend-referenceapps/repository/archive/master.zip && \
    unzip master.zip && \
    cd ascend-referenceapps-master/mxIndex_samples/faiss-python && \
    swig -python -c++ -Doverride= -module swig_ascendfaiss -I${PYTHON_HEADER} -I${FAISS_INSTALL_PATH}/include -I${MXINDEX_INSTALL_PATH}/include -DSWIGWORDSIZE64 -o swig_ascendfaiss.cpp swig_ascendfaiss.swig && \
    g++ -std=c++11 -DFINTEGER=int -fopenmp -I/usr/local/include -I${ASCEND_INSTALL_PATH}/acllib/include -I${ASCEND_INSTALL_PATH}/runtime/include -I${DRIVER_INSTALL_PATH}/driver/kernel/inc/driver -I${DRIVER_INSTALL_PATH}/driver/kernel/libc_sec/include -fPIC -fstack-protector-all -Wall -Wreturn-type -D_FORTIFY_SOURCE=2 -g -O3 -Wall -Wextra -I${PYTHON_HEADER} -I/home/HwHiAiUser/.local/lib/${PYTHON_VERSION}/site-packages/numpy/core/include -I${FAISS_INSTALL_PATH}/include -I${MXINDEX_INSTALL_PATH}/include -c swig_ascendfaiss.cpp -o swig_ascendfaiss.o && \
    g++ -std=c++11 -shared -fopenmp -L${ASCEND_INSTALL_PATH}/acllib/lib64 -L${ASCEND_INSTALL_PATH}/runtime/lib64 -L${DRIVER_INSTALL_PATH}/driver/lib64 -L${DRIVER_INSTALL_PATH}/driver/lib64/common -L${DRIVER_INSTALL_PATH}/driver/lib64/driver -L${FAISS_INSTALL_PATH}/lib -L${MXINDEX_INSTALL_PATH}/lib -Wl,-rpath-link=${ASCEND_INSTALL_PATH}/acllib/lib64:${ASCEND_INSTALL_PATH}/runtime/lib64:${DRIVER_INSTALL_PATH}/driver/lib64:${DRIVER_INSTALL_PATH}/driver/lib64/common:${DRIVER_INSTALL_PATH}/driver/lib64/driver -L/usr/local/lib -Wl,-z,relro -Wl,-z,now -Wl,-z,noexecstack -s -o _swig_ascendfaiss.so swig_ascendfaiss.o -L.. -lascendfaiss -lfaiss -lascend_hal -lacl_retr -lascendcl -lc_sec -lopenblas && \
    ${PYTHON_VERSION} -m build && \
    cd dist && pip3 install ascendfaiss*.whl

ENV LD_LIBRARY_PATH=/home/HwHiAiUser/Ascend/mxIndex/lib:/home/HwHiAiUser/faiss/faiss1.7.4/lib:$LD_LIBRARY_PATH


#安装mxrag
RUN tar -xzf Ascend-mindxsdk-mxrag_*_linux-${ARCH}.tar.gz && \
    cd mindxsdk-mxrag/ && \
    pip3 install mx_rag-*-none-linux_${ARCH}.whl && \
    pip3 install -r requirements.txt

# 安装mxrag第三方依赖
RUN pip3 install ragas==0.1.9 rank_bm25==0.2.2 readability_lxml==0.8.1 html_text==0.6.2

# 安装torch 和 torch-npu
RUN pip3 install torch-${TORCH_VERSION}*_${ARCH}.whl && pip3 install  torch_npu-${TORCH_VERSION}*_${ARCH}.whl

# 添加环境变量
RUN sed -i '$a\export PYTHONPATH/home/HwHiAiUser/.local/lib/$PYTHON_VERSION/site-packages/mx_rag/libs:$PYTHONPATH' /home/HwHiAiUser/.bashrc && \
    sed -i '$a\export LD_PRELOAD=$(ls /home/HwHiAiUser/.local/lib/$PYTHON_VERSION/site-packages/scikit_learn.libs/libgomp-*):$LD_PRELOAD' /home/HwHiAiUser/.bashrc && \
    sed -i '$a\source /home/HwHiAiUser/Ascend/ascend-toolkit/set_env.sh' /home/HwHiAiUser/.bashrc && \
	sed -i '$a\export PATH=/home/HwHiAiUser/.local/bin:$PATH' /home/HwHiAiUser/.bashrc && \
    sed -i 's/$PYTHON_VERSION/'"$PYTHON_VERSION"'/g' /home/HwHiAiUser/.bashrc


#清理临时目录
USER root
RUN rm -rf /tmp/*

USER HwHiAiUser:HwHiAiUser
RUN touch  /home/HwHiAiUser/.vimrc && \
	echo 'set fileencodings=utf-8,ucs-bom,gb18030,gbk,gb2312,cp936' >> /home/HwHiAiUser/.vimrc && \
	sed -i '$a\set termencoding=utf-8' /home/HwHiAiUser/.vimrc && \
	sed -i '$a\set encoding=utf-8' /home/HwHiAiUser/.vimrc

WORKDIR /home/HwHiAiUser
