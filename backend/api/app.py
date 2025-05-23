#!/usr/bin/env python
# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify, render_template, send_from_directory, render_template_string, make_response
from flask_cors import CORS
import os
import json
import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime
import logging
import sys
import webbrowser
import threading
import time
import uuid
import warnings

# 添加项目根目录到Python路径以便导入其他模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 导入项目其他模块
from backend.models.recommendation_engine import MusicRecommender
from backend.models.ai_music_agent import MusicRecommenderAgent
from backend.utils.spotify_integration import SpotifyManager
from backend.models.recommendation_engine import RecommendationEngine
from backend.models.user_manager import UserManager
from backend.models.emotion_analyzer import EmotionAnalyzer

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('app.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

# 获取项目根目录的绝对路径
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# 设置静态文件夹和模板文件夹的绝对路径
STATIC_FOLDER = os.path.join(ROOT_DIR, 'frontend', 'static')
TEMPLATE_FOLDER = os.path.join(ROOT_DIR, 'frontend', 'templates')

logger.info(f"根目录: {ROOT_DIR}")
logger.info(f"静态文件夹: {STATIC_FOLDER}")
logger.info(f"模板文件夹: {TEMPLATE_FOLDER}")

app = Flask(__name__, 
            static_folder=STATIC_FOLDER, 
            template_folder=TEMPLATE_FOLDER)
CORS(app)  # 启用跨域支持

# 支持的语言
SUPPORTED_LANGUAGES = ['zh', 'en']
DEFAULT_LANGUAGE = 'zh'

# 每个请求前处理语言设置
@app.before_request
def before_request():
    logger.debug(f"收到请求: {request.path}, Headers: {request.headers}")
    
    # 获取请求中的语言偏好
    lang = request.args.get('lang', DEFAULT_LANGUAGE)
    if lang not in SUPPORTED_LANGUAGES:
        lang = DEFAULT_LANGUAGE
    
    # 保存到g对象以便在请求处理中使用
    request.language = lang
    logger.debug(f"使用语言: {lang}")

# 添加响应头中的语言信息
@app.after_request
def after_request(response):
    # 设置内容语言响应头
    response.headers['Content-Language'] = getattr(request, 'language', DEFAULT_LANGUAGE)
    return response

# 配置选项 - 使用环境变量
DATA_DIR = os.environ.get('DATA_DIR', 'processed_data')
USE_MSD = os.environ.get('USE_MSD', 'true').lower() == 'true'  # 启用百万歌曲数据集
FORCE_RETRAIN = os.environ.get('FORCE_RETRAIN', 'false').lower() == 'true'  # 是否强制重新训练模型
MODEL_TYPE = os.environ.get('MODEL_TYPE', 'svd')  # 模型类型: svd, knn, nmf
SVD_N_FACTORS = int(os.environ.get('SVD_N_FACTORS', 100))  # SVD模型特征数量
SVD_N_EPOCHS = int(os.environ.get('SVD_N_EPOCHS', 20))  # SVD模型训练轮数
SVD_REG_ALL = float(os.environ.get('SVD_REG_ALL', 0.05))  # SVD模型正则化参数
CONTENT_WEIGHT = float(os.environ.get('CONTENT_WEIGHT', 0.3))  # 混合推荐中内容推荐的权重
SAMPLE_SIZE = int(os.environ.get('SAMPLE_SIZE', 0)) if os.environ.get('SAMPLE_SIZE') else None  # 数据采样大小，None表示使用全部数据
SPOTIFY_CLIENT_ID = os.environ.get('SPOTIFY_CLIENT_ID', '')
SPOTIFY_CLIENT_SECRET = os.environ.get('SPOTIFY_CLIENT_SECRET', '')

# 7digital API密钥
DIGITAL7_API_KEY = os.environ.get('SEVENDIGITAL_API_KEY', '')
DIGITAL7_API_SECRET = os.environ.get('SEVENDIGITAL_API_SECRET', '')

# 输出配置信息
logger.info(f"数据目录: {DATA_DIR}")
logger.info(f"使用MSD: {USE_MSD}")
logger.info(f"强制重训: {FORCE_RETRAIN}")
logger.info(f"模型类型: {MODEL_TYPE}")
logger.info(f"SVD特征数: {SVD_N_FACTORS}")
logger.info(f"SVD训练轮数: {SVD_N_EPOCHS}")
logger.info(f"SVD正则化参数: {SVD_REG_ALL}")
logger.info(f"内容推荐权重: {CONTENT_WEIGHT}")
logger.info(f"数据采样大小: {SAMPLE_SIZE if SAMPLE_SIZE else '全部数据'}")
logger.info(f"Spotify API: {'已配置' if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET else '未配置'}")
logger.info(f"7digital API: {'已配置' if DIGITAL7_API_KEY and DIGITAL7_API_SECRET else '未配置'}")

if not DIGITAL7_API_KEY or not DIGITAL7_API_SECRET:
    logger.warning("未提供7digital API密钥，预览功能可能受限")

# 初始化数据库
def init_db():
    """初始化SQLite数据库"""
    logger.info("初始化数据库...")
    conn = sqlite3.connect('../../music_recommender.db')
    cursor = conn.cursor()
    
    # 创建用户表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT,
        created_at TEXT NOT NULL,
        is_developer BOOLEAN NOT NULL
    )
    ''')
    
    # 创建用户评分表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_ratings (
        user_id TEXT NOT NULL,
        track_id TEXT NOT NULL,
        rating INTEGER NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, track_id)
    )
    ''')
    
    # 用户反馈表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_feedback (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        track_id TEXT NOT NULL,
        feedback TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 创建聊天历史表
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        message TEXT NOT NULL,
        response TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # 添加开发者账号
    add_developer_account(cursor)
    
    conn.commit()
    conn.close()
    logger.info("数据库初始化完成")

