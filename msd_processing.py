#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Million Song Dataset (MSD) 处理与训练脚本

本脚本用于处理MSD数据集并训练推荐模型，然后将模型保存到文件并自动下载到本地。
设计用于在Google Colab环境中运行。
"""

import os
import sys
import time
import pickle
import json
import logging
import argparse
from collections import defaultdict

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def install_dependencies():
    """安装必要的依赖库"""
    logger.info("安装必要的依赖...")
    import subprocess
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', 'pandas', 'numpy', 'scikit-learn', 'h5py', 'surprise'])
    logger.info("依赖安装完成")

def mount_drive():
    """挂载Google Drive"""
    try:
        from google.colab import drive
        logger.info("正在挂载Google Drive...")
        drive.mount('/content/drive')
        logger.info("Google Drive挂载成功")
        return True
    except ImportError:
        logger.warning("未检测到Colab环境，跳过挂载Google Drive")
        return False

def download_data(from_drive=True, drive_msd_path=None, drive_triplets_path=None):
    """下载MSD数据集"""
    if from_drive and drive_msd_path and drive_triplets_path:
        logger.info(f"从Google Drive加载数据: {drive_msd_path} 和 {drive_triplets_path}")
        msd_path = drive_msd_path
        triplets_path = drive_triplets_path
    else:
        # 直接从网络下载
        logger.info("从网络下载MSD数据...")
        import subprocess
        if not os.path.exists('msd_summary_file.h5'):
            subprocess.check_call(['wget', 'http://millionsongdataset.com/sites/default/files/AdditionalFiles/msd_summary_file.h5'])
        
        if not os.path.exists('train_triplets.txt'):
            if not os.path.exists('train_triplets.txt.zip'):
                subprocess.check_call(['wget', 'http://millionsongdataset.com/sites/default/files/challenge/train_triplets.txt.zip'])
            subprocess.check_call(['unzip', 'train_triplets.txt.zip'])
        
        msd_path = 'msd_summary_file.h5'
        triplets_path = 'train_triplets.txt'
        
    logger.info("数据下载/加载完成")
    return msd_path, triplets_path

def process_msd_metadata(h5_path, sample_size=None):
    """处理MSD元数据"""
    logger.info(f"从文件加载元数据: {h5_path}")
    
    import h5py
    import numpy as np
    import pandas as pd
    
    with h5py.File(h5_path, 'r') as h5:
        # 提取元数据字段
        song_ids = h5['songs']['song_id'][:]
        track_ids = h5['songs']['track_id'][:]
        artist_ids = h5['songs']['artist_id'][:]
        artist_names = h5['songs']['artist_name'][:]
        titles = h5['songs']['title'][:]
        
        # 尝试获取更多元数据（如果存在）
        release_years = h5['songs']['year'][:] if 'year' in h5['songs'] else np.zeros_like(song_ids)
        artist_familiarity = h5['songs']['artist_familiarity'][:] if 'artist_familiarity' in h5['songs'] else np.zeros_like(song_ids)
        artist_hotttnesss = h5['songs']['artist_hotttnesss'][:] if 'artist_hotttnesss' in h5['songs'] else np.zeros_like(song_ids)
        
    # 转换为字符串
    song_ids = [s.decode('utf-8') for s in song_ids]
    track_ids = [t.decode('utf-8') for t in track_ids]
    artist_ids = [a.decode('utf-8') for a in artist_ids]
    artist_names = [a.decode('utf-8') for a in artist_names]
    titles = [t.decode('utf-8') for t in titles]
    
    # 创建DataFrame
    metadata = pd.DataFrame({
        'song_id': song_ids,
        'track_id': track_ids,
        'artist_id': artist_ids,
        'artist_name': artist_names,
        'track_name': titles,
        'year': release_years,
        'artist_familiarity': artist_familiarity,
        'artist_hotttnesss': artist_hotttnesss
    })
    
    # 采样（如果指定）
    if sample_size and len(metadata) > sample_size:
        logger.info(f"对元数据进行采样: {sample_size}")
        metadata = metadata.sample(sample_size, random_state=42)
    
    logger.info(f"元数据处理完成，共 {len(metadata)} 首歌曲")
    return metadata

def process_msd_triplets(triplets_path, metadata_df, sample_size=None):
    """处理用户播放记录数据"""
    logger.info(f"从文件加载用户播放记录: {triplets_path}")
    
    import pandas as pd
    from collections import defaultdict
    
    # 仅保留元数据中的歌曲ID，用于过滤播放记录
    valid_song_ids = set(metadata_df['song_id'])
    
    # 读取播放记录（可能很大，使用分块处理）
    user_plays = defaultdict(dict)  # {user_id: {song_id: play_count}}
    
    # 随机采样的用户ID集合
    if sample_size:
        sample_users = set()
    
    with open(triplets_path, 'r') as f:
        # 首先统计用户和歌曲数量，用于决定采样策略
        line_count = 0
        for i, line in enumerate(f):
            if i % 1000000 == 0:
                logger.info(f"已处理 {i} 行...")
            line_count += 1
            
            if sample_size and i < 1000000 and len(sample_users) < sample_size:
                user_id = line.strip().split('\t')[0]
                sample_users.add(user_id)
    
    logger.info(f"总行数: {line_count}")
    
    # 重新打开文件，提取播放记录
    with open(triplets_path, 'r') as f:
        for i, line in enumerate(f):
            if i % 1000000 == 0:
                logger.info(f"处理记录 {i}/{line_count}...")
                
            user_id, song_id, play_count = line.strip().split('\t')
            play_count = int(play_count)
            
            # 如果采样，仅保留采样用户
            if sample_size and user_id not in sample_users:
                continue
                
            # 仅保留元数据中的歌曲
            if song_id in valid_song_ids:
                user_plays[user_id][song_id] = play_count
    
    # 转换为DataFrame格式
    records = []
    for user_id, songs in user_plays.items():
        for song_id, play_count in songs.items():
            # 根据播放次数计算评分(1-5)
            rating = min(5, 1 + int(play_count / 5))
            records.append({'user_id': user_id, 'song_id': song_id, 'play_count': play_count, 'rating': rating})
    
    triplets_df = pd.DataFrame(records)
    logger.info(f"处理了 {len(triplets_df)} 条用户-歌曲交互记录")
    
    return triplets_df

def compute_song_similarity(metadata_df):
    """计算歌曲内容相似度矩阵"""
    logger.info("计算歌曲内容相似度...")
    
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    import pandas as pd
    
    # 创建特征文本：艺术家名称 + 歌曲名称
    metadata_df['features'] = metadata_df['artist_name'] + ' ' + metadata_df['track_name']
    
    # 使用TF-IDF向量化文本特征
    vectorizer = TfidfVectorizer(min_df=2, max_df=0.8, stop_words='english')
    tfidf_matrix = vectorizer.fit_transform(metadata_df['features'])
    
    # 计算相似度矩阵
    similarity_matrix = cosine_similarity(tfidf_matrix)
    
    # 创建歌曲ID映射
    song_indices = pd.Series(metadata_df.index, index=metadata_df['song_id'])
    
    logger.info(f"相似度矩阵大小: {similarity_matrix.shape}")
    return similarity_matrix, song_indices

def train_cf_model(triplets_df):
    """训练协同过滤模型并寻找最佳参数"""
    logger.info("训练协同过滤模型并寻找最佳参数...")
    
    from surprise import Dataset, Reader, SVD
    from surprise.model_selection import GridSearchCV
    
    # 准备数据
    reader = Reader(rating_scale=(1, 5))
    if 'rating' in triplets_df.columns:
        data = Dataset.load_from_df(triplets_df[['user_id', 'song_id', 'rating']], reader)
    else:
        # 如果没有rating列，使用play_count
        data = Dataset.load_from_df(triplets_df[['user_id', 'song_id', 'play_count']], reader)
    
    # 定义参数网格
    param_grid = {
        'n_epochs': [20, 30],
        'lr_all': [0.002, 0.005],
        'reg_all': [0.02, 0.05, 0.1]
    }
    
    # 使用SVD算法
    gs = GridSearchCV(SVD, param_grid, measures=['rmse', 'mae'], cv=3)
    gs.fit(data)
    
    # 获取最佳参数
    best_params = gs.best_params['rmse']
    logger.info(f"最佳参数: {best_params}")
    
    # 使用最佳参数训练完整模型
    model = SVD(
        n_factors=best_params.get('n_factors', 100),
        n_epochs=best_params.get('n_epochs', 20),
        lr_all=best_params.get('lr_all', 0.005),
        reg_all=best_params.get('reg_all', 0.02)
    )
    trainset = data.build_full_trainset()
    model.fit(trainset)
    
    logger.info("协同过滤模型训练完成")
    return model, best_params

def extract_popular_songs(triplets_df, metadata_df, top_n=100):
    """提取热门歌曲"""
    logger.info(f"提取前 {top_n} 首热门歌曲...")
    
    # 按播放次数分组计算总和
    song_popularity = triplets_df.groupby('song_id')['play_count'].sum().reset_index()
    song_popularity = song_popularity.sort_values('play_count', ascending=False)
    
    # 获取前N首热门歌曲
    popular_songs = song_popularity.head(top_n)
    
    # 合并元数据
    popular_with_metadata = popular_songs.merge(metadata_df, on='song_id')
    
    logger.info(f"已提取 {len(popular_with_metadata)} 首热门歌曲")
    return popular_with_metadata

def save_processed_data(metadata_df, triplets_df, similarity_matrix, song_indices, cf_model, best_params, popular_songs, output_dir):
    """保存处理好的数据和模型"""
    os.makedirs(output_dir, exist_ok=True)
    logger.info(f"保存结果到目录: {output_dir}")
    
    # 保存元数据
    metadata_file = os.path.join(output_dir, 'songs_metadata.pkl')
    metadata_df.to_pickle(metadata_file)
    logger.info(f"已保存元数据: {metadata_file}")
    
    # 保存用户-歌曲交互数据
    triplets_file = os.path.join(output_dir, 'user_song_plays.pkl')
    triplets_df.to_pickle(triplets_file)
    logger.info(f"已保存用户-歌曲交互数据: {triplets_file}")
    
    # 保存相似度矩阵和索引
    similarity_file = os.path.join(output_dir, 'song_similarity.pkl')
    with open(similarity_file, 'wb') as f:
        pickle.dump((similarity_matrix, song_indices), f)
    logger.info(f"已保存相似度矩阵: {similarity_file}")
    
    # 保存协同过滤模型
    model_file = os.path.join(output_dir, 'cf_model.pkl')
    with open(model_file, 'wb') as f:
        pickle.dump(cf_model, f)
    logger.info(f"已保存协同过滤模型: {model_file}")
    
    # 保存最佳参数
    params_file = os.path.join(output_dir, 'best_params.json')
    with open(params_file, 'w') as f:
        json.dump(best_params, f, indent=4)
    logger.info(f"已保存最佳参数: {params_file}")
    
    # 保存热门歌曲
    popular_file = os.path.join(output_dir, 'popular_songs.pkl')
    popular_songs.to_pickle(popular_file)
    logger.info(f"已保存热门歌曲: {popular_file}")
    
    # 创建README记录处理信息
    readme_file = os.path.join(output_dir, 'README.txt')
    with open(readme_file, 'w') as f:
        f.write(f"处理时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"元数据数量: {len(metadata_df)}\n")
        f.write(f"用户-歌曲交互记录数量: {len(triplets_df)}\n")
        f.write(f"相似度矩阵大小: {similarity_matrix.shape}\n")
        f.write(f"协同过滤最佳参数: {best_params}\n")
        f.write(f"热门歌曲数量: {len(popular_songs)}\n")
    logger.info(f"已创建处理信息记录: {readme_file}")
    
    logger.info("所有数据和模型已成功保存!")
    return True

def zip_and_download(output_dir):
    """将结果压缩并下载到本地"""
    import subprocess
    
    logger.info(f"压缩结果目录: {output_dir}")
    zip_file = "/content/processed_msd_data.zip"
    subprocess.check_call(['zip', '-r', zip_file, f"{output_dir}/*"])
    
    try:
        from google.colab import files
        logger.info("正在下载处理结果...")
        files.download(zip_file)
        logger.info(f"下载已开始，请在浏览器中检查文件: {zip_file}")
    except ImportError:
        logger.warning("未检测到Colab环境，无法自动下载文件")
        logger.info(f"请手动从以下位置获取文件: {zip_file}")
    
    return True

def main():
    """主处理流程"""
    parser = argparse.ArgumentParser(description='处理MSD数据集并训练推荐模型')
    
    parser.add_argument('--sample-size', type=int, default=100000, 
                        help='样本大小，设置为0使用全部数据')
    parser.add_argument('--output-dir', type=str, default='/content/drive/MyDrive/processed_msd_data',
                        help='输出目录路径')
    parser.add_argument('--from-drive', action='store_true',
                        help='从Google Drive加载数据')
    parser.add_argument('--msd-path', type=str, 
                        default='/content/drive/MyDrive/msd_summary_file.h5',
                        help='MSD元数据文件路径')
    parser.add_argument('--triplets-path', type=str,
                        default='/content/drive/MyDrive/train_triplets.txt',
                        help='用户播放记录文件路径')
    
    args = parser.parse_args()
    
    # 转换sample_size为None如果是0
    sample_size = args.sample_size if args.sample_size > 0 else None
    
    logger.info("开始MSD数据处理和推荐模型训练流程")
    
    # 1. 安装依赖
    install_dependencies()
    
    # 2. 导入pandas和numpy (这里需要在依赖安装之后再导入)
    import pandas as pd
    import numpy as np
    
    # 3. 挂载Google Drive(如果需要)
    if args.from_drive:
        mount_drive()
    
    # 4. 下载/加载数据
    msd_path, triplets_path = download_data(
        from_drive=args.from_drive,
        drive_msd_path=args.msd_path,
        drive_triplets_path=args.triplets_path
    )
    
    # 5. 处理元数据
    metadata_df = process_msd_metadata(msd_path, sample_size=sample_size)
    
    # 6. 处理用户-歌曲交互数据
    triplets_df = process_msd_triplets(triplets_path, metadata_df, sample_size=sample_size)
    
    # 7. 计算歌曲内容相似度
    similarity_matrix, song_indices = compute_song_similarity(metadata_df)
    
    # 8. 训练协同过滤模型
    cf_model, best_params = train_cf_model(triplets_df)
    
    # 9. 提取热门歌曲
    popular_songs = extract_popular_songs(triplets_df, metadata_df)
    
    # 10. 保存处理结果
    save_processed_data(
        metadata_df=metadata_df,
        triplets_df=triplets_df,
        similarity_matrix=similarity_matrix,
        song_indices=song_indices,
        cf_model=cf_model,
        best_params=best_params,
        popular_songs=popular_songs,
        output_dir=args.output_dir
    )
    
    # 11. 压缩并下载结果
    zip_and_download(args.output_dir)
    
    logger.info("MSD数据处理和推荐模型训练流程完成!")
    
    # 输出使用说明
    print("\n" + "="*80)
    print("使用说明".center(80))
    print("="*80)
    print("""
下载完成后，请按以下步骤操作：

1. 解压'processed_msd_data.zip'文件
2. 将解压后的所有文件复制到本地应用的'processed_data'目录
3. 确保'app.py'和'recommendation_engine.py'能正确加载这些文件
4. 使用以下配置参数启动应用：
   - USE_MSD=true
   - DATA_DIR=processed_data
   - 使用'best_params.json'中的参数设置其他配置项

这样，您的应用就能使用经过训练的MSD数据模型进行推荐了！
    """)
    print("="*80)

if __name__ == "__main__":
    main() 