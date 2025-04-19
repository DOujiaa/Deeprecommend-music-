"""
生成测试用户评分数据

该脚本会为测试用户生成随机评分数据，解决"用户-歌曲交互数据不足"的问题
"""

import os
import sqlite3
import pandas as pd
import numpy as np
import random
from datetime import datetime
import argparse
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('generate_ratings')

def create_test_users(db_path, num_users=5):
    """创建测试用户"""
    logger.info(f"创建 {num_users} 个测试用户")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    test_users = []
    now = datetime.now().isoformat()
    
    for i in range(1, num_users + 1):
        user_id = f"test_user_{i}"
        username = f"测试用户{i}"
        
        # 检查用户是否已存在
        cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
        if cursor.fetchone() is None:
            cursor.execute(
                'INSERT INTO users VALUES (?, ?, ?, ?)',
                (user_id, username, "password123", now)
            )
            test_users.append(user_id)
            logger.info(f"已创建用户: {user_id}")
        else:
            test_users.append(user_id)
            logger.info(f"用户已存在: {user_id}")
    
    conn.commit()
    conn.close()
    
    return test_users

def load_songs(processed_data_dir):
    """加载歌曲元数据"""
    songs_metadata_path = os.path.join(processed_data_dir, 'songs_metadata.pkl')
    
    if not os.path.exists(songs_metadata_path):
        logger.error(f"歌曲元数据文件不存在: {songs_metadata_path}")
        return None
    
    try:
        songs_metadata = pd.read_pickle(songs_metadata_path)
        logger.info(f"已加载 {len(songs_metadata)} 首歌曲")
        return songs_metadata
    except Exception as e:
        logger.error(f"加载歌曲元数据出错: {e}")
        return None

def generate_ratings(db_path, user_ids, songs_metadata, ratings_per_user=20):
    """为每个用户生成随机评分"""
    if songs_metadata is None or len(songs_metadata) == 0:
        logger.error("无法生成评分：没有歌曲元数据")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    # 获取所有歌曲ID
    song_ids = songs_metadata['song_id'].values
    
    # 为每个用户生成评分
    for user_id in user_ids:
        # 随机选择歌曲进行评分
        selected_songs = np.random.choice(song_ids, min(ratings_per_user, len(song_ids)), replace=False)
        
        # 检查用户现有评分数量
        cursor.execute('SELECT COUNT(*) FROM user_ratings WHERE user_id = ?', (user_id,))
        existing_ratings = cursor.fetchone()[0]
        
        if existing_ratings >= ratings_per_user:
            logger.info(f"用户 {user_id} 已有 {existing_ratings} 条评分记录，跳过")
            continue
        
        # 生成随机评分
        for song_id in selected_songs:
            # 随机生成1-5的评分
            rating = random.randint(1, 5)
            
            # 检查是否已经有该评分
            cursor.execute(
                'SELECT rating FROM user_ratings WHERE user_id = ? AND track_id = ?', 
                (user_id, song_id)
            )
            result = cursor.fetchone()
            
            if result is None:
                # 插入新评分
                cursor.execute(
                    'INSERT INTO user_ratings (user_id, track_id, rating, timestamp) VALUES (?, ?, ?, ?)',
                    (user_id, song_id, rating, now)
                )
        
        # 计算插入的评分数量
        cursor.execute('SELECT COUNT(*) FROM user_ratings WHERE user_id = ?', (user_id,))
        new_ratings_count = cursor.fetchone()[0]
        
        logger.info(f"用户 {user_id} 评分记录: {new_ratings_count} 条")
    
    # 保存播放次数数据
    conn.commit()
    
    # 导出用户播放记录数据到processed_data中
    cursor.execute('SELECT user_id, track_id, rating FROM user_ratings')
    ratings_data = cursor.fetchall()
    
    conn.close()
    
    # 创建DataFrame并保存
    if ratings_data:
        user_song_plays = pd.DataFrame(ratings_data, columns=['user_id', 'song_id', 'rating'])
        
        # 添加plays列，使用rating值的2倍作为播放次数
        user_song_plays['plays'] = user_song_plays['rating'] * 2
        
        # 保存到processed_data目录
        output_path = os.path.join('processed_data', 'user_song_plays.pkl')
        user_song_plays.to_pickle(output_path)
        logger.info(f"已将 {len(user_song_plays)} 条用户评分数据保存到 {output_path}")
    
    return True

def main():
    parser = argparse.ArgumentParser(description='生成测试用户评分数据')
    parser.add_argument('--users', type=int, default=10, help='测试用户数量')
    parser.add_argument('--ratings', type=int, default=20, help='每个用户的评分数量')
    parser.add_argument('--db_path', type=str, default='music_recommender.db', help='数据库路径')
    parser.add_argument('--data_dir', type=str, default='processed_data', help='处理后数据目录')
    
    args = parser.parse_args()
    
    logger.info("开始生成测试评分数据")
    
    # 创建测试用户
    test_users = create_test_users(args.db_path, args.users)
    
    # 加载歌曲元数据
    songs_metadata = load_songs(args.data_dir)
    
    # 生成评分数据
    if generate_ratings(args.db_path, test_users, songs_metadata, args.ratings):
        logger.info("测试评分数据生成完成")
        logger.info("请使用 python start_clean.py 重启应用程序")
    else:
        logger.error("测试评分数据生成失败")

if __name__ == "__main__":
    main() 