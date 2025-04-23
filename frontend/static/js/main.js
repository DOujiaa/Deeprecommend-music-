/**
 * 深度推荐音乐系统 - 主JavaScript文件
 * 包含Vue.js应用初始化和核心功能实现
 */

console.log('深度推荐音乐系统初始化开始');

// 音乐游戏变量
let musicGame = null;
let previewGame = null;

// 初始化游戏预览
setTimeout(() => {
  const previewCanvas = document.getElementById('musicPreviewCanvas');
  if (previewCanvas) {
    initGamePreview();
  }
}, 500);

function initGamePreview() {
  const canvas = document.getElementById('musicPreviewCanvas');
  if (!canvas) return;
  
  const ctx = canvas.getContext('2d');
  if (!ctx) return;
  
  // 调整canvas大小
  canvas.width = canvas.parentElement.clientWidth;
  
  // 绘制预览
  let particles = [];
  const genres = [
      { name: "流行", color: "#9B4BFF" },
      { name: "摇滚", color: "#FF5252" },
      { name: "电子", color: "#2196F3" },
      { name: "嘻哈", color: "#4CAF50" },
      { name: "古典", color: "#FFEB3B" },
      { name: "爵士", color: "#FF9800" },
  ];
  
  // 创建粒子
  for (let i = 0; i < 12; i++) {
    const genre = genres[Math.floor(Math.random() * genres.length)];
    particles.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height - canvas.height,
      size: 30,
      speed: Math.random() * 1 + 1,
      color: genre.color,
      genre: genre.name
    });
  }
  
  // 创建玩家
  const player = {
    x: canvas.width / 2 - 25,
    y: canvas.height - 50,
    width: 50,
    height: 50,
    color: '#8A2BE2'
  };
  
  function drawPreview() {
    // 清除画布
    ctx.fillStyle = '#191919';
    ctx.fillRect(0, 0, canvas.width, canvas.height);
    
    // 添加背景元素
    ctx.strokeStyle = 'rgba(138, 43, 226, 0.2)';
    for (let i = 0; i < 8; i++) {
      const x = Math.sin(Date.now() / 2000 + i) * canvas.width / 3 + canvas.width / 2;
      const y = i * canvas.height / 8;
      const width = Math.cos(Date.now() / 3000 + i) * 15 + 30;
      
      ctx.beginPath();
      ctx.arc(x, y, width, 0, Math.PI * 2);
      ctx.stroke();
    }
    
    // 绘制玩家
    ctx.fillStyle = player.color;
    ctx.beginPath();
    ctx.arc(
        player.x + player.width / 2,
        player.y + player.height / 2,
        player.width / 2,
        0,
        Math.PI * 2
    );
    ctx.fill();
    
    // 渲染粒子
    for (let i = 0; i < particles.length; i++) {
      const p = particles[i];
      
      // 更新位置
      p.y += p.speed;
      
      // 如果超出屏幕底部，重置到顶部
      if (p.y > canvas.height) {
        p.y = -p.size;
        p.x = Math.random() * canvas.width;
      }
      
      // 绘制粒子
      ctx.fillStyle = p.color;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.size / 2, 0, Math.PI * 2);
      ctx.fill();
      
      // 添加文字
      ctx.fillStyle = '#FFFFFF';
      ctx.font = '12px Arial';
      ctx.textAlign = 'center';
      ctx.fillText(p.genre, p.x, p.y + 4);
    }
    
    // 添加"点击开始游戏"文字
    ctx.fillStyle = '#FFFFFF';
    ctx.font = '18px Arial';
    ctx.textAlign = 'center';
    ctx.fillText('点击开始音乐收集游戏', canvas.width / 2, 30);
    
    requestAnimationFrame(drawPreview);
  }
  
  drawPreview();
}

