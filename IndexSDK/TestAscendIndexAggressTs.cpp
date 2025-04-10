/*
 * Copyright(C) 2023. Huawei Technologies Co.,Ltd. All rights reserved.
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

 // 需要生成aicpu算子+flat算法512维算子+ mask算子
#include <algorithm>
#include <cstdio>
#include <cstdlib>
#include <future>
#include <iostream>
#include <memory>
#include <random>
#include <sys/stat.h>
#include <thread>
#include <atomic>
#include <cstring>
#include <securec.h>
#include <gtest/gtest.h>
#include <sys/time.h>
#include "faiss/ascend/AscendIndexFlat.h"
#include "faiss/ascend/AscendIndexTS.h"
#include "faiss/impl/AuxIndexStructures.h"

namespace {
    using idx_t = int64_t;
    using FeatureAttr = faiss::ascend::FeatureAttr;
    using AttrFilter = faiss::ascend::AttrFilter;
    const int DEVICE_ID = 0;

    inline double GetMillisecs()
    {
        struct timeval tv {
            0, 0
        };
        gettimeofday(&tv, nullptr);
        return tv.tv_sec * 1e3 + tv.tv_usec * 1e-3;
    }

    void FeatureGenerator(std::vector<float> &features)
    {
        size_t n = features.size();
        for (size_t i = 0; i < n; ++i) {
            features[i] = drand48();
        }
    }

    void FeatureAttrGenerator(std::vector<FeatureAttr> &attrs)
    {
        size_t n = attrs.size();
        int power = 4;
        for (size_t i = 0; i < n; ++i) {
            attrs[i].time = int32_t(i % power);
            attrs[i].tokenId = int32_t(i % power);
        }
    }
}

namespace faiss {
namespace ascend {
template <typename AggressParam>
class AscendAggressBase {
public:
    struct AggressPromisParam {
        std::promise<int32_t> retval;
        AggressParam param;
    };

    AscendAggressBase(uint32_t dim, int32_t core, std::initializer_list<uint16_t> supportBatch)
        : m_runningFlag(true), m_dim(dim), m_supportBatch(supportBatch)
    {
        m_workThread = std::move(std::thread(&AscendAggressBase::AggressWorkProcess, this));
        if (core != -1) {
            cpu_set_t cpuset;
            CPU_ZERO(&cpuset);
            CPU_SET(core, &cpuset);
            pthread_setaffinity_np(m_workThread.native_handle(), sizeof(cpu_set_t), &cpuset);
        }
    }

    virtual ~AscendAggressBase()
    {
        m_runningFlag.store(false, std::memory_order_acq_rel);
        m_workThread.join();
    }

    void SetCondWaitQueueLen(int queueLen)
    {
        m_waitQueueLen.store(queueLen, std::memory_order_release);
    }

    int32_t SearchWithAggres(AggressParam SearchParam)
    {
        if (!m_runningFlag.load(std::memory_order_acquire)) {
            return -1;
        }

        AggressPromisParam promisParam;
        promisParam.param = SearchParam;
        auto retval = promisParam.retval.get_future();
        {
            std::lock_guard<std::mutex> lk(m_mutex);
            m_queue.push_back(&promisParam);
            m_cond.notify_one();
        } // 解锁
        return retval.get();
    }

protected:
    // pure virtual function
    virtual int32_t AggressSearch(AggressParam *) = 0;
    virtual AggressParam *CreateBatchQueryData(
        std::vector<AggressPromisParam *> &batchQuery) = 0;
    virtual void DestoryBatchQueryData(AggressParam *batchQueryData) = 0;
    virtual void SpliceBatchQueryData(
        AggressParam *batchQueryData,
        std::vector<AggressPromisParam *> &batchQuery) = 0;

    uint32_t BatchPadding(std::vector<AggressPromisParam *> &batchQuery)
    {
        uint32_t paddingCnt = 0;
        AggressPromisParam *paddingValue = batchQuery[0];
        for (auto i : m_supportBatch) {
            if (i >= batchQuery.size()) {
                paddingCnt = i - batchQuery.size();
                break;
            }
        }

        for (auto i = 0u; i < paddingCnt; i++) {
            batchQuery.push_back(paddingValue);
        }
        return paddingCnt;
    }

    static void RemovePadding(std::vector<AggressPromisParam *> &batchQuery, uint32_t paddingCnt)
    {
        while (paddingCnt-- != 0) {
            batchQuery.pop_back();
        }
    }

    static void ReturnValue(std::vector<AggressPromisParam *> *batchQuery, int32_t ret)
    {
        std::for_each(batchQuery->begin(), batchQuery->end(),
            [ret](AggressPromisParam *query) {
                query->retval.set_value(ret);
            });
    }

    static void AgressSearchPorcess(AscendAggressBase *index, std::vector<AggressPromisParam *> *batchQuery)
    {
        std::unique_ptr<std::vector<AggressPromisParam *>> batchQueryScope(batchQuery);
        auto paddingCnt = index->BatchPadding(*batchQuery);

        // step3: 构造组合之后的查询数据
        auto deletor = [index](AggressParam *batchQueryData) {
            index->DestoryBatchQueryData(batchQueryData);
        };
        auto batchQueryData = std::unique_ptr<AggressParam, decltype(deletor)>(
            index->CreateBatchQueryData(*batchQuery), deletor);

        // step4: 调用原生search接口进行查询
        auto ret = index->AggressSearch(batchQueryData.get());
        RemovePadding(*batchQuery, paddingCnt);

        if (ret != 0) {
            ReturnValue(batchQuery, ret);
            return;
        }

        // step5: 分割查询之后的数据，并设置
        index->SpliceBatchQueryData(batchQueryData.get(), *batchQuery);

        // step6: 返回成功
        ReturnValue(batchQuery, ret);
    }

    bool GetBatchQuery(std::vector<AggressPromisParam *> *batchQuery)
    {
        std::unique_lock<std::mutex> lk(m_mutex);
        // step1: 等待条件满足 两个条件超时，或者队列超过阈值退出
        int waitTime = 15;
        m_cond.wait_for(lk, std::chrono::milliseconds(waitTime),
                        [this]() {
                            return m_queue.size() >=
                                    static_cast<size_t>(m_waitQueueLen.load(std::memory_order_acquire));
                        });

        if (m_queue.empty()) {
            return false;
        } // 解锁

        auto first = m_queue[0];
        auto filter = [first](AggressPromisParam *queryParam) {
            return first->param.CanGroup(queryParam->param);
        };

        std::copy_if(m_queue.begin(), m_queue.end(), std::back_inserter(*batchQuery), filter);
        m_queue.erase(std::remove_if(m_queue.begin(), m_queue.end(), filter), m_queue.end());
        return true;
    } // 解锁

    void AggressWorkProcess()
    {
        while (m_runningFlag.load(std::memory_order_acquire)) {
            auto *batchQuery = new std::vector<AggressPromisParam *>;
            if (!GetBatchQuery(batchQuery)) {
                delete batchQuery;
                continue;
            }

            auto task = std::thread(&AgressSearchPorcess, this, batchQuery);
            task.detach(); // 该线程交由promise进行关闭,这里detach
        }
    }

    std::thread m_workThread;
    std::vector<AggressPromisParam *> m_queue;
    std::atomic<bool> m_runningFlag;
    std::condition_variable m_cond;
    std::mutex m_mutex;

    uint32_t m_dim{0};
    std::atomic<int> m_waitQueueLen{1};
    std::vector<uint16_t> m_supportBatch;
};

struct AggressTsParam {
    uint32_t count{0};
    float *features{nullptr};
    AttrFilter *attrFilter{nullptr};
    bool shareAttrFilter{false};
    uint32_t topk{0};
    int64_t *labels{nullptr};
    float *distances{nullptr};
    uint32_t *validNums{nullptr};
    bool enableTimeFilter{false};

    // 用户需要实现CanGroup函数，组batch时将调用该函数进行判断是否能够组合成batch
    bool CanGroup(AggressTsParam &other) { return topk == other.topk; }
};

using AgressIndexBase = AscendAggressBase<AggressTsParam>;

// 继承聚合基类和时空索引基类 需要实现 构造聚合 分割聚合 销毁聚合三个函数
class AggressTsIndex : public AgressIndexBase, public AscendIndexTS {
public:
    explicit AggressTsIndex(uint32_t dim = 0, int32_t core = -1,
        std::initializer_list<uint16_t> supportBatch = {})
        : AgressIndexBase(dim, core, supportBatch), AscendIndexTS() {}

    ~AggressTsIndex() override = default;

private:
    // 该函数由线程任务调用
    int32_t AggressSearch(AggressTsParam *batchQueryData) override
    {
        // 调用AscendIndexTS search接口进行查询
        return Search(batchQueryData->count, batchQueryData->features,
            batchQueryData->attrFilter, batchQueryData->shareAttrFilter,
            batchQueryData->topk, batchQueryData->labels,
            batchQueryData->distances, batchQueryData->validNums,
            batchQueryData->enableTimeFilter);
    }

    // 构造聚合
    AggressTsParam *CreateBatchQueryData(std::vector<AggressPromisParam *> &batchQuery) override
    {
        AggressTsParam *batchQueryData = new AggressTsParam;
        batchQueryData->count = batchQuery.size();
        batchQueryData->features = new float[batchQueryData->count * m_dim];
        batchQueryData->attrFilter = new AttrFilter[batchQueryData->count];
        batchQueryData->shareAttrFilter = batchQuery[0]->param.shareAttrFilter;
        batchQueryData->topk = batchQuery[0]->param.topk;
        batchQueryData->labels =
            new int64_t[batchQueryData->count * batchQueryData->topk];
        batchQueryData->distances =
            new float[batchQueryData->count * batchQueryData->topk];
        batchQueryData->validNums = new uint32_t[batchQueryData->count];
        batchQueryData->enableTimeFilter = batchQuery[0]->param.enableTimeFilter;

        for (auto i = 0u; i < batchQueryData->count; i++) {
            auto ret = memcpy_s(batchQueryData->features + i * m_dim,
                m_dim * sizeof(float), batchQuery[i]->param.features, m_dim * sizeof(float));
            if (ret != 0) {
                std::cerr << "ERROR: fail to memcpy features" << std::endl;
            }
            ret = memcpy_s(batchQueryData->attrFilter + i, sizeof(AttrFilter),
                batchQuery[i]->param.attrFilter, sizeof(AttrFilter));
            if (ret != 0) {
                std::cerr << "ERROR: fail to memcpy attrFilter" << std::endl;
            }
        }
        return batchQueryData;
    }

    // 分割聚合
    void SpliceBatchQueryData(AggressTsParam *batchQueryData,
        std::vector<AggressPromisParam *> &batchQuery) override
    {
        for (auto i = 0u; i < batchQuery.size(); i++) {
            auto ret = memcpy_s(batchQuery[i]->param.labels,
                batchQueryData->topk * sizeof(int64_t),
                batchQueryData->labels + i * batchQueryData->topk,
                batchQueryData->topk * sizeof(int64_t));
            if (ret != 0) {
                std::cerr << "ERROR: fail to memcpy label" << std::endl;
                return;
            }
            ret = memcpy_s(batchQuery[i]->param.distances,
                batchQueryData->topk * sizeof(float),
                batchQueryData->distances + i * batchQueryData->topk,
                batchQueryData->topk * sizeof(float));
            if (ret != 0) {
                std::cerr << "ERROR: fail to memcpy distances" << std::endl;
                return;
            }
            *(batchQuery[i]->param.validNums) = batchQueryData->validNums[i];
        }
    }

    // 销毁聚合
    void DestoryBatchQueryData(AggressTsParam *batchQueryData) override
{
    if (batchQueryData->features != nullptr) {
        delete[] (batchQueryData->features);
    }
    if (batchQueryData->attrFilter != nullptr) {
        delete[] (batchQueryData->attrFilter);
    }
    if (batchQueryData->labels != nullptr) {
        delete[] (batchQueryData->labels);
    }
    if (batchQueryData->distances != nullptr) {
        delete[] (batchQueryData->distances);
    }
    if (batchQueryData->validNums != nullptr) {
        delete[] (batchQueryData->validNums);
    }
    delete batchQueryData;
}
};
}
}

void InitAndAdd(uint32_t dim, idx_t ntotal, uint32_t tokenNum,
    faiss::ascend::AggressTsIndex *tsIndex, std::vector<float>& features)
{
    auto res = tsIndex->Init(DEVICE_ID, dim, tokenNum, faiss::ascend::AlgorithmType::FLAT_IP_FP16);
    EXPECT_EQ(res, 0);
    printf("[---add ---------]\n");
    FeatureGenerator(features);

    std::vector<int64_t> labels;
    for (int i = 0; i < ntotal; ++i) {
        labels.push_back(i);
    }

    std::vector<FeatureAttr> attrs(ntotal);
    FeatureAttrGenerator(attrs);
    auto ts = GetMillisecs();
    res = tsIndex->AddFeature(ntotal, features.data(), attrs.data(), labels.data());
    auto te = GetMillisecs();
    printf("add %ld cost %f ms\n", ntotal, te - ts);
    EXPECT_EQ(res, 0);
    int64_t validNum = 0;
    tsIndex->GetFeatureNum(&validNum);
    EXPECT_EQ(validNum, ntotal);
}

TEST(TestAscendIndexAggressTS, search)
{
    uint32_t dim = 512;
    uint32_t tokenNum = 2500;
    idx_t ntotal = 100000;
    int queryNums = 100;
    std::vector<int> topks = {100};
    std::vector<float> features(ntotal * dim);
    faiss::ascend::AggressTsIndex *tsIndex = new faiss::ascend::AggressTsIndex(dim);
    InitAndAdd(dim, ntotal, tokenNum, tsIndex, features);

    for (auto k : topks)
    {
        std::vector<float> distances(queryNums * k, -1);
        std::vector<int64_t> labelRes(queryNums * k, 10);
        std::vector<float> faissDistances(queryNums * k, -1);
        std::vector<int64_t> faissLabelRes(queryNums * k, 10);
        std::vector<uint32_t> validNum(queryNums, 0);
        uint32_t size = queryNums * dim;
        std::vector<float> querys(size);
        querys.assign(features.begin(), features.begin() + size);

        uint32_t setlen = (uint32_t)((tokenNum + 7) / 8);
        std::vector<uint8_t> bitSet(setlen, 0);

        // 00001111
        bitSet[0] = 0x1 << 0 | 0x1 << 1 | 0x1 << 2 | 0x1 << 3;
        AttrFilter filter{};
        filter.timesStart = 0;
        filter.timesEnd = 3;
        filter.tokenBitSet = bitSet.data();
        filter.tokenBitSetLen = setlen;

        std::vector<AttrFilter> queryFilters(queryNums, filter);
        std::vector<std::future<int32_t>> searchGroup;

        for (auto query = 0; query < queryNums; query++)
        {
            faiss::ascend::AggressTsParam params;
            params.count = 1;
            params.features = querys.data() + query * dim;
            params.attrFilter = queryFilters.data() + query;
            params.topk = k;
            params.labels = labelRes.data() + query * k;
            params.distances = distances.data() + query * k;
            params.validNums = validNum.data() + query;
            params.enableTimeFilter = false;

            // 异步调用 组batch
            searchGroup.emplace_back(
                std::async(std::launch::async, &faiss::ascend::AggressTsIndex::SearchWithAggres, tsIndex, params));
        }

        std::for_each(searchGroup.begin(), searchGroup.end(), [](std::future<int32_t> &task) {
            auto ret = task.get();
            EXPECT_EQ(ret, 0);
        });
    }

    delete tsIndex;
}

int main(int argc, char **argv)
{
    testing::InitGoogleTest(&argc, argv);

    return RUN_ALL_TESTS();
}