def add_developer_account(cursor):
    """添加开发者账号到数据库"""
    # 检查开发者账号是否已存在
    cursor.execute("SELECT * FROM users WHERE username = ?", ("test",))
    result = cursor.fetchone()
    
    if not result:
        # 添加开发者账号
        cursor.execute(
            "INSERT INTO users (id, username, password, email, created_at, is_developer) VALUES (?, ?, ?, ?, ?, ?)", 
            ("dev-001", "test", "test123", "", datetime.now().isoformat(), True)
        )
        logger.info("已添加开发者账号: test")
    else:
        logger.info("开发者账号已存在")

# 初始化数据库
init_db()

# 打印诊断信息
logger.info("Python搜索路径:")
for p in sys.path:
    logger.info(f"  - {p}")

logger.info("MusicRecommender类检查:")
try:
    import inspect
    sig = inspect.signature(MusicRecommender.__init__)
    logger.info(f"MusicRecommender.__init__参数: {sig}")
    logger.info(f"MusicRecommender模块路径: {MusicRecommender.__module__}")
    logger.info(f"MusicRecommender文件位置: {inspect.getfile(MusicRecommender)}")
except Exception as e:
    logger.error(f"检查MusicRecommender类时出错: {e}")

# 初始化推荐引擎
logger.info(f"初始化推荐引擎 (USE_MSD={USE_MSD}, FORCE_RETRAIN={FORCE_RETRAIN})...")
recommender = MusicRecommender(
    data_dir=DATA_DIR, 
    use_msd=USE_MSD, 
    force_retrain=FORCE_RETRAIN,
    model_type=MODEL_TYPE,
    svd_n_factors=SVD_N_FACTORS,
    svd_n_epochs=SVD_N_EPOCHS,
    svd_reg_all=SVD_REG_ALL,
    content_weight=CONTENT_WEIGHT,
    sample_size=SAMPLE_SIZE
)
logger.info("推荐引擎初始化完成")

# 初始化AI代理
logger.info("初始化AI音乐代理...")
ai_agent = MusicRecommenderAgent(
    data_dir=DATA_DIR, 
    use_msd=USE_MSD,
    recommender=recommender  # 传递已初始化的推荐引擎实例
)
logger.info("AI音乐代理初始化完成")

# 初始化Spotify管理器
logger.info("初始化Spotify管理器...")
spotify_manager = SpotifyManager(client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET)
logger.info("Spotify管理器初始化完成")

# 数据库连接路径统一使用相对路径
DB_PATH = '../../music_recommender.db'

@app.route('/')
def home():
    """提供前端页面"""
    # 从文件中读取模板内容
    template_path = os.path.join(TEMPLATE_FOLDER, 'index.html')
    logger.info(f"加载模板: {template_path}")
    
    try:
        with open(template_path, 'r', encoding='utf-8') as file:
            template_content = file.read()
        
        # 在Jinja2处理前，将Vue.js的双大括号替换为安全的形式
        # 这里我们使用{$ $}暂时替代Vue.js的{{ }}，渲染后再替换回来
        processed_content = template_content.replace('{{', '{$').replace('}}', '$}')
        
        # 使用Jinja2渲染模板
        rendered_content = render_template_string(processed_content)
        
        # 渲染后，将临时语法替换回Vue.js的双大括号
        final_content = rendered_content.replace('{$', '{{').replace('$}', '}}')
        
        return final_content
    except Exception as e:
        logger.error(f"加载模板出错: {str(e)}")
        return f"加载前端页面出错: {str(e)}", 500

@app.route('/static/<path:path>')
def send_static(path):
    """提供静态文件"""
    logger.info(f"请求静态文件: {path}")
    return send_from_directory(STATIC_FOLDER, path)

