/*
 * Copyright(C) 2024. Huawei Technologies Co.,Ltd. All rights reserved.
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

// 需要生成aicpu算子+int8flat算子(-d 64)

#include <random>
#include <iostream>
#include <sys/time.h>
#include <gtest/gtest.h>
#include <faiss/ascend/AscendIndexInt8Flat.h>
#include <faiss/ascend/AscendCloner.h>
#include <faiss/ascend/custom/IReduction.h>
#include <faiss/impl/AuxIndexStructures.h>
#include <faiss/Clustering.h>
#include <faiss/index_io.h>


namespace {
using recallMap = std::unordered_map<int, float>;
const int SEARCH_NUM = 1;
const int MILLI_SECOND = 1000;
inline double GetMillisecs()
{
    struct timeval tv {
        0, 0
    };
    gettimeofday(&tv, nullptr);
    return tv.tv_sec * 1e3 + tv.tv_usec * 1e-3;
}

inline void AssertInt8Equal(size_t count, const int8_t *gt, const int8_t *data)
{
    for (size_t i = 0; i < count; i++) {
        ASSERT_TRUE(gt[i] == data[i]) << "i: " << i << " gt: " << int(gt[i]) << " data: " << int(data[i]) << std::endl;
    }
}

inline void sqEncode(const faiss::ScalarQuantizer sq, const float *base, int8_t *baseInt8, const size_t n)
{
    int offset = 128;
    std::vector<uint8_t> queryUint8(n * sq.code_size);
    sq.compute_codes(base, queryUint8.data(), n);
    for (size_t i = 0; i < n * sq.code_size; i++) {
        baseInt8[i] = queryUint8[i] - offset;
    }
}

void ReduceData(size_t ntotal, int dimIn, int dimOut, std::vector<int8_t>& baseInt8,
    std::vector<int8_t>& queryInt8)
{
    float trainRatio = 0.01;
    int trainNum = ntotal * trainRatio;
    printf("generate data\n");
    std::vector<float> base(ntotal * dimIn);
    std::vector<float> baseOut(ntotal * dimOut);
    for (size_t i = 0; i < ntotal * dimIn; i++) {
            base[i] = drand48();
    }
    // create Pcar IReduction
    faiss::ascend::ReductionConfig reductionConfig(dimIn, dimOut, 0, true);
    std::string method = "PCAR";
    faiss::ascend::IReduction *reduction = CreateReduction(method, reductionConfig);
    // train reduction
    reduction->train(trainNum, base.data());

    // start reduction
    reduction->reduce(ntotal, base.data(), baseOut.data());

    // start scalarQuantizer float -> int8
    faiss::ScalarQuantizer sq = faiss::ScalarQuantizer(dimOut, faiss::ScalarQuantizer::QuantizerType::QT_8bit);
    sq.train(trainNum, baseOut.data());
    sqEncode(sq, baseOut.data(), baseInt8.data(), ntotal);

    std::vector<float> query(SEARCH_NUM * dimIn);
    std::vector<float> queryOut(SEARCH_NUM * dimOut);
    
    for (int i = 0; i < SEARCH_NUM * dimIn; i++) {
        query[i] = drand48();
    }
    reduction->reduce(SEARCH_NUM, query.data(), queryOut.data());
    sqEncode(sq, queryOut.data(), queryInt8.data(), SEARCH_NUM);
    delete reduction;
}

TEST(TestAscendIndexInt8Flat, QPS)
{
    int dimIn = 256;
    int dimOut = 64;
    size_t ntotal = 7000000;
    try {
        std::vector<int8_t> baseInt8(ntotal * dimOut);
        std::vector<int8_t> queryInt8(SEARCH_NUM * dimOut);
    
        ReduceData(ntotal, dimIn, dimOut, baseInt8, queryInt8);
    
        // create index
        faiss::ascend::AscendIndexInt8FlatConfig conf({ 0 }, 1024 * 1024 * 1024);
        faiss::ascend::AscendIndexInt8Flat index(dimOut, faiss::METRIC_INNER_PRODUCT, conf);
        index.verbose = true;
    
        printf("add data\n");
        index.add(ntotal, baseInt8.data());
    
        int warmUpTimes = 10 ;
        std::vector<float> distw(127 * 10, 0);
        std::vector<faiss::idx_t> labelw(127 * 10, 0);
        for (int i = 0; i < warmUpTimes; i++) {
            index.search(127, baseInt8.data(), 10, distw.data(), labelw.data());
        }
        
        int k = 100;
        int loopTimes = 10;
        std::vector<float> dist(SEARCH_NUM * k, 0);
        std::vector<faiss::idx_t> label(SEARCH_NUM * k, 0);
    
        double ts = GetMillisecs();
        for (int l = 0; l < loopTimes; l++) {
            // query data reduction and sq
            index.search(SEARCH_NUM, queryInt8.data(), k, dist.data(), label.data());
        }
        double te = GetMillisecs();
        printf("base:%zu, dim:%d, search num:%d, topk:%d, QPS:%.4f\n", ntotal, dimOut, SEARCH_NUM,
            k, MILLI_SECOND * SEARCH_NUM * loopTimes / (te - ts));
    } catch (std::exception &e) {
        printf("%s\n", e.what());
        throw std::exception();
    }
}

} // namespace

int main(int argc, char **argv)
{
    testing::InitGoogleTest(&argc, argv);

    return RUN_ALL_TESTS();
}
