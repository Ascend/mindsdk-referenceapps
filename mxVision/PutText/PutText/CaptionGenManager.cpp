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

#include <vector>
#include <iostream>
#include <sys/stat.h>
#include <opencv2/core.hpp>
#include <opencv2/imgcodecs.hpp>
#include "CaptionGenManager.h"

using namespace std;

const std::string UNK_SYMBOL = "?";
const std::string DELIM = "+";
struct FontFile{
    std::string fontName;
    std::string fontSize;
};
//以下关于字符管理的常量需自行配置
static const std::string FONT_DIR_PATH = "../vocab/";
static const FontFile timesNewRoman = {"times", "60px"};
static const FontFile simsun = {"simsun", "60px"};
FontFile FONT_LIST[] = {timesNewRoman, simsun};
int FONT_NUMBER = sizeof(FONT_LIST) / sizeof(FONT_LIST[0]);

CaptionGenManager::CaptionGenManager()
{
    bool success = this->Init();
    if (!success) {
        throw std::runtime_error("Can not init CaptionGenManager!");
    }
}

bool CaptionGenManager::Init()
{
    //支持加载多个字库
    for (int i = 0; i < FONT_NUMBER; i++) {
        // 根据字体名构造字体的配置文件路径
        std::string fontSize = FONT_LIST[i].fontSize;
        std::string vocabFilePath = FONT_DIR_PATH + FONT_LIST[i].fontName + "_" + fontSize + ".txt";
        std::string vocabImageFilePath = FONT_DIR_PATH + FONT_LIST[i].fontName + "_" + fontSize + ".bin";
        FontInfo fontInfo;
        fontInfo.name = FONT_LIST[i].fontName;
        if (!_checkFileExists(vocabFilePath)) {
            LogError << "The vocab txt file (" << vocabFilePath << ") is not a regular file or not exists.";
            return false;
        }
        if (!_checkFileExists(vocabImageFilePath)) {
            LogError << "The vocab image file (" << vocabImageFilePath << ") is not a regular file or not exists.";
            return false;
        }
        // 加载词典
        bool success = _loadVocab(vocabFilePath, fontInfo);
        if (!success) {
            LogError << "Fail to find vocabFilePath!";
            continue;
        }
        // 加载词典图片
        cv::Mat vocabImage;
        success = _loadMapBin(vocabImageFilePath, vocabImage, fontInfo, std::stoi(fontSize.substr(0, fontSize.size()-2)));
        if (!success) {
            LogError << "Load vocab Image fail.";
            continue;
        }
        // 读取原始图片
        std::vector<uint32_t> hsize_vec;
        hsize_vec.push_back(vocabImage.rows);
        hsize_vec.push_back(vocabImage.cols);
        hsize_vec.push_back(1);
        std::vector<uint8_t> src(vocabImage.reshape(0, 1));
        MxBase::Tensor vocabImageNpu(src.data(), hsize_vec, MxBase::TensorDType::UINT8, -1);
        vocabImageNpu.ToDevice(0);
        fontInfo.vocabImage = vocabImageNpu;
        // 词典和字库图片均加载成功，则放入fontsInfo库中，供后续使用
        fontsInfo_[FONT_LIST[i].fontName + fontSize] = fontInfo;
        LogInfo << "Successfully load font: " << FONT_LIST[i].fontName;
    }
    if (fontsInfo_.empty()) {
        LogError << "No available font.";
        return false;
    }
    return true;
}

/**
 * 判断字体是否合法
 * 根据在fontsInfo库中是否有font这个key判断
 **/
bool CaptionGenManager::isFontValid(const std::string &font, const std::string &fontSize)
{
    return fontsInfo_.count(font + fontSize);
}

/**
 * 检查字符的index
 * @param font: 字体，前面已经对异常字体进行处理，此处不需要判空
 * @param item: 被查找的字符，词典中没有该字符则以UNK_SYMBOL代替
 **/
int CaptionGenManager::FindIndex(const std::string &font, const std::string &fontSize, const std::string &item)
{
    if (fontsInfo_[font + fontSize].vocab.find(item) != fontsInfo_[font + fontSize].vocab.end()) {
        return fontsInfo_[font + fontSize].vocab[item];
    } else {
        // 字符中找不到的token，全用UNK_SYMBOL表示
        return FindIndex(font, fontSize, UNK_SYMBOL);
    }
}

/**
 * 检查字符在字库图片中的宽度
 * @param font： 字体，不同字体宽度不同
 * @param index: 待检索字符的index
 **/
