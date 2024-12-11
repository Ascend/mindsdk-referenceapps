/*
 * Copyright (c) Huawei Technologies Co., Ltd. 2024-2024. All rights reserved.
 * Description: ConfigParser implementation.
 * Author: MindX SDK
 * Create: 2024
 * History: NA
 */

#ifndef MINDX_SDK_SAMPLE_CONFIGPARSER_H
#define MINDX_SDK_SAMPLE_CONFIGPARSER_H

#include <map>
#include <string>
#include <fstream>
#include <iostream>
#include "MxBase/MxBase.h"


class ConfigParser {
public:
    // Read the config file and save the useful infomation with the key-value pairs format in configData_
    APP_ERROR ParseConfig(const std::string &fileName);

    // Get the string value by key name
    APP_ERROR GetStringValue(const std::string &name, std::string &value) const;

    // Get the unsigned int value by key name
    APP_ERROR GetUnsignedIntValue(const std::string &name, unsigned int &value) const;


private:
    std::map<std::string, std::string> configData_ = {}; // Variable to store key-value pairs
    // Remove spaces from both left and right based on the string
    inline void Trim(std::string &str) const;
};

#endif