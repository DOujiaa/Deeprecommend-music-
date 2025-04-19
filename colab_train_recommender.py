#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
深度推荐音乐系统 - 混合推荐模型训练脚本
适用于Google Colab环境

训练流程:
1. 加载并预处理音乐数据
2. 训练多种推荐模型（SVD++、NCF、MLP、协同过滤）
3. 实现混合推荐策略
4. 保存训练好的模型
"""

import os
import sys
import numpy as np
import pandas as pd
import pickle
import logging
import tensorflow as tf
from tensorflow.keras.models import Model, Sequential, load_model
from tensorflow.keras.layers import Input, Embedding, Flatten, Dense, Concatenate, Multiply
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.regularizers import l2
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler
from surprise import SVD, SVDpp, Dataset, Reader, accuracy
from surprise.model_selection import cross_validate
import matplotlib.pyplot as plt
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Google Drive挂载（在Colab环境中使用）
MOUNT_DRIVE = True  # 设置为True以挂载Google Drive

if MOUNT_DRIVE:
    try:
        from google.colab import drive
        drive.mount('/content/gdrive')
        MODEL_PATH = '/content/gdrive/MyDrive/music_recommender_models/'
        DATA_PATH = '/content/gdrive/MyDrive/music_data/'
        # 创建模型保存目录
        os.makedirs(MODEL_PATH, exist_ok=True)
        os.makedirs(DATA_PATH, exist_ok=True)
        logger.info(f"Google Drive已挂载，模型将保存至: {MODEL_PATH}")
    except ImportError:
        logger.warning("未检测到Google Colab环境，使用本地路径")
        MODEL_PATH = './models/'
        DATA_PATH = './data/'
        os.makedirs(MODEL_PATH, exist_ok=True)
        os.makedirs(DATA_PATH, exist_ok=True)
else:
    MODEL_PATH = './models/'
    DATA_PATH = './data/'
    os.makedirs(MODEL_PATH, exist_ok=True)
    os.makedirs(DATA_PATH, exist_ok=True)

class MusicRecommenderTrainer:
    """音乐推荐系统模型训练器
    
    训练多种推荐模型并实现混合推荐策略。
    支持的模型：SVD++、神经协同过滤(NCF)、多层感知机(MLP)和基于用户的协同过滤。
    """
    
    def __init__(self, data_path=DATA_PATH, model_path=MODEL_PATH, 
                 content_weight=0.3, cf_weight=0.3, ncf_weight=0.2, mlp_weight=0.2,
                 use_sample=True, sample_size=100000):
        """初始化推荐系统训练器
        
        Args:
            data_path: 数据存放路径
            model_path: 模型保存路径
            content_weight: 内容推荐权重
            cf_weight: 协同过滤权重
            ncf_weight: 神经协同过滤权重
            mlp_weight: 多层感知机权重
            use_sample: 是否使用采样数据
            sample_size: 采样数据大小
        """
        self.data_path = data_path
        self.model_path = model_path
        self.content_weight = content_weight
        self.cf_weight = cf_weight
        self.ncf_weight = ncf_weight
        self.mlp_weight = mlp_weight
        self.use_sample = use_sample
        self.sample_size = sample_size
        
        # 数据集
        self.ratings_df = None
        self.songs_df = None
        self.user_item_matrix = None
        
        # 模型
        self.svdpp_model = None
        self.ncf_model = None
        self.mlp_model = None
        
        # 模型映射
        self.user_mapping = {}
        self.item_mapping = {}
        self.reverse_user_mapping = {}
        self.reverse_item_mapping = {}
        
        logger.info("初始化音乐推荐系统训练器")
        logger.info(f"混合策略权重: 内容({content_weight}) CF({cf_weight}) NCF({ncf_weight}) MLP({mlp_weight})")
    
    def download_data(self):
        """下载示例数据集（如果在Colab环境中）
        
        如果不在Colab环境中，可以手动下载数据集到data_path
        """
        try:
            import gdown
            
            # 示例：使用Million Song Dataset子集或Last.fm数据集
            # 这里使用的URL是示例，需要替换为实际数据集URL
            lastfm_url = "https://files.grouplens.org/datasets/hetrec2011/hetrec2011-lastfm-2k.zip"
            million_song_url = "http://millionsongdataset.com/sites/default/files/challenge/train_triplets.txt.zip"
            
            logger.info("下载Last.fm数据集...")
            os.system(f"wget {lastfm_url} -P {self.data_path}")
            os.system(f"unzip {self.data_path}hetrec2011-lastfm-2k.zip -d {self.data_path}")
            
            logger.info("下载完成")
        except ImportError:
            logger.warning("未安装gdown，请手动下载数据集")
            logger.info("推荐数据集: Last.fm (https://grouplens.org/datasets/hetrec-2011/)")
            logger.info("或Million Song Dataset (http://millionsongdataset.com/)")
    
    def load_data(self):
        """加载数据集
        
        加载用户-歌曲评分数据和歌曲元数据
        """
        try:
            # 尝试不同数据集路径
            datasets = [
                (f"{self.data_path}hetrec2011-lastfm-2k/user_artists.dat", "\t", ["userID", "artistID", "weight"]),
                (f"{self.data_path}ratings.csv", ",", ["user_id", "song_id", "rating"]),
                (f"{self.data_path}user_song_ratings.csv", ",", ["user_id", "song_id", "rating"])
            ]
            
            for path, sep, columns in datasets:
                if os.path.exists(path):
                    logger.info(f"加载数据集: {path}")
                    if path.endswith('.dat'):
                        self.ratings_df = pd.read_csv(path, sep=sep, names=columns, encoding='latin1')
                        # 将weight列重命名为rating
                        if "weight" in self.ratings_df.columns:
                            self.ratings_df.rename(columns={"weight": "rating", "userID": "user_id", "artistID": "song_id"}, inplace=True)
                    else:
                        self.ratings_df = pd.read_csv(path, sep=sep)
                    break
            
            if self.ratings_df is None:
                # 创建示例数据
                logger.warning("未找到数据集，创建示例数据")
                self._create_sample_data()
            else:
                logger.info(f"加载了 {len(self.ratings_df)} 条评分记录")
                
                # 重命名列以确保一致性
                if "user" in self.ratings_df.columns and "user_id" not in self.ratings_df.columns:
                    self.ratings_df.rename(columns={"user": "user_id"}, inplace=True)
                if "item" in self.ratings_df.columns and "song_id" not in self.ratings_df.columns:
                    self.ratings_df.rename(columns={"item": "song_id"}, inplace=True)
                if "rating" not in self.ratings_df.columns and "listen_count" in self.ratings_df.columns:
                    self.ratings_df.rename(columns={"listen_count": "rating"}, inplace=True)
                
                # 标准化评分
                if self.ratings_df["rating"].max() > 5:
                    scaler = MinMaxScaler(feature_range=(1, 5))
                    self.ratings_df["rating"] = scaler.fit_transform(self.ratings_df[["rating"]])
                    
                # 采样数据
                if self.use_sample and len(self.ratings_df) > self.sample_size:
                    self.ratings_df = self.ratings_df.sample(n=self.sample_size, random_state=42)
                    logger.info(f"采样后数据大小: {len(self.ratings_df)}")
            
            # 加载或创建歌曲元数据
            songs_path = f"{self.data_path}songs.csv"
            if os.path.exists(songs_path):
                self.songs_df = pd.read_csv(songs_path)
                logger.info(f"加载了 {len(self.songs_df)} 首歌曲的元数据")
            else:
                # 从评分数据中提取唯一歌曲ID并创建基本元数据
                song_ids = self.ratings_df["song_id"].unique()
                self.songs_df = pd.DataFrame({
                    "song_id": song_ids,
                    "title": [f"Song {i}" for i in song_ids],
                    "artist": [f"Artist {i % 100}" for i in song_ids],
                    "genre": [f"Genre {i % 10}" for i in song_ids]
                })
                logger.info(f"创建了 {len(self.songs_df)} 首歌曲的基本元数据")
            
            # 创建映射字典
            self._create_mappings()
            
            # 创建用户-物品矩阵
            self._create_user_item_matrix()
            
        except Exception as e:
            logger.error(f"加载数据出错: {str(e)}")
            raise
    
    def _create_sample_data(self):
        """创建示例数据集用于测试"""
        logger.info("创建示例数据集...")
        
        # 生成100个用户、1000首歌曲和10000条评分
        n_users = 100
        n_songs = 1000
        n_ratings = 10000
        
        # 生成用户ID和歌曲ID
        user_ids = list(range(1, n_users + 1))
        song_ids = list(range(1, n_songs + 1))
        
        # 随机生成评分数据
        np.random.seed(42)
        sampled_users = np.random.choice(user_ids, n_ratings)
        sampled_songs = np.random.choice(song_ids, n_ratings)
        ratings = np.random.uniform(1, 5, n_ratings).round(1)
        
        # 创建DataFrame
        self.ratings_df = pd.DataFrame({
            "user_id": sampled_users,
            "song_id": sampled_songs,
            "rating": ratings
        })
        
        # 创建歌曲元数据
        genres = ["Pop", "Rock", "Electronic", "Hip Hop", "Classical", "Jazz", "R&B", "Country", "Folk", "Metal"]
        self.songs_df = pd.DataFrame({
            "song_id": song_ids,
            "title": [f"Song {i}" for i in song_ids],
            "artist": [f"Artist {i % 100 + 1}" for i in song_ids],
            "genre": [genres[i % len(genres)] for i in song_ids]
        })
        
        # 保存示例数据
        self.ratings_df.to_csv(f"{self.data_path}ratings.csv", index=False)
        self.songs_df.to_csv(f"{self.data_path}songs.csv", index=False)
        
        logger.info(f"创建了示例数据: {n_users}个用户, {n_songs}首歌曲, {n_ratings}条评分")
    
    def _create_mappings(self):
        """创建用户和歌曲ID的映射"""
        unique_users = self.ratings_df["user_id"].unique()
        unique_items = self.ratings_df["song_id"].unique()
        
        self.user_mapping = {user: i for i, user in enumerate(unique_users)}
        self.item_mapping = {item: i for i, item in enumerate(unique_items)}
        self.reverse_user_mapping = {i: user for user, i in self.user_mapping.items()}
        self.reverse_item_mapping = {i: item for item, i in self.item_mapping.items()}
        
        logger.info(f"创建了映射: {len(self.user_mapping)}个用户, {len(self.item_mapping)}首歌曲")
    
    def _create_user_item_matrix(self):
        """创建用户-物品交互矩阵"""
        n_users = len(self.user_mapping)
        n_items = len(self.item_mapping)
        
        self.user_item_matrix = np.zeros((n_users, n_items))
        
        for _, row in self.ratings_df.iterrows():
            user_idx = self.user_mapping[row["user_id"]]
            item_idx = self.item_mapping[row["song_id"]]
            self.user_item_matrix[user_idx, item_idx] = row["rating"]
        
        logger.info(f"创建了用户-物品矩阵: 形状{self.user_item_matrix.shape}")
    
    def train_svdpp_model(self, n_factors=100, n_epochs=20, lr_all=0.005, reg_all=0.02):
        """训练SVD++模型
        
        Args:
            n_factors: 潜在因子数量
            n_epochs: 训练轮数
            lr_all: 学习率
            reg_all: 正则化参数
        """
        logger.info(f"训练SVD++模型: 因子数{n_factors}, 轮数{n_epochs}")
        
        reader = Reader(rating_scale=(self.ratings_df["rating"].min(), self.ratings_df["rating"].max()))
        data = Dataset.load_from_df(self.ratings_df[["user_id", "song_id", "rating"]], reader)
        
        # 训练集
        trainset = data.build_full_trainset()
        
        # 初始化SVD++模型
        self.svdpp_model = SVDpp(n_factors=n_factors, n_epochs=n_epochs, lr_all=lr_all, reg_all=reg_all)
        
        # 训练模型
        self.svdpp_model.fit(trainset)
        
        # 交叉验证评估
        cv_results = cross_validate(self.svdpp_model, data, measures=['RMSE', 'MAE'], cv=3, verbose=False)
        
        logger.info(f"SVD++模型评估: RMSE={cv_results['test_rmse'].mean():.4f}, MAE={cv_results['test_mae'].mean():.4f}")
        
        # 保存模型
        with open(f"{self.model_path}svdpp_model.pkl", 'wb') as f:
            pickle.dump(self.svdpp_model, f)
        
        logger.info(f"SVD++模型已保存至 {self.model_path}svdpp_model.pkl")
    
    def train_ncf_model(self, embedding_size=50, epochs=20, batch_size=256):
        """训练神经协同过滤(NCF)模型
        
        Args:
            embedding_size: 嵌入向量大小
            epochs: 训练轮数
            batch_size: 批次大小
        """
        logger.info(f"训练神经协同过滤(NCF)模型: 嵌入大小{embedding_size}, 轮数{epochs}")
        
        # 准备训练数据
        X_train = pd.DataFrame({
            "user": self.ratings_df["user_id"].map(self.user_mapping),
            "item": self.ratings_df["song_id"].map(self.item_mapping),
        })
        y_train = self.ratings_df["rating"].values
        
        # 构建NCF模型
        n_users = len(self.user_mapping)
        n_items = len(self.item_mapping)
        
        # 用户嵌入
        user_input = Input(shape=(1,), name="user_input")
        user_embedding = Embedding(n_users, embedding_size, name="user_embedding")(user_input)
        user_vec = Flatten(name="user_flatten")(user_embedding)
        
        # 物品嵌入
        item_input = Input(shape=(1,), name="item_input")
        item_embedding = Embedding(n_items, embedding_size, name="item_embedding")(item_input)
        item_vec = Flatten(name="item_flatten")(item_embedding)
        
        # 点积层
        dot_layer = Multiply()([user_vec, item_vec])
        
        # MLP层
        concat = Concatenate()([user_vec, item_vec])
        fc1 = Dense(64, activation="relu")(concat)
        fc2 = Dense(32, activation="relu")(fc1)
        fc3 = Dense(16, activation="relu")(fc2)
        
        # 组合层
        combine = Concatenate()([dot_layer, fc3])
        
        # 输出层
        output = Dense(1, activation="linear")(combine)
        
        # 完整模型
        self.ncf_model = Model([user_input, item_input], output)
        self.ncf_model.compile(loss="mse", optimizer=Adam(learning_rate=0.001))
        
        # 模型概要
        self.ncf_model.summary()
        
        # 训练模型
        history = self.ncf_model.fit(
            [X_train["user"].values, X_train["item"].values], 
            y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2,
            verbose=1
        )
        
        # 保存模型
        self.ncf_model.save(f"{self.model_path}ncf_model.h5")
        
        # 保存映射
        with open(f"{self.model_path}user_item_mappings.pkl", 'wb') as f:
            pickle.dump({
                "user_mapping": self.user_mapping,
                "item_mapping": self.item_mapping,
                "reverse_user_mapping": self.reverse_user_mapping,
                "reverse_item_mapping": self.reverse_item_mapping
            }, f)
        
        logger.info(f"NCF模型已保存至 {self.model_path}ncf_model.h5")
        
        # 绘制损失曲线
        plt.figure(figsize=(10, 6))
        plt.plot(history.history['loss'], label='训练损失')
        plt.plot(history.history['val_loss'], label='验证损失')
        plt.title('NCF模型训练损失')
        plt.xlabel('轮数')
        plt.ylabel('损失')
        plt.legend()
        plt.grid(True)
        plt.savefig(f"{self.model_path}ncf_loss.png")
        plt.close()
    
    def train_mlp_model(self, embedding_size=50, epochs=20, batch_size=256):
        """训练多层感知机(MLP)模型
        
        Args:
            embedding_size: 嵌入向量大小
            epochs: 训练轮数
            batch_size: 批次大小
        """
        logger.info(f"训练多层感知机(MLP)模型: 嵌入大小{embedding_size}, 轮数{epochs}")
        
        # 准备训练数据
        X_train = pd.DataFrame({
            "user": self.ratings_df["user_id"].map(self.user_mapping),
            "item": self.ratings_df["song_id"].map(self.item_mapping),
        })
        y_train = self.ratings_df["rating"].values
        
        # 构建MLP模型
        n_users = len(self.user_mapping)
        n_items = len(self.item_mapping)
        
        # 用户嵌入
        user_input = Input(shape=(1,), name="user_input")
        user_embedding = Embedding(n_users, embedding_size, name="user_embedding")(user_input)
        user_vec = Flatten(name="user_flatten")(user_embedding)
        
        # 物品嵌入
        item_input = Input(shape=(1,), name="item_input")
        item_embedding = Embedding(n_items, embedding_size, name="item_embedding")(item_input)
        item_vec = Flatten(name="item_flatten")(item_embedding)
        
        # 拼接嵌入
        concat = Concatenate()([user_vec, item_vec])
        
        # MLP层
        fc1 = Dense(128, activation="relu")(concat)
        fc2 = Dense(64, activation="relu")(fc1)
        fc3 = Dense(32, activation="relu")(fc2)
        fc4 = Dense(16, activation="relu")(fc3)
        
        # 输出层
        output = Dense(1, activation="linear")(fc4)
        
        # 完整模型
        self.mlp_model = Model([user_input, item_input], output)
        self.mlp_model.compile(loss="mse", optimizer=Adam(learning_rate=0.001))
        
        # 模型概要
        self.mlp_model.summary()
        
        # 训练模型
        history = self.mlp_model.fit(
            [X_train["user"].values, X_train["item"].values], 
            y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_split=0.2,
            verbose=1
        )
        
        # 保存模型
        self.mlp_model.save(f"{self.model_path}mlp_model.h5")
        logger.info(f"MLP模型已保存至 {self.model_path}mlp_model.h5")
        
        # 绘制损失曲线
        plt.figure(figsize=(10, 6))
        plt.plot(history.history['loss'], label='训练损失')
        plt.plot(history.history['val_loss'], label='验证损失')
        plt.title('MLP模型训练损失')
        plt.xlabel('轮数')
        plt.ylabel('损失')
        plt.legend()
        plt.grid(True)
        plt.savefig(f"{self.model_path}mlp_loss.png")
        plt.close()
    
    def train_cf_model(self, algorithm='user'):
        """训练协同过滤模型
        
        Args:
            algorithm: 算法类型，'user'为基于用户的协同过滤，'item'为基于物品的协同过滤
        """
        logger.info(f"训练{algorithm}协同过滤模型")
        
        # 这里只保存用户-物品矩阵，实际推荐时计算相似度
        with open(f"{self.model_path}user_item_matrix.pkl", 'wb') as f:
            pickle.dump({
                "matrix": self.user_item_matrix,
                "user_mapping": self.user_mapping,
                "item_mapping": self.item_mapping,
                "reverse_user_mapping": self.reverse_user_mapping,
                "reverse_item_mapping": self.reverse_item_mapping,
                "algorithm": algorithm
            }, f)
        
        logger.info(f"协同过滤模型已保存至 {self.model_path}user_item_matrix.pkl")
    
    def visualize_user_item_matrix(self):
        """可视化用户-物品矩阵"""
        plt.figure(figsize=(12, 10))
        plt.imshow(self.user_item_matrix, cmap='viridis')
        plt.colorbar(label='评分')
        plt.title('用户-歌曲交互矩阵')
        plt.xlabel('歌曲ID (索引)')
        plt.ylabel('用户ID (索引)')
        plt.savefig(f"{self.model_path}user_item_matrix.png")
        plt.close()
        
        logger.info(f"用户-物品矩阵可视化已保存至 {self.model_path}user_item_matrix.png")
    
    def analyze_data(self):
        """分析数据集特征"""
        if self.ratings_df is None:
            logger.warning("无法分析数据：数据未加载")
            return
        
        logger.info("分析数据集...")
        
        # 基本统计信息
        n_users = len(self.ratings_df["user_id"].unique())
        n_items = len(self.ratings_df["song_id"].unique())
        n_ratings = len(self.ratings_df)
        
        density = n_ratings / (n_users * n_items) * 100
        
        logger.info(f"用户数: {n_users}")
        logger.info(f"歌曲数: {n_items}")
        logger.info(f"评分数: {n_ratings}")
        logger.info(f"矩阵密度: {density:.4f}%")
        
        # 评分分布
        plt.figure(figsize=(12, 6))
        
        plt.subplot(1, 2, 1)
        self.ratings_df["rating"].hist(bins=20)
        plt.title('评分分布')
        plt.xlabel('评分')
        plt.ylabel('频率')
        plt.grid(True)
        
        # 用户活跃度分布
        plt.subplot(1, 2, 2)
        self.ratings_df["user_id"].value_counts().hist(bins=20)
        plt.title('用户活跃度分布')
        plt.xlabel('评分数量')
        plt.ylabel('用户数')
        plt.grid(True)
        
        plt.tight_layout()
        plt.savefig(f"{self.model_path}data_analysis.png")
        plt.close()
        
        logger.info(f"数据分析结果已保存至 {self.model_path}data_analysis.png")
        
        # 保存分析结果
        analysis_results = {
            "n_users": n_users,
            "n_items": n_items,
            "n_ratings": n_ratings,
            "density": density,
            "rating_mean": self.ratings_df["rating"].mean(),
            "rating_std": self.ratings_df["rating"].std(),
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        with open(f"{self.model_path}analysis_results.json", 'w') as f:
            import json
            json.dump(analysis_results, f, indent=4)
    
    def export_model_info(self):
        """导出模型信息，方便项目集成"""
        model_info = {
            "model_path": self.model_path,
            "content_weight": self.content_weight,
            "cf_weight": self.cf_weight,
            "ncf_weight": self.ncf_weight,
            "mlp_weight": self.mlp_weight,
            "n_users": len(self.user_mapping) if self.user_mapping else 0,
            "n_items": len(self.item_mapping) if self.item_mapping else 0,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "mappings_path": f"{self.model_path}user_item_mappings.pkl",
            "models": {
                "svdpp": f"{self.model_path}svdpp_model.pkl",
                "ncf": f"{self.model_path}ncf_model.h5",
                "mlp": f"{self.model_path}mlp_model.h5",
                "cf": f"{self.model_path}user_item_matrix.pkl"
            }
        }
        
        with open(f"{self.model_path}model_info.json", 'w') as f:
            import json
            json.dump(model_info, f, indent=4)
        
        logger.info(f"模型信息已导出至 {self.model_path}model_info.json")
    
    def train_all_models(self):
        """训练所有推荐模型"""
        logger.info("开始训练所有推荐模型...")
        
        try:
            # 加载数据
            self.load_data()
            
            # 分析数据
            self.analyze_data()
            
            # 可视化用户-物品矩阵
            self.visualize_user_item_matrix()
            
            # 训练SVD++模型
            self.train_svdpp_model()
            
            # 训练神经协同过滤模型
            self.train_ncf_model()
            
            # 训练多层感知机模型
            self.train_mlp_model()
            
            # 训练协同过滤模型
            self.train_cf_model()
            
            # 导出模型信息
            self.export_model_info()
            
            logger.info("所有模型训练完成!")
            
        except Exception as e:
            logger.error(f"训练过程中出错: {str(e)}")
            raise

def main():
    """主函数"""
    logger.info("启动音乐推荐系统模型训练")
    
    # 创建推荐系统训练器
    trainer = MusicRecommenderTrainer(
        content_weight=0.3,
        cf_weight=0.3,
        ncf_weight=0.2,
        mlp_weight=0.2,
        use_sample=True,
        sample_size=50000
    )
    
    # 训练所有模型
    trainer.train_all_models()
    
    logger.info("训练完成")

if __name__ == "__main__":
    main() 