// Vue.js应用实例 - 直接初始化，不包装在DOMContentLoaded事件中
window.app = new Vue({
  el: '#app',
  
  // 数据层
  data: {
    // 应用状态
    currentTab: 'login',
    isLoading: false,
    isLoadingRecommendations: false,
    currentLanguage: 'zh',
    isDeveloperMode: false,
    notifications: [],
    
    // 用户相关
    currentUser: null,
    isLoggedIn: false,
    username: '',
    email: '',
    password: '',
    newUsername: '',
    newEmail: '',
    newPassword: '',
    loginError: '',
    registerError: '',
    
    // 歌曲数据
    sampleSongs: [],
    recommendations: [],
    
    // 聊天功能
    chatMessages: [],
    currentMessage: '',
    isChatLoading: false,
    
    // 游戏数据
    gameResults: null,
    
    // 音频播放器
    currentAudio: null,
    isPlaying: false,
    currentPlayingId: null,
    
    // 情感相关数据
    userEmotion: null,
    emotionInput: '',
    showEmotionDetector: false,
    emotionDetector: null,
    
    // 添加预设音乐预览URL（这些URL可以直接播放，无需Spotify API密钥）
    previewUrls: [
        'https://p.scdn.co/mp3-preview/3eb16018c2a700240e9dfb8817b6f2d041f15eb1', // Shape of You
        'https://p.scdn.co/mp3-preview/e2f5edb569c73916235f2cadc8290b3dde522179', // Blinding Lights
        'https://p.scdn.co/mp3-preview/74456889dc17ca44897559c14ec7de20f431dd82', // Dance Monkey
        'https://p.scdn.co/mp3-preview/84a68eef8a7d26be04b81c21621f32adcf44b825', // Circles
        'https://p.scdn.co/mp3-preview/8250dc653c7abe6e89552a22c30b52b4d7414b41', // Watermelon Sugar
        'https://p.scdn.co/mp3-preview/94278c37595c695fa5178c50a07ec84aff4a87e7', // Bad Guy
        'https://p.scdn.co/mp3-preview/b3414442c1b791361a904eb74fc72796d2b0ea8e', // Don't Start Now
        'https://p.scdn.co/mp3-preview/f5e5c9bea97ed89086b73391ff26c6b13d6c0a3c', // Everything I Wanted
        'https://p.scdn.co/mp3-preview/6e31fcf3cf65888b11ba9fb28e9c9d007698b17b', // Memories
        'https://p.scdn.co/mp3-preview/4fd6d07817c006591ecf162c3cd52e19a1df13e1'  // Someone You Loved
    ],
    
    // 其他现有数据
  },
  
  // 计算属性
  computed: {
    // 检查是否评分了足够的歌曲
    hasRatedEnoughSongs() {
      let ratedCount = 0;
      this.sampleSongs.forEach(song => {
        if (song.rating > 0) ratedCount++;
      });
      return ratedCount >= 5; // 至少需要评分5首歌曲
    },
    
    // 翻译函数
    t() {
      return (key) => {
        const translations = {
          'zh': {
            'home': '首页',
            'login': '登录',
            'register': '注册',
            'username': '用户名',
            'email': '邮箱',
            'password': '密码',
            'loginPrompt': '已有账号？点击登录',
            'registerPrompt': '没有账号？点击注册',
            'logout': '退出',
            'user': '用户',
            'welcome': '欢迎',
            'rate': '评分',
            'rateSubtitle': '为歌曲评分，帮助我们了解您的偏好',
            'notRated': '尚未评分',
            'recommend': '推荐',
            'recommendSubtitle': '基于您的评分和偏好推荐的音乐',
            'loading': '加载中...',
            'noRecommendations': '暂无推荐，请先评分一些歌曲',
            'rateMore': '去评分更多歌曲',
            'getRecommendations': '获取推荐',
            'needMoreRatings': '请至少对5首歌曲进行评分',
            'chat': '聊天',
            'chatSubtitle': '与AI助手聊天，获取个性化音乐推荐',
            'chatWelcome': '你好！我是AI音乐助手，可以帮你找到你喜欢的音乐。试着告诉我你喜欢什么类型的音乐或者你喜欢的歌手吧！',
            'typeSomething': '输入消息...',
            'game': '游戏',
            'gameSubtitle': '通过游戏收集音乐道具，表达您的音乐偏好'
          },
          'en': {
            'home': 'Home',
            'login': 'Login',
            'register': 'Register',
            'username': 'Username',
            'email': 'Email',
            'password': 'Password',
            'loginPrompt': 'Already have an account? Login',
            'registerPrompt': 'No account? Register',
            'logout': 'Logout',
            'user': 'User',
            'welcome': 'Welcome',
            'rate': 'Rate',
            'rateSubtitle': 'Rate songs to help us understand your preferences',
            'notRated': 'Not rated yet',
            'recommend': 'Recommend',
            'recommendSubtitle': 'Music recommendations based on your ratings and preferences',
            'loading': 'Loading...',
            'noRecommendations': 'No recommendations yet. Please rate some songs first.',
            'rateMore': 'Rate more songs',
            'getRecommendations': 'Get Recommendations',
            'needMoreRatings': 'Please rate at least 5 songs',
            'chat': 'Chat',
            'chatSubtitle': 'Chat with AI assistant to get personalized music recommendations',
            'chatWelcome': 'Hello! I\'m the AI Music Assistant. I can help you find music you\'ll love. Try telling me what genres or artists you like!',
            'typeSomething': 'Type a message...',
            'game': 'Game',
            'gameSubtitle': 'Collect music items through a game to express your music preferences'
          }
        };
        
        return translations[this.currentLanguage][key] || key;
      };
    }
  },
  
  // 方法
  methods: {
    // 语言切换
    switchLanguage(lang) {
      this.currentLanguage = lang;
      // 本地存储用户语言偏好
      localStorage.setItem('preferredLanguage', lang);
      this.addNotification(lang === 'zh' ? '已切换到中文' : 'Switched to English', 'is-success');
    },
    
    // 添加格式化消息方法
    formatMessage(text) {
      if (!text) return '';
      // 将换行符转换为HTML换行
      return text.replace(/\n/g, '<br>');
    },
    
    // 添加格式化时间方法
    formatTime(timestamp) {
      if (!timestamp) return '';
      const date = new Date(timestamp);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    },
    
    // 登录
    login() {
      this.isLoading = true;
      this.loginError = '';
      
      // 模拟登录请求
      setTimeout(() => {
        // 测试用户
        if ((this.email === 'test@example.com' || this.email === 'a@a.com') && this.username === 'test') {
          this.isLoggedIn = true;
          this.currentUser = {
            id: 'user-123',
            username: this.username,
            email: this.email,
            isDeveloper: true
          };
          localStorage.setItem('user', JSON.stringify(this.currentUser));
          this.currentTab = 'welcome';
          this.loadSampleSongs();
          this.addNotification('登录成功！欢迎回来，' + this.username, 'is-success');
        } else {
          this.loginError = '登录失败，请检查用户名和邮箱';
        }
        this.isLoading = false;
      }, 1000);
    },
    
    // 注册
    register() {
      this.isLoading = true;
      this.registerError = '';
      
      // 模拟注册请求
      setTimeout(() => {
        // 简单验证
        if (!this.newUsername || !this.newEmail || !this.newPassword) {
          this.registerError = '请填写所有必填字段';
          this.isLoading = false;
          return;
        }
        
        // 模拟成功注册
        this.isLoggedIn = true;
        this.currentUser = {
          id: 'user-' + Math.floor(Math.random() * 1000),
          username: this.newUsername,
          email: this.newEmail,
          isDeveloper: false
        };
        localStorage.setItem('user', JSON.stringify(this.currentUser));
        this.currentTab = 'welcome';
        this.loadSampleSongs();
        this.addNotification('注册成功！欢迎，' + this.newUsername, 'is-success');
        this.isLoading = false;
      }, 1000);
    },
    
    // 登出
    logout() {
      this.isLoggedIn = false;
      this.currentUser = null;
      localStorage.removeItem('user');
      this.currentTab = 'login';
      this.addNotification('您已成功登出', 'is-info');
      
      // 清除游戏状态
      if (musicGame) {
        musicGame.stopGame();
        musicGame = null;
      }
    },
    
    // 检查会话
    checkSession() {
      const savedUser = localStorage.getItem('user');
      if (savedUser) {
        try {
          this.currentUser = JSON.parse(savedUser);
          this.isLoggedIn = true;
          this.currentTab = 'welcome';
          this.loadSampleSongs();
        } catch (e) {
          console.error('无法解析保存的用户数据', e);
          localStorage.removeItem('user');
        }
      }
      
      // 恢复语言设置
      const savedLanguage = localStorage.getItem('language');
      if (savedLanguage) {
        this.currentLanguage = savedLanguage;
      }
    },
    
    // 加载示例歌曲
    loadSampleSongs() {
      this.isLoading = true;
      
      // 模拟API请求
      setTimeout(() => {
        this.sampleSongs = [
          { id: 101, title: "Shape of You", artist: "Ed Sheeran", album_image: "https://i.scdn.co/image/ab67616d0000b273ba5db46f4b838ef6027e6f96", preview_url: this.previewUrls[0] },
          { id: 102, title: "Blinding Lights", artist: "The Weeknd", album_image: "https://i.scdn.co/image/ab67616d0000b2738863bc11d2aa12b54f5aeb36", preview_url: this.previewUrls[1] },
          { id: 103, title: "Dance Monkey", artist: "Tones and I", album_image: "https://i.scdn.co/image/ab67616d0000b2739f39192ec5a1f04f7c08d9ab", preview_url: this.previewUrls[2] },
          { id: 104, title: "Circles", artist: "Post Malone", album_image: "https://i.scdn.co/image/ab67616d0000b27399e211c11052dcb57a592f6c", preview_url: this.previewUrls[3] },
          { id: 105, title: "Watermelon Sugar", artist: "Harry Styles", album_image: "https://i.scdn.co/image/ab67616d0000b273da5d5aeeabacacc1263c0f4b", preview_url: this.previewUrls[4] },
          { id: 106, title: "Bad Guy", artist: "Billie Eilish", album_image: "https://i.scdn.co/image/ab67616d0000b273a91c10fe9472d9bd89802e5a", preview_url: this.previewUrls[5] },
          { id: 107, title: "Don't Start Now", artist: "Dua Lipa", album_image: "https://i.scdn.co/image/ab67616d0000b273bd26ede1ae69327010d49946", preview_url: this.previewUrls[6] },
          { id: 108, title: "Everything I Wanted", artist: "Billie Eilish", album_image: "https://i.scdn.co/image/ab67616d0000b273a91c10fe9472d9bd89802e5a", preview_url: this.previewUrls[7] },
          { id: 109, title: "Memories", artist: "Maroon 5", album_image: "https://i.scdn.co/image/ab67616d0000b273b25ef9c9015bdd771fbda74d", preview_url: this.previewUrls[8] },
          { id: 110, title: "Someone You Loved", artist: "Lewis Capaldi", album_image: "https://i.scdn.co/image/ab67616d0000b2733c65bbfd4c0f45af8c4b6e59", preview_url: this.previewUrls[9] }
        ];
        this.isLoading = false;
      }, 1000);
    },
    
    // 评分歌曲
    rateSong(song, rating) {
      song.rating = rating;
      this.addNotification(`已为 "${song.title}" 评分 ${rating} 星`, 'is-success');
    },
    
    // 获取推荐
    getRecommendations() {
      if (!this.hasRatedEnoughSongs) return;
      
      this.isLoadingRecommendations = true;
      this.currentTab = 'recommend';
      
      // 模拟API请求
      setTimeout(() => {
        // 根据评分生成模拟推荐
        const ratedSongs = this.sampleSongs.filter(song => song.rating > 0);
        const highRatedArtists = {};
        
        ratedSongs.forEach(song => {
          if (song.rating >= 4) {
            if (!highRatedArtists[song.artist]) {
              highRatedArtists[song.artist] = 0;
            }
            highRatedArtists[song.artist] += song.rating;
          }
        });
        
        // 模拟推荐结果
        this.recommendations = [
          { id: 101, title: "November Rain", artist: "Guns N' Roses", album_image: "https://via.placeholder.com/150", explanation: "因为你喜欢摇滚音乐和Guns N' Roses的其他歌曲" },
          { id: 102, title: "Hello", artist: "Adele", album_image: "https://via.placeholder.com/150", explanation: "基于你对Adele的高评分" },
          { id: 103, title: "Thriller", artist: "Michael Jackson", album_image: "https://via.placeholder.com/150", explanation: "与你喜欢的流行音乐风格相似" },
          { id: 104, title: "Wonderwall", artist: "Oasis", album_image: "https://via.placeholder.com/150", explanation: "摇滚音乐爱好者的经典选择" },
          { id: 105, title: "Nothing Else Matters", artist: "Metallica", album_image: "https://via.placeholder.com/150", explanation: "为摇滚音乐爱好者推荐" },
          { id: 106, title: "Someone Like You", artist: "Adele", album_image: "https://via.placeholder.com/150", explanation: "基于你对Adele的高评分" },
          { id: 107, title: "布拉格广场", artist: "周杰伦", album_image: "https://via.placeholder.com/150", explanation: "因为你喜欢周杰伦的其他歌曲" },
          { id: 108, title: "稻香", artist: "周杰伦", album_image: "https://via.placeholder.com/150", explanation: "因为你喜欢周杰伦的其他歌曲" }
        ];
        
        this.isLoadingRecommendations = false;
        this.addNotification('根据您的评分生成了推荐', 'is-success');
      }, 1500);
    },
    
    // 处理图片加载错误
    handleImageError(event) {
      event.target.src = '/static/img/default-album.png';
    },
    
    // 喜欢歌曲
    likeSong(song) {
      this.addNotification(`已添加 "${song.title}" 到我喜欢的音乐`, 'is-success');
    },
    
    // 不喜欢歌曲
    dislikeSong(song) {
      this.addNotification(`已将 "${song.title}" 标记为不喜欢`, 'is-warning');
      // 从推荐列表中移除
      this.recommendations = this.recommendations.filter(s => s.id !== song.id);
    },
    
    // 发送聊天消息
    async sendMessage() {
      if (!this.currentMessage.trim()) return;
      
      const userMessage = this.currentMessage.trim();
      this.chatMessages.push({
          content: userMessage,
          isUser: true,
          timestamp: new Date()
      });
      this.currentMessage = '';
      
      // 滚动到底部
      this.$nextTick(() => {
          const chatMessages = document.querySelector('.chat-messages');
          if (chatMessages) {
              chatMessages.scrollTop = chatMessages.scrollHeight;
          }
      });
      
      // 处理用户发送的消息
      this.isChatLoading = true;
      
      try {
          // 情感分析
          const emotionResult = await this.emotionDetector.detectFromText(userMessage);
          
          // 基于情感检测结果构建AI回复
          let aiResponse = '';
          
          // 音乐推荐关键词检测
          const recommendKeywords = ['推荐', '音乐', '歌曲', '听什么', '想听', '歌'];
          const mentalHealthKeywords = ['难过', '伤心', '焦虑', '压力', '不开心', '痛苦', '烦恼', '困扰', '失眠', '抑郁'];
          const needsRecommendation = recommendKeywords.some(keyword => userMessage.includes(keyword));
          const needsEmotionalSupport = mentalHealthKeywords.some(keyword => userMessage.includes(keyword));
          
          // 如果用户请求音乐推荐
          if (needsRecommendation) {
              // 保存情感状态
              this.userEmotion = emotionResult;
              
              // 根据情感状态生成回复
              const emotion = emotionResult.emotion;
              aiResponse = `我感觉到你现在的情绪是"${emotion}"。让我为你推荐一些适合这种心情的音乐...`;
              
              // 添加回复
              this.chatMessages.push({
                  content: aiResponse,
                  isUser: false,
                  timestamp: new Date()
              });
              
              // 在聊天框中直接推荐歌曲
              // 选择3首情感匹配的歌曲
              const recommendedSongs = this.sampleSongs
                  .sort(() => 0.5 - Math.random())
                  .slice(0, 3)
                  .map(song => ({
                      ...song,
                      // 确保有预览URL
                      preview_url: song.preview_url || this.previewUrls[Math.floor(Math.random() * this.previewUrls.length)]
                  }));
                  
              // 构建推荐消息
              let songRecommendations = '根据你的心情，我推荐这些歌曲：\n\n';
              recommendedSongs.forEach((song, index) => {
                  songRecommendations += `${index + 1}. ${song.title} - ${song.artist}\n`;
                  // 添加情感相关的推荐理由
                  songRecommendations += `   ${this.emotionDetector.generateRecommendationReason(emotion)}\n\n`;
              });
              
              songRecommendations += '你可以点击"试听"按钮来收听这些歌曲。希望这些音乐能够陪伴你度过这段时光。';
              
              // 添加歌曲推荐回复
              setTimeout(() => {
                  this.chatMessages.push({
                      content: songRecommendations,
                      isUser: false,
                      timestamp: new Date(),
                      songs: recommendedSongs  // 附加歌曲数据供显示
                  });
                  
                  // 滚动到底部
                  this.$nextTick(() => {
                      const chatMessages = document.querySelector('.chat-messages');
                      if (chatMessages) {
                          chatMessages.scrollTop = chatMessages.scrollHeight;
                      }
                  });
                  
                  this.isChatLoading = false;  // 加载完成后设置状态为false
              }, 1000);
              
              // 同时更新推荐页面
              this.recommendations = recommendedSongs.map(song => {
                  return {
                      ...song,
                      recommendationReason: this.emotionDetector.generateRecommendationReason(emotion)
                  };
              });
          } 
          // 如果用户需要情感支持
          else if (needsEmotionalSupport) {
              // 心理咨询师风格的回复
              const therapistResponses = {
                  '高兴': [
                      '很高兴看到你今天心情不错！这种积极的状态是很珍贵的。你能分享一下是什么让你感到如此开心吗？',
                      '你的好心情透过文字都能感受到。珍惜这样的时刻，也许有些音乐可以帮你延续这种愉悦感？'
                  ],
                  '平静': [
                      '你看起来很平静，这是思考和感受音乐的好时刻。需要一些能够伴随这种宁静的曲子吗？',
                      '平静的时刻很适合聆听音乐，让声音和情感一起流动。有什么特定类型的音乐你现在想听吗？',
                      '在这平静的时刻，适合的音乐可以是一个很好的伴侣。需要我为你推荐一些吗？'
                  ],
                  '悲伤': [
                      '我能感受到你的情绪有些低落。音乐有时能够理解和表达我们无法用言语形容的感受。要不要听些能共鸣你心情的歌曲？',
                      '当感到悲伤时，合适的音乐可以成为一种情感出口。有时听一些能够理解我们情绪的歌曲，反而会让人感到被理解和安慰。需要我推荐一些吗？',
                      '悲伤是我们情感体验的重要部分。适当的音乐陪伴可能会给你一些安慰。我可以推荐一些能够陪伴你此刻心情的音乐，如果你想听的话。'
                  ],
                  '愤怒': [
                      '看起来你现在可能有些烦躁。音乐有时可以帮助我们释放和转化这些强烈的情绪。要听一些有力量的音乐来宣泄情绪吗？',
                      '感到愤怒或烦躁是很自然的情绪反应。有些音乐可以帮助表达和释放这些感受，或者转移注意力。需要我推荐一些吗？',
                      '你似乎有些不悦。音乐是一种强大的情绪调节工具，无论是想要释放还是平复情绪，都有适合的曲目。需要一些建议吗？'
                  ],
                  '兴奋': [
                      '你的兴奋之情溢于言表！这种充满活力的状态正适合一些节奏强劲、令人振奋的音乐。要来点推荐吗？',
                      '感受到你的热情和兴奋！这种状态下聆听音乐会特别有感染力。要听一些能够配合和延续这份活力的音乐吗？',
                      '你的兴奋情绪真让人感染！想要一些能够匹配这种活力四溢状态的音乐推荐吗？'
                  ],
                  '放松': [
                      '享受这份放松的时刻！适合的背景音乐可以让这种舒适感更加完美。需要一些轻柔、舒缓的音乐推荐吗？',
                      '放松时光配上恰到好处的音乐，是生活中的小确幸。要听一些能够帮你维持这种惬意状态的曲子吗？',
                      '放松的时刻真是珍贵。如果你想要一些能够伴随这种平和状态的音乐，我很乐意推荐一些。'
                  ],
                  '焦虑': [
                      '我注意到你可能有些紧张或焦虑。音乐有时能够帮助我们找回平静和安全感。需要一些能够帮助放松的音乐建议吗？',
                      '焦虑的感觉可能令人不适，但这是很常见的情绪反应。一些特定的音乐可以帮助减轻这种感受。要试试看吗？',
                      '感到焦虑时，正念音乐可能会有所帮助。缓慢的节奏和和谐的旋律能够帮助我们重新找回平静。需要我推荐一些吗？'
                  ]
              };
              
              // 从对应情绪的心理咨询师回复中随机选择一个
              const emotionResponses = therapistResponses[emotionResult.emotion] || therapistResponses['平静'];
              aiResponse = emotionResponses[Math.floor(Math.random() * emotionResponses.length)];
              
              // 添加心理咨询师风格回复
              this.chatMessages.push({
                  content: aiResponse,
                  isUser: false,
                  timestamp: new Date()
              });
              
              // 稍后提供音乐建议
              setTimeout(() => {
                  const therapeuticMessage = `音乐疗法经常被用于帮助人们处理情绪。如果你愿意，我可以为你推荐一些适合当前心情的音乐。你只需说"推荐音乐"，我就会为你找些能够共鸣或抚慰你情感的歌曲。`;
                  
                  this.chatMessages.push({
                      content: therapeuticMessage,
                      isUser: false,
                      timestamp: new Date()
                  });
                  
                  // 滚动到底部
                  this.$nextTick(() => {
                      const chatMessages = document.querySelector('.chat-messages');
                      if (chatMessages) {
                          chatMessages.scrollTop = chatMessages.scrollHeight;
                      }
                  });
                  
                  this.isChatLoading = false;  // 加载完成后设置状态为false
              }, 2000);
          } else {
              // 一般聊天回复
              const responses = {
                  '高兴': [
                      '看起来你心情不错！有什么我能帮你的吗？或许你想听些和你心情同样愉快的音乐？',
                      '你的好心情感染了我！需要一些音乐推荐来延续这份愉悦吗？',
                      '真高兴看到你这么开心！音乐是分享和延续快乐的好方式，需要我推荐一些吗？'
                  ],
                  '平静': [
                      '你看起来很平静，这是思考和感受音乐的好时刻。需要一些能够伴随这种宁静的曲子吗？',
                      '平静的时刻很适合聆听音乐，让声音和情感一起流动。有什么特定类型的音乐你现在想听吗？',
                      '在这平静的时刻，适合的音乐可以是一个很好的伴侣。需要我为你推荐一些吗？'
                  ]
              };
              
              // 从对应情绪类别的回复中随机选择一个，如果没有匹配情绪则使用平静类别
              const emotionResponses = responses[emotionResult.emotion] || responses['平静'];
              aiResponse = emotionResponses[Math.floor(Math.random() * emotionResponses.length)];
              
              // 添加一般聊天回复
              this.chatMessages.push({
                  content: aiResponse,
                  isUser: false,
                  timestamp: new Date()
              });
              
              this.isChatLoading = false;  // 设置聊天加载状态为false
          }
          
          // 滚动到底部
          this.$nextTick(() => {
              const chatMessages = document.querySelector('.chat-messages');
              if (chatMessages) {
                  chatMessages.scrollTop = chatMessages.scrollHeight;
              }
          });
      } catch (error) {
          console.error('处理聊天消息时出错:', error);
          this.addNotification('抱歉，处理消息时出现了问题', 'is-danger');
          this.isChatLoading = false;  // 确保出错时也设置状态为false
      }
    },
    
    // 播放歌曲预览
    async playSongPreview(songOrUrl, songTitle, songArtist) {
      try {
          // 判断参数类型，支持两种调用方式
          let url, title, artist;

          if (typeof songOrUrl === 'object' && songOrUrl !== null) {
              // 第一种方式：传入歌曲对象
              url = songOrUrl.preview_url;
              title = songOrUrl.title;
              artist = songOrUrl.artist;
          } else {
              // 第二种方式：传入单独的参数
              url = songOrUrl;
              title = songTitle || '示例歌曲';
              artist = songArtist || '未知艺术家';
          }

          // 如果没有预览URL，使用预设URL列表中的随机一个
          if (!url) {
              url = this.previewUrls[Math.floor(Math.random() * this.previewUrls.length)];
              console.log("使用随机预览URL:", url);
          }

          console.log("开始播放音乐预览:", url, title, artist);

          // 使用audio元素播放
          const audioPlayer = document.getElementById('audioPlayer');
          const playerContainer = document.getElementById('audioPlayerContainer');
          const playPauseBtn = document.getElementById('playPauseBtn');
          const audioTitle = document.getElementById('audioTitle');
          const audioArtist = document.getElementById('audioArtist');
          const closeBtn = document.getElementById('closeAudioPlayer');
          
          if (!audioPlayer || !playerContainer) {
              console.error('找不到音频播放器元素');
              this.addNotification('音频播放器初始化失败', 'is-danger');
              return;
          }
          
          // 设置音频源
          audioPlayer.src = url;
          
          // 更新播放器信息
          audioTitle.textContent = title;
          audioArtist.textContent = artist;
          
          // 显示播放器
          playerContainer.classList.remove('hidden');
          
          // 播放音频
          const playPromise = audioPlayer.play();
          
          if (playPromise !== undefined) {
              playPromise.then(_ => {
                  // 播放成功
                  console.log("音频播放成功");
                  this.addNotification(`正在播放: ${title} - ${artist}`, 'is-info');
              })
              .catch(error => {
                  // 播放失败
                  console.error("音频播放失败:", error);
                  this.addNotification('无法播放音频，可能是由于浏览器限制', 'is-warning');
                  playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
              });
          }
          
          // 添加播放/暂停切换
          playPauseBtn.onclick = function() {
              if (audioPlayer.paused) {
                  audioPlayer.play().catch(e => console.error("播放失败:", e));
                  playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
              } else {
                  audioPlayer.pause();
                  playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
              }
          };
          
          // 音频结束事件
          audioPlayer.onended = function() {
              playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
          };
          
          // 关闭按钮
          closeBtn.onclick = function() {
              audioPlayer.pause();
              playerContainer.classList.add('hidden');
          };
      } catch (error) {
          console.error("播放音乐出错:", error);
          this.addNotification('播放音乐时发生错误', 'is-danger');
      }
    },
    
    // 初始化音乐游戏
    initMusicGame() {
      if (this.currentTab === 'game') {
        // 清除先前的游戏
        if (musicGame) {
          musicGame.stopGame();
        }
        
        // 初始化新游戏
        musicGame = initMusicGame('game-canvas-container', this.handleGameComplete);
      }
    },
    
    // 处理游戏完成
    handleGameComplete(results) {
      console.log('游戏结果:', results);
      this.gameResults = results;
      this.showGameResults = true;
      
      // 添加情感分析
      const dominantGenre = Object.entries(results)
          .sort((a, b) => b[1] - a[1])[0][0];
          
      // 使用情感检测器将音乐风格映射到情感
      const emotionResult = this.emotionDetector.mapGenreToEmotion(dominantGenre);
      this.userEmotion = emotionResult;
      
      this.addNotification(`根据您喜欢的${dominantGenre}音乐，分析出您可能的情绪是: ${emotionResult.emotion}`, 'is-info');
    },
    
    // 使用游戏结果获取推荐
    useGameResultsForRecommendations() {
      if (!this.gameResults) {
          this.addNotification('请先完成音乐游戏', 'is-warning');
          return;
      }
      
      this.loading = true;
      this.currentTab = 'recommend'; // 确保切换到推荐页面
      
      // 如果已经有情绪分析，使用它来获取推荐
      if (this.userEmotion) {
          // 获取最受欢迎的流派
          const genres = Object.entries(this.gameResults)
              .sort((a, b) => b[1] - a[1])
              .map(entry => entry[0]);
              
          // 前端模拟实现：基于随机挑选歌曲并添加推荐理由
          setTimeout(() => {
              this.recommendations = this.sampleSongs
                  .sort(() => 0.5 - Math.random())
                  .slice(0, 6)
                  .map(song => {
                      return {
                          ...song,
                          // 加入游戏收集到的流派信息
                          recommendationReason: `根据您在游戏中喜欢的${genres[0]}音乐，以及检测到的"${this.userEmotion.emotion}"情绪，${this.emotionDetector.generateRecommendationReason(this.userEmotion.emotion)}`
                      };
                  });
              
              this.loading = false;
              this.addNotification('根据游戏结果生成了新推荐', 'is-success');
          }, 1000);
      } else {
          // 如果没有情绪分析，使用原本的游戏结果获取推荐
          setTimeout(() => {
              this.recommendations = this.sampleSongs
                  .sort(() => 0.5 - Math.random())
                  .slice(0, 6);
              this.loading = false;
              this.addNotification('根据游戏结果生成了新推荐', 'is-success');
          }, 1000);
      }
      
      this.showGameResults = false;
    },
    
    // 添加通知
    addNotification(message, type = 'is-info') {
      const id = Date.now();
      const icon = this.getNotificationIcon(type);
      
      this.notifications.push({
        id,
        message,
        type,
        icon
      });
      
      // 5秒后自动移除
      setTimeout(() => {
        this.removeNotification(id);
      }, 5000);
    },
    
    // 获取通知图标
    getNotificationIcon(type) {
      switch (type) {
        case 'is-success': return 'check-circle';
        case 'is-danger': return 'exclamation-circle';
        case 'is-warning': return 'exclamation-triangle';
        default: return 'info-circle';
      }
    },
    
    // 移除通知
    removeNotification(id) {
      this.notifications = this.notifications.filter(n => n.id !== id);
    },
    
    // 初始化情感检测器
    initEmotionDetector() {
      this.emotionDetector = new EmotionDetector();
    },
    
    // 切换情感输入界面
    toggleEmotionInput() {
      this.showEmotionDetector = !this.showEmotionDetector;
      if (this.showEmotionDetector) {
          // 如果打开了情感输入，滚动到该区域
          this.$nextTick(() => {
              const container = document.querySelector('.emotion-input-container');
              if (container) {
                  container.scrollIntoView({ behavior: 'smooth' });
              }
          });
      }
    },
    
    // 处理情感输入
    async detectEmotion() {
      if (!this.emotionInput.trim()) {
          this.addNotification('请输入您当前的心情', 'is-warning');
          return;
      }
      
      this.addNotification('正在分析您的情绪...', 'is-info');
      const result = await this.emotionDetector.detectFromText(this.emotionInput);
      
      this.userEmotion = result;
      this.addNotification(`检测到您当前的情绪: ${result.emotion}`, 'is-success');
      
      // 自动获取情感推荐
      this.getEmotionBasedRecommendations();
    },
    
    // 获取基于情感的音乐推荐
    async getEmotionBasedRecommendations() {
      if (!this.userEmotion) {
          this.addNotification('请先输入您的心情', 'is-warning');
          return;
      }
      
      this.loading = true;
      try {
          // 在实际项目中，应该调用后端API获取推荐
          // const response = await axios.post('/api/recommend_by_emotion', {
          //     user_id: this.userId,
          //     emotion: this.userEmotion.emotion,
          //     valence: this.userEmotion.valence,
          //     energy: this.userEmotion.energy
          // });
          // this.recommendations = response.data.recommendations;
          
          // 前端模拟实现：基于随机挑选歌曲并添加推荐理由
          this.recommendations = this.sampleSongs
              .sort(() => 0.5 - Math.random())
              .slice(0, 6)
              .map(song => {
                  return {
                      ...song,
                      // 使用情感检测器生成推荐理由
                      recommendationReason: this.emotionDetector.generateRecommendationReason(this.userEmotion.emotion)
                  };
              });
          
          this.addNotification('根据您的情绪推荐了新音乐', 'is-success');
      } catch (error) {
          console.error('获取推荐失败:', error);
          this.addNotification('推荐失败，请稍后再试', 'is-danger');
      } finally {
          this.loading = false;
      }
    },
    
    // 导航到情感推荐页面
    navigateToEmotionRecommend() {
      this.currentTab = 'recommend'; // 切换到推荐标签页
      this.$nextTick(() => {
        this.showEmotionDetector = true; // 显示情感输入界面
        // 滚动到情感输入区域
        setTimeout(() => {
          const container = document.querySelector('.emotion-input-container');
          if (container) {
            container.scrollIntoView({ behavior: 'smooth' });
          }
        }, 300);
      });
    },
    
    // 使用建议的聊天提示
    useSuggestion(suggestion) {
      this.currentMessage = suggestion;
      this.sendMessage();
    },
    
    // 初始化页面按钮事件绑定
    initButtonEvents() {
      console.log('初始化按钮事件');
      
      // 确保Vue已完全渲染DOM
      this.$nextTick(() => {
        // 为所有带有data-tab属性的元素添加点击事件
        document.querySelectorAll('[data-tab]').forEach(el => {
          el.addEventListener('click', (e) => {
            e.preventDefault();
            const tab = el.getAttribute('data-tab');
            if (tab) {
              console.log('切换到标签页:', tab);
              this.currentTab = tab;
            }
          });
        });
        
        // 为所有试听按钮添加事件监听器
        const previewButtons = document.querySelectorAll('.button[data-preview-id]');
        if (previewButtons.length > 0) {
          previewButtons.forEach(button => {
            console.log('找到试听按钮:', button);
            button.addEventListener('click', (event) => {
              event.preventDefault();
              const songId = button.getAttribute('data-preview-id');
              const song = this.findSongById(songId);
              if (song) {
                this.playSongPreview(song);
              }
            });
          });
        }
      });
    },
    
    // 通过ID查找歌曲
    findSongById(id) {
      // 在sampleSongs和recommendations中查找
      const allSongs = [...this.sampleSongs, ...this.recommendations];
      return allSongs.find(song => song.id === parseInt(id));
    },
  },
  
  // 侦听器
  watch: {
    currentTab(newTab, oldTab) {
      if (newTab === 'game') {
        // 初始化游戏
        this.$nextTick(() => {
          this.initMusicGame();
        });
      } else if (oldTab === 'game' && musicGame) {
        // 停止游戏
        musicGame.stopGame();
      }
    }
  },
  
  // 组件挂载后
  mounted() {
    console.log('Vue应用已挂载');
    this.checkSession();
    
    // 初始化汉堡菜单
    const $navbarBurgers = Array.prototype.slice.call(document.querySelectorAll('.navbar-burger'), 0);
    if ($navbarBurgers.length > 0) {
      $navbarBurgers.forEach(el => {
        el.addEventListener('click', () => {
          const target = el.dataset.target;
          const $target = document.getElementById(target);
          el.classList.toggle('is-active');
          $target.classList.toggle('is-active');
        });
      });
    }
    
    // 初始化页面按钮事件绑定
    this.initButtonEvents();
    
    // 初始化情感检测器
    this.initEmotionDetector();
    
    // 为audio元素添加事件监听器
    const audioPlayer = document.getElementById('audioPlayer');
    const playPauseBtn = document.getElementById('playPauseBtn');
    const closeBtn = document.getElementById('closeAudioPlayer');
    
    if (audioPlayer && playPauseBtn && closeBtn) {
      console.log('音频播放器元素已找到并初始化');
      
      playPauseBtn.addEventListener('click', function() {
        if (audioPlayer.paused) {
          audioPlayer.play().catch(e => console.error("播放失败:", e));
          playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
        } else {
          audioPlayer.pause();
          playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
        }
      });
      
      audioPlayer.addEventListener('ended', function() {
        playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
      });
      
      closeBtn.addEventListener('click', function() {
        audioPlayer.pause();
        document.getElementById('audioPlayerContainer').classList.add('hidden');
      });
    } else {
      console.error('未找到音频播放器元素，无法初始化');
    }
    
    // 页面初始化完成后，给所有带有@click的元素添加实际的点击事件处理
    this.$nextTick(() => {
      const clickables = document.querySelectorAll('[data-vue-action]');
      console.log('找到可点击元素:', clickables.length);
      
      // 为所有页面导航链接添加点击事件
      document.querySelectorAll('[data-tab]').forEach(el => {
        el.addEventListener('click', (e) => {
          e.preventDefault();
          const tab = el.getAttribute('data-tab');
          if (tab) {
            this.currentTab = tab;
            console.log('切换到标签页:', tab);
          }
        });
      });
      
      // 初始化游戏预览
      setTimeout(() => {
        const previewCanvas = document.getElementById('musicPreviewCanvas');
        if (previewCanvas) {
          initGamePreview();
        }
      }, 500);
    });
  }
});
