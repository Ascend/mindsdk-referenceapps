set -e
. ./urls.conf
# OpenBLAS
wget ${OpenBLAS_SH} -O OpenBLAS-0.3.10.tar.gz
tar -xf OpenBLAS-0.3.10.tar.gz
cd OpenBLAS-0.3.10
make FC=gfortran USE_OPENMP=1 -j
make install
ln -s /opt/OpenBLAS/lib/libopenblas.so /usr/lib/libopenblas.so
cd .. && rm -f OpenBLAS-0.3.10.tar.gz && rm -rf OpenBLAS-0.3.10

# faiss 1.7.4
install_path=/usr/local/faiss/faiss1.7.4
wget ${FAISS_SH} -O faiss-1.7.4.tar.gz
tar -xf faiss-1.7.4.tar.gz && cd faiss-1.7.4/faiss

arch="$(uname -m)"
if [ "${arch}" = "aarch64" ]; then
  gcc_version="$(gcc -dumpversion)"
  if ["${gcc_version}" = "4.8.5" ]; then
    sed -i '20i /*' utils/simdlib.h
    sed -i '24i */' utils/simdlib.h
  fi
fi
sed -i "131 i\\
    \\
    virtual void search_with_filter (idx_t n, const float *x, idx_t k,\\
                                     float *distances, idx_t *labels, const void *mask = nullptr) const {} \\
" Index.h
sed -i "38 i\\
    \\
template <typename IndexT>\\
IndexIDMapTemplate<IndexT>::IndexIDMapTemplate (IndexT *index, std::vector<idx_t> &ids):\\
    index (index),\\
    own_fields (false)\\
{\\
    this->is_trained = index->is_trained;\\
    this->metric_type = index->metric_type;\\
    this->verbose = index->verbose;\\
    this->d = index->d;\\
    id_map = ids;\\
}\\
" IndexIDMap.cpp
sed -i "29 i\\
    \\
    explicit IndexIDMapTemplate (IndexT *index, std::vector<idx_t> &ids);\\
" IndexIDMap.h
sed -i "199 i\\
    utils/sorting.h
" CMakeLists.txt

cd ..
cmake -B build . -DFAISS_ENABLE_GPU=OFF -DFAISS_ENABLE_PYTHON=OFF -DBUILD_TESTING=OFF -DBUILD_SHARED_LIBS=ON -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=${install_path}
cd build && make -j && make install
cd ../.. && rm -rf faiss-1.7.4*

wget ${RELEASE_SH} && \
cp release-1.8.1.tar.gz /tmp/googletest-release-1.8.1.tar.gz && \
tar xf release-1.8.1.tar.gz && cd googletest-release-1.8.1 && \
cmake -DBUILD_SHARED_LIBS=ON -DCMAKE_INSTALL_PREFIX=/usr/local/gtest . && make -j && make install && \
cd .. && rm -rf release-1.8.1.tar.gz googletest-release-1.8.1