import os
import subprocess
import matplotlib.pyplot as plt
import numpy as np
import sys
import csv

# 1. 異なるデータサイズでSTREAMをコンパイル＆実行する
REPEAT = 10
DATA_SIZE = 2**25
thread_num = "20"

results = {}

# STREAMソースコードのパス（stream.cが存在するディレクトリ）
stream_source_path = "/home/date/tools/STREAM/stream.c"

# コンパイル設定（例: -O3最適化）
compiler = "icx"
compile_flags = "-O3 -qopenmp -mcmodel=large"
env = os.environ.copy()
env["OMP_NUM_THREADS"] = thread_num  # OMP_NUM_THREADS を設定
env["KMP_AFFINITY"] = "compact"#,granularity=core,1,0"  # OMP_NUM_THREADS を設定
elf = "/home/date/tools/STREAM/stream"


# DPU側で1-8並列で監視を実行するため、手作業で繰り返す
# 1GBでREPEAT回の平均を取る
for i in range(REPEAT):
    # コンパイル時に -DSTREAM_ARRAY_SIZE={size} を指定
    compile_command = (
        f"{compiler} {compile_flags} -DSTREAM_TYPE=double -DSTREAM_ARRAY_SIZE={DATA_SIZE} {stream_source_path} -o " + elf
    )
    # コンパイル
    subprocess.run(compile_command, shell=True, check=True)
    
    # 実行
    command = "numactl -l " + elf
    process = subprocess.run(command, shell=True, capture_output=True, text=True, env=env)
    output = process.stdout
    
    # 結果を解析して保存
    for line in output.splitlines():
        if "Copy:" in line:
            print(DATA_SIZE//2**17,line.split()[2])
            copy_result = float(line.split()[2])
        elif "Scale:" in line:
            scale_result = float(line.split()[2])
        elif "Add:" in line:
            add_result = float(line.split()[2])
        elif "Triad:" in line:
            triad_result = float(line.split()[2])
    
    # データサイズごとの結果を保存
    results[i] = {
        "Copy": copy_result,
        "Scale": scale_result,
        "Add": add_result,
        "Triad": triad_result,
    }
output_dir = "stream_latency_change_moni"
os.makedirs(output_dir, exist_ok=True)  # 結果保存用ディレクトリを作成


output_data = {}

result_file = os.path.join(output_dir, "result.txt")
for operation in ["Copy", "Scale", "Add", "Triad"]:
    output_data[operation] = {}
    avg_res = 0
    min_res = float('inf')
    max_res = float('-inf')
    for i in range(REPEAT):
        res = results[i][operation]
        avg_res += res
        if res < min_res:
            min_res = res
        if max_res < res:
            max_res = res
    
    output_data[operation]["avg"] = avg_res/REPEAT
    output_data[operation]["min"] = min_res
    output_data[operation]["max"] = max_res


# CSVファイルに出力
csv_file = os.path.join(output_dir, "result.csv")
with open(csv_file, "w", newline='') as csvfile:
    csvwriter = csv.writer(csvfile)
    # ヘッダーを書き込む
    csvwriter.writerow(["Operation", "Average (seconds)", "Minimum (seconds)", "Maximum (seconds)"])
    # データを書き込む
    for operation in ["Copy", "Scale", "Add", "Triad"]:
        csvwriter.writerow([
            operation,
            f"{output_data[operation]['avg']:.6f}",
            f"{output_data[operation]['min']:.6f}",
            f"{output_data[operation]['max']:.6f}"
        ])