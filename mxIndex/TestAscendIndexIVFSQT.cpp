/*
 * Copyright(C) 2020. Huawei Technologies Co.,Ltd. All rights reserved.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

#include <algorithm>
#include <cmath>
#include <iostream>
#include <vector>
#include <random>
#include <cfloat>
#include <sys/time.h>

#include <faiss/ascend/custom/AscendIndexIVFSQT.h>
#include <faiss/ascend/AscendCloner.h>
#include <faiss/index_io.h>

using namespace std;

void Norm(float *data, size_t n, size_t dim)
{
#pragma omp parallel for if(n > 100)
    for (size_t i = 0; i < n; ++i) {
        float l2norm = 0;
        for (size_t j = 0; j < dim; ++j) {
            l2norm += data[i * dim + j] * data[i * dim + j];
        }
        l2norm = sqrt(l2norm);
        if (fabs(l2norm) < FLT_EPSILON) {
            std::cerr << "Error: Invalid l2norm value." << std::endl;
        }
        for (size_t j = 0; j < dim; ++j) {
            data[i * dim + j] = data[i * dim + j] / l2norm;
        }
    }
}

const size_t DIM_IN = 256;
const size_t DIM_OUT = 64;
const float THRESHOLD = 1.5;
const size_t ADD_TOTAL = 6000000;

const int FUZZYK = 3;
const size_t K = 100;
const size_t QUERY_NUM = 500000;
const std::vector<int> DEVICE = {0};
const int FAST_RAND_MAX = 0x7FFF;
unsigned int g_seed = 5678;
inline int FastRand(void)
{
    const int mutipliyNum = 214013;
    const int addNum = 2531011;
    const int rshiftNum = 16;
    g_seed = (mutipliyNum * g_seed + addNum);
    return (g_seed >> rshiftNum) & FAST_RAND_MAX;
}

inline double GetMillisecs()
{
    struct timeval tv {
        0, 0
    };
    gettimeofday(&tv, nullptr);
    return tv.tv_sec * 1e3 + tv.tv_usec * 1e-3;
}

void TestAscendToCpu(faiss::ascend::AscendIndexIVFSQT *index, std::vector<float>& data,
    std::vector<float>& dist, std::vector<faiss::idx_t>& label)
{
    const char *globalFileName = "IVFSQT.faiss";
    cout << "Test index_ascend_to_cpu For IVFSQT, result save to " << globalFileName << endl;
    faiss::Index *cpuIndex = faiss::ascend::index_ascend_to_cpu(index);
    faiss::write_index(cpuIndex, globalFileName);
    delete cpuIndex;
    cout << "Test index_ascend_to_cpu For IVFSQT finished" << endl;

    cout << "Test index_cpu_to_ascend For IVFSQT, read from " << globalFileName << endl;
    faiss::Index *initIndex = faiss::read_index(globalFileName);
    faiss::ascend::AscendIndexIVFSQT *realIndex =
        dynamic_cast<faiss::ascend::AscendIndexIVFSQT *>(faiss::ascend::index_cpu_to_ascend(
            DEVICE, initIndex));
    cout << "Test index_cpu_to_ascend For IVFSQT, finished" << endl;
    realIndex->search(QUERY_NUM, data.data(), K, dist.data(), label.data());

    delete realIndex;
    delete initIndex;
}

int main(int argc, char **argv)
{
    const size_t nlist = 16384;
    const size_t trainTotal = 2000000;
    const int niter = 16;
    const int centroids = 256;

    std::vector<float> data(DIM_IN * ADD_TOTAL);
    cout << "generate data" << endl;
    for (size_t i = 0; i < data.size(); i++) {
        data[i] = 1.0 * FastRand() / FAST_RAND_MAX;
    }

    Norm(data.data(), ADD_TOTAL, DIM_IN);

    faiss::ascend::AscendIndexIVFSQT *index = nullptr;
    try {
        cout << "index start" << endl;
        faiss::ascend::AscendIndexIVFSQTConfig conf({DEVICE});
        conf.cp.niter = niter;
        conf.useKmeansPP = true;
        conf.cp.max_points_per_centroid = centroids;
        cout << "index init" << endl;

        index = new faiss::ascend::AscendIndexIVFSQT(DIM_IN, DIM_OUT, nlist,
            faiss::ScalarQuantizer::QuantizerType::QT_8bit, faiss::MetricType::METRIC_INNER_PRODUCT, conf);

        index->verbose = true;
        index->setFuzzyK(FUZZYK);
        index->setThreshold(THRESHOLD);

        cout << "train start" << endl;
        index->train(trainTotal, data.data());

        cout << "add start" << endl;
        index->add(ADD_TOTAL, data.data());

        cout << "update start" << endl;
        index->update();

        cout << "search start" << endl;
        std::vector<float> dist(QUERY_NUM * K, 0.0);
        std::vector<faiss::idx_t> label(QUERY_NUM * K, 0);

        double start = GetMillisecs();
        index->search(QUERY_NUM, data.data(), K, dist.data(), label.data());
        double end = GetMillisecs();
        cout << "search finished successfully" << endl;
        cout << "search time cost:" << end - start << " ms" << endl;
        TestAscendToCpu(index, data, dist, label);
        delete index;
    } catch (faiss::FaissException& e) {
        cout << "Exception caught!" << e.what() << endl;
        if (index == nullptr) {
            delete index;
        }
        return -1;
    }

    return 0;
}
