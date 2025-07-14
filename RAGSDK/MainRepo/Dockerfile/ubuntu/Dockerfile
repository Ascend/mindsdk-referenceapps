FROM ubuntu:20.04

WORKDIR /tmp

ARG ARCH=aarch64
ARG PYTHON_VERSION=python3.11
ARG TORCH_VERSION=2.1.0
# 设置时区禁用交互式配置
ENV DEBIAN_FRONTEND=noninteractive
    
RUN apt-get update && apt-get install -y software-properties-common && add-apt-repository -y ppa:deadsnakes/ppa && apt-get update
RUN apt-get update && apt-get install -y vim tar zip unzip git curl wget dos2unix make gcc g++ ccache gfortran libssl-dev libpq-dev swig ffmpeg

RUN apt-get update && apt-get install -y build-essential ${PYTHON_VERSION}  ${PYTHON_VERSION}-dev ${PYTHON_VERSION}-distutils ${PYTHON_VERSION}-venv 
COPY ./package/urls.conf /tmp/urls.conf
RUN . /tmp/urls.conf && curl $PYPI_URL | ${PYTHON_VERSION} &&  update-alternatives --install /usr/bin/python3 python3 /usr/bin/${PYTHON_VERSION} 1

#配置 python3-config
RUN ln -sf /usr/bin/${PYTHON_VERSION}-config /usr/local/bin/python3-config

# 安装cmake
RUN . /tmp/urls.conf && wget $CMAKE_URL && \
    tar -zxf cmake-3.24.3.tar.gz && \
    cd cmake-3.24.3 && \
    ./bootstrap && make -j && make install

# 请根据在服务器上执行npu-smi info 命令进行查询，将查询到的"Name"字段最后一位数字删除后值修改PLATFORM字段
ARG PLATFORM=310P

#解决blinker无法卸载的问题
RUN apt-get remove -y python3-blinker && apt-get autoremove -y

# 安装cann 依赖
RUN pip3 install --upgrade setuptools && pip3 install numpy==1.26.4 decorator==5.1.1 sympy==1.12 cffi==1.16.0 pyyaml==6.0.1 pathlib2==2.3.7.post1 protobuf==5.26.0 scipy==1.12.0 requests==2.31.0 psutil==5.9.8 absl-py==2.1.0 attrs==23.2.0

# 安装torch for x86
# RUN pip3 install torch=="${TORCH_VERSION}" --index-url https://download.pytorch.org/whl/cpu 
# 安装torch-npu
# RUN pip3 install torch-npu=="${TORCH_VERSION}".post3

# 安装cann-toolkit和kernel
COPY ./package/Ascend-cann*_linux-${ARCH}.run /tmp/
RUN useradd -d /home/HwHiAiUser -u 1000 -m -s /bin/bash HwHiAiUser
RUN bash /tmp/Ascend-cann-toolkit*_linux-${ARCH}.run --install --install-for-all --quiet
RUN bash /tmp/Ascend-cann-kernels*_linux-${ARCH}.run --install --install-for-all --quiet
#安装 nnal
RUN bash -c "source /usr/local/Ascend/ascend-toolkit/set_env.sh && bash /tmp/Ascend-cann-nnal*_linux-${ARCH}.run --install --quiet"  
    
ENV ASCEND_HOME_PATH=/usr/local/Ascend/ascend-toolkit/latest
ENV TOOLCHAIN_HOME=/usr/local/Ascend/ascend-toolkit/latest/toolkit
ENV ASCEND_TOOLKIT_HOME=/usr/local/Ascend/ascend-toolkit/latest
ENV ASCEND_OPP_PATH=/usr/local/Ascend/ascend-toolkit/latest/opp
ENV ASCEND_AICPU_PATH=/usr/local/Ascend/ascend-toolkit/latest
ENV LD_LIBRARY_PATH=/usr/local/Ascend/driver/lib64:/usr/local/Ascend/driver/lib64/common:/usr/local/Ascend/driver/lib64/driver:$LD_LIBRARY_PATH

RUN pip3 install build wheel


# 安装openblas
ARG OPENBLAS_INSTALL_PATH=/usr/local/Ascend/OpenBLAS
RUN . /tmp/urls.conf && cd /tmp && \
    git clone $OPENBLAS_URL && \
	cd OpenBLAS && \
	git checkout v0.3.10 && \
    make FC=gfortran USE_OPENMP=1 -j && \
	make PREFIX=${OPENBLAS_INSTALL_PATH} install 
ENV LD_LIBRARY_PATH=${OPENBLAS_INSTALL_PATH}/lib:$LD_LIBRARY_PATH


