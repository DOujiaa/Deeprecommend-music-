"""
7digital API集成测试脚本

用于测试7digital API的连接和功能。
"""

import os
import sys
import logging
import argparse

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 导入所需模块
from backend.utils.sevendigital_api import (
    get_trackid_from_text_search,
    get_preview_from_trackid,
    get_preview_url
)

def test_api_connection():
    """测试API连接状态"""
    # 检查环境变量是否设置
    api_key = os.environ.get('SEVENDIGITAL_API_KEY')
    api_secret = os.environ.get('SEVENDIGITAL_API_SECRET')
    
    if not api_key or api_key == 'your_api_key_here':
        logger.error("未设置7digital API密钥，请在.env文件中设置SEVENDIGITAL_API_KEY")
        return False
    
    if not api_secret or api_secret == 'your_api_secret_here':
        logger.warning("未设置7digital API密钥密钥，可能会影响某些功能")
    
    logger.info("7digital API配置已检测")
    return True

def test_search_by_title(title, artist=""):
    """测试通过标题搜索歌曲"""
    logger.info(f"搜索歌曲: {title} - {artist if artist else '(不指定艺术家)'}")
    
    result = get_trackid_from_text_search(title, artistname=artist)
    
    if result:
        found_title, track_id = result
        logger.info(f"找到匹配歌曲: {found_title} (ID: {track_id})")
        return result
    else:
        logger.error(f"未找到匹配歌曲")
        return None

def test_preview_by_trackid(track_id):
    """测试通过track ID获取预览URL"""
    logger.info(f"获取曲目ID {track_id} 的预览URL")
    
    preview_url = get_preview_from_trackid(track_id)
    
    if preview_url:
        logger.info(f"找到预览URL: {preview_url}")
        return preview_url
    else:
        logger.error(f"未找到预览URL")
        return None

def test_combined_flow(title, artist=""):
    """测试完整流程：搜索歌曲并获取预览URL"""
    logger.info(f"测试完整流程: {title} - {artist if artist else '(不指定艺术家)'}")
    
    preview_url = get_preview_url(track_name=title, artist_name=artist)
    
    if preview_url:
        logger.info(f"成功获取预览URL: {preview_url}")
        return preview_url
    else:
        logger.error(f"未能获取预览URL")
        return None

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='测试7digital API集成')
    parser.add_argument('--title', help='要搜索的歌曲标题', default='Shape of You')
    parser.add_argument('--artist', help='艺术家名称(可选)', default='Ed Sheeran')
    args = parser.parse_args()
    
    # 测试API连接
    if not test_api_connection():
        sys.exit(1)
    
    # 测试搜索功能
    search_result = test_search_by_title(args.title, args.artist)
    
    # 如果搜索成功，测试预览URL
    if search_result:
        _, track_id = search_result
        test_preview_by_trackid(track_id)
    
    # 测试完整流程
    test_combined_flow(args.title, args.artist)
    
    logger.info("测试完成")

if __name__ == "__main__":
    main() 