"""
Copyright 2026 Huawei Technologies Co., Ltd

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

import os
import sys

def split_jsonl(input_file, train_file=None, test_file=None, split_ratio=0.8):
    """
    Split a JSONL file into train/test sets sequentially.
    """
    # Check input file
    if not os.path.isfile(input_file):
        raise FileNotFoundError(f"Input file not found: {input_file}")

    # Validate split ratio
    if not (0.0 <= split_ratio <= 1.0):
        raise ValueError(f"split_ratio must be between 0.0 and 1.0, got {split_ratio}")

    # Generate default output names if not provided
    base, ext = os.path.splitext(input_file)
    if train_file is None:
        train_file = f"{base}-train{ext}"
    if test_file is None:
        test_file = f"{base}-test{ext}"

    # Read all lines
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception as e:
        raise IOError(f"Error reading input file: {e}") from e
    
    total = len(lines)
    split_idx = int(total * split_ratio)

    train_lines = lines[:split_idx]
    test_lines = lines[split_idx:]

    print(f"Total lines: {total}")
    print(f"Training lines: {len(train_lines)} ({split_ratio*100:.1f}%)")
    print(f"Test lines: {len(test_lines)} ({(1-split_ratio)*100:.1f}%)")

    # Write training file
    try:
        with open(train_file, 'w', encoding='utf-8') as f:
            f.writelines(train_lines)
        print(f"Training file saved: {train_file}")
    except Exception as e:
        raise IOError(f"Error writing training file: {e}") from e

    # Write test file
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            f.writelines(test_lines)
        print(f"Test file saved: {test_file}")
    except Exception as e:
        raise IOError(f"Error writing test file: {e}") from e

def main():
    # Simple command line parsing
    # Usage: python script.py input.jsonl [train.jsonl] [test.jsonl] [ratio]
    args = sys.argv[1:]
    if len(args) < 1:
        print("Usage: python split_jsonl.py <input_file> [train_file] [test_file] [split_ratio]")
        print("Example: python split_jsonl.py data.jsonl train.jsonl test.jsonl 0.9")
        return

    input_file = args[0]
    train_file = args[1] if len(args) > 1 else None
    test_file = args[2] if len(args) > 2 else None
    split_ratio = float(args[3]) if len(args) > 3 else 0.8

    split_jsonl(input_file, train_file, test_file, split_ratio)


if __name__ == "__main__":
    main()