int CaptionGenManager::FindWidth(const std::string &font, const std::string &fontSize, const int index)
{
    if (fontsInfo_[font + fontSize].wordWidth.find(index) != fontsInfo_[font + fontSize].wordWidth.end()) {
        return fontsInfo_[font + fontSize].wordWidth[index];
    } else {
        return FindWidth(font, fontSize, FindIndex(font, fontSize, UNK_SYMBOL));
    }
}

/**
 * 检查字符在字库图片中的高度
 * @param font： 字体，不同字体宽度不同
 * @param index: 待检索字符的index
 **/
int CaptionGenManager::FindHeight(const std::string &font, const std::string &fontSize)
{
    return fontsInfo_[font + fontSize].wordHeight;
}

// std::string 去除尾 \r, \n, \t
std::string RemoveRnt(std::string s)
{
    size_t n = s.find_last_not_of(" \r\n\t");
    if (n != std::string::npos) {
        s.erase(n + 1, s.size() - n);
    }
    return s;
}

std::vector<std::string> split(const std::string &str, const std::string &delim) // 将分割后的子字符串存储在vector中
{
    if (delim.size() == 0) {
        return {str};
    }
    std::vector<std::string> res;
    if (str.empty()) return res;

    std::string strs = str + delim; // ******扩展字符串以方便检索最后一个分割出的字符串
    size_t pos;
    size_t size = 80; // 预期的打点 当前为8

    for (uint i = 0; i < size; ++i) {
        pos = strs.find(delim, i);  // pos为分隔符第一次出现的位置，从i到pos之前的字符串是分隔出来的字符串
        if (pos < size) {  // 如果查找到，如果没有查找到分隔符，pos为string::npos
            std::string s = strs.substr(i, pos - i);  // ****从i开始长度为pos-i的子字符串
            res.push_back(s);  // 两个连续空格之间切割出的字符串为空字符串，这里没有判断s是否为空，所以最后的结果中有空字符的输出
            i = (uint) (pos + delim.size() - 1);
        }
    }
    return res;
}

// 读入文本文件到内存对象中
bool CaptionGenManager::_loadVocab(const std::string &vocabFile, FontInfo &singleFont)
{
    std::ifstream fin(vocabFile, std::ios::in);
    std::string word;

    if (!fin.is_open()) {
        LogError << "Unable to read file " << vocabFile;
        return false;
    }
    int index = 0;
    while (getline(fin, word)) {
        // 每一行按+号拆分成数组
        std::vector<std::string> split_words = split(word, DELIM);
        singleFont.vocab[RemoveRnt(split_words[0])] = index;
        singleFont.wordWidth[index] = std::stoi(split_words[1]);
        singleFont.wordHeight = std::stoi(split_words[2]);
        index++;
    }
    singleFont.wordNum = index;
    LogInfo << "nvocab.size(): " << singleFont.vocab.size();
    LogInfo << "wordWidth.size(): " << singleFont.wordWidth.size();
    fin.close();
    LogInfo << "Successfully load vocab file.";
    LogInfo << "Vocab length = " << singleFont.vocab.size();
    return true;
}

bool CaptionGenManager::_loadMapBin(const std::string &filePath, cv::Mat &map, FontInfo &singleFont, int imageCols)
{
    const char *filenamechar = filePath.c_str();
    FILE *fpr = fopen(filenamechar, "rb");
    if (fpr == nullptr) {
        LogError << "_loadMapBin can not open the file " << filePath << ".";
        return false;
    }
    int channels = 1;
    int type = 0;
    int vocabImageRows = singleFont.wordHeight * singleFont.wordNum;
    map = cv::Mat::zeros(vocabImageRows, imageCols, type);
    auto *pData = (uchar *) map.data;
    for (int i = 0; i < vocabImageRows * imageCols; i++) {
        fread(&pData[i], sizeof(uchar), 1, fpr);
    }
    fclose(fpr);
    LogInfo << "Read vocab image over. Channel is " << channels << ", type is " << type << ". rows is " << vocabImageRows << ", cols is" << imageCols << ".";
    return true;
}

// 返回字体图片
MxBase::Tensor CaptionGenManager::getVocabImage(const std::string &font, const std::string &fontSize)
{
    if (fontsInfo_.count(font + fontSize) > 0) {
        return fontsInfo_[font + fontSize].vocabImage;
    }
    MxBase::Tensor emptyTensor;
    return emptyTensor;
}

bool CaptionGenManager::_checkFileExists(const std::string &filePath)
{
    struct stat buffer;
    return (stat(filePath.c_str(), &buffer) == 0);
}

void CaptionGenManager::DeInit()
{
    fontsInfo_.clear();
}