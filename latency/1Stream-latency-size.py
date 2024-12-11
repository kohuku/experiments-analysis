import os
import subprocess
import matplotlib.pyplot as plt
import numpy as np
import sys

# 1. 異なるデータサイズでSTREAMをコンパイル＆実行する
data_sizes = [2**i for i in range(17, 33)]  # 2^17 (1M(size x double(8byte))) から 2^32 (32GB) まで
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

# 実行してデータを収集
for size in data_sizes:
    # コンパイル時に -DSTREAM_ARRAY_SIZE={size} を指定
    compile_command = (
        f"{compiler} {compile_flags} -DSTREAM_TYPE=double -DSTREAM_ARRAY_SIZE={size} {stream_source_path} -o " + elf
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
            print(size//2**17,line.split()[2])
            copy_result = float(line.split()[2])
        elif "Scale:" in line:
            scale_result = float(line.split()[2])
        elif "Add:" in line:
            add_result = float(line.split()[2])
        elif "Triad:" in line:
            triad_result = float(line.split()[2])
    
    # データサイズごとの結果を保存
    results[size//(2**17)] = {
        "Copy": copy_result,
        "Scale": scale_result,
        "Add": add_result,
        "Triad": triad_result,
    }
output_dir = "stream_latency_change_size"
# 2. 折れ線グラフを作成
def plot_results(results, operation):
    # 2. 折れ線グラフを作成してPNG形式で保存
    
    os.makedirs(output_dir, exist_ok=True)  # 結果保存用ディレクトリを作成

    sizes = sorted(results.keys())
    values = [results[size][operation] for size in sizes]
    
    plt.figure(figsize=(10, 6))
    plt.plot(sizes, values, marker='o', color='blue', linewidth=2)
    plt.xscale('log', base=2)  # x軸を2の対数スケールに設定
    plt.title(f"STREAM {operation} Performance")
    plt.xlabel("Data Size (MB, log scale)")
    plt.ylabel("Bandwidth (GB/s)")
    plt.grid(True, which="both", linestyle='--', linewidth=0.5)
    plt.ylim(0, max(values) * 1.2)  # Y軸の余白を少し広げる
    
    # x軸のラベルを調整
    plt.xticks(sizes, labels=[str(size) for size in sizes])  # 実際のサイズ値をラベルとして設定
    # ファイル名を設定して保存
    output_file = os.path.join(output_dir, f"stream_{operation.lower()}.png")
    plt.savefig(output_file)
    plt.close()
    print(f"Saved {operation} plot to {output_file}",file=sys.stderr)

# Copy, Scale, Add, Triadごとにプロット
for operation in ["Copy", "Scale", "Add", "Triad"]:
    plot_results(results, operation)
    


result_file = os.path.join(output_dir, "result.txt")
with open(result_file, "w") as f:
    for operation in ["Copy", "Scale", "Add", "Triad"]:
        f.write(f"{operation}\n")
        for size in data_sizes:
            data_line = f"{size//2**17}MB : {results[size//2**17][operation]:.6f} second\n"
            f.write(data_line)
        f.write("\n")
