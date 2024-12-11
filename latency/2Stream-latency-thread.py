import os
import subprocess
import matplotlib.pyplot as plt
import numpy as np

# 1. 異なるデータサイズでSTREAMをコンパイル＆実行する
#data_sizes = [2**i for i in range(17, 33)]  # 2^17 (1M(size x double(8byte))) から 2^32 (32GB) まで
data_size = 2**24 #128MB L3(25M)
thread_nums = [str(i) for i in range(1,21)]

results = {}

# STREAMソースコードのパス（stream.cが存在するディレクトリ）
stream_source_path = "/home/date/tools/STREAM/stream.c"

# コンパイル設定（例: -O3最適化）
compiler = "icx"
compile_flags = "-O3 -qopenmp -mcmodel=large"

env = os.environ.copy()
env["KMP_AFFINITY"] = "compact -mavx2"#,granularity=core,1,0"  # OMP_NUM_THREADS を設定
env["KMP_AFFINITY"] = "compact"#,granularity=core,1,0"  # OMP_NUM_THREADS を設定, numactl -lと同じ
#env["KMP_AFFINITY"] = "scatter"  # OMP_NUM_THREADS を設定

elf = "/home/date/tools/STREAM/stream"

# 実行してデータを収集
for thread_num in thread_nums:
    env["OMP_NUM_THREADS"] = thread_num  # OMP_NUM_THREADS を設定
    # コンパイル時に -DSTREAM_ARRAY_SIZE={size} を指定
    compile_command = (
        f"{compiler} {compile_flags} -mavx2 -DSTREAM_TYPE=double -DSTREAM_ARRAY_SIZE={data_size} {stream_source_path} -o " + elf
    )
    # コンパイル
    subprocess.run(compile_command, shell=True, check=True,env=env)
    
    # 実行
    process = subprocess.run(elf, shell=True, capture_output=True, text=True, env=env)
    output = process.stdout
    
    # 結果を解析して保存
    for line in output.splitlines():
        if "Copy:" in line:
            print(thread_num,line.split()[2])
            copy_result = float(line.split()[2])
        elif "Scale:" in line:
            scale_result = float(line.split()[2])
        elif "Add:" in line:
            add_result = float(line.split()[2])
        elif "Triad:" in line:
            triad_result = float(line.split()[2])
    
    # データサイズごとの結果を保存
    results[thread_num] = {
        "Copy": copy_result,
        "Scale": scale_result,
        "Add": add_result,
        "Triad": triad_result,
    }

# 2. 折れ線グラフを作成
def plot_results(results, operation):
    # 2. 折れ線グラフを作成してPNG形式で保存
    output_dir = f"stream_latency_{str(data_size//2**17)}M"
    os.makedirs(output_dir, exist_ok=True)  # 結果保存用ディレクトリを作成

    values = [results[thread_num][operation] for thread_num in thread_nums]
    
    plt.figure(figsize=(10, 6))
    plt.plot(thread_nums, values, marker='o', color='blue', linewidth=2)
    plt.title(f"STREAM {operation} Performance")
    plt.xlabel("# of thread")
    plt.ylabel("Avg latency (GB/s)")
    plt.grid(True, which="both", linestyle='--', linewidth=0.5)
    plt.ylim(0, max(values) * 1.2)  # Y軸の余白を少し広げる
    
    # ファイル名を設定して保存
    output_file = os.path.join(output_dir, f"stream_{operation.lower()}.png")
    plt.savefig(output_file)
    plt.close()
    print(f"Saved {operation} plot to {output_file}")

# Copy, Scale, Add, Triadごとにプロット
for operation in ["Copy", "Scale", "Add", "Triad"]:
    plot_results(results, operation)
