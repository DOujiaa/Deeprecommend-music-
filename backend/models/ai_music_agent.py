import requests
import json
import sqlite3
import re
import os
import logging
from .recommendation_engine import MusicRecommender
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from backend.utils.ai_service import AIService
from backend.models.emotion_analyzer import EmotionAnalyzer

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MusicRecommenderAgent:
    """音乐推荐AI代理，结合AI对话能力与推荐引擎"""
    
    def __init__(self, db_path='../../music_recommender.db', spotify_client_id=None, spotify_client_secret=None, sevend_api_key=None, recommender=None, hkbu_api_key=None, data_dir=None, use_msd=False):
        """
        初始化音乐推荐代理
        
        参数:
            db_path: 数据库路径
            spotify_client_id: Spotify API客户端ID
            spotify_client_secret: Spotify API客户端密钥
            sevend_api_key: 7digital API密钥
            recommender: 可选，外部推荐器实例
            hkbu_api_key: HKBU API密钥，用于AI情绪分析
            data_dir: 数据目录路径 (用于兼容app.py中的初始化方式)
            use_msd: 是否使用百万歌曲数据集 (用于兼容app.py中的初始化方式)
        """
        self.db_path = db_path
        
        # 初始化API密钥
        self.hkbu_api_key = hkbu_api_key or os.environ.get('HKBU_API_KEY', "333cac1b-8367-480e-b2e7-8fa06024dd14")
        
        # 初始化AI服务
        self.ai_service = AIService(api_key=self.hkbu_api_key)
        logger.info("AI服务初始化完成")
        
        # 初始化情绪分析器
        self.emotion_analyzer = EmotionAnalyzer(api_key=self.hkbu_api_key)
        logger.info("情绪分析器初始化完成")
        
        # 初始化音乐推荐器，如果提供了外部推荐器则使用它，否则创建新实例
        if recommender:
            self.recommender = recommender
            logger.info("使用外部提供的音乐推荐器实例")
        else:
            # 如果提供了data_dir，就使用它
            if data_dir:
                self.recommender = MusicRecommender(data_dir=data_dir, use_msd=use_msd)
                logger.info(f"创建新的音乐推荐器实例 (data_dir={data_dir}, use_msd={use_msd})")
            else:
                self.recommender = MusicRecommender(db_path)
                logger.info("创建新的音乐推荐器实例 (使用db_path)")
        
        # 初始化Spotify客户端
        self.spotify_client_id = spotify_client_id or os.environ.get('SPOTIFY_CLIENT_ID')
        self.spotify_client_secret = spotify_client_secret or os.environ.get('SPOTIFY_CLIENT_SECRET')
        
        if self.spotify_client_id and self.spotify_client_secret:
            try:
                self.spotify = spotipy.Spotify(
                    auth_manager=SpotifyClientCredentials(
                        client_id=self.spotify_client_id,
                        client_secret=self.spotify_client_secret
                    )
                )
                logger.info("Spotify客户端初始化成功")
            except Exception as e:
                self.spotify = None
                logger.error(f"Spotify客户端初始化失败: {e}")
        else:
            self.spotify = None
            logger.warning("未提供Spotify凭据，Spotify功能将不可用")
        
        # 7digital API配置
        self.sevend_api_key = sevend_api_key or os.environ.get('SEVEN_DIGITAL_API_KEY')
        if not self.sevend_api_key:
            logger.warning("未提供7digital API密钥，预览功能可能受限")
        
        # 初始化对话历史记录
        self.conversation_history = []
        logger.info("音乐推荐代理初始化完成")
        
        self.current_user_id = None
        
    def process_message(self, user_id, user_message):
        """处理用户消息并返回回复"""
        self.current_user_id = user_id
        
        # 保存消息历史
        self.conversation_history.append({"role": "user", "content": user_message})
        
        # 检测意图
        intent = self._detect_intent(user_message)
        logger.info(f"检测到意图: {intent}")
        
        if intent == "get_recommendations":
            # 生成推荐
            if self.recommender:
                recommendations = self.recommender.get_hybrid_recommendations(user_id, top_n=5)
                ai_response = self._format_recommendations(recommendations)
            else:
                ai_response = "抱歉，推荐系统暂时不可用。请稍后再试。"
        
        elif intent == "song_info":
            # 尝试提取歌曲名称
            song_name = self._extract_song_name(user_message)
            if song_name:
                ai_response = self._get_song_info(song_name)
            else:
                ai_response = "抱歉，我无法确定您询问的是哪首歌曲。请提供具体的歌曲名称。"
        
        elif intent == "artist_info":
            # 尝试提取艺术家名称
            artist_name = self._extract_artist_name(user_message)
            if artist_name:
                ai_response = self._get_artist_info(artist_name)
            else:
                ai_response = "抱歉，我无法确定您询问的是哪位艺术家。请提供具体的艺术家名称。"
        
        elif intent == "artist_recommendations":
            # 尝试提取艺术家名称并推荐该艺术家的歌曲
            artist_name = self._extract_artist_name(user_message)
            if artist_name and self.recommender:
                recommendations = self.recommender.get_recommendations_by_artist(artist_name)
                ai_response = self._format_recommendations(recommendations, 
                                                          intro_text=f"以下是{artist_name}的热门歌曲：")
            else:
                ai_response = "抱歉，我无法推荐该艺术家的歌曲。请确认艺术家名称或稍后再试。"
        
        elif intent == "rate_song":
            # 尝试提取评分信息
            song_name, rating = self._extract_rating_info(user_message)
            if song_name and rating:
                ai_response = self._save_rating(user_id, song_name, rating)
            else:
                ai_response = "抱歉，我无法理解您的评分。请指明歌曲名称和1-5之间的评分。"
        
        elif intent == "feedback":
            # 尝试提取反馈信息
            song_name, feedback = self._extract_feedback(user_message)
            if song_name and feedback:
                ai_response = self._save_feedback(user_id, song_name, feedback)
            else:
                ai_response = "抱歉，我无法理解您的反馈。请明确表示您喜欢或不喜欢某首歌曲。"
        
        elif intent == "preview_song":
            # 尝试提取歌曲名称并获取预览
            song_name = self._extract_song_name(user_message)
            artist_name = self._extract_artist_name(user_message)
            if song_name:
                preview_url = self._get_preview_url(song_name, artist_name)
                if preview_url:
                    ai_response = f"您可以在这里试听《{song_name}》: {preview_url}"
                else:
                    ai_response = f"抱歉，我无法找到歌曲《{song_name}》的试听链接。"
            else:
                ai_response = "抱歉，我无法确定您想试听哪首歌曲。请提供具体的歌曲名称。"
        
        elif intent == "emotion_comfort":
            # 分析情绪并提供安慰和音乐推荐
            ai_response = self._provide_emotion_based_recommendation(user_id, user_message)
        
        else:
            # 使用Claude API生成通用回复
            ai_response = self._get_claude_response(user_message)
        
        # 保存AI回复到历史
        self.conversation_history.append({"role": "assistant", "content": ai_response})
        
        return ai_response
    
    def _detect_intent(self, message):
        """检测用户意图"""
        message = message.lower()
        
        if any(word in message for word in ["推荐", "recommend", "喜欢什么", "听什么", "推荐一些", "推荐歌曲"]):
            if any(word in message for word in ["艺术家", "歌手", "乐队", "音乐家"]):
                return "artist_recommendations"
            return "get_recommendations"
        
        elif any(word in message for word in ["这首歌", "歌曲信息", "告诉我关于这首歌", "歌词", "歌曲"]) and ("?" in message or "？" in message):
            return "song_info"
        
        elif any(word in message for word in ["艺术家", "歌手", "乐队", "音乐家"]) and ("?" in message or "？" in message):
            return "artist_info"
        
        elif any(word in message for word in ["评分", "打分", "评价", "rating", "rate"]):
            return "rate_song"
        
        elif any(word in message for word in ["喜欢", "不喜欢", "讨厌", "like", "dislike"]):
            return "feedback"
        
        elif any(word in message for word in ["试听", "听一下", "preview", "播放", "听听"]):
            return "preview_song"
            
        # 情绪相关意图检测
        elif any(word in message for word in ["难过", "伤心", "悲伤", "压力", "焦虑", "开心", "高兴", "兴奋", 
                                             "生气", "愤怒", "无聊", "疲惫", "孤独", "思念", "失落", 
                                             "想哭", "不开心", "抑郁", "烦躁", "心情"]):
            return "emotion_comfort"
        
        return "general"
    
    def _extract_song_name(self, message):
        """从消息中提取歌曲名称"""
        # 此处仅为简单示例，实际应用中可使用NER或其他更复杂的方法
        
        # 尝试从书名号中提取
        if "《" in message and "》" in message:
            start_idx = message.find("《")
            end_idx = message.find("》", start_idx + 1)
            if end_idx > start_idx:
                return message[start_idx + 1:end_idx]
                
        # 尝试从引号中提取
        if """ in message and """ in message:
            start_idx = message.find(""")
            end_idx = message.find(""", start_idx + 1)
            if end_idx > start_idx:
                return message[start_idx + 1:end_idx]
        
        # 尝试从指示词后提取
        indicators = ["歌曲", "歌", "song", "track"]
        for indicator in indicators:
            if indicator in message:
                parts = message.split(indicator)
                if len(parts) > 1 and parts[1].strip():
                    return parts[1].strip().split()[0]
        
        return None
    
    def _extract_artist_name(self, message):
        """从消息中提取艺术家名称"""
        indicators = ["艺术家", "歌手", "乐队", "artist", "singer", "band"]
        
        for indicator in indicators:
            if indicator in message:
                parts = message.split(indicator)
                if len(parts) > 1 and parts[1].strip():
                    return parts[1].strip().split()[0]
        
        # 尝试提取常见歌手名字的格式，如"周杰伦的歌"
        pattern = r'([A-Za-z\u4e00-\u9fa5]+)(的歌|的音乐)'
        match = re.search(pattern, message)
        if match:
            return match.group(1)
            
        return None
    
    def _extract_rating_info(self, message):
        """从消息中提取歌曲名称和评分"""
        song_name = self._extract_song_name(message)
        
        # 查找1-5之间的数字
        rating_match = re.search(r'([1-5])分', message) or re.search(r'([1-5])\s?stars', message) or re.search(r'rating\s?([1-5])', message)
        rating = int(rating_match.group(1)) if rating_match else None
        
        return song_name, rating
    
    def _extract_feedback(self, message):
        """从消息中提取歌曲名称和反馈（喜欢/不喜欢）"""
        song_name = self._extract_song_name(message)
        
        if "喜欢" in message or "like" in message.lower():
            feedback = "like"
        elif "不喜欢" in message or "讨厌" in message or "dislike" in message.lower() or "hate" in message.lower():
            feedback = "dislike"
        else:
            feedback = None
            
        return song_name, feedback
    
    def _format_recommendations(self, recommendations, intro_text=None):
        """格式化推荐结果为易读的回复"""
        if not recommendations:
            return "很抱歉，目前无法为您生成推荐。请先对一些歌曲进行评分，这样我可以更好地了解您的音乐偏好。"
        
        response = intro_text or "根据您的偏好，我为您推荐以下歌曲：\n\n"
        
        for i, rec in enumerate(recommendations):
            response += f"{i+1}. 《{rec['track_name']}》 - {rec['artist_name']}\n"
            response += f"   {rec['explanation']}\n\n"
        
        response += "您对这些推荐满意吗？如果喜欢其中某首歌曲，可以告诉我\"我喜欢第X首\"或\"试听第X首\"。"
        
        return response
    
    def _get_song_info(self, song_name):
        """获取歌曲信息"""
        logger.info(f"获取歌曲信息: {song_name}")
        
        # 先使用MSD数据集查找
        if self.recommender and hasattr(self.recommender, 'songs_metadata'):
            matching_songs = self.recommender.songs_metadata[
                self.recommender.songs_metadata['track_name'].str.contains(song_name, case=False)
            ]
            
            if len(matching_songs) > 0:
                song_info = matching_songs.iloc[0]
                artist_name = song_info['artist_name']
                
                # 尝试从Spotify获取更多信息
                spotify_info = self._get_spotify_data(song_name, artist_name)
                
                if spotify_info:
                    # 添加预览URL
                    preview_url = self._get_preview_url(song_name, artist_name)
                    preview_text = f"\n\n您可以在这里试听: {preview_url}" if preview_url else ""
                    
                    return (f"《{spotify_info['name']}》是由{spotify_info['artist']}演唱的歌曲，"
                           f"收录在专辑《{spotify_info['album']}》中，于{spotify_info['release_date']}发行。"
                           f"这首歌在Spotify的流行度为{spotify_info['popularity']}/100。{preview_text}")
                
                # 如果没有Spotify信息，使用MSD数据
                album_name = song_info.get('album_name', '未知专辑')
                artist_familiarity = song_info.get('artist_familiarity', 0)
                release_year = song_info.get('year', 0)
                year_info = f"于{release_year}年发行" if release_year and release_year > 0 else ""
                
                return f"《{song_name}》是{artist_name}演唱的歌曲，收录在专辑《{album_name}》中，{year_info}。"
        
        # 如果MSD没有找到，使用Spotify
        if self.spotify:
            try:
                # 搜索歌曲
                spotify_info = self._get_spotify_data(song_name)
                
                if spotify_info:
                    # 添加预览URL
                    preview_url = self._get_preview_url(song_name, spotify_info['artist'])
                    preview_text = f"\n\n您可以在这里试听: {preview_url}" if preview_url else ""
                    
                    return (f"《{spotify_info['name']}》是由{spotify_info['artist']}演唱的歌曲，"
                           f"收录在专辑《{spotify_info['album']}》中，于{spotify_info['release_date']}发行。"
                           f"这首歌在Spotify的流行度为{spotify_info['popularity']}/100。{preview_text}")
            except Exception as e:
                logger.error(f"获取歌曲信息出错: {e}")
                pass
        
        return f"关于《{song_name}》，我没有找到太多信息。您想了解这首歌的哪些方面呢？"
    
    def _get_spotify_data(self, song_name, artist_name=None):
        """使用Spotify API获取更详细的歌曲信息"""
        if not self.spotify:
            return None
        
        try:
            # 构建查询
            query = f"track:{song_name}"
            if artist_name:
                query += f" artist:{artist_name}"
            
            # 搜索歌曲
            results = self.spotify.search(q=query, type='track', limit=1)
            
            if not results['tracks']['items']:
                return None
                
            track = results['tracks']['items'][0]
            
            # 提取有用信息
            track_info = {
                'name': track['name'],
                'artist': track['artists'][0]['name'],
                'album': track['album']['name'],
                'release_date': track['album']['release_date'],
                'duration_ms': track['duration_ms'],
                'popularity': track['popularity'],
                'preview_url': track['preview_url'],
                'album_image': track['album']['images'][0]['url'] if track['album']['images'] else None,
                'external_url': track['external_urls']['spotify'] if 'spotify' in track['external_urls'] else None
            }
            
            return track_info
        
        except Exception as e:
            logger.error(f"获取Spotify数据出错: {e}")
            return None
    
    def _get_artist_info(self, artist_name):
        """获取艺术家信息"""
        logger.info(f"获取艺术家信息: {artist_name}")
        
        # 先使用MSD数据集查找
        artist_info_text = ""
        artist_songs = []
        
        if self.recommender and hasattr(self.recommender, 'songs_metadata'):
            matching_artists = self.recommender.songs_metadata[
                self.recommender.songs_metadata['artist_name'].str.contains(artist_name, case=False)
            ]
            
            if len(matching_artists) > 0:
                # 获取该艺术家的热门歌曲
                artist_songs = matching_artists['track_name'].unique()[:5]  # 取前5首
                
                # 获取艺术家信息
                artist_info = matching_artists.iloc[0]
                familiarity = artist_info.get('artist_familiarity', 0)
                popularity = "较为知名" if familiarity > 0.5 else "小众"
                
                artist_info_text = f"{artist_name}是一位{popularity}音乐人，在我的数据库中收录了{len(matching_artists)}首歌曲。"
        
        # 尝试从Spotify获取更多信息
        if self.spotify:
            try:
                # 搜索艺术家
                results = self.spotify.search(q=f'artist:{artist_name}', type='artist', limit=1)
                if results['artists']['items']:
                    artist = results['artists']['items'][0]
                    
                    # 格式化回复
                    genres = ", ".join(artist['genres']) if artist['genres'] else "未知"
                    followers = artist['followers']['total']
                    popularity = artist['popularity']
                    
                    artist_info_text = (f"{artist['name']}是一位音乐人，音乐风格包括{genres}。"
                                      f"在Spotify上有{followers}位粉丝，流行度为{popularity}/100。")
            except Exception as e:
                logger.error(f"获取艺术家Spotify信息出错: {e}")
                # 如果Spotify失败，使用之前的MSD信息
                pass
        
        # 如果有歌曲信息，添加到回复中
        if artist_songs:
            artist_info_text += f"\n\n{artist_name}的代表作品包括："
            for i, song in enumerate(artist_songs):
                artist_info_text += f"\n{i+1}. 《{song}》"
            
            # 添加推荐信息
            if self.recommender:
                artist_info_text += f"\n\n如果您想听{artist_name}的音乐，可以说\"推荐{artist_name}的歌曲\"。"
        
        if artist_info_text:
            return artist_info_text
        else:
            return f"关于{artist_name}，我没有找到太多信息。您想了解这位艺术家的哪些方面呢？"
    
    def _save_rating(self, user_id, song_name, rating):
        """保存用户评分"""
        # 首先尝试找到歌曲ID
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 通过模糊匹配查找歌曲
        cursor.execute("""
        SELECT song_id FROM songs_metadata 
        WHERE track_name LIKE ? LIMIT 1
        """, (f"%{song_name}%",))
        
        result = cursor.fetchone()
        
        if result:
            track_id = result[0]
            
            # 保存评分
            cursor.execute("""
            INSERT OR REPLACE INTO user_ratings (user_id, song_id, rating, timestamp)
            VALUES (?, ?, ?, datetime('now'))
            """, (user_id, track_id, rating))
            
            conn.commit()
            conn.close()
            
            return f"我已记录您对《{song_name}》的{rating}分评价。感谢您的反馈！基于这个评分，我会为您推荐更符合口味的歌曲。"
        else:
            conn.close()
            return f"抱歉，我找不到《{song_name}》这首歌。请确认歌曲名称是否正确。"
    
    def _save_feedback(self, user_id, song_name, feedback):
        """保存用户反馈"""
        # 首先尝试找到歌曲ID
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 通过模糊匹配查找歌曲
        cursor.execute("""
        SELECT song_id FROM songs_metadata 
        WHERE track_name LIKE ? LIMIT 1
        """, (f"%{song_name}%",))
        
        result = cursor.fetchone()
        
        if result:
            track_id = result[0]
            
            # 保存反馈
            cursor.execute("""
            INSERT INTO user_feedback (user_id, song_id, feedback, timestamp)
            VALUES (?, ?, ?, datetime('now'))
            """, (user_id, track_id, feedback))
            
            # 同时更新评分
            rating = 5 if feedback == "like" else 1
            cursor.execute("""
            INSERT OR REPLACE INTO user_ratings (user_id, song_id, rating, timestamp)
            VALUES (?, ?, ?, datetime('now'))
            """, (user_id, track_id, rating))
            
            conn.commit()
            conn.close()
            
            feedback_text = "喜欢" if feedback == "like" else "不喜欢"
            return f"我已记录您{feedback_text}《{song_name}》。我会据此调整未来的推荐。"
        else:
            conn.close()
            return f"抱歉，我找不到《{song_name}》这首歌。请确认歌曲名称是否正确。"
    
    def _get_preview_url(self, song_name, artist_name=None):
        """获取歌曲预览URL"""
        # 首先尝试从Spotify获取预览URL
        if self.spotify:
            spotify_info = self._get_spotify_data(song_name, artist_name)
            if spotify_info and spotify_info['preview_url']:
                return spotify_info['preview_url']
        
        # 如果没有Spotify预览URL或Spotify不可用，尝试使用7digital
        if self.sevend_api_key:
            # 尝试根据歌曲和艺术家找到7digital的trackid
            track_id = self._get_trackid_from_text_search(song_name, artist_name or "")
            if track_id:
                _, digital_id = track_id
                preview_url = self._get_preview_from_trackid(digital_id)
                if preview_url:
                    return preview_url
        
        # 都失败了，返回None
        return None
    
    def _get_trackid_from_text_search(self, title, artistname=''):
        """
        搜索艺术家+标题使用7digital搜索API
        返回 None 如果有问题，或者元组 (title,trackid)
        """
        if not self.digital7_api_key:
            return None
            
        url = 'http://api.7digital.com/1.2/track/search?'
        url += 'oauth_consumer_key='+self.digital7_api_key
        query = title
        if artistname != '':
            query = artistname + ' ' + query
        query = requests.utils.quote(query)
        url += '&q='+query
        
        try:
            response = requests.get(url)
            response.raise_for_status()  # 如果请求失败，会引发异常
            
            # 解析XML响应
            import xml.etree.ElementTree as ET
            xmldoc = ET.fromstring(response.text)
            
            # 检查状态
            status = xmldoc.get('status')
            if status != 'ok':
                return None
                
            # 查找搜索结果
            search_results = xmldoc.findall('.//searchResult')
            if not search_results:
                return None
                
            # 获取第一个结果
            track = search_results[0].find('.//track')
            if track is None:
                return None
                
            track_title = track.find('.//title').text
            track_id = int(track.get('id'))
            
            return (track_title, track_id)
            
        except Exception as e:
            logger.error(f"使用7digital搜索时出错: {e}")
            return None
    
    def _get_preview_from_trackid(self, trackid):
        """
        请求特定曲目的预览，获取XML答案
        在使用给定的曲目ID调用API后，返回预览URL
        """
        if not self.digital7_api_key:
            return None
        
        url = 'http://api.7digital.com/1.2/track/preview?redirect=false'
        url += '&trackid='+str(trackid)
        url += '&oauth_consumer_key='+self.digital7_api_key
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            
            # 解析XML响应
            import xml.etree.ElementTree as ET
            xmldoc = ET.fromstring(response.text)
            
            # 检查状态
            status = xmldoc.get('status')
            if status != 'ok':
                return None
                
            # 获取预览URL
            url_elem = xmldoc.find('.//url')
            if url_elem is not None and url_elem.text:
                return url_elem.text
            
            return None
            
        except Exception as e:
            logger.error(f"获取7digital预览URL时出错: {e}")
            return None
    
    def _get_claude_response(self, user_message):
        """调用AI服务获取回复"""
        # 构建对话历史
        messages = []
        if len(self.conversation_history) > 0:
            # 取最近的几轮对话
            for msg in self.conversation_history[-4:]:
                messages.append(msg)
        
        # 添加当前用户消息
        messages.append({"role": "user", "content": user_message})
        
        # 设置系统指令
        system = "你是一位音乐推荐助手，擅长讨论音乐并提供推荐。请用友好和礼貌的中文回答用户的问题。回答中要简洁明确，不要自我介绍。"
        
        # 使用AI服务发送请求
        try:
            return self.ai_service.send_message(messages, system=system)
        except Exception as e:
            logger.error(f"AI服务调用错误: {e}")
            return "抱歉，我暂时无法回应您的问题。请稍后再试。"
    
    def _provide_emotion_based_recommendation(self, user_id, message):
        """根据用户情绪分析结果提供安慰和推荐歌曲"""
        logger.info(f"为用户 {user_id} 提供基于情绪的推荐")
        
        try:
            # 使用情绪分析器分析用户情绪
            emotion_analysis = self.emotion_analyzer.analyze_emotion(message)
            
            emotion = emotion_analysis.get('emotion', 'neutral')
            intensity = emotion_analysis.get('intensity', 0.5)
            description = emotion_analysis.get('description', '您的情绪状态')
            music_suggestion = emotion_analysis.get('music_suggestion', '舒缓的流行音乐')
            
            logger.info(f"情绪分析结果: {emotion}, 强度: {intensity}, 音乐建议: {music_suggestion}")
            
            # 从情绪分析器获取安慰话语
            comfort_message = self._get_comfort_message(emotion, intensity, description)
            
            # 获取基于情绪的音乐推荐
            recommendations = self._get_emotion_based_songs(user_id, emotion, music_suggestion)
            
            # 组合回复
            response = f"{comfort_message}\n\n基于您的情绪状态，我为您推荐以下歌曲："
            
            for i, rec in enumerate(recommendations):
                response += f"\n{i+1}. 《{rec['track_name']}》 - {rec['artist_name']}"
                if 'explanation' in rec:
                    response += f"\n   {rec['explanation']}"
            
            response += "\n\n希望这些歌曲能够陪伴您度过这段时光。如果您想试听其中某首歌曲，请告诉我。"
            
            return response
            
        except Exception as e:
            logger.error(f"生成情绪安慰推荐时出错: {e}")
            # 如果出错，提供一个通用回复
            return "我注意到您的情绪波动，音乐是调节情绪的好方法。让我为您推荐一些舒缓的歌曲，希望能够帮助您改善心情。"
    
    def analyze_user_emotion(self, message):
        """
        分析用户消息中的情绪，返回情绪类型、强度和描述
        
        参数:
            message: 用户消息文本
            
        返回:
            情绪分析结果，包含emotion、intensity、description和music_suggestion字段
        """
        logger.info(f"开始分析用户情绪: {message[:50]}...")
        
        try:
            # 使用情绪分析器分析情绪
            emotion_data = self.emotion_analyzer.analyze_emotion(message)
            logger.info(f"情绪分析完成: {emotion_data}")
            return emotion_data
        except Exception as e:
            logger.error(f"情绪分析失败: {e}")
            # 返回默认情绪
            return {
                "emotion": "neutral",
                "intensity": 0.5,
                "description": "无法确定情绪状态",
                "music_suggestion": "流行音乐"
            }

    def get_comfort_message(self, emotion, intensity, description):
        """
        根据情绪生成安慰消息
        
        参数:
            emotion: 情绪类型
            intensity: 情绪强度
            description: 情绪描述
            
        返回:
            安慰消息
        """
        logger.info(f"为情绪'{emotion}'(强度:{intensity})生成安慰消息")
        
        try:
            # 使用情绪分析器生成安慰消息
            comfort_message = self._get_comfort_message(emotion, intensity, description)
            logger.info(f"生成安慰消息: {comfort_message[:50]}...")
            return comfort_message
        except Exception as e:
            logger.error(f"生成安慰消息失败: {e}")
            # 使用内部方法提供默认安慰消息
            return self._get_comfort_message(emotion, intensity, description)

    def _get_comfort_message(self, emotion, intensity, description):
        """根据情绪类型和强度生成安慰话语"""
        if emotion in ['sad', 'depressed', 'upset', 'disappointed', 'heartbroken', 'melancholy']:
            if intensity > 0.7:
                return f"我理解您现在可能感到很沮丧。{description}的感觉确实很难受，请记住这些情绪都是暂时的，您不必独自面对。"
            else:
                return f"看起来您有些低落。{description}是很常见的情绪，有时候通过音乐发泄一下情感是很好的方式。"
            
        elif emotion in ['anxious', 'stressed', 'worried', 'nervous', 'overwhelmed']:
            if intensity > 0.7:
                return f"我能感受到您现在很焦虑。{description}时，音乐可以帮助我们平静下来，调整呼吸，找回平静。"
            else:
                return f"您似乎有些紧张。{description}的时候，适当放松一下，听些舒缓的音乐或许会有所帮助。"
            
        elif emotion in ['angry', 'frustrated', 'irritated', 'annoyed']:
            if intensity > 0.7:
                return f"您现在似乎很生气。{description}的感觉确实令人难受，但请记住，找到释放情绪的健康方式很重要。"
            else:
                return f"您看起来有些烦躁。{description}是很正常的情绪反应，有时候通过音乐可以帮助缓解这种感觉。"
            
        elif emotion in ['happy', 'excited', 'elated', 'joyful', 'cheerful']:
            return f"您现在看起来心情很好！{description}真是美妙的感觉，让我们用欢快的音乐来延续这种好心情。"
        
        elif emotion in ['nostalgic', 'sentimental', 'longing']:
            return f"您似乎有些怀旧。{description}让我们回忆过去的美好时光，音乐常常能唤起那些珍贵的记忆。"
        
        elif emotion in ['bored', 'tired', 'exhausted', 'fatigued']:
            return f"您可能感到有些疲惫或无聊。{description}时，一些振奋精神的音乐或许能帮助您重新找回活力。"
        
        elif emotion in ['lonely', 'isolated', 'abandoned']:
            return f"您似乎感到有些孤独。{description}是我们都会经历的情绪，音乐有时候能成为心灵的陪伴。"
        
        else:  # neutral or other emotions
            return f"谢谢您分享您的心情。音乐是表达和调节情绪的好方法，让我为您选择一些适合现在心情的歌曲。"

    def _get_emotion_based_songs(self, user_id, emotion, music_suggestion):
        """根据情绪和音乐建议获取推荐歌曲"""
        try:
            recommendations = []
            
            # 尝试通过推荐引擎获取相关歌曲
            if self.recommender:
                # 从用户的评分历史中获取符合情绪类型的歌曲
                user_recs = self.recommender.get_hybrid_recommendations(user_id, top_n=3)
                if user_recs:
                    for rec in user_recs:
                        rec['explanation'] = f"根据您的历史喜好，这首歌可能适合您现在的心情"
                        recommendations.append(rec)
            
            # 如果推荐不足，添加基于情绪类型的通用推荐
            if len(recommendations) < 5:
                # 根据不同情绪类型选择合适的热门歌曲
                mood_songs = self._get_mood_specific_songs(emotion, music_suggestion, 5 - len(recommendations))
                recommendations.extend(mood_songs)
            
            return recommendations
            
        except Exception as e:
            logger.error(f"获取情绪歌曲推荐时出错: {e}")
            # 如果出错，返回一些通用音乐推荐
            return [
                {"track_name": "Yesterday", "artist_name": "The Beatles", "explanation": "经典怀旧歌曲，适合沉思的时刻"},
                {"track_name": "Weightless", "artist_name": "Marconi Union", "explanation": "这首歌被科学证明有助于减轻焦虑"},
                {"track_name": "Happy", "artist_name": "Pharrell Williams", "explanation": "欢快的节奏，有助于提升情绪"},
                {"track_name": "Someone Like You", "artist_name": "Adele", "explanation": "深情的歌曲，适合抒发情感"},
                {"track_name": "Heal the World", "artist_name": "Michael Jackson", "explanation": "温暖人心的歌曲，带来希望"}
            ]

    def _get_mood_specific_songs(self, emotion, music_suggestion, count=5):
        """获取特定情绪类型的歌曲推荐"""
        # 基于情绪类型的预设歌曲集合
        emotion_songs = {
            'happy': [
                {"track_name": "Happy", "artist_name": "Pharrell Williams", "explanation": "欢快的节奏，让人情不自禁想跳舞"},
                {"track_name": "I Gotta Feeling", "artist_name": "Black Eyed Peas", "explanation": "充满活力的歌曲，适合提升情绪"},
                {"track_name": "Uptown Funk", "artist_name": "Mark Ronson ft. Bruno Mars", "explanation": "节奏感强烈，让人心情愉悦"},
                {"track_name": "好日子", "artist_name": "宋祖英", "explanation": "欢快喜庆的中文歌曲，传递积极能量"},
                {"track_name": "阳光总在风雨后", "artist_name": "许美静", "explanation": "温暖励志的歌曲，带来希望"}
            ],
            'sad': [
                {"track_name": "Someone Like You", "artist_name": "Adele", "explanation": "深情的歌声，适合宣泄情感"},
                {"track_name": "Skinny Love", "artist_name": "Birdy", "explanation": "忧伤的旋律，共鸣心灵的孤独"},
                {"track_name": "Say Something", "artist_name": "A Great Big World", "explanation": "触动人心的伤感歌曲"},
                {"track_name": "后来", "artist_name": "刘若英", "explanation": "经典的怀旧伤感歌曲，适合回忆过去"},
                {"track_name": "晴天", "artist_name": "周杰伦", "explanation": "柔和忧伤的旋律，回忆青春的味道"}
            ],
            'anxious': [
                {"track_name": "Weightless", "artist_name": "Marconi Union", "explanation": "被科学证明能减轻焦虑的歌曲"},
                {"track_name": "Breathe Me", "artist_name": "Sia", "explanation": "抚慰心灵的旋律，让人慢慢平静下来"},
                {"track_name": "Intro", "artist_name": "The xx", "explanation": "简约清澈的节奏，有助于调整呼吸"},
                {"track_name": "平凡之路", "artist_name": "朴树", "explanation": "深沉的歌声，让人找到内心的力量"},
                {"track_name": "菊次郎的夏天", "artist_name": "久石让", "explanation": "治愈系纯音乐，缓解紧张情绪"}
            ],
            'angry': [
                {"track_name": "Numb", "artist_name": "Linkin Park", "explanation": "强烈的节奏，适合发泄情绪"},
                {"track_name": "Stronger", "artist_name": "Kanye West", "explanation": "节奏强劲，帮助转化负面情绪"},
                {"track_name": "fighters", "artist_name": "Foo Fighters", "explanation": "充满力量的摇滚乐，释放压力"},
                {"track_name": "Beyond", "artist_name": "Beyond", "explanation": "经典摇滚，充满力量感"},
                {"track_name": "怒放的生命", "artist_name": "汪峰", "explanation": "高亢的歌声，唤起内心的力量"}
            ],
            'nostalgic': [
                {"track_name": "Yesterday", "artist_name": "The Beatles", "explanation": "经典怀旧歌曲，适合回忆过去"},
                {"track_name": "Reminiscing", "artist_name": "The Little River Band", "explanation": "轻柔的旋律，唤起美好回忆"},
                {"track_name": "罗大佑", "artist_name": "光阴的故事", "explanation": "经典怀旧歌曲，回味过去时光"},
                {"track_name": "童年", "artist_name": "罗大佑", "explanation": "唤起童年记忆的经典歌曲"},
                {"track_name": "往事只能回味", "artist_name": "韩宝仪", "explanation": "经典老歌，带你回到过去"}
            ],
            'neutral': [
                {"track_name": "The Scientist", "artist_name": "Coldplay", "explanation": "平和的旋律，适合静静聆听"},
                {"track_name": "Clocks", "artist_name": "Coldplay", "explanation": "经典旋律，适合各种情绪状态"},
                {"track_name": "遥远的她", "artist_name": "张学友", "explanation": "经典粤语歌曲，悠扬的旋律"},
                {"track_name": "稻香", "artist_name": "周杰伦", "explanation": "温暖励志的歌曲，适合日常聆听"},
                {"track_name": "夜空中最亮的星", "artist_name": "逃跑计划", "explanation": "充满希望的旋律，给人力量"}
            ]
        }
        
        # 根据情绪类型选择歌曲集合
        if emotion in emotion_songs:
            songs = emotion_songs[emotion]
        else:
            # 如果找不到匹配的情绪类型，使用通用歌曲集合
            songs = emotion_songs['neutral']
        
        # 如果有音乐建议，添加到解释中
        for song in songs:
            song['explanation'] += f"，这种{music_suggestion}风格的音乐可能适合您当前的心情"
        
        # 返回指定数量的歌曲
        return songs[:count]

# API接口，可集成到Flask应用中
def handle_agent_request(user_id, message):
    agent = MusicRecommenderAgent()
    return agent.process_message(user_id, message)

if __name__ == "__main__":
    # 测试代码
    agent = MusicRecommenderAgent()
    
    test_messages = [
        "你好，我是新用户",
        "我喜欢周杰伦的歌",
        "能推荐一些歌曲给我吗？",
        "我给《七里香》打4分",
        "我不喜欢摇滚乐",
        "谢谢你的推荐"
    ]
    
    for msg in test_messages:
        print(f"\n用户: {msg}")
        response = agent.process_message("test_user_123", msg)
        print(f"AI: {response}") 