# 安装faiss
ARG FAISS_INSTALL_PATH=/usr/local/faiss/faiss1.10.0
RUN . /tmp/urls.conf && wget $FAISS_URL && \
    tar -xf v1.10.0.tar.gz && \
    cd faiss-1.10.0/faiss && \
    sed -i "149 i virtual void search_with_filter (idx_t n, const float *x, idx_t k, float *distances, idx_t *lables, const void *mask = nullptr) const{}" Index.h && \
    sed -i "49 i template <typename IndexT> IndexIDMapTemplate<IndexT>::IndexIDMapTemplate (IndexT *index, std::vector<idx_t> &ids): index (index), own_fields (false) { this->is_trained = index->is_trained; this->metric_type = index->metric_type; this->verbose = index->verbose; this->d = index->d; id_map = ids; }" IndexIDMap.cpp && \
    sed -i "30 i explicit IndexIDMapTemplate (IndexT *index, std::vector<idx_t> &ids);" IndexIDMap.h && \
    sed -i "217 i utils/sorting.h" CMakeLists.txt && \
    cd .. && cmake -B build . -DFAISS_ENABLE_GPU=OFF -DPython_EXECUTABLE=/usr/bin/python3 -DBUILD_TESTING=OFF -DBUILD_SHARED_LIBS=ON -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=${FAISS_INSTALL_PATH} && \
    make -C build -j faiss && \
    make -C build -j swigfaiss && \
    cd build/faiss/python && python3 setup.py bdist_wheel && \
    cd ../../.. && make -C build install && \
    cd build/faiss/python && cp libfaiss_python_callbacks.so ${FAISS_INSTALL_PATH}/lib && \
    cd dist && \
    pip3 install faiss-1.10.0*.whl

# 安装index
COPY ./package/Ascend-mindxsdk-mxindex*_linux-${ARCH}.run /tmp/
RUN bash /tmp/Ascend-mindxsdk-mxindex*_linux-${ARCH}.run --quiet --install --install-path=/usr/local/Ascend --platform=${PLATFORM}
ENV MX_INDEX_MODELPATH=/home/ascend/modelpath
RUN cd /usr/local/Ascend/mxIndex/ops && ./custom_opp_${ARCH}.run && mkdir -p /home/ascend/modelpath

# 安装ascendfaiss，到这里了
ARG FAISS_INSTALL_PATH=/usr/local/faiss/faiss1.10.0
ARG MXINDEX_INSTALL_PATH=/usr/local/Ascend/mxIndex
ARG PYTHON_HEADER=/usr/include/${PYTHON_VERSION}/
ARG ASCEND_INSTALL_PATH=/usr/local/Ascend/ascend-toolkit/latest
ARG DRIVER_INSTALL_PATH=/usr/local/Ascend

COPY ./package/driver /usr/local/Ascend/driver
RUN . /tmp/urls.conf && wget $ASCENDFAISS_URL


RUN unzip master.zip && \
    cd mindsdk-referenceapps-master/IndexSDK/faiss-python && \
    swig -python -c++ -Doverride= -module swig_ascendfaiss -I${PYTHON_HEADER} -I${FAISS_INSTALL_PATH}/include -I${MXINDEX_INSTALL_PATH}/include -DSWIGWORDSIZE64 -o swig_ascendfaiss.cpp swig_ascendfaiss.swig && \
    g++ -std=c++11 -DFINTEGER=int -fopenmp -I/usr/local/include -I${ASCEND_INSTALL_PATH}/acllib/include -I${ASCEND_INSTALL_PATH}/runtime/include -I${DRIVER_INSTALL_PATH}/driver/kernel/inc/driver -I${DRIVER_INSTALL_PATH}/driver/kernel/libc_sec/include -fPIC -fstack-protector-all -Wall -Wreturn-type -D_FORTIFY_SOURCE=2 -g -O3 -Wall -Wextra -I${PYTHON_HEADER} -I/usr/local/lib/${PYTHON_VERSION}/dist-packages/numpy/core/include -I${FAISS_INSTALL_PATH}/include -I${MXINDEX_INSTALL_PATH}/include -c swig_ascendfaiss.cpp -o swig_ascendfaiss.o && \
    g++ -std=c++11 -shared -fopenmp -L${ASCEND_INSTALL_PATH}/lib64 -L${ASCEND_INSTALL_PATH}/acllib/lib64 -L${ASCEND_INSTALL_PATH}/runtime/lib64 -L${DRIVER_INSTALL_PATH}/driver/lib64 -L${DRIVER_INSTALL_PATH}/driver/lib64/common -L${DRIVER_INSTALL_PATH}/driver/lib64/driver -L${FAISS_INSTALL_PATH}/lib -L${MXINDEX_INSTALL_PATH}/lib -Wl,-rpath-link=${ASCEND_INSTALL_PATH}/acllib/lib64:${ASCEND_INSTALL_PATH}/runtime/lib64:${DRIVER_INSTALL_PATH}/driver/lib64:${DRIVER_INSTALL_PATH}/driver/lib64/common:${DRIVER_INSTALL_PATH}/driver/lib64/driver -L/usr/local/lib -Wl,-z,relro -Wl,-z,now -Wl,-z,noexecstack -s -o _swig_ascendfaiss.so swig_ascendfaiss.o -L.. -lascendfaiss -lfaiss -lascend_hal -lacl_retr -lascendcl -lc_sec -lacl_op_compiler && \
    ${PYTHON_VERSION} -m build && \
    cd dist && pip3 install ascendfaiss*.whl

    
#ENV LD_LIBRARY_PATH=/usr/local/Ascend/mxIndex/lib:/usr/local/faiss/faiss1.10.0/lib:$LD_LIBRARY_PATH