@app.route('/developer')
def developer_panel():
    """提供开发者管理面板"""
    # 从文件中读取模板内容
    template_path = os.path.join(TEMPLATE_FOLDER, 'developer.html')
    logger.info(f"加载开发者面板模板: {template_path}")
    
    try:
        with open(template_path, 'r', encoding='utf-8') as file:
            template_content = file.read()
        
        # 在Jinja2处理前，将Vue.js的双大括号替换为安全的形式
        # 这里我们使用{$ $}暂时替代Vue.js的{{ }}，渲染后再替换回来
        processed_content = template_content.replace('{{', '{$').replace('}}', '$}')
        
        # 使用Jinja2渲染模板
        rendered_content = render_template_string(processed_content)
        
        # 渲染后，将临时语法替换回Vue.js的双大括号
        final_content = rendered_content.replace('{$', '{{').replace('$}', '}}')
        
        return final_content
    except Exception as e:
        logger.error(f"加载开发者面板模板出错: {str(e)}")
        return f"加载开发者面板出错: {str(e)}", 500

@app.route('/api/user/register', methods=['POST'])
def register_user():
    """注册新用户"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    email = data.get('email', '')
    admin_id = data.get('admin_id')  # 如果是管理员添加用户，则提供此参数
    is_developer = data.get('is_developer', False)  # 是否为开发者账号
    
    if not username:
        return jsonify({'error': '用户名不能为空'}), 400
    
    if not password:
        return jsonify({'error': '密码不能为空'}), 400
    
    # 如果指定了开发者权限，需要验证操作者是否有管理员权限
    if is_developer and admin_id:
        try:
            # 验证管理员权限
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            
            cursor.execute('''
            SELECT is_developer FROM users WHERE id = ?
            ''', (admin_id,))
            
            admin_result = cursor.fetchone()
            
            if not admin_result or not bool(admin_result[0]):
                conn.close()
                return jsonify({'error': '无权限设置开发者权限'}), 403
                
            conn.close()
        except Exception as e:
            logger.error(f"验证管理员权限时出错: {str(e)}", exc_info=True)
            return jsonify({'error': '验证管理员权限时出错'}), 500
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查用户是否已存在
    cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
    existing_user = cursor.fetchone()
    
    if existing_user:
        conn.close()
        return jsonify({'error': '用户名已存在'}), 400
    
    # 生成一个随机ID
    user_id = str(uuid.uuid4())
    
    # 添加新用户
    now = datetime.now().isoformat()
    try:
        # 存储开发者状态
        developer_value = 1 if is_developer else 0
        
        cursor.execute(
            'INSERT INTO users (id, username, password, email, created_at, is_developer) VALUES (?, ?, ?, ?, ?, ?)', 
            (user_id, username, password, email, now, developer_value)
        )
        conn.commit()
        
        logger.info(f"用户注册成功: {username} (ID: {user_id}, 开发者: {is_developer})")
        
        return jsonify({
            'message': '用户注册成功', 
            'user_id': user_id,
            'is_developer': is_developer
        })
    except Exception as e:
        logger.error(f"用户注册失败: {str(e)}", exc_info=True)
        return jsonify({'error': f'注册失败: {str(e)}'}), 500
    finally:
        conn.close()

@app.route('/api/user/login', methods=['POST'])
def login_user():
    """用户登录API，如果用户不存在则创建"""
    data = request.json
    user_id = data.get('user_id')
    username = data.get('username')
    password = data.get('password', '')  # 默认为空密码
    email = data.get('email', '')  # 添加email字段
    
    if not username:
        return jsonify({'error': '用户名不能为空'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查用户是否存在
    cursor.execute("SELECT id, password, is_developer FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    
    if not user:
        # 创建新用户
        now = datetime.now().isoformat()
        # 生成一个随机ID，如果没有提供
        if not user_id:
            user_id = str(uuid.uuid4())
        
        cursor.execute(
            "INSERT INTO users (id, username, password, email, created_at, is_developer) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username, password, email, now, 0)  # 非开发者账号
        )
        conn.commit()
        is_developer = False
    else:
        # 获取用户信息
        user_id, stored_password, is_developer = user
        is_developer = bool(is_developer)
        
        # 密码不正确时（针对开发者账号）
        if is_developer and password != stored_password:
            conn.close()
            return jsonify({'error': '密码不正确'}), 401
    
    # 记录登录时间
    logger.info(f"用户 {username} 登录成功 (ID: {user_id}, 开发者: {is_developer})")
    
    conn.close()
    
    return jsonify({
        "message": "Login successful", 
        "user_id": user_id,
        "username": username,
        "is_developer": is_developer
    })

@app.route('/api/songs/sample', methods=['GET'])
def get_sample_songs():
    """获取样本歌曲用于初始评分"""
    # 从推荐引擎获取热门歌曲
    popular_songs = recommender.get_popular_songs(top_n=20)
    
    return jsonify({
        'songs': popular_songs
    })

@app.route('/api/sample_songs')
def sample_songs():
    """获取样本歌曲用于前端展示"""
    # 从推荐引擎获取热门歌曲
    popular_songs = recommender.get_popular_songs(top_n=20)
    
    return jsonify(popular_songs)

@app.route('/api/user_ratings/<user_id>')
def user_ratings(user_id):
    """获取用户的评分记录"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取用户的评分数据
    cursor.execute('SELECT track_id, rating FROM user_ratings WHERE user_id = ?', (user_id,))
    ratings = cursor.fetchall()
    
    conn.close()
    
    # 转换为{track_id: rating}格式
    ratings_dict = {track_id: rating for track_id, rating in ratings}
    
    return jsonify(ratings_dict)

