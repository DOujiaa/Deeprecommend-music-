#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
音乐推荐引擎 - 简化版

此模块包含音乐推荐系统的核心功能，但使用简化的推荐逻辑。
复杂的推荐算法(SVD++, NCF, MLP)将在未来更新中实现。
"""

import os
import sys
import numpy as np
import pandas as pd
import logging
import random
import pickle
import json
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)

class MusicRecommender:
    """音乐推荐系统类
    
    简化版的推荐引擎，提供基本的推荐功能。
    高级算法(SVD++, NCF, MLP)将在未来实现。
    """
    
    def __init__(self, data_dir='processed_data', use_msd=True, force_retrain=False, 
                 model_type='svdpp', svd_n_factors=100, svd_n_epochs=20, svd_reg_all=0.02, 
                 content_weight=0.3, cf_weight=0.3, ncf_weight=0.2, mlp_weight=0.2,
                 user_based=True, sample_size=None):
        """初始化推荐系统
        
        Args:
            data_dir: 数据目录
            use_msd: 是否使用Million Song Dataset
            force_retrain: 是否强制重新训练模型
            model_type: 模型类型 ('svdpp', 'cf', 'ncf', 'mlp')
            svd_n_factors: SVD++模型的潜在因子数
            svd_n_epochs: SVD++模型的训练轮数
            svd_reg_all: SVD++模型的正则化参数
            content_weight: 内容推荐权重
            cf_weight: 协同过滤权重
            ncf_weight: 神经协同过滤权重
            mlp_weight: 多层感知机权重
            user_based: 是否使用基于用户的协同过滤
            sample_size: 采样大小
        """
        self.data_dir = data_dir
        self.use_msd = use_msd
        self.force_retrain = force_retrain
        self.model_type = model_type
        self.svd_n_factors = svd_n_factors
        self.svd_n_epochs = svd_n_epochs
        self.svd_reg_all = svd_reg_all
        self.content_weight = content_weight
        self.cf_weight = cf_weight
        self.ncf_weight = ncf_weight
        self.mlp_weight = mlp_weight
        self.user_based = user_based
        self.sample_size = sample_size
        
        # 创建数据目录
        os.makedirs(self.data_dir, exist_ok=True)
        
        # 数据存储
        self.user_ratings = {}  # 用户评分
        self.songs_df = None    # 歌曲元数据
        self.interactions_df = None  # 用户-歌曲交互数据
        
        # 加载数据
        self._load_data()
        
        logger.info(f"音乐推荐系统初始化完成: 模型类型={model_type}, 数据目录={data_dir}")
        
    def _load_data(self):
        """加载数据
        
        加载用户评分数据和歌曲元数据
        """
        try:
            # 歌曲元数据文件路径
            songs_file = os.path.join(self.data_dir, 'songs.csv')
            interactions_file = os.path.join(self.data_dir, 'user_song_interactions.csv')
            
            # 检查文件是否存在，如果不存在则创建样本数据
            if not os.path.exists(songs_file) or not os.path.exists(interactions_file):
                logger.info("数据文件不存在，创建样本数据...")
                self._create_sample_data()
        
        # 加载歌曲元数据
            self.songs_df = pd.read_csv(songs_file)
            logger.info(f"加载了 {len(self.songs_df)} 首歌曲的元数据")
            
            # 加载用户-歌曲交互数据
            self.interactions_df = pd.read_csv(interactions_file)
            logger.info(f"加载了 {len(self.interactions_df)} 条用户-歌曲交互记录")
            
            # 构建用户评分字典
            self.user_ratings = defaultdict(dict)
            for _, row in self.interactions_df.iterrows():
                self.user_ratings[row['user_id']][row['song_id']] = row['rating']
            
            logger.info(f"构建了 {len(self.user_ratings)} 个用户的评分数据")
            
        except Exception as e:
            logger.error(f"加载数据时出错: {str(e)}")
            # 发生错误时创建样本数据
            self._create_sample_data()
    
    def _create_sample_data(self):
        """创建样本数据
        
        当无法加载真实数据时，创建样本数据用于测试
        """
        try:
            # 样本歌曲数据
            sample_songs = []
            for i in range(1, 1001):
                song = {
                    'song_id': f"S{i:04d}",
                    'track_name': f"Song {i}",
                    'artist_name': f"Artist {i % 50 + 1}",
                    'album_name': f"Album {i % 100 + 1}",
                    'genre': random.choice(['Pop', 'Rock', 'Jazz', 'Classical', 'Hip Hop', 'Electronic', 'Country', 'R&B']),
                    'year': random.randint(1980, 2023)
                }
                sample_songs.append(song)
            
            # 创建歌曲数据框
            self.songs_df = pd.DataFrame(sample_songs)
            
            # 样本用户-歌曲交互数据
            sample_interactions = []
            for user_id in range(1, 21):
                # 每个用户评分10-30首歌
                num_ratings = random.randint(10, 30)
                # 随机选择歌曲ID
                song_indices = random.sample(range(len(sample_songs)), num_ratings)
                
                for idx in song_indices:
                    interaction = {
                        'user_id': f"U{user_id:03d}",
                        'song_id': sample_songs[idx]['song_id'],
                        'rating': random.uniform(1, 5),
                        'timestamp': int(datetime.now().timestamp())
                    }
                    sample_interactions.append(interaction)
            
            # 创建交互数据框
            self.interactions_df = pd.DataFrame(sample_interactions)
            
            # 构建用户评分字典
            self.user_ratings = defaultdict(dict)
            for _, row in self.interactions_df.iterrows():
                self.user_ratings[row['user_id']][row['song_id']] = row['rating']
            
            # 保存样本数据
            songs_file = os.path.join(self.data_dir, 'songs.csv')
            interactions_file = os.path.join(self.data_dir, 'user_song_interactions.csv')
            
            self.songs_df.to_csv(songs_file, index=False)
            self.interactions_df.to_csv(interactions_file, index=False)
            
            logger.info(f"创建了样本数据: {len(self.songs_df)}首歌曲, {len(self.interactions_df)}条交互记录")
            
        except Exception as e:
            logger.error(f"创建样本数据时出错: {str(e)}")
            raise
    
    def get_recommendations(self, user_id, top_n=10):
        """获取推荐
        
        简化版的推荐方法，未实现复杂算法
        
        Args:
            user_id: 用户ID
            top_n: 推荐数量
            
        Returns:
            推荐歌曲列表
        """
        # 如果用户没有评分记录，返回热门歌曲
        if user_id not in self.user_ratings or not self.user_ratings[user_id]:
            return self.get_popular_songs(top_n)
        
        # 使用基于用户的协同过滤
        recommended_songs = self._get_cf_recommendations(user_id, top_n)
        
        # 添加歌曲元数据
        result = []
        for song_id, score in recommended_songs:
            song_info = self.songs_df[self.songs_df['song_id'] == song_id]
            if not song_info.empty:
                song_data = song_info.iloc[0].to_dict()
                song_data['score'] = score
                song_data['explanation'] = f"根据您的音乐品味推荐"
                
                # 确保兼容前端展示所需的字段
                if 'track_name' in song_data and 'title' not in song_data:
                    song_data['title'] = song_data['track_name']
                if 'artist_name' in song_data and 'artist' not in song_data:
                    song_data['artist'] = song_data['artist_name']
                
                result.append(song_data)
        
        # 如果推荐数量不足，添加热门歌曲
        if len(result) < top_n:
            popular_songs = self.get_popular_songs(top_n - len(result))
            # 避免重复
            existing_ids = {song['song_id'] for song in result}
            for song in popular_songs:
                if song['song_id'] not in existing_ids:
                    song['explanation'] = "热门歌曲推荐"
                    result.append(song)
        
        return result[:top_n]
    
    def _get_cf_recommendations(self, user_id, top_n=10):
        """基于协同过滤的推荐
        
        简化版的基于用户的协同过滤，计算用户相似度并推荐相似用户喜欢的歌曲
        
        Args:
            user_id: 用户ID
            top_n: 推荐数量
            
        Returns:
            推荐歌曲ID和分数列表 [(song_id, score), ...]
        """
        # 用户已评分的歌曲
        user_songs = set(self.user_ratings[user_id].keys())
        
        # 计算用户相似度
        user_sim_scores = {}
        for other_id, other_ratings in self.user_ratings.items():
            if other_id == user_id:
                continue
            
            # 共同评分的歌曲
            common_songs = user_songs.intersection(other_ratings.keys())
            if len(common_songs) < 3:  # 至少有3首共同评分的歌曲
                continue
        
            # 计算余弦相似度
            sum_xy = sum(self.user_ratings[user_id][song] * other_ratings[song] for song in common_songs)
            sum_x2 = sum(self.user_ratings[user_id][song] ** 2 for song in common_songs)
            sum_y2 = sum(other_ratings[song] ** 2 for song in common_songs)
            
            if sum_x2 == 0 or sum_y2 == 0:
                continue
            
            sim = sum_xy / (np.sqrt(sum_x2) * np.sqrt(sum_y2))
            user_sim_scores[other_id] = sim
        
        # 如果没有相似用户，返回热门歌曲
        if not user_sim_scores:
            logger.warning(f"用户 {user_id} 没有相似用户，返回热门歌曲")
            return [(song['song_id'], 0) for song in self.get_popular_songs(top_n)]
        
        # 根据相似度排序
        sorted_users = sorted(user_sim_scores.items(), key=lambda x: x[1], reverse=True)
        
        # 推荐相似用户喜欢但当前用户未评分的歌曲
        song_scores = defaultdict(float)
        sim_sums = defaultdict(float)
        
        for other_id, sim in sorted_users[:20]:  # 只考虑前20个最相似的用户
            for song_id, rating in self.user_ratings[other_id].items():
                if song_id in user_songs:
                    continue  # 跳过用户已评分的歌曲
                
                song_scores[song_id] += sim * rating
                sim_sums[song_id] += abs(sim)
        
        # 计算加权评分
        recommendations = []
        for song_id, score in song_scores.items():
            if sim_sums[song_id] > 0:
                recommendations.append((song_id, score / sim_sums[song_id]))
        
        # 排序并返回前N个推荐
        recommendations.sort(key=lambda x: x[1], reverse=True)
        return recommendations[:top_n]
    
    def get_popular_songs(self, top_n=10):
        """获取热门歌曲
        
        根据评分次数和平均评分获取热门歌曲
        
        Args:
            top_n: 返回的歌曲数量
            
        Returns:
            热门歌曲列表
        """
        if self.interactions_df is None or self.songs_df is None:
            return self._get_default_sample_songs(top_n)
        
        try:
            # 计算每首歌曲的评分次数和平均评分
            song_stats = self.interactions_df.groupby('song_id').agg({
                'rating': ['count', 'mean']
            })
            song_stats.columns = ['rating_count', 'avg_rating']
            song_stats.reset_index(inplace=True)
            
            # 只考虑至少有3次评分的歌曲
            song_stats = song_stats[song_stats['rating_count'] >= 3]
            
            # 计算热门度分数 (评分数 * 平均评分)
            song_stats['popularity'] = song_stats['rating_count'] * song_stats['avg_rating']
            
            # 排序并获取前N首歌曲
            top_songs = song_stats.sort_values('popularity', ascending=False).head(top_n)
            
            # 获取完整歌曲信息
            result = []
            for _, row in top_songs.iterrows():
                song_info = self.songs_df[self.songs_df['song_id'] == row['song_id']]
                if not song_info.empty:
                    song_data = song_info.iloc[0].to_dict()
                    song_data['score'] = row['popularity']
                    song_data['explanation'] = f"热门歌曲，评分次数: {row['rating_count']:.0f}, 平均评分: {row['avg_rating']:.1f}"
                    
                    # 确保兼容前端展示所需的字段
                    if 'track_name' in song_data and 'title' not in song_data:
                        song_data['title'] = song_data['track_name']
                    if 'artist_name' in song_data and 'artist' not in song_data:
                        song_data['artist'] = song_data['artist_name']
                    
                    result.append(song_data)
            
            # 如果热门歌曲不足，返回样本歌曲补充
            if len(result) < top_n:
                result.extend(self._get_default_sample_songs(top_n - len(result)))
            
            return result[:top_n]
            
        except Exception as e:
            logger.error(f"获取热门歌曲时出错: {str(e)}")
            return self._get_default_sample_songs(top_n)
    
    def _get_default_sample_songs(self, top_n=10):
        """获取默认样本歌曲
        
        当无法获取真实数据时，返回默认歌曲列表
        
        Args:
            top_n: 返回的歌曲数量
            
        Returns:
            样本歌曲列表
        """
        # 预定义的样本歌曲
        sample_songs = [
            {
                'song_id': 'S0001',
                'track_name': '晴天',
                'title': '晴天',
                'artist_name': '周杰伦',
                'artist': '周杰伦',
                'album_name': '叶惠美',
                'genre': 'Pop',
                'year': 2003,
                'score': 5.0,
                'explanation': '热门华语歌曲'
            },
            {
                'song_id': 'S0002',
                'track_name': 'Shape of You',
                'title': 'Shape of You',
                'artist_name': 'Ed Sheeran',
                'artist': 'Ed Sheeran',
                'album_name': '÷ (Divide)',
                'genre': 'Pop',
                'year': 2017,
                'score': 4.9,
                'explanation': '全球热门流行歌曲'
            },
            {
                'song_id': 'S0003',
                'track_name': 'Bohemian Rhapsody',
                'title': 'Bohemian Rhapsody',
                'artist_name': 'Queen',
                'artist': 'Queen',
                'album_name': 'A Night at the Opera',
                'genre': 'Rock',
                'year': 1975,
                'score': 4.8,
                'explanation': '经典摇滚名曲'
            },
            {
                'song_id': 'S0004',
                'track_name': 'Uptown Funk',
                'title': 'Uptown Funk',
                'artist_name': 'Mark Ronson ft. Bruno Mars',
                'artist': 'Mark Ronson ft. Bruno Mars',
                'album_name': 'Uptown Special',
                'genre': 'Funk',
                'year': 2014,
                'score': 4.7,
                'explanation': '充满活力的现代放克'
            },
            {
                'song_id': 'S0005',
                'track_name': '稻香',
                'title': '稻香',
                'artist_name': '周杰伦',
                'artist': '周杰伦',
                'album_name': '魔杰座',
                'genre': 'Pop',
                'year': 2008,
                'score': 4.6,
                'explanation': '温馨励志的华语流行曲'
            },
            {
                'song_id': 'S0006',
                'track_name': 'Billie Jean',
                'title': 'Billie Jean',
                'artist_name': 'Michael Jackson',
                'artist': 'Michael Jackson',
                'album_name': 'Thriller',
                'genre': 'Pop',
                'year': 1982,
                'score': 4.5,
                'explanation': '流行音乐经典之作'
            },
            {
                'song_id': 'S0007',
                'track_name': 'Hotel California',
                'title': 'Hotel California',
                'artist_name': 'Eagles',
                'artist': 'Eagles',
                'album_name': 'Hotel California',
                'genre': 'Rock',
                'year': 1976,
                'score': 4.4,
                'explanation': '摇滚乐的里程碑'
            },
            {
                'song_id': 'S0008',
                'track_name': 'Imagine',
                'title': 'Imagine',
                'artist_name': 'John Lennon',
                'artist': 'John Lennon',
                'album_name': 'Imagine',
                'genre': 'Pop',
                'year': 1971,
                'score': 4.3,
                'explanation': '充满和平理想的经典歌曲'
            },
            {
                'song_id': 'S0009',
                'track_name': '起风了',
                'title': '起风了',
                'artist_name': '买辣椒也用券',
                'artist': '买辣椒也用券',
                'album_name': '起风了',
                'genre': 'Pop',
                'year': 2019,
                'score': 4.2,
                'explanation': '近年华语流行热门歌曲'
            },
            {
                'song_id': 'S0010',
                'track_name': 'Shallow',
                'title': 'Shallow',
                'artist_name': 'Lady Gaga & Bradley Cooper',
                'artist': 'Lady Gaga & Bradley Cooper',
                'album_name': 'A Star Is Born Soundtrack',
                'genre': 'Pop',
                'year': 2018,
                'score': 4.1,
                'explanation': '奥斯卡获奖歌曲'
            },
            {
                'song_id': 'S0011',
                'track_name': '骄傲的少年',
                'title': '骄傲的少年',
                'artist_name': '南征北战',
                'artist': '南征北战',
                'album_name': '骄傲的少年',
                'genre': 'Pop/Rock',
                'year': 2015,
                'score': 4.0,
                'explanation': '充满正能量的青春歌曲'
            },
            {
                'song_id': 'S0012',
                'track_name': 'Yesterday',
                'title': 'Yesterday',
                'artist_name': 'The Beatles',
                'artist': 'The Beatles',
                'album_name': 'Help!',
                'genre': 'Pop',
                'year': 1965,
                'score': 3.9,
                'explanation': '摇滚乐队的经典民谣'
            }
        ]
        
        # 打乱顺序并返回前N首
        random.shuffle(sample_songs)
        return sample_songs[:top_n]
    
    def get_similar_songs(self, song_id, top_n=5):
        """获取相似歌曲
        
        基于相同艺术家和流派的简单相似歌曲推荐
        
        Args:
            song_id: 歌曲ID
            top_n: 返回的相似歌曲数量
            
        Returns:
            相似歌曲列表
        """
        if self.songs_df is None:
            return []
        
        try:
            # 获取目标歌曲信息
            song_info = self.songs_df[self.songs_df['song_id'] == song_id]
            if song_info.empty:
                return []
            
            target_song = song_info.iloc[0]
            
            # 根据相同艺术家和流派查找相似歌曲
            similar_by_artist = self.songs_df[
                (self.songs_df['artist_name'] == target_song['artist_name']) & 
                (self.songs_df['song_id'] != song_id)
            ]
            
            similar_by_genre = self.songs_df[
                (self.songs_df['genre'] == target_song['genre']) & 
                (self.songs_df['artist_name'] != target_song['artist_name']) & 
                (self.songs_df['song_id'] != song_id)
            ]
            
            # 优先选择同一艺术家的歌曲
            similar_songs = []
            
            # 添加同一艺术家的歌曲
            if len(similar_by_artist) > 0:
                for _, song in similar_by_artist.sample(min(len(similar_by_artist), top_n)).iterrows():
                    song_data = song.to_dict()
                    song_data['explanation'] = f"来自相同艺术家: {song['artist_name']}"
                    # 确保兼容前端展示所需的字段
                    if 'track_name' in song_data and 'title' not in song_data:
                        song_data['title'] = song_data['track_name']
                    if 'artist_name' in song_data and 'artist' not in song_data:
                        song_data['artist'] = song_data['artist_name']
                    similar_songs.append(song_data)
            
            # 如果相似歌曲不足，添加相同流派的歌曲
            if len(similar_songs) < top_n and len(similar_by_genre) > 0:
                remaining = top_n - len(similar_songs)
                for _, song in similar_by_genre.sample(min(len(similar_by_genre), remaining)).iterrows():
                    song_data = song.to_dict()
                    song_data['explanation'] = f"相同音乐风格: {song['genre']}"
                    # 确保兼容前端展示所需的字段
                    if 'track_name' in song_data and 'title' not in song_data:
                        song_data['title'] = song_data['track_name']
                    if 'artist_name' in song_data and 'artist' not in song_data:
                        song_data['artist'] = song_data['artist_name']
                    similar_songs.append(song_data)
            
            # 如果仍然不足，添加随机歌曲
            if len(similar_songs) < top_n:
                remaining = top_n - len(similar_songs)
                random_songs = self.songs_df[
                    (self.songs_df['song_id'] != song_id) & 
                    (~self.songs_df['song_id'].isin([s['song_id'] for s in similar_songs]))
                ].sample(min(len(self.songs_df), remaining))
                
                for _, song in random_songs.iterrows():
                    song_data = song.to_dict()
                    song_data['explanation'] = "您可能也会喜欢这首歌"
                    # 确保兼容前端展示所需的字段
                    if 'track_name' in song_data and 'title' not in song_data:
                        song_data['title'] = song_data['track_name']
                    if 'artist_name' in song_data and 'artist' not in song_data:
                        song_data['artist'] = song_data['artist_name']
                    similar_songs.append(song_data)
            
            return similar_songs
            
        except Exception as e:
            logger.error(f"获取相似歌曲时出错: {str(e)}")
            return []
    
    def get_recommendations_by_emotion(self, emotion, top_n=5):
        """根据情绪推荐歌曲
        
        基于预定义的情绪-流派映射推荐歌曲
        
        Args:
            emotion: 情绪标签 (happy, sad, energetic, relaxed, etc.)
            top_n: 推荐数量
            
        Returns:
            推荐歌曲列表
        """
        if self.songs_df is None:
            return self._get_default_sample_songs(top_n)
        
        try:
            # 情绪-流派映射
            emotion_genre_map = {
                'happy': ['Pop', 'Dance', 'Electronic'],
                'sad': ['Blues', 'Jazz', 'Folk', 'Classical'],
                'energetic': ['Rock', 'Metal', 'Hip Hop', 'Electronic'],
                'relaxed': ['Ambient', 'Classical', 'Jazz', 'Folk'],
                'romantic': ['R&B', 'Soul', 'Pop'],
                'angry': ['Metal', 'Punk', 'Rock'],
                'nostalgic': ['Oldies', 'Country', 'Folk']
            }
            
            # 默认使用Pop流派
            genres = emotion_genre_map.get(emotion.lower(), ['Pop'])
            
            # 查找匹配流派的歌曲
            matching_songs = self.songs_df[self.songs_df['genre'].isin(genres)]
            
            # 如果没有匹配的歌曲，返回随机歌曲
            if len(matching_songs) == 0:
                matching_songs = self.songs_df
            
            # 随机选择歌曲
            result = []
            selected_songs = matching_songs.sample(min(len(matching_songs), top_n))
            
            for _, song in selected_songs.iterrows():
                song_data = song.to_dict()
                song_data['explanation'] = f"适合{emotion}情绪的{song['genre']}歌曲"
                # 确保兼容前端展示所需的字段
                if 'track_name' in song_data and 'title' not in song_data:
                    song_data['title'] = song_data['track_name']
                if 'artist_name' in song_data and 'artist' not in song_data:
                    song_data['artist'] = song_data['artist_name']
                result.append(song_data)
            
            return result
            
        except Exception as e:
            logger.error(f"获取情绪推荐时出错: {str(e)}")
            return self._get_default_sample_songs(top_n)
    
    # 在这里添加必要的其他方法，以确保与原始API兼容
    
    def get_super_hybrid_recommendations(self, user_id, top_n=10):
        """获取混合推荐 - 简化版
        
        仅使用基础协同过滤，没有实现复杂算法
        
        Args:
            user_id: 用户ID
            top_n: 推荐数量
            
        Returns:
            推荐歌曲列表
        """
        # 直接调用普通推荐方法
        return self.get_recommendations(user_id, top_n)
    
    def get_svdpp_recommendations(self, user_id, top_n=10):
        """获取SVD++推荐 - 简化版
        
        由于SVD++模型尚未实现，返回普通推荐
        
        Args:
            user_id: 用户ID
            top_n: 推荐数量
            
        Returns:
            推荐歌曲列表
        """
        # 直接调用普通推荐方法
        return self.get_recommendations(user_id, top_n)
    
    def get_ncf_recommendations(self, user_id, top_n=10):
        """获取神经协同过滤推荐 - 简化版
        
        由于NCF模型尚未实现，返回普通推荐
        
        Args:
            user_id: 用户ID
            top_n: 推荐数量
            
        Returns:
            推荐歌曲列表
        """
        # 直接调用普通推荐方法
        return self.get_recommendations(user_id, top_n)
    
    def get_mlp_recommendations(self, user_id, top_n=10):
        """获取多层感知机推荐 - 简化版
        
        由于MLP模型尚未实现，返回普通推荐
        
        Args:
            user_id: 用户ID
            top_n: 推荐数量
            
        Returns:
            推荐歌曲列表
        """
        # 直接调用普通推荐方法
        return self.get_recommendations(user_id, top_n)
    
    def get_cf_recommendations(self, user_id, top_n=10):
        """获取协同过滤推荐
        
        Args:
            user_id: 用户ID
            top_n: 推荐数量
            
        Returns:
            推荐歌曲列表
        """
        return self.get_recommendations(user_id, top_n)
    
    def get_content_recommendations(self, user_id, top_n=10):
        """获取基于内容的推荐 - 简化版
        
        由于内容模型尚未实现，返回普通推荐
        
        Args:
            user_id: 用户ID
            top_n: 推荐数量
            
        Returns:
            推荐歌曲列表
        """
        # 直接调用普通推荐方法
        return self.get_recommendations(user_id, top_n)
    
    def get_hybrid_recommendations(self, user_id, top_n=10):
        """获取混合推荐 - 简化版
        
        混合了协同过滤和基于内容的推荐结果，由于高级模型尚未实现，返回普通推荐
        
        Args:
            user_id: 用户ID
            top_n: 推荐数量
            
        Returns:
            推荐歌曲列表
        """
        # 在完整实现中，这里应该是协同过滤和基于内容的推荐结果的加权混合
        # 简化版中直接调用普通推荐方法
        return self.get_recommendations(user_id, top_n)

    def get_recommendations_by_artist(self, artist_name, top_n=5):
        """获取指定艺术家的歌曲推荐
        
        Args:
            artist_name: 艺术家名称
            top_n: 返回歌曲数量
            
        Returns:
            该艺术家的歌曲列表
        """
        if self.songs_df is None:
            return self._get_default_sample_songs(top_n)
        
        try:
            # 查找匹配的艺术家歌曲
            artist_songs = self.songs_df[self.songs_df['artist_name'].str.contains(artist_name, case=False, na=False)]
            
            # 如果没有匹配的歌曲，返回默认歌曲
            if len(artist_songs) == 0:
                return self._get_default_sample_songs(top_n)
            
            # 随机选择歌曲
            result = []
            selected_songs = artist_songs.sample(min(len(artist_songs), top_n))
            
            for _, song in selected_songs.iterrows():
                song_data = song.to_dict()
                song_data['explanation'] = f"{artist_name}的歌曲"
                # 确保兼容前端展示所需的字段
                if 'track_name' in song_data and 'title' not in song_data:
                    song_data['title'] = song_data['track_name']
                if 'artist_name' in song_data and 'artist' not in song_data:
                    song_data['artist'] = song_data['artist_name']
                result.append(song_data)
            
            return result
        
        except Exception as e:
            logger.error(f"获取艺术家歌曲时出错: {str(e)}")
            return self._get_default_sample_songs(top_n)

if __name__ == "__main__":
    # 实例化并训练推荐引擎
    recommender = MusicRecommender(data_dir='processed_data', use_msd=True)
    
    # 测试推荐功能
    try:
        test_user = recommender.user_ratings.keys()[0]
        print(f"为用户 {test_user} 生成推荐:")
        recommendations = recommender.get_recommendations(test_user, top_n=5)
        
        for i, rec in enumerate(recommendations):
            print(f"{i+1}. {rec['track_name']} - {rec['artist_name']}")
            print(f"   {rec['explanation']}")
    except Exception as e:
        print(f"测试推荐时出错: {e}")
    
    # 测试热门歌曲功能
    print("\n热门歌曲:")
    popular_songs = recommender.get_popular_songs(top_n=3)
    for i, song in enumerate(popular_songs):
        print(f"{i+1}. {song['track_name']} - {song['artist_name']}") 

# 添加别名使RecommendationEngine指向MusicRecommender类
RecommendationEngine = MusicRecommender 