# 安装toch_npu
#RUN pip3 install torch-${TORCH_VERSION}*_${ARCH}.whl && pip3 install torch_npu-${TORCH_VERSION}*_${ARCH}.whl
RUN pip3 install torch-npu=="${TORCH_VERSION}".post8

# 安装mxrag
COPY ./package/Ascend-mindxsdk-mxrag_*_linux-${ARCH}.run /tmp/
RUN bash /tmp/Ascend-mindxsdk-mxrag_*_linux-${ARCH}.run --install --install-path=/usr/local/Ascend --quiet --platform=${PLATFORM}
RUN pip3 install -r /usr/local/Ascend/mxRag/requirements.txt

# 安装mxrag第三方依赖
RUN pip3 install ragas==0.1.9 rank_bm25==0.2.2 readability_lxml==0.8.1 html_text==0.6.2 gradio==3.50.2
#清理临时目录
RUN rm -rf ./* && rm -rf /usr/local/Ascend/driver

# 添加环境变量
RUN sed -i '$a\export PYTHONPATH=/root/.local/lib/$PYTHON_VERSION/site-packages/mx_rag/libs/:$PYTHONPATH' /root/.bashrc  && \
    sed -i '$a\export LD_PRELOAD=$(ls /usr/local/lib/$PYTHON_VERSION/dist-packages/scikit_learn.libs/libgomp-*):$LD_PRELOAD' /root/.bashrc && \
    sed -i '$a\source /usr/local/Ascend/ascend-toolkit/set_env.sh' /root/.bashrc && \
    sed -i '$a\source /usr/local/Ascend/nnal/atb/set_env.sh' /root/.bashrc && \
	sed -i '$a\source /usr/local/Ascend/mxRag/script/set_env.sh' /root/.bashrc && \
    sed -i '$a\export LD_LIBRARY_PATH=/usr/local/Ascend/mxIndex/lib:/usr/local/faiss/faiss1.10.0/lib:$LD_LIBRARY_PATH' /root/.bashrc && \
    sed -i '$a\export PATH=/usr/local/bin:$PATH' /root/.bashrc && \
    sed -i 's/$PYTHON_VERSION/'"$PYTHON_VERSION"'/g' /root/.bashrc && \
	sed -i '$a\export LOGURU_FORMAT="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message!r}</level>"' /root/.bashrc
    

USER HwHiAiUser:HwHiAiUser

# 安装index for HwHiAiUser
COPY ./package/Ascend-mindxsdk-mxindex*_linux-${ARCH}.run /tmp/
RUN bash /tmp/Ascend-mindxsdk-mxindex*_linux-${ARCH}.run --quiet --install --install-path=/home/HwHiAiUser/Ascend --platform=${PLATFORM}

# 安装mxrag for HwHiAiUser
COPY ./package/Ascend-mindxsdk-mxrag_*_linux-${ARCH}.run /tmp/
RUN bash /tmp/Ascend-mindxsdk-mxrag_*_linux-${ARCH}.run --install --install-path=/home/HwHiAiUser/Ascend --quiet --platform=${PLATFORM}

# 添加环境变量 for HwHiAiUser用户
RUN sed -i '$a\export PYTHONPATH=/home/HwHiAiUser/.local/lib/$PYTHON_VERSION/site-packages/mx_rag/libs/:$PYTHONPATH' /home/HwHiAiUser/.bashrc  && \
    sed -i '$a\export LD_PRELOAD=$(ls /usr/local/lib/$PYTHON_VERSION/dist-packages/scikit_learn.libs/libgomp-*):$LD_PRELOAD' /home/HwHiAiUser/.bashrc && \
    sed -i '$a\source /usr/local/Ascend/ascend-toolkit/set_env.sh' /home/HwHiAiUser/.bashrc && \
    sed -i '$a\source /usr/local/Ascend/nnal/atb/set_env.sh' /home/HwHiAiUser/.bashrc && \
	sed -i '$a\source /home/HwHiAiUser/Ascend/mxRag/script/set_env.sh' /home/HwHiAiUser/.bashrc && \
    sed -i '$a\export LD_LIBRARY_PATH=/home/HwHiAiUser/Ascend/mxIndex/lib:/usr/local/faiss/faiss1.10.0/lib:$LD_LIBRARY_PATH' /home/HwHiAiUser/.bashrc && \
	sed -i '$a\export PATH=/usr/local/bin:$PATH' /home/HwHiAiUser/.bashrc && \
    sed -i 's/$PYTHON_VERSION/'"$PYTHON_VERSION"'/g' /home/HwHiAiUser/.bashrc && \
	sed -i '$a\export LOGURU_FORMAT="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message!r}</level>"' /home/HwHiAiUser/.bashrc

ENV MX_INDEX_MULTITHREAD=1
ENV MX_INDEX_FINALIZE=0

USER root
RUN chmod +r /usr/local/Ascend/ascend-toolkit/latest/opp/vendors/config.ini
RUN rm -rf /tmp/*
USER HwHiAiUser:HwHiAiUser

WORKDIR /home/HwHiAiUser