@app.route('/api/rate_song', methods=['POST'])
def rate_song_api():
    """API：用户对歌曲进行评分"""
    data = request.json
    user_id = data.get('user_id')
    track_id = data.get('track_id')
    rating = data.get('rating')
    
    if not user_id or not track_id or not rating:
        return jsonify({'error': '缺少必要参数'}), 400
    
    if not isinstance(rating, int) or rating < 1 or rating > 5:
        return jsonify({'error': '评分必须是1-5之间的整数'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    cursor.execute('''
    INSERT OR REPLACE INTO user_ratings (user_id, track_id, rating, timestamp)
    VALUES (?, ?, ?, ?)
    ''', (user_id, track_id, rating, now))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': '评分成功'})

@app.route('/api/recommendations/<user_id>')
def user_recommendations(user_id):
    """获取用户推荐歌曲，并用Spotify数据丰富结果"""
    logger.info(f"为用户 {user_id} 生成推荐")
    try:
        # 从推荐引擎获取推荐
        recommendations = recommender.get_hybrid_recommendations(user_id, top_n=10)
        
        # 如果没有足够的推荐（如新用户），补充热门歌曲
        if len(recommendations) < 10:
            logger.info(f"用户 {user_id} 推荐数量不足，补充热门歌曲")
            popular_songs = recommender.get_popular_songs(top_n=10-len(recommendations))
            recommendations.extend(popular_songs)
        
        # 用Spotify数据丰富推荐结果
        enhanced_recommendations = []
        for rec in recommendations:
            enhanced_rec = spotify_manager.enrich_recommendation(rec)
            enhanced_recommendations.append(enhanced_rec)
        
        logger.info(f"成功为用户 {user_id} 生成 {len(enhanced_recommendations)} 条推荐")
        return jsonify(enhanced_recommendations)
    except Exception as e:
        logger.error(f"生成推荐时出错: {str(e)}", exc_info=True)
        return jsonify({'error': '生成推荐时出错'}), 500

@app.route('/api/feedback', methods=['POST'])
def submit_feedback_api():
    """API：提交用户对推荐的反馈"""
    data = request.json
    user_id = data.get('user_id')
    track_id = data.get('track_id')
    feedback_type = data.get('feedback_type')  # 'like' 或 'dislike'
    
    if not user_id or not track_id or not feedback_type:
        return jsonify({'error': '缺少必要参数'}), 400
    
    if feedback_type not in ['like', 'dislike']:
        return jsonify({'error': '反馈类型无效'}), 400
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    # 记录反馈
    cursor.execute('''
    INSERT INTO user_feedback (user_id, track_id, feedback, timestamp)
    VALUES (?, ?, ?, ?)
    ''', (user_id, track_id, feedback_type, now))
    
    # 如果是喜欢，添加一个高评分；如果是不喜欢，添加一个低评分
    rating = 5 if feedback_type == 'like' else 1
    cursor.execute('''
    INSERT OR REPLACE INTO user_ratings (user_id, track_id, rating, timestamp)
    VALUES (?, ?, ?, ?)
    ''', (user_id, track_id, rating, now))
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': '反馈提交成功'})

@app.route('/api/evaluation/stats', methods=['GET'])
def get_evaluation_stats():
    """获取评估统计数据（用于管理员）"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 获取用户数
    cursor.execute('SELECT COUNT(*) FROM users')
    users_count = cursor.fetchone()[0]
    
    # 获取评分数
    cursor.execute('SELECT COUNT(*) FROM user_ratings')
    ratings_count = cursor.fetchone()[0]
    
    # 获取反馈数
    cursor.execute('SELECT COUNT(*) FROM user_feedback')
    feedback_count = cursor.fetchone()[0]
    
    # 获取平均评分
    cursor.execute('SELECT AVG(rating) FROM user_ratings')
    avg_rating = cursor.fetchone()[0]
    
    # 获取喜欢/不喜欢比例
    cursor.execute('''
    SELECT feedback, COUNT(*) FROM user_feedback
    GROUP BY feedback
    ''')
    feedback_stats = dict(cursor.fetchall())
    
    conn.close()
    
    return jsonify({
        'users_count': users_count,
        'ratings_count': ratings_count,
        'feedback_count': feedback_count,
        'avg_rating': avg_rating,
        'feedback_stats': feedback_stats
    })

@app.route('/api/evaluation', methods=['POST'])
def submit_evaluation_api():
    """API：提交用户满意度问卷"""
    data = request.json
    user_id = data.get('user_id')
    responses = data.get('responses')
    comment = data.get('comment', '')
    
    if not user_id or not responses:
        return jsonify({'error': '缺少必要参数'}), 400
    
    # 保存评估结果到文件
    evaluation_dir = 'evaluation_results'
    os.makedirs(evaluation_dir, exist_ok=True)
    
    with open(f'{evaluation_dir}/evaluation_{user_id}.json', 'w') as f:
        json.dump({
            'user_id': user_id,
            'timestamp': datetime.now().isoformat(),
            'responses': responses,
            'comment': comment
        }, f)
    
    return jsonify({'message': '评估提交成功'})

@app.route('/api/chat', methods=['POST'])
def chat_api():
    """API：与AI代理对话"""
    data = request.json
    user_id = data.get('user_id')
    message = data.get('message')
    
    if not user_id or not message:
        return jsonify({'error': '缺少必要参数'}), 400
    
    # 获取AI代理回复
    response = ai_agent.process_message(user_id, message)
    
    # 保存对话历史
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    cursor.execute('''
    INSERT INTO chat_history (user_id, message, response, timestamp)
    VALUES (?, ?, ?, ?)
    ''', (user_id, message, response, now))
    
    conn.commit()
    conn.close()
    
    return jsonify({'response': response})

@app.route('/api/chat/history', methods=['GET'])
def get_chat_history():
    """获取用户的聊天历史"""
    user_id = request.args.get('user_id')
    limit = request.args.get('limit', default=10, type=int)
    
    if not user_id:
        return jsonify({'error': '缺少用户ID'}), 400
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 获取最近的聊天记录，按时间倒序
        cursor.execute('''
        SELECT message, response, timestamp 
        FROM chat_history 
        WHERE user_id = ? 
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (user_id, limit))
        
        history = cursor.fetchall()
        conn.close()
        
        # 转换为更易用的格式
        formatted_history = []
        for msg, resp, time in history:
            formatted_history.append({
                'user_message': msg,
                'ai_response': resp,
                'timestamp': time
            })
        
        return jsonify(formatted_history)
    except Exception as e:
        logger.error(f"获取聊天历史出错: {str(e)}", exc_info=True)
        return jsonify({'error': '获取聊天历史出错'}), 500

@app.route('/api/songs/by_artist/<artist_name>')
def get_songs_by_artist(artist_name):
    """获取特定艺术家的歌曲，并用Spotify数据丰富结果"""
    logger.info(f"获取艺术家 '{artist_name}' 的歌曲")
    try:
        # 从本地推荐引擎获取艺术家歌曲
        songs = recommender.get_recommendations_by_artist(artist_name, top_n=10)
        
        # 如果本地数据不足，补充从Spotify获取的信息
        if len(songs) < 5:
            try:
                # 获取艺术家信息
                artist_info = spotify_manager.get_artist_info(artist_name=artist_name)
                if artist_info and 'top_tracks' in artist_info:
                    # 转换为与本地推荐相同的格式
                    for track in artist_info['top_tracks']:
                        if len(songs) >= 10:
                            break
                        songs.append({
                            'track_id': track['id'],
                            'track_name': track['name'],
                            'artist_name': artist_name,
                            'album_cover': track.get('image'),
                            'preview_url': track.get('preview_url'),
                            'score': float(artist_info.get('popularity', 50)) / 100,
                            'explanation': f"{artist_name}在Spotify上的热门歌曲"
                        })
            except Exception as e:
                logger.warning(f"从Spotify获取艺术家歌曲时出错: {e}")
        
        # 用Spotify数据丰富结果
        enhanced_songs = []
        for song in songs:
            enhanced_song = spotify_manager.enrich_recommendation(song)
            enhanced_songs.append(enhanced_song)
        
        return jsonify(enhanced_songs)
    except Exception as e:
        logger.error(f"获取艺术家歌曲时出错: {str(e)}", exc_info=True)
        return jsonify({'error': '获取艺术家歌曲时出错'}), 500

@app.route('/api/similar_songs/<track_id>')
def get_similar_songs(track_id):
    """获取与给定歌曲相似的歌曲，并用Spotify数据丰富结果"""
    logger.info(f"获取与歌曲 {track_id} 相似的歌曲")
    try:
        # 从本地推荐引擎获取相似歌曲
        similar_songs = recommender.get_similar_songs(track_id, top_n=5)
        
        # 获取歌曲信息用于Spotify查询
        song_info = None
        for song in similar_songs:
            if song.get('track_id') == track_id:
                song_info = song
                break
        
        if not song_info and len(similar_songs) == 0:
            # 尝试从数据库获取歌曲信息
            try:
                conn = sqlite3.connect(DB_PATH)
                cursor = conn.cursor()
                cursor.execute('SELECT track_id, track_name, artist_name FROM songs WHERE track_id = ?', (track_id,))
                result = cursor.fetchone()
                if result:
                    song_info = {'track_id': result[0], 'track_name': result[1], 'artist_name': result[2]}
                conn.close()
            except Exception as e:
                logger.warning(f"从数据库获取歌曲信息时出错: {e}")
        
        # 如果本地相似歌曲不足，补充从Spotify获取的相似歌曲
        if len(similar_songs) < 3 and song_info:
            try:
                spotify_similar = spotify_manager.get_similar_tracks(
                    track_name=song_info.get('track_name'),
                    artist_name=song_info.get('artist_name'),
                    limit=5-len(similar_songs)
                )
                similar_songs.extend(spotify_similar)
            except Exception as e:
                logger.warning(f"从Spotify获取相似歌曲时出错: {e}")
        
        # 用Spotify数据丰富结果
        enhanced_songs = []
        for song in similar_songs:
            enhanced_song = spotify_manager.enrich_recommendation(song)
            enhanced_songs.append(enhanced_song)
        
        return jsonify(enhanced_songs)
    except Exception as e:
        logger.error(f"获取相似歌曲时出错: {str(e)}", exc_info=True)
        return jsonify({'error': '获取相似歌曲时出错'}), 500

@app.route('/api/spotify/track_info', methods=['GET'])
def get_spotify_track_info():
    """获取Spotify歌曲详细信息"""
    track_name = request.args.get('track_name')
    artist_name = request.args.get('artist_name')
    track_id = request.args.get('track_id')
    
    if not track_id and not track_name:
        return jsonify({'error': '必须提供track_id或track_name'}), 400
    
    try:
        track_info = spotify_manager.get_track_info(track_id=track_id, track_name=track_name, artist_name=artist_name)
        if track_info:
            return jsonify(track_info)
        return jsonify({'error': '未找到歌曲信息'}), 404
    except Exception as e:
        logger.error(f"获取Spotify歌曲信息时出错: {str(e)}", exc_info=True)
        return jsonify({'error': '获取Spotify歌曲信息时出错'}), 500

@app.route('/api/spotify/artist_info', methods=['GET'])
def get_spotify_artist_info():
    """获取Spotify艺术家详细信息"""
    artist_name = request.args.get('artist_name')
    artist_id = request.args.get('artist_id')
    
    if not artist_id and not artist_name:
        return jsonify({'error': '必须提供artist_id或artist_name'}), 400
    
    try:
        artist_info = spotify_manager.get_artist_info(artist_id=artist_id, artist_name=artist_name)
        if artist_info:
            return jsonify(artist_info)
        return jsonify({'error': '未找到艺术家信息'}), 404
    except Exception as e:
        logger.error(f"获取Spotify艺术家信息时出错: {str(e)}", exc_info=True)
        return jsonify({'error': '获取Spotify艺术家信息时出错'}), 500

@app.route('/api/spotify/new_releases', methods=['GET'])
def get_spotify_new_releases():
    """获取Spotify新发行专辑"""
    limit = request.args.get('limit', 10, type=int)
    country = request.args.get('country', 'US')
    
    try:
        new_releases = spotify_manager.get_new_releases(limit=limit, country=country)
        return jsonify(new_releases)
    except Exception as e:
        logger.error(f"获取Spotify新发行专辑时出错: {str(e)}", exc_info=True)
        return jsonify({'error': '获取Spotify新发行专辑时出错'}), 500

@app.route('/api/spotify/similar_tracks', methods=['GET'])
def get_spotify_similar_tracks():
    """获取Spotify相似歌曲推荐"""
    track_name = request.args.get('track_name')
    artist_name = request.args.get('artist_name')
    track_id = request.args.get('track_id')
    limit = request.args.get('limit', 5, type=int)
    
    if not track_id and not track_name:
        return jsonify({'error': '必须提供track_id或track_name'}), 400
    
    try:
        similar_tracks = spotify_manager.get_similar_tracks(
            track_id=track_id, 
            track_name=track_name, 
            artist_name=artist_name, 
            limit=limit
        )
        return jsonify(similar_tracks)
    except Exception as e:
        logger.error(f"获取Spotify相似歌曲时出错: {str(e)}", exc_info=True)
        return jsonify({'error': '获取Spotify相似歌曲时出错'}), 500

@app.route('/api/emotion/analyze', methods=['POST'])
def analyze_emotion_api():
    """API：分析用户情绪并返回适合的音乐推荐"""
    data = request.json
    user_id = data.get('user_id')
    message = data.get('message')
    
    if not user_id or not message:
        return jsonify({'error': '缺少必要参数'}), 400
    
    logger.info(f"用户 {user_id} 请求情绪分析: {message[:50]}...")
    
    try:
        # 使用AI服务分析情绪
        emotion_analysis = ai_agent.ai_service.analyze_emotion(message)
        
        # 使用音乐推荐代理生成基于情绪的推荐
        response = ai_agent._provide_emotion_based_recommendation(user_id, message)
        
        # 保存对话历史
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute('''
        INSERT INTO chat_history (user_id, message, response, timestamp)
        VALUES (?, ?, ?, ?)
        ''', (user_id, message, response, now))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'emotion': emotion_analysis.get('emotion', 'neutral'),
            'intensity': emotion_analysis.get('intensity', 0.5),
            'description': emotion_analysis.get('description', ''),
            'music_suggestion': emotion_analysis.get('music_suggestion', ''),
            'response': response
        })
    except Exception as e:
        logger.error(f"情绪分析API出错: {str(e)}", exc_info=True)
        return jsonify({'error': '处理情绪分析请求时出错'}), 500

@app.route('/api/emotion/music', methods=['GET'])
def get_emotion_music_api():
    """API：获取适合特定情绪的音乐列表"""
    user_id = request.args.get('user_id')
    emotion = request.args.get('emotion', 'neutral')
    
    if not user_id:
        return jsonify({'error': '缺少必要参数'}), 400
    
    logger.info(f"用户 {user_id} 请求情绪音乐列表: {emotion}")
    
    try:
        # 直接使用音乐推荐代理的方法获取特定情绪的歌曲
        music_suggestion = "适合当前情绪的"  # 默认建议
        emotion_songs = ai_agent._get_mood_specific_songs(emotion, music_suggestion, count=10)
        
        # 用Spotify数据丰富推荐结果
        enriched_songs = []
        for song in emotion_songs:
            try:
                enriched_song = spotify_manager.enrich_recommendation({
                    'track_name': song['track_name'],
                    'artist_name': song['artist_name'],
                    'explanation': song['explanation']
                })
                enriched_songs.append(enriched_song)
            except Exception as e:
                # 如果丰富失败，使用原始数据
                logger.warning(f"丰富歌曲信息失败: {e}")
                enriched_songs.append(song)
        
        return jsonify(enriched_songs)
    except Exception as e:
        logger.error(f"获取情绪音乐列表时出错: {str(e)}", exc_info=True)
        return jsonify({'error': '获取情绪音乐列表时出错'}), 500

# 添加开发者角色管理API
@app.route('/api/user/developer/status', methods=['GET'])
def get_developer_status():
    """获取用户的开发者状态"""
    user_id = request.args.get('user_id')
    
    if not user_id:
        return jsonify({'error': '缺少用户ID'}), 400
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 查询用户是否为开发者
        cursor.execute('''
        SELECT is_developer FROM users WHERE id = ?
        ''', (user_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            return jsonify({'error': '用户不存在'}), 404
        
        is_developer = bool(result[0])
        
        return jsonify({
            'user_id': user_id,
            'is_developer': is_developer
        })
    except Exception as e:
        logger.error(f"获取开发者状态出错: {str(e)}", exc_info=True)
        return jsonify({'error': '获取开发者状态出错'}), 500

@app.route('/api/user/developer/set', methods=['POST'])
def set_developer_status():
    """设置用户的开发者状态（需要权限）"""
    data = request.json
    admin_id = data.get('admin_id')  # 执行此操作的管理员ID
    target_user_id = data.get('user_id')  # 目标用户ID
    is_developer = data.get('is_developer', False)  # 要设置的开发者状态
    
    if not admin_id or not target_user_id:
        return jsonify({'error': '缺少必要参数'}), 400
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 首先检查操作者是否为开发者
        cursor.execute('''
        SELECT is_developer FROM users WHERE id = ?
        ''', (admin_id,))
        
        admin_result = cursor.fetchone()
        
        if not admin_result or not bool(admin_result[0]):
            conn.close()
            return jsonify({'error': '无权限执行此操作'}), 403
        
        # 检查目标用户是否存在
        cursor.execute('''
        SELECT id FROM users WHERE id = ?
        ''', (target_user_id,))
        
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': '目标用户不存在'}), 404
        
        # 设置目标用户的开发者状态
        developer_value = 1 if is_developer else 0
        cursor.execute('''
        UPDATE users SET is_developer = ? WHERE id = ?
        ''', (developer_value, target_user_id))
        
        conn.commit()
        conn.close()
        
        logger.info(f"管理员 {admin_id} 将用户 {target_user_id} 的开发者状态设置为 {is_developer}")
        
        return jsonify({
            'message': '设置开发者状态成功',
            'user_id': target_user_id,
            'is_developer': is_developer
        })
    except Exception as e:
        logger.error(f"设置开发者状态出错: {str(e)}", exc_info=True)
        return jsonify({'error': '设置开发者状态出错'}), 500

@app.route('/api/user/developer/list', methods=['GET'])
def list_developers():
    """获取所有开发者用户列表（需要权限）"""
    admin_id = request.args.get('admin_id')
    
    if not admin_id:
        return jsonify({'error': '缺少管理员ID'}), 400
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 首先检查操作者是否为开发者
        cursor.execute('''
        SELECT is_developer FROM users WHERE id = ?
        ''', (admin_id,))
        
        admin_result = cursor.fetchone()
        
        if not admin_result or not bool(admin_result[0]):
            conn.close()
            return jsonify({'error': '无权限执行此操作'}), 403
        
        # 获取所有开发者用户
        cursor.execute('''
        SELECT id, username, created_at FROM users WHERE is_developer = 1
        ''')
        
        developers = cursor.fetchall()
        conn.close()
        
        # 格式化结果
        formatted_developers = []
        for dev_id, username, created_at in developers:
            formatted_developers.append({
                'id': dev_id,
                'username': username,
                'created_at': created_at
            })
        
        return jsonify(formatted_developers)
    except Exception as e:
        logger.error(f"获取开发者列表出错: {str(e)}", exc_info=True)
        return jsonify({'error': '获取开发者列表出错'}), 500

# 添加查看所有用户的API（仅开发者可用）
@app.route('/api/user/all', methods=['GET'])
def get_all_users():
    """获取所有用户列表（仅限开发者使用）"""
    admin_id = request.args.get('admin_id')
    
    if not admin_id:
        return jsonify({'error': '缺少管理员ID'}), 400
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 首先检查操作者是否为开发者
        cursor.execute('''
        SELECT is_developer FROM users WHERE id = ?
        ''', (admin_id,))
        
        admin_result = cursor.fetchone()
        
        if not admin_result or not bool(admin_result[0]):
            conn.close()
            return jsonify({'error': '无权限执行此操作'}), 403
        
        # 获取所有用户
        cursor.execute('''
        SELECT id, username, created_at, is_developer FROM users
        ''')
        
        users = cursor.fetchall()
        conn.close()
        
        # 格式化结果
        formatted_users = []
        for user_id, username, created_at, is_developer in users:
            formatted_users.append({
                'id': user_id,
                'username': username,
                'created_at': created_at,
                'is_developer': bool(is_developer)
            })
        
        return jsonify(formatted_users)
    except Exception as e:
        logger.error(f"获取所有用户列表出错: {str(e)}", exc_info=True)
        return jsonify({'error': '获取所有用户列表出错'}), 500

@app.route('/api/user/delete', methods=['DELETE'])
def delete_user():
    """删除用户（仅限开发者使用）"""
    admin_id = request.args.get('admin_id')
    user_id = request.args.get('user_id')
    
    if not admin_id or not user_id:
        return jsonify({'error': '缺少必要参数'}), 400
    
    # 不允许删除主开发者账号
    if user_id == 'dev-001':
        return jsonify({'error': '不能删除主开发者账号'}), 403
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 首先检查操作者是否为开发者
        cursor.execute('''
        SELECT is_developer FROM users WHERE id = ?
        ''', (admin_id,))
        
        admin_result = cursor.fetchone()
        
        if not admin_result or not bool(admin_result[0]):
            conn.close()
            return jsonify({'error': '无权限执行此操作'}), 403
        
        # 检查要删除的用户是否存在
        cursor.execute('''
        SELECT id FROM users WHERE id = ?
        ''', (user_id,))
        
        if not cursor.fetchone():
            conn.close()
            return jsonify({'error': '用户不存在'}), 404
        
        # 删除用户相关数据
        cursor.execute('DELETE FROM user_ratings WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM user_feedback WHERE user_id = ?', (user_id,))
        cursor.execute('DELETE FROM chat_history WHERE user_id = ?', (user_id,))
        
        # 删除用户
        cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        logger.info(f"管理员 {admin_id} 删除了用户 {user_id}")
        
        return jsonify({
            'message': '用户删除成功',
            'user_id': user_id
        })
    except Exception as e:
        logger.error(f"删除用户时出错: {str(e)}", exc_info=True)
        return jsonify({'error': '删除用户时出错'}), 500

def open_browser():
    """在新线程中打开浏览器"""
    # 等待服务器启动
    time.sleep(1.5)
    webbrowser.open('http://127.0.0.1:5000')

if __name__ == '__main__':
    logger.info("启动音乐推荐系统应用...")
    # 启动一个线程来打开浏览器
    threading.Thread(target=open_browser).start()
    app.run(debug=True, use_reloader=False) 