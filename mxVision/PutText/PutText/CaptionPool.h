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
#ifndef CAPTIONPOOL_H
#define CAPTIONPOOL_H

#include <iostream>
#include <list>
#include <unordered_map>
#include "MxBase/MxBase.h"

template <typename K, typename V>
class LimitedSizeMap {
public:
    LimitedSizeMap(size_t max_size) : max_size(max_size) {}

    void put(const K& key, const V& value) {
        if (map.find(key) == map.end()) {
            if (order.size() >= max_size) {
                K oldest = order.front();
                order.pop_front();
                map.erase(oldest);
            }
            order.push_back(key);
        } else {
            order.remove(key);
            order.push_back(key);
        }
        map[key] = value;
    }

    bool get(const K& key, V& value) {
        if (map.find(key) != map.end()) {
            value = map[key];
            return true;
        }
        return false;
    }

    bool isExist(const K& key) {
        if (map.find(key) != map.end()) {
            return true;
        }
        return false;
    }

private:
    size_t max_size;
    std::list<K> order;
    std::unordered_map<K, V> map;
};

class CaptionPool {
public:
    APP_ERROR putCaptionAndMask(std::string text1, std::string text2, MxBase::Tensor caption, MxBase::Tensor mask);

    APP_ERROR getCaptionAndMask(std::string text1, std::string text2, MxBase::Tensor& caption, MxBase::Tensor& mask);
    

    bool isCaptionExist(std::string text1, std::string text2);

    APP_ERROR putCaptionLength(std::string text, int length);

    APP_ERROR getCaptionLength(std::string text, int& length);

    bool isCaptionLengthExist(std::string text);

private:
    LimitedSizeMap<std::string, MxBase::Tensor> text2CaptionMap_ = LimitedSizeMap<std::string, MxBase::Tensor>(10);
    LimitedSizeMap<std::string, MxBase::Tensor> text2MaskMap_ = LimitedSizeMap<std::string, MxBase::Tensor>(10);
    LimitedSizeMap<std::string, int> text2Lenghth_ = LimitedSizeMap<std::string, int>(10);
};

#endif