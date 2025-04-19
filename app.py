"""
音乐推荐系统主应用程序入口点
这个文件导入重组后的模块，并启动Flask应用程序
"""

import sys
import os
import logging
import dotenv
import webbrowser
import threading
import time

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 加载环境变量
logger.info("加载环境变量...")
dotenv_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')
if os.path.exists(dotenv_path):
    dotenv.load_dotenv(dotenv_path)
    logger.info(f"从 {dotenv_path} 加载环境变量")
else:
    logger.warning("未找到.env文件，将使用系统环境变量")

# 设置默认环境变量（如果未在.env文件中指定）
os.environ.setdefault('USE_MSD', 'true')  # 默认使用百万歌曲数据集
os.environ.setdefault('DATA_DIR', 'processed_data')  # 默认数据目录
os.environ.setdefault('FORCE_RETRAIN', 'false')  # 默认不强制重训
os.environ.setdefault('MODEL_TYPE', 'svd')  # 默认使用SVD模型
os.environ.setdefault('SVD_N_FACTORS', '100')  # SVD模型参数: 特征数量
os.environ.setdefault('SVD_N_EPOCHS', '20')  # SVD模型参数: 训练轮数
os.environ.setdefault('SVD_REG_ALL', '0.05')  # SVD模型参数: 正则化参数
os.environ.setdefault('CONTENT_WEIGHT', '0.3')  # 混合推荐中内容推荐的权重
os.environ.setdefault('TOP_N', '10')  # 推荐结果数量

# 将项目根目录添加到Python路径
root_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(root_dir)

# 设置工作目录
os.chdir(root_dir)
logger.info(f"设置工作目录为: {root_dir}")

# 导入后端API模块
from backend.api.app import app

# 验证静态文件夹和模板文件夹路径
static_folder = os.path.join(root_dir, 'frontend', 'static')
template_folder = os.path.join(root_dir, 'frontend', 'templates')

if os.path.exists(static_folder):
    logger.info(f"静态文件夹存在: {static_folder}")
else:
    logger.error(f"静态文件夹不存在: {static_folder}")

if os.path.exists(template_folder):
    logger.info(f"模板文件夹存在: {template_folder}")
else:
    logger.error(f"模板文件夹不存在: {template_folder}")

# 定义浏览器自动打开函数
def open_browser():
    """在应用启动后自动打开浏览器"""
    time.sleep(1)  # 等待服务器启动
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    url = f"http://localhost:{port}"
    
    logger.info(f"自动打开浏览器访问: {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    # 打印环境配置情况
    logger.info(f"Spotify API: {'已配置' if os.environ.get('SPOTIFY_CLIENT_ID') else '未配置'}")
    logger.info(f"Claude API: {'已配置' if os.environ.get('ANTHROPIC_API_KEY') else '未配置'}")
    logger.info(f"数据目录: {os.environ.get('DATA_DIR')}")
    logger.info(f"使用MSD: {os.environ.get('USE_MSD')}")
    logger.info(f"强制重训: {os.environ.get('FORCE_RETRAIN')}")
    logger.info(f"模型类型: {os.environ.get('MODEL_TYPE')}")
    logger.info(f"混合权重: {os.environ.get('CONTENT_WEIGHT')}")
    
    # 启动浏览器线程
    threading.Timer(1.5, open_browser).start()
    
    # 启动Flask应用程序
    host = os.environ.get('HOST', '0.0.0.0')
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'true').lower() == 'true'
    
    logger.info(f"启动服务器: {host}:{port}, 调试模式: {debug}")
    app.run(debug=debug, host=host, port=port) 