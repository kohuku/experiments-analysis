import pandas as pd

# stats.csv からデータを読み込む
file_path = "3/stats.csv"  # stats.csv のパスを指定してください
df = pd.read_csv(file_path)

# Operationを分解して 'OperationName' と 'Num' を作成
df[['OperationName', 'Num']] = df['Operation'].str.extract(r'([A-Za-z]+)(\d+)')
df['Num'] = df['Num'].astype(int)

# 各OperationNameごとにCSVを作成
for operation_name in df['OperationName'].unique():
    subset = df[df['OperationName'] == operation_name]
    
    # 必要な形式にピボットテーブルを作成
    stats_df = subset.pivot_table(index=None, columns='Num', values=['Average', 'Minimum', 'Maximum'])
    
    # # 列名をフラット化（MultiIndexかどうかを確認して処理）
    if isinstance(stats_df.columns, pd.MultiIndex):
        stats_df.columns = [f"{col[0]}_{col[1]}" for col in stats_df.columns]
    else:
        stats_df.columns = [str(col) for col in stats_df.columns]
    
    # avg, max, min のデータを作成
    avg_row = ['avg'] + stats_df.loc[:, stats_df.columns].iloc[0].tolist()
    max_row = ['max'] + stats_df.loc[:, stats_df.columns].iloc[1].tolist()
    min_row = ['min'] + stats_df.loc[:, stats_df.columns].iloc[2].tolist()
    
    # 新しいデータフレームを作成
    final_df = pd.DataFrame([avg_row, max_row, min_row], columns=[''] + list(stats_df.columns))
    
    # CSVファイルに保存
    filename = f"{operation_name}_stats.csv"
    final_df.to_csv(filename, index=False, header=True)  # ヘッダーを有効にする
    print(f"ファイル {filename} が作成されました。")
