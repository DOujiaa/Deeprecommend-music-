/**
 * 音乐推荐系统主JavaScript文件
 * 包含Vue.js应用初始化和核心功能实现
 */

// 等待页面加载完成
document.addEventListener('DOMContentLoaded', function() {
  console.log('音乐推荐系统应用已初始化');
  
  // 全局事件总线，用于组件间通信
  const EventBus = new Vue();
  
  // Vue.js应用实例
  const app = new Vue({
    el: '#app',
    
    // 数据属性
    data: {
      // 应用状态
      currentTab: 'welcome',
      isLoading: false,
      isLoadingRecommendations: false,
      currentLanguage: 'zh',
      isDeveloperMode: false,
      isRegistering: false,
      loginUsername: "",
      loginPassword: "",
      loginEmail: "",
      showLoginForm: true,
      showWelcomeOptions: false,
      showPreferencesSurvey: false,
      surveyCompleted: false,
      
      // 用户相关
      username: '',
      email: '',
      password: '',
      loginErrorMessage: '',
      loginForm: {
        username: '',
        email: '',
        password: ''
      },
      
      // 音乐偏好选项
      musicGenres: [
        '流行', '摇滚', '嘻哈', '电子', '爵士', '古典', 
        'R&B', '乡村', '民谣', '金属', '蓝调', '世界音乐',
        '独立', '实验', '氛围', '朋克', '雷鬼', '灵魂',
        '放克', '迪斯科', '布鲁斯', '拉丁', '英伦', '另类'
      ],
      selectedGenres: [],
      
      // 推荐算法设置
      recommendationAlgorithms: {
        hybrid: {
          name: '混合推荐',
          description: '结合SVD++、NCF、MLP算法和协同过滤提供更准确的推荐',
          selected: true
        },
        collaborative: {
          name: '协同过滤',
          description: '基于用户行为和偏好的相似性推荐音乐',
          selected: false
        },
        svdpp: {
          name: 'SVD++算法',
          description: '基于矩阵分解的推荐算法',
          selected: false
        },
        content: {
          name: '内容推荐',
          description: '基于音乐特征推荐相似风格的歌曲',
          selected: false
        }
      },
      
      // 音乐调查问卷
      surveyQuestions: [
        {
          id: 'music_genres',
          question: '您喜欢哪些音乐类型？',
          type: 'multiple',
          options: [], // 将在初始化时填充
          answer: []
        },
        {
          id: 'listening_frequency',
          question: '您多久听一次音乐？',
          type: 'single',
          options: ['每天', '每周几次', '偶尔', '很少'],
          answer: ''
        },
        {
          id: 'preferred_era',
          question: '您偏好哪个年代的音乐？',
          type: 'multiple',
          options: ['60年代', '70年代', '80年代', '90年代', '2000年代', '2010年代', '2020年代'],
          answer: []
        },
        {
          id: 'mood_preference',
          question: '您通常在什么心情下听音乐？',
          type: 'multiple',
          options: ['放松时', '工作/学习时', '运动时', '社交时', '伤心时', '开心时'],
          answer: []
        },
        {
          id: 'discovery_preference',
          question: '您更喜欢发现新音乐还是听熟悉的歌曲？',
          type: 'single',
          options: ['总是寻找新音乐', '偶尔尝试新音乐', '主要听熟悉的歌曲', '只听我已知的歌曲'],
          answer: ''
        }
      ],
      
      // 管理员功能相关
      allUsers: [],
      newUser: {
        username: '',
        email: '',
        password: '',
        isDeveloper: false
      },
      editingUser: null,
      
      // 内容对象 - 修复模板中使用的content对象
      content: {
        welcome: {
          title: '欢迎使用音乐推荐系统',
          subtitle: '选择下面的选项开始您的音乐之旅',
          talkToAI: '与AI音乐助手聊天',
          talkToAIDesc: '向AI助手询问音乐推荐、艺术家信息或表达您的情绪，获取个性化音乐建议',
          fillQuestionnaire: '填写音乐问卷',
          fillQuestionnaireDesc: '通过对歌曲评分，帮助我们了解您的音乐偏好，获取更精准的推荐'
        },
        rate: {
          title: '对歌曲评分',
          subtitle: '请对以下歌曲进行评分，以帮助我们了解您的音乐品味',
          notRated: '未评分',
          continueButton: '获取推荐',
          needMoreRatings: '请至少对5首歌曲评分'
        },
        recommend: {
          title: '个性化推荐',
          subtitle: '根据您的评分，我们推荐以下歌曲',
          loading: '正在为您生成推荐...',
          noRecommendations: '暂无推荐，请先评分更多歌曲',
          rateMore: '返回评分更多歌曲'
        },
        chat: {
          title: 'AI音乐助手',
          subtitle: '与AI助手交流，获取音乐推荐和信息',
          welcome: '你好！我是你的AI音乐助手。我可以帮你找歌曲、了解艺术家、获取推荐，或者回答音乐相关问题。请随时向我提问！',
          inputPlaceholder: '输入您的问题或要求...'
        },
        evaluate: {
          title: '系统评估',
          subtitle: '请对推荐系统进行评价，帮助我们改进',
          submit: '提交评估',
          thanks: '感谢您的反馈！',
          select: '请选择',
          rating: {
            veryDissatisfied: '非常不满意',
            dissatisfied: '不满意',
            neutral: '一般',
            satisfied: '满意',
            verySatisfied: '非常满意'
          },
          feedback: '其他建议或意见',
          feedbackPlaceholder: '请输入您的建议或意见...',
          submitButton: '提交评价',
          thankYou: '感谢您的反馈！'
        },
        header: {
          title: '欢迎，',
          subtitle: '探索您的专属音乐世界',
          logout: '退出'
        },
        tabs: {
          welcome: '欢迎',
          rate: '评分',
          recommend: '推荐',
          chat: '聊天',
          evaluate: '评估'
        },
        footer: {
          title: '音乐推荐系统',
          description: '一个基于AI的个性化音乐推荐系统'
        },
        errors: {
          emptyUsername: '请输入用户名',
          loginFailed: '登录失败，请检查您的用户名和密码'
        },
        success: {
          login: '登录成功！'
        }
      },
      
      // 翻译对象
      translationsZh: {
        welcome: '欢迎使用音乐推荐系统',
        description: '探索个性化音乐推荐',
        login: '登录',
        register: '注册',
        userId: '用户ID',
        username: '用户名',
        password: '密码',
        submit: '提交',
        cancel: '取消',
        rate: '评分',
        recommend: '推荐',
        chat: '聊天',
        evaluate: '评估',
        moreInfo: '更多信息',
        rateThisSong: '为这首歌评分',
        similar: '相似歌曲',
        artist: '艺术家',
        album: '专辑',
        releaseDate: '发行日期',
        popularity: '流行度',
        listen: '收听',
        chatWithAI: '与AI音乐助手聊天',
        sendMessage: '发送消息',
        typeMessage: '输入消息...',
        loading: '加载中...',
        error: '出错了',
        retry: '重试',
        noResults: '没有结果',
        welcome_message: '你好！我是你的AI音乐助手。我可以帮你找歌曲、了解艺术家、获取推荐，或者回答音乐相关问题。请随时向我提问！',
        developer: '开发者',
        logout: '退出登录',
        enterUsername: '请输入用户名',
        enterEmail: '请输入邮箱',
        enterPassword: '请输入密码'
      },
      translationsEn: {
        welcome: 'Welcome to Music Recommendation System',
        description: 'Explore personalized music recommendations',
        login: 'Login',
        register: 'Register',
        userId: 'User ID',
        username: 'Username',
        password: 'Password',
        submit: 'Submit',
        cancel: 'Cancel',
        rate: 'Rate',
        recommend: 'Recommend',
        chat: 'Chat',
        evaluate: 'Evaluate',
        moreInfo: 'More Info',
        rateThisSong: 'Rate this song',
        similar: 'Similar Songs',
        artist: 'Artist',
        album: 'Album',
        releaseDate: 'Release Date',
        popularity: 'Popularity',
        listen: 'Listen',
        chatWithAI: 'Chat with AI Music Assistant',
        sendMessage: 'Send Message',
        typeMessage: 'Type a message...',
        loading: 'Loading...',
        error: 'Error',
        retry: 'Retry',
        noResults: 'No Results',
        welcome_message: 'Hello! I am your AI music assistant. I can help you find songs, learn about artists, get recommendations, or answer music-related questions. Feel free to ask me anything!',
        developer: 'Developer',
        logout: 'Logout',
        welcome_title: 'Welcome to Music Recommendation System',
        welcome_subtitle: 'Choose an option below to start your music journey',
        welcome_talkToAI: 'Chat with AI Music Assistant',
        welcome_talkToAIDesc: 'Ask the AI assistant for music recommendations, artist information, or express your emotions for personalized music suggestions',
        welcome_fillQuestionnaire: 'Fill Music Questionnaire',
        welcome_fillQuestionnaireDesc: 'Rate songs to help us understand your music preferences and get more accurate recommendations'
      },
      
      // 评估问题
      evaluationQuestions: [
        { id: 'recommendation_quality', text: '您对系统的推荐质量满意吗？' },
        { id: 'ui_experience', text: '您对系统的用户界面体验满意吗？' },
        { id: 'overall_satisfaction', text: '您对系统的整体体验满意吗？' }
      ],
      evaluationResponses: [],
      evaluationSubmitted: false,
      
      // 用户信息
      user: {
        id: null,
        username: '',
        email: '',
        isLoggedIn: false,
        isDeveloper: false
      },
      
      // 音乐数据
      sampleSongs: [
        {
          track_id: '1',
          track_name: '晴天',
          artist_name: '周杰伦',
          title: '晴天',
          artist: '周杰伦',
          album_image: '/static/img/default-album.png',
          preview_url: null
        },
        {
          track_id: '2',
          track_name: 'Shape of You',
          artist_name: 'Ed Sheeran',
          title: 'Shape of You',
          artist: 'Ed Sheeran',
          album_image: '/static/img/default-album.png',
          preview_url: null
        },
        {
          track_id: '3',
          track_name: '演员',
          artist_name: '薛之谦',
          title: '演员',
          artist: '薛之谦',
          album_image: '/static/img/default-album.png',
          preview_url: null
        },
        {
          track_id: '4',
          track_name: 'Uptown Funk',
          artist_name: 'Mark Ronson ft. Bruno Mars',
          title: 'Uptown Funk',
          artist: 'Mark Ronson ft. Bruno Mars',
          album_image: '/static/img/default-album.png',
          preview_url: null
        },
        {
          track_id: '5',
          track_name: '漂洋过海来看你',
          artist_name: '刘明湘',
          title: '漂洋过海来看你',
          artist: '刘明湘',
          album_image: '/static/img/default-album.png',
          preview_url: null
        },
      ],
      userRatings: {},
      recommendations: [
        {
          track_id: 'rec1',
          track_name: '爱情转移',
          artist_name: '陈奕迅',
          title: '爱情转移',
          artist: '陈奕迅',
          explanation: '基于您对周杰伦的喜好推荐',
          album_image: '/static/img/default-album.png',
          preview_url: null
        },
        {
          track_id: 'rec2',
          track_name: 'Thinking Out Loud',
          artist_name: 'Ed Sheeran',
          title: 'Thinking Out Loud',
          artist: 'Ed Sheeran',
          explanation: '与您喜欢的 Shape of You 风格相似',
          album_image: '/static/img/default-album.png',
          preview_url: null
        },
        {
          track_id: 'rec3',
          track_name: '丑八怪',
          artist_name: '薛之谦',
          title: '丑八怪',
          artist: '薛之谦',
          explanation: '来自您喜欢的艺术家薛之谦',
          album_image: '/static/img/default-album.png',
          preview_url: null
        }
      ],
      
      // 聊天相关
      chatMessage: '',
      chatHistory: [],
      chatMessages: [],
      chatInput: '',
      isTyping: false,
      
      // 评估数据
      satisfactionLevel: 0,
      feedbackText: '',
      evaluationComment: '',
      
      // 系统消息
      notification: {
        message: '',
        type: 'info',
        isVisible: false
      },
      
      // 通知列表
      notifications: [],
      
      // 音频播放
      currentPreviewUrl: null,
      audioPlayer: null,
      
      // 情绪分析相关
      emotionKeywords: [
        '难过', '伤心', '悲伤', '压力', '焦虑', '开心', '高兴', '兴奋', 
        '生气', '愤怒', '无聊', '疲惫', '孤独', '思念', '失落', 
        '想哭', '不开心', '抑郁', '烦躁', '心情'
      ],
      lastEmotionAnalysis: null,
      isEmotionAnalysing: false,
      
      translations: {
        zh: {
          appTitle: '深度推荐音乐',
          recommendations: '推荐',
          chat: '聊天',
          evaluation: '评价',
          developer: '开发者模式',
          logout: '退出登录'
        },
        en: {
          appTitle: 'Deep Recommend Music',
          recommendations: 'Recommendations',
          chat: 'Chat',
          evaluation: 'Evaluation',
          developer: 'Developer Mode',
          logout: 'Log Out'
        }
      },
      
      // 底部描述更新以提及混合推荐算法
      footerDescription: {
        zh: '本系统采用混合推荐算法 (SVD++, NCF, MLP 和协同过滤)，结合内容分析和用户行为，提供个性化音乐推荐。',
        en: 'This system uses a hybrid recommendation algorithm (SVD++, NCF, MLP, and Collaborative Filtering), combining content analysis and user behavior to provide personalized music recommendations.'
      },
      
      // 用户偏好
      preferences: [],
      
      // 默认推荐歌曲
      defaultRecommendations: [
        {
          track_id: 'default_1',
          track_name: '千里之外',
          artist_name: '周杰伦',
          title: '千里之外',
          artist: '周杰伦',
          explanation: '热门华语歌曲推荐'
        },
        {
          track_id: 'default_2',
          track_name: '起风了',
          artist_name: '买辣椒也用券',
          title: '起风了',
          artist: '买辣椒也用券',
          explanation: '近期流行歌曲推荐'
        }
      ]
    },
    
    // 计算属性
    computed: {
      // 已评分的歌曲数量
      ratedSongsCount() {
        return Object.keys(this.userRatings).length;
      },
      
      // 用户是否可以获取推荐
      canGetRecommendations() {
        return this.ratedSongsCount >= 5 && this.user.isLoggedIn;
      },
      
      // 用户是否已经评分足够的歌曲
      hasRatedEnoughSongs() {
        return this.ratedSongsCount >= 5;
      },
      
      // 显示语言
      t() {
        return (key) => {
          const translations = this.currentLanguage === 'zh' ? this.translationsZh : this.translationsEn;
          return translations[key] || key;
        };
      },
      
      // 评估是否完成
      isEvaluationComplete() {
        return this.evaluationResponses.filter(r => r !== '').length === this.evaluationQuestions.length;
      },
      
      // 登录状态 (兼容模板中的变量名)
      isLoggedIn() {
        return this.user.isLoggedIn;
      }
    },
    
    // 监听属性变化
    watch: {
      currentLanguage(newVal) {
        localStorage.setItem('preferredLanguage', newVal);
      },
      'user.isLoggedIn'(newValue) {
        if (newValue) {
          // 保存用户ID到本地存储
          localStorage.setItem('musicRecommendUserId', this.user.id);
        }
      }
    },
    
    // 创建时执行
    created() {
      // 从本地存储加载语言偏好
      const savedLanguage = localStorage.getItem('preferredLanguage');
      if (savedLanguage) {
        this.currentLanguage = savedLanguage;
      }
      
      // 初始化加载状态
      this.isLoading = false;
      this.isLoadingRecommendations = false;
      
      // 设置translations对象
      if (!this.translations || !this.translations.zh || !this.translations.zh.welcome) {
        // 确保translations对象完整
        this.translations = {
          zh: {
            appTitle: '深度推荐音乐',
            recommendations: '推荐',
            chat: '聊天',
            evaluation: '评价',
            developer: '开发者模式',
            logout: '退出登录',
            tabs: {
              welcome: '欢迎',
              rate: '评分',
              recommend: '推荐',
              chat: '聊天',
              evaluate: '评估',
              admin: '用户管理'
            },
            welcome: {
              title: '欢迎使用音乐推荐系统',
              subtitle: '选择下面的选项开始您的音乐之旅',
              talkToAI: '与AI音乐助手聊天',
              talkToAIDesc: '向AI助手询问音乐推荐、艺术家信息或表达您的情绪，获取个性化音乐建议',
              fillQuestionnaire: '填写音乐问卷',
              fillQuestionnaireDesc: '通过对歌曲评分，帮助我们了解您的音乐偏好，获取更精准的推荐'
            }
          },
          en: {
            appTitle: 'Deep Recommend Music',
            recommendations: 'Recommendations',
            chat: 'Chat',
            evaluation: 'Evaluation',
            developer: 'Developer Mode',
            logout: 'Log Out',
            tabs: {
              welcome: 'Welcome',
              rate: 'Rate',
              recommend: 'Recommend',
              chat: 'Chat',
              evaluate: 'Evaluate',
              admin: 'User Admin'
            },
            welcome: {
              title: 'Welcome to Music Recommendation System',
              subtitle: 'Choose an option below to start your music journey',
              talkToAI: 'Chat with AI Music Assistant',
              talkToAIDesc: 'Ask the AI assistant for music recommendations, artist information, or express your emotions for personalized music suggestions',
              fillQuestionnaire: 'Fill Music Questionnaire',
              fillQuestionnaireDesc: 'Rate songs to help us understand your music preferences and get more accurate recommendations'
            }
          }
        };
      }
      
      // 设置默认示例歌曲，防止渲染错误
      this.sampleSongs = [
        { 
          track_id: '1', 
          track_name: '晴天', 
          artist_name: '周杰伦', 
          album_name: '叶惠美',
          title: '晴天',
          artist: '周杰伦',
          rating: 5,  // 默认评分为5
          album_image: '/static/img/default-album.png'
        },
        { 
          track_id: '2', 
          track_name: 'Shape of You', 
          artist_name: 'Ed Sheeran', 
          album_name: 'Divide',
          title: 'Shape of You',
          artist: 'Ed Sheeran',
          rating: 4,  // 默认评分为4
          album_image: '/static/img/default-album.png'
        },
        {
          track_id: '3',
          track_name: '演员',
          artist_name: '薛之谦',
          album_name: '绅士',
          title: '演员',
          artist: '薛之谦',
          rating: 5,
          album_image: '/static/img/default-album.png'
        },
        {
          track_id: '4',
          track_name: 'Uptown Funk',
          artist_name: 'Mark Ronson ft. Bruno Mars',
          album_name: 'Uptown Special',
          title: 'Uptown Funk',
          artist: 'Mark Ronson ft. Bruno Mars',
          rating: 4,
          album_image: '/static/img/default-album.png'
        },
        {
          track_id: '5',
          track_name: '漂洋过海来看你',
          artist_name: '刘明湘',
          album_name: '漂洋过海来看你',
          title: '漂洋过海来看你',
          artist: '刘明湘',
          rating: 5,
          album_image: '/static/img/default-album.png'
        }
      ];
      
      // 设置默认推荐数据，防止渲染错误
      this.recommendations = [
        {
          track_id: 'rec1',
          track_name: '告白气球',
          artist_name: '周杰伦',
          explanation: '根据您喜欢的周杰伦的作品推荐',
          title: '告白气球',
          artist: '周杰伦',
          album_image: '/static/img/default-album.png'
        },
        {
          track_id: 'rec2',
          track_name: 'Perfect',
          artist_name: 'Ed Sheeran',
          explanation: '与您喜欢的Shape of You风格相似',
          title: 'Perfect',
          artist: 'Ed Sheeran',
          album_image: '/static/img/default-album.png'
        },
        {
          track_id: 'rec3',
          track_name: '光年之外',
          artist_name: '邓紫棋',
          explanation: '基于您的流行音乐偏好推荐',
          title: '光年之外',
          artist: '邓紫棋',
          album_image: '/static/img/default-album.png'
        },
        {
          track_id: 'rec4',
          track_name: 'Thinking Out Loud',
          artist_name: 'Ed Sheeran',
          explanation: '与您喜欢的Shape of You的艺术家相同',
          title: 'Thinking Out Loud',
          artist: 'Ed Sheeran',
          album_image: '/static/img/default-album.png'
        },
        {
          track_id: 'rec5',
          track_name: '安静',
          artist_name: '周杰伦',
          explanation: '根据您喜欢的周杰伦的作品推荐',
          title: '安静',
          artist: '周杰伦',
          album_image: '/static/img/default-album.png'
        }
      ];
      
      // 初始化必要的数据，避免undefined错误
      this.chatMessages = [];
      if (!Array.isArray(this.chatMessages)) {
        this.chatMessages = [];
      }
      
      // 确保内容对象存在
      if (!this.content) {
        this.content = {
          welcome: {
            title: '欢迎使用音乐推荐系统',
            subtitle: '选择下面的选项开始您的音乐之旅',
            talkToAI: '与AI音乐助手聊天',
            talkToAIDesc: '向AI助手询问音乐推荐、艺术家信息或表达您的情绪，获取个性化音乐建议',
            fillQuestionnaire: '填写音乐问卷',
            fillQuestionnaireDesc: '通过对歌曲评分，帮助我们了解您的音乐偏好，获取更精准的推荐'
          },
          rate: {
            title: '对歌曲评分',
            subtitle: '请对以下歌曲进行评分，以帮助我们了解您的音乐品味',
            notRated: '未评分',
            continueButton: '获取推荐',
            needMoreRatings: '请至少对5首歌曲评分'
          },
          recommend: {
            title: '个性化推荐',
            subtitle: '根据您的评分，我们推荐以下歌曲',
            loading: '正在为您生成推荐...',
            noRecommendations: '暂无推荐，请先评分更多歌曲',
            rateMore: '返回评分更多歌曲'
          },
          chat: {
            title: 'AI音乐助手',
            subtitle: '与AI助手交流，获取音乐推荐和信息',
            welcome: '你好！我是你的AI音乐助手。我可以帮你找歌曲、了解艺术家、获取推荐，或者回答音乐相关问题。请随时向我提问！',
            inputPlaceholder: '输入您的问题或要求...'
          },
          evaluate: {
            title: '系统评估',
            subtitle: '请对推荐系统进行评价，帮助我们改进',
            submit: '提交评估',
            thanks: '感谢您的反馈！'
          },
          header: {
            title: '欢迎，',
            subtitle: '探索您的专属音乐世界',
            logout: '退出'
          },
          tabs: {
            welcome: '欢迎',
            rate: '评分',
            recommend: '推荐',
            chat: '聊天',
            evaluate: '评估'
          },
          footer: {
            title: '音乐推荐系统',
            description: '一个基于AI的个性化音乐推荐系统'
          },
          errors: {
            emptyUsername: '请输入用户名',
            loginFailed: '登录失败，请检查您的用户名和密码'
          },
          success: {
            login: '登录成功！'
          }
        };
      }
      
      // 初始化情绪关键词数组
      if (!this.emotionKeywords || !Array.isArray(this.emotionKeywords)) {
        this.emotionKeywords = [
          '难过', '伤心', '悲伤', '压力', '焦虑', '开心', '高兴', '兴奋', 
          '生气', '愤怒', '无聊', '疲惫', '孤独', '思念', '失落', 
          '想哭', '不开心', '抑郁', '烦躁', '心情'
        ];
      }
      
      // 确保其他变量有默认值
      this.chatInput = '';
      this.notifications = [];
      this.evaluationResponses = [];
      this.currentPreviewUrl = null;
      
      // 预设用户评分数据
      this.userRatings = {
        '1': 5, // 晴天评分为5
        '2': 4, // Shape of You评分为4
        '3': 5, // 演员评分为5
        '4': 4, // Uptown Funk评分为4
        '5': 5  // 漂洋过海来看你评分为5
      };
      
      // 添加AI欢迎消息
      this.chatMessages.push({
        content: `欢迎，${this.user.username}！我是您的AI音乐助手。请问您想了解什么音乐信息或获取什么推荐？`,
        isUser: false
      });
      
      // 显示欢迎通知
      this.showNotification('欢迎使用音乐推荐系统！我们已为您准备了一些推荐。', 'success');
      
      // 自动加载示例歌曲（但不调用API）
      console.log('已加载示例歌曲:', this.sampleSongs.length);
      console.log('已设置用户评分:', Object.keys(this.userRatings).length);
      
      // 定时动画效果
      setTimeout(() => {
        const cards = document.querySelectorAll('.recommendation-item');
        if (cards && cards.length > 0) {
          cards.forEach((card, index) => {
            setTimeout(() => {
              card.classList.add('animate__animated', 'animate__fadeInUp');
            }, index * 100);
          });
        }
      }, 500);
    },
    
    // 方法定义
    methods: {
      // 获取对应语言的翻译
      getTranslation(key) {
        const translations = this.currentLanguage === 'zh' ? 
          (this.translations.zh || this.translationsZh) : 
          (this.translations.en || this.translationsEn);
        return translations[key] || key;
      },
      
      // 切换语言
      switchLanguage(lang) {
        if (lang) {
          this.currentLanguage = lang;
        } else {
          // 如果没有提供参数，则切换语言
          this.currentLanguage = this.currentLanguage === 'zh' ? 'en' : 'zh';
        }
        document.documentElement.lang = this.currentLanguage;
      },
      
      // 切换标签页
      switchTab(tab) {
        if (tab === 'welcome') {
          console.log("切换到欢迎页面");
        }
        this.currentTab = tab;
        
        // 如果切换到推荐标签页，获取推荐
        if (tab === 'recommend' && this.canGetRecommendations) {
          this.getRecommendations();
        }
        
        // 如果切换到聊天标签页，加载聊天历史
        if (tab === 'chat' && this.user.isLoggedIn) {
          this.getChatHistory();
        }
      },
      
      // 检查用户会话
      checkUserSession() {
        const storedUser = localStorage.getItem('user');
        if (storedUser) {
          this.user = JSON.parse(storedUser);
        }
      },
      
      // 加载初始数据
      loadInitialData() {
        // 加载示例歌曲
        this.loadSampleSongs();
        
        // 如果用户已登录，获取用户评分记录
        if (this.user.isLoggedIn) {
          this.getUserRatings();
        }
      },
      
      // 加载示例歌曲
      loadSampleSongs() {
        // 使用预设的示例歌曲数据，不发送API请求
        console.log('使用预设的示例歌曲数据');
        
        // 设置加载状态
        this.isLoading = true;
        
        // 模拟网络延迟
        setTimeout(() => {
          this.isLoading = false;
          console.log('已加载示例歌曲:', this.sampleSongs.length);
          
          // 如果有用户评分数据，应用到歌曲上
          if (Object.keys(this.userRatings).length > 0) {
            this.sampleSongs.forEach(song => {
              if (this.userRatings[song.track_id]) {
                song.rating = this.userRatings[song.track_id];
              }
            });
          }
        }, 500);
      },
      
      // 获取用户评分记录
      getUserRatings() {
        if (!this.user.isLoggedIn) return;
        
        this.isLoading = true;
        
        // 使用用户名作为ID
        const userId = this.user.id || this.user.username;
        
        axios.get(`/api/user_ratings/${userId}`)
          .then(response => {
            this.userRatings = response.data || {};
            console.log('已加载用户评分:', Object.keys(this.userRatings).length);
            
            // 更新示例歌曲的评分
            if (this.sampleSongs.length > 0) {
              this.sampleSongs.forEach(song => {
                if (this.userRatings[song.track_id]) {
                  this.$set(song, 'rating', this.userRatings[song.track_id]);
                }
              });
            }
          })
          .catch(error => {
            console.error('加载用户评分失败:', error);
          })
          .finally(() => {
            this.isLoading = false;
          });
      },
      
      // 评分歌曲
      rateSong(trackId, rating) {
        if (!this.user.isLoggedIn) {
          this.showNotification('请先登录后再评分', 'warning');
          return;
        }
        
        this.isLoading = true;
        
        // 动画效果标记该歌曲已评分
        const songElement = document.querySelector(`[data-track-id="${trackId}"]`);
        if (songElement) {
          songElement.classList.add('animate__animated', 'animate__pulse');
          setTimeout(() => {
            songElement.classList.remove('animate__animated', 'animate__pulse');
          }, 1000);
        }
        
        axios.post('/api/rate_song', {
          user_id: this.user.id,
          track_id: trackId,
          rating: rating
        })
          .then(response => {
            // 更新本地评分记录
            this.$set(this.userRatings, trackId, rating);
            console.log('歌曲评分成功:', trackId, rating);
            
            // 检查是否可以获取推荐
            if (this.canGetRecommendations) {
              this.showNotification('您已评分足够的歌曲，可以获取个性化推荐了', 'success');
            }
          })
          .catch(error => {
            console.error('歌曲评分失败:', error);
            this.showNotification('评分失败，请重试', 'danger');
          })
          .finally(() => {
            this.isLoading = false;
          });
      },
      
      // 获取推荐歌曲
      getRecommendations() {
        // 我们已经有预设的推荐数据，直接使用它们
        console.log('使用预设的推荐数据');
        
        // 设置加载状态
        this.isLoadingRecommendations = true;
        
        // 模拟网络请求延迟
        setTimeout(() => {
          this.isLoadingRecommendations = false;
          
          // 添加动画效果
          setTimeout(() => {
            const cards = document.querySelectorAll('.recommendation-item');
            if (cards && cards.length > 0) {
              cards.forEach((card, index) => {
                setTimeout(() => {
                  card.classList.add('animate__animated', 'animate__fadeInUp');
                }, index * 100);
              });
            }
          }, 100);
          
          this.showNotification('已为您生成推荐歌曲！', 'success');
        }, 1000);
      },
      
      // 发送聊天消息
      sendChatMessage() {
        if (!this.chatInput.trim() || !this.user.isLoggedIn) return;
        
        const message = this.chatInput.trim();
        this.chatInput = '';
        
        // 添加用户消息到聊天历史
        this.chatMessages.push({
          content: message,
          isUser: true
        });
        
        // 滚动到底部
        this.$nextTick(() => {
          const chatContainer = document.querySelector('.chat-messages');
          if (chatContainer) {
            chatContainer.scrollTop = chatContainer.scrollHeight;
          }
        });
        
        this.isLoading = true;
        
        // 确保emotionKeywords存在
        if (!this.emotionKeywords || !Array.isArray(this.emotionKeywords)) {
          this.emotionKeywords = [
            '难过', '伤心', '悲伤', '压力', '焦虑', '开心', '高兴', '兴奋', 
            '生气', '愤怒', '无聊', '疲惫', '孤独', '思念', '失落', 
            '想哭', '不开心', '抑郁', '烦躁', '心情'
          ];
        }
        
        // 检查是否包含情绪关键词
        const containsEmotionKeyword = this.emotionKeywords.some(keyword => message.includes(keyword));
        
        if (containsEmotionKeyword) {
          // 如果包含情绪关键词，使用情绪分析API
          this.analyzeEmotionAndRecommend(message);
        } else {
          // 否则使用常规聊天API
          this.sendRegularChatMessage(message);
        }
      },
      
      /**
       * 发送常规聊天消息到API
       */
      sendRegularChatMessage(message) {
        axios.post('/api/chat', {
          user_id: this.user.id,
          message: message
        })
          .then(response => {
            // 添加 AI 回复到聊天历史
            this.chatHistory.push({
              sender: 'ai',
              message: response.data.response,
              timestamp: new Date().toISOString()
            });
            
            // 兼容模板变量
            this.chatMessages.push({
              content: response.data.response,
              isUser: false
            });
            
            // 如果回复中包含推荐，更新推荐列表
            if (response.data.response.includes('推荐') && response.data.response.includes('歌曲')) {
              // 检查当前是否在聊天标签，如果是，可以提供切换到推荐标签的按钮
              if (this.currentTab === 'chat') {
                this.showNotification('AI助手已为您生成音乐推荐，可以在推荐标签查看', 'info');
              }
              
              // 尝试获取最新推荐
              this.getRecommendations();
            }
          })
          .catch(error => {
            console.error('聊天请求出错:', error);
            this.showNotification('发送消息失败，请稍后再试', 'danger');
            
            // 添加错误消息
            this.chatHistory.push({
              sender: 'ai',
              message: '抱歉，我暂时无法回应。请稍后再试。',
              timestamp: new Date().toISOString()
            });
            
            // 兼容模板变量
            this.chatMessages.push({
              content: '抱歉，我暂时无法回应。请稍后再试。',
              isUser: false
            });
          })
          .finally(() => {
            this.isLoading = false;
            // 滚动到底部
            this.$nextTick(() => {
              const chatContainer = document.querySelector('.chat-messages');
              if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
              }
            });
          });
      },
      
      /**
       * 分析用户情绪并推荐音乐
       */
      analyzeEmotionAndRecommend(message) {
        if (!message || !this.user || !this.user.id) {
          console.error('analyzeEmotionAndRecommend: 参数不完整');
          this.showNotification('无法分析情绪，请稍后再试', 'error');
          this.isLoading = false;
          return;
        }
        
        this.isEmotionAnalysing = true;
        
        axios.post('/api/emotion/analyze', {
          user_id: this.user.id,
          message: message
        })
          .then(response => {
            // 保存情绪分析结果
            this.lastEmotionAnalysis = {
              emotion: response.data.emotion || 'neutral',
              intensity: response.data.intensity || 0.5,
              description: response.data.description || '您的情绪状态',
              music_suggestion: response.data.music_suggestion || '适合您当前情绪的音乐'
            };
            
            // 添加 AI 回复到聊天历史
            this.chatMessages.push({
              content: response.data.response || '我了解了您的情绪，让我为您推荐一些适合的音乐。',
              isUser: false
            });
            
            // 如果用户当前在聊天标签，提示可以在推荐标签查看相关音乐
            if (this.currentTab === 'chat') {
              this.showNotification('AI助手已分析您的情绪并推荐了适合的音乐', 'info');
            }
            
            // 尝试获取基于情绪的音乐推荐
            if (response.data.emotion) {
              this.getEmotionBasedMusic(response.data.emotion);
            }
          })
          .catch(error => {
            console.error('情绪分析请求出错:', error);
            
            // 添加错误消息
            this.chatMessages.push({
              content: '抱歉，我暂时无法分析您的情绪。请稍后再试或尝试不同的表达方式。',
              isUser: false
            });
            
            this.showNotification('情绪分析失败，请稍后再试', 'danger');
          })
          .finally(() => {
            this.isLoading = false;
            this.isEmotionAnalysing = false;
            
            // 滚动到底部
            this.$nextTick(() => {
              const chatContainer = document.querySelector('.chat-messages');
              if (chatContainer) {
                chatContainer.scrollTop = chatContainer.scrollHeight;
              }
            });
          });
      },
      
      /**
       * 获取基于情绪的音乐推荐
       */
      getEmotionBasedMusic(emotion) {
        if (!this.user || !this.user.isLoggedIn || !emotion) {
          console.error('getEmotionBasedMusic: 缺少必要参数');
          return;
        }
        
        this.isLoading = true;
        
        // 确保先设置默认推荐，防止undefined错误
        this.recommendations = [
          {
            track_id: 'default1',
            track_name: '情绪推荐歌曲1',
            artist_name: '情绪艺术家1',
            explanation: `基于您的${emotion}情绪推荐`,
            title: '情绪推荐歌曲1',
            artist: '情绪艺术家1',
            album_image: '/static/img/default-album.png'
          },
          {
            track_id: 'default2',
            track_name: '情绪推荐歌曲2',
            artist_name: '情绪艺术家2',
            explanation: `基于您的${emotion}情绪推荐`,
            title: '情绪推荐歌曲2',
            artist: '情绪艺术家2',
            album_image: '/static/img/default-album.png'
          }
        ];
        
        axios.get(`/api/emotion/music?user_id=${this.user.id}&emotion=${emotion}`)
          .then(response => {
            // 确保返回数据是数组
            if (response.data && Array.isArray(response.data) && response.data.length > 0) {
              // 确保每个推荐对象都有title和artist字段
              const processedRecommendations = response.data.map(rec => {
                // 确保rec是一个对象
                if (!rec || typeof rec !== 'object') {
                  return {
                    track_id: '未知ID',
                    track_name: '未知标题',
                    artist_name: '未知艺术家',
                    title: '未知标题',
                    artist: '未知艺术家',
                    explanation: `基于您的${emotion}情绪推荐`,
                    album_image: '/static/img/default-album.png'
                  };
                }
                
                return {
                  ...rec,
                  track_id: rec.track_id || rec.id || `未知ID_${Math.random()}`,
                  track_name: rec.track_name || rec.title || '未知标题',
                  artist_name: rec.artist_name || rec.artist || '未知艺术家',
                  title: rec.track_name || rec.title || '未知标题',
                  artist: rec.artist_name || rec.artist || '未知艺术家',
                  explanation: rec.explanation || `基于您的${emotion}情绪推荐`,
                  album_image: rec.album_image || rec.image || '/static/img/default-album.png'
                };
              });
              
              // 更新推荐列表
              this.recommendations = processedRecommendations;
            }
            
            // 如果用户当前在聊天标签，可以提供一个按钮切换到推荐标签
            if (this.currentTab === 'chat') {
              // 添加一个提示，可以用按钮切换
              this.showNotification('情绪音乐已准备好，可在推荐标签查看', 'success');
            }
          })
          .catch(error => {
            console.error('获取情绪音乐失败:', error);
            this.showNotification('获取情绪音乐推荐失败，使用默认推荐', 'danger');
            // 默认推荐已在方法开始时设置
          })
          .finally(() => {
            this.isLoading = false;
          });
      },
      
      // 获取聊天历史
      getChatHistory() {
        if (!this.user.isLoggedIn) return;
        
        this.isLoading = true;
        
        axios.get(`/api/chat/history?user_id=${this.user.id}`)
          .then(response => {
            this.chatHistory = response.data.history || [];
            console.log('已加载聊天历史:', this.chatHistory.length);
            
            // 转换为兼容模板的格式
            this.chatMessages = this.chatHistory.flatMap(record => [
              { content: record.user_message, isUser: true },
              { content: record.ai_response, isUser: false }
            ]);
          })
          .catch(error => {
            console.error('加载聊天历史失败:', error);
          })
          .finally(() => {
            this.isLoading = false;
          });
      },
      
      /**
       * 使用预设提示消息
       */
      usePrompt(prompt) {
        if (!prompt) return;
        
        this.chatInput = prompt;
        
        this.$nextTick(() => {
          // 让输入框获取焦点
          const inputElement = document.querySelector('.chat-input-container input');
          if (inputElement) {
            inputElement.focus();
          }
          
          // 也可以直接发送消息
          // this.sendChatMessage();
        });
      },
      
      // 提交反馈
      submitFeedback(songId, feedbackType) {
        if (!this.user.isLoggedIn) return;
        
        axios.post('/api/feedback', {
          user_id: this.user.id,
          track_id: songId,
          feedback_type: feedbackType
        })
          .then(response => {
            console.log('反馈提交成功:', songId, feedbackType);
            this.showNotification('感谢您的反馈！', 'success');
            
            // 从推荐列表中移除该歌曲并添加淡出动画
            if (feedbackType === 'dislike') {
              const index = this.recommendations.findIndex(song => song.track_id === songId);
              if (index !== -1) {
                const songElement = document.querySelectorAll('.card')[index];
                if (songElement) {
                  songElement.classList.add('animate__animated', 'animate__fadeOut');
                  
                  setTimeout(() => {
                    this.recommendations.splice(index, 1);
                  }, 500);
                }
              }
            }
          })
          .catch(error => {
            console.error('反馈提交失败:', error);
            this.showNotification('反馈提交失败，请重试', 'danger');
          });
      },
      
      // 提交满意度评估
      submitEvaluation() {
        if (!this.user.isLoggedIn || !this.isEvaluationComplete) return;
        
        this.isLoading = true;
        
        axios.post('/api/evaluation', {
          user_id: this.user.id,
          responses: this.evaluationResponses,
          comment: this.evaluationComment
        })
          .then(response => {
            console.log('满意度评估提交成功:', this.evaluationResponses);
            this.showNotification('感谢您的评价！', 'success');
            this.evaluationSubmitted = true;
            this.satisfactionLevel = 0;
            this.feedbackText = '';
          })
          .catch(error => {
            console.error('满意度评估提交失败:', error);
            this.showNotification('评价提交失败，请重试', 'danger');
          })
          .finally(() => {
            this.isLoading = false;
          });
      },
      
      // 显示通知
      showNotification(message, type = 'info') {
        this.notification.message = message;
        this.notification.type = type;
        this.notification.isVisible = true;
        
        // 添加到通知列表
        const notificationType = type === 'danger' ? 'is-danger' : 
                                type === 'warning' ? 'is-warning' : 
                                type === 'success' ? 'is-success' : 'is-info';
        this.notifications.push({
          message: message,
          type: notificationType
        });
        
        // 3秒后自动隐藏通知
        setTimeout(() => {
          this.notification.isVisible = false;
        }, 3000);
        
        // 3秒后从通知列表中移除
        setTimeout(() => {
          if (this.notifications.length > 0) {
            this.notifications.shift();
          }
        }, 3000);
      },
      
      // 用户注册
      register() {
        if (!this.username.trim()) {
          this.loginErrorMessage = '请输入用户名';
          return;
        }
        
        if (!this.email.trim()) {
          this.loginErrorMessage = '请输入邮箱';
          return;
        }
        
        if (!this.password.trim()) {
          this.loginErrorMessage = '请输入密码';
          return;
        }
        
        this.isLoading = true;
        this.loginErrorMessage = '';
        
        // 准备注册数据
        const registerData = {
          username: this.username,
          password: this.password,
          email: this.email
        };
        
        // 发送注册请求
        axios.post('/api/user/register', registerData)
          .then(response => {
            console.log('注册成功:', response.data);
            
            if (response.data && response.data.user_id) {
              // 注册成功，自动登录
              this.user = {
                id: response.data.user_id,
                username: response.data.username || this.username,
                email: this.email,
                isLoggedIn: true,
                isDeveloper: response.data.is_developer || false
              };
              
              // 保存到本地存储
              localStorage.setItem('userId', this.user.id);
              localStorage.setItem('username', this.user.username);
              localStorage.setItem('email', this.user.email);
              localStorage.setItem('isLoggedIn', 'true');
              localStorage.setItem('isDeveloper', this.user.isDeveloper ? 'true' : 'false');
              
              // 显示成功通知
              this.showNotification('注册并登录成功！', 'success');
              
              // 加载初始数据
              this.loadSampleSongs();
              
              // 添加AI欢迎消息
              this.chatMessages.push({
                content: `欢迎，${this.username}！我是您的AI音乐助手。请问您想了解什么音乐信息或获取什么推荐？`,
                isUser: false
              });
            } else {
              // 注册成功但没有返回用户ID，尝试登录
              this.login();
            }
          })
          .catch(error => {
            console.error('注册失败:', error);
            
            // 显示错误消息
            if (error.response && error.response.data && error.response.data.error) {
              this.loginErrorMessage = error.response.data.error;
            } else {
              this.loginErrorMessage = '注册失败，请重试';
            }
            
            this.isLoading = false;
          });
      },
      
      /**
       * 用户登录
       */
      login: function() {
        console.log("开始登录流程，当前用户名：", this.username, "当前绑定字段:", document.querySelector("input[v-model='username']") ? true : false);
        
        if (this.user && this.user.isLoggedIn) {
            console.log("用户已登录，跳过登录过程");
            return;
        }
        
        if (!this.username) {
            // 修复错误：确保即使在英文界面下也能访问错误消息
            let errorMessage = "请输入用户名";
            
            // 安全地访问errors对象
            if (this.content && this.content[this.currentLanguage] && 
                this.content[this.currentLanguage].errors && 
                this.content[this.currentLanguage].errors.emptyUsername) {
                errorMessage = this.content[this.currentLanguage].errors.emptyUsername;
            }
            
            this.addNotification(errorMessage, 'is-danger');
            return;
        }
        
        // 开始登录流程
        this.isLoading = true;
        
        // 准备登录数据
        var loginData = {
            username: this.username,
            email: this.email || "",
            password: this.password || ""
        };
        
        console.log("登录数据:", loginData);
        
        // 开发者登录逻辑简化
        if (this.isDeveloperMode && !this.password) {
            loginData.password = "test123";
        }
        
        axios.post('/api/user/login', loginData)
            .then(response => {
                console.log("登录成功:", response.data);
                
                // 确保用户数据包含所有必要字段
                const userData = {
                    username: response.data.username || this.username,
                    email: response.data.email || this.email || "",
                    isDeveloper: response.data.is_developer || false,
                    isLoggedIn: true,
                    id: response.data.id || response.data.user_id || Date.now()
                };
                
                // 保存用户会话到本地存储
                localStorage.setItem('user', JSON.stringify(userData));
                localStorage.setItem('user_session', JSON.stringify(userData)); // 同时保存到两个key
                localStorage.setItem('userId', userData.id);
                localStorage.setItem('username', userData.username);
                localStorage.setItem('isLoggedIn', 'true');
                
                // 更新应用状态
                this.user = userData;
                this.username = userData.username;
                this.isDeveloperMode = userData.isDeveloper;
                
                // 重置登录表单
                this.loginUsername = "";
                this.password = "";
                this.loginEmail = "";
                this.isRegistering = false;
                
                // 加载初始数据
                this.loadInitialData();
                
                // 修改这里：登录成功后显示欢迎页面
                this.currentTab = 'welcome';
                
                // 安全地访问成功消息
                let successMessage = "登录成功！";
                if (this.content && this.content[this.currentLanguage] && 
                    this.content[this.currentLanguage].success && 
                    this.content[this.currentLanguage].success.login) {
                    successMessage = this.content[this.currentLanguage].success.login;
                }
                
                this.addNotification(successMessage, 'is-success');
                
                // 向控制台打印登录成功信息
                console.log("用户登录成功", this.user);
                console.log("当前Tab:", this.currentTab);
            })
            .catch(error => {
                console.error("登录错误:", error.response ? error.response.data : error);
                
                // 安全地访问错误消息
                let errorMessage = "登录失败，请检查您的用户名和密码";
                if (this.content && this.content[this.currentLanguage] && 
                    this.content[this.currentLanguage].errors && 
                    this.content[this.currentLanguage].errors.loginFailed) {
                    errorMessage = this.content[this.currentLanguage].errors.loginFailed;
                }
                
                if (error.response && error.response.data && error.response.data.error) {
                    errorMessage = error.response.data.error;
                }
                
                this.addNotification(errorMessage, 'is-danger');
            })
            .finally(() => {
                this.isLoading = false;
            });
      },
      
      /**
       * 选择填写调查问卷
       */
      chooseSurvey: function() {
        // 初始化调查问卷
        this.surveyQuestions.find(q => q.id === 'music_genres').options = this.musicGenres;
        this.surveyCompleted = false;
        this.showWelcomeOptions = false;
        this.showPreferencesSurvey = true;
        this.currentTab = 'survey';
      },
      
      /**
       * 选择AI聊天
       */
      chooseAIChat: function() {
        this.showWelcomeOptions = false;
        this.currentTab = 'chat';
        this.loadChatHistory();
      },
      
      /**
       * 回答调查问题
       */
      answerQuestion: function(questionId, answer) {
        const question = this.surveyQuestions.find(q => q.id === questionId);
        if (!question) return;
        
        if (question.type === 'single') {
          // 单选题直接设置答案
          question.answer = answer;
        } else if (question.type === 'multiple') {
          // 多选题处理选中/取消选中
          const index = question.answer.indexOf(answer);
          if (index === -1) {
            // 添加选项
            question.answer.push(answer);
          } else {
            // 移除选项
            question.answer.splice(index, 1);
          }
        }
      },
      
      /**
       * 提交调查问卷
       */
      submitSurvey: function() {
        // 收集用户偏好
        this.preferences = [];
        
        // 将问卷答案转换为偏好
        this.surveyQuestions.forEach(question => {
          if (question.id === 'music_genres' && question.answer.length > 0) {
            this.selectedGenres = [...question.answer];
          }
          
          if (question.answer && 
             (question.type === 'single' && question.answer !== '') || 
             (question.type === 'multiple' && question.answer.length > 0)) {
            this.preferences.push({
              preference_id: question.id,
              preference_type: question.type,
              preference_value: JSON.stringify(question.answer)
            });
          }
        });
        
        // 保存用户偏好到本地存储
        localStorage.setItem('user_preferences', JSON.stringify(this.preferences));
        
        // 标记调查完成
        this.surveyCompleted = true;
        this.showPreferencesSurvey = false;
        
        // 加载个性化推荐
        this.getPersonalizedRecommendations();
        
        // 显示通知
        this.showNotification(
          this.currentLanguage === 'zh' ? '感谢您完成调查！' : 'Thank you for completing the survey!',
          'success'
        );
      },
      
      /**
       * 跳过调查
       */
      skipSurvey: function() {
        this.surveyCompleted = true;
        this.showPreferencesSurvey = false;
        
        // 加载默认推荐
        this.recommendations = [...this.defaultRecommendations];
        this.currentTab = 'recommendations';
        
        // 通知用户
        this.showNotification(
          this.currentLanguage === 'zh' ? '已跳过调查' : 'Survey skipped',
          'info'
        );
      },
      
      /**
       * 获取个性化推荐
       */
      getPersonalizedRecommendations: function() {
        // 设置加载状态
        this.isLoading = true;
        this.recommendations = [...this.defaultRecommendations]; // 设置默认值
        
        // 准备请求参数
        const params = {
          user_id: this.user.id,
          genres: this.selectedGenres.join(',')
        };
        
        // 切换到推荐选项卡
        this.currentTab = 'recommendations';
        
        // 向API发送请求
        axios.get('/api/recommendations/personalized', { params: params })
          .then(response => {
            this.isLoading = false;
            
            if (response.data && response.data.recommendations && response.data.recommendations.length > 0) {
              // 确保每个推荐项都有title和artist字段
              this.recommendations = response.data.recommendations.map(rec => {
                return {
                  track_id: rec.track_id || '',
                  track_name: rec.track_name || '',
                  artist_name: rec.artist_name || '',
                  title: rec.title || rec.track_name || '',
                  artist: rec.artist || rec.artist_name || '',
                  explanation: rec.explanation || '根据您的偏好推荐'
                };
              });
              
              // 记录加载的推荐数量
              console.log('已加载' + this.recommendations.length + '条个性化推荐');
              
              // 添加动画效果
              setTimeout(() => {
                const cards = document.querySelectorAll('.recommendation-card');
                cards.forEach((card, index) => {
                  setTimeout(() => {
                    card.classList.add('show');
                  }, index * 100);
                });
              }, 100);
            } else {
              // 推荐加载失败，使用默认推荐
              console.log('未能获取个性化推荐，使用默认推荐');
            }
          })
          .catch(error => {
            this.isLoading = false;
            console.error('获取个性化推荐出错:', error);
            
            // 显示错误通知
            this.showNotification(
              this.currentLanguage === 'zh' ? '获取推荐失败，请稍后再试' : 'Failed to get recommendations, please try again later',
              'error'
            );
          });
      },
      
      // 登出用户
      logoutUser: function() {
        // 清除用户状态
        this.user.id = null;
        this.user.username = '';
        this.user.email = '';
        this.user.isLoggedIn = false;
        this.user.isDeveloper = false;
        
        // 清除本地存储
        localStorage.removeItem('user');
        localStorage.removeItem('user_preferences');
        
        // 重置界面状态
        this.showLoginForm = true;
        this.showWelcomeOptions = false;
        this.showPreferencesSurvey = false;
        this.currentTab = 'welcome';
        this.selectedGenres = [];
        
        // 清空问卷答案
        this.surveyQuestions.forEach(question => {
          if (question.type === 'single') {
            question.answer = '';
          } else {
            question.answer = [];
          }
        });
        
        // 显示通知
        this.showNotification(
          this.currentLanguage === 'zh' ? '已成功退出登录' : 'Successfully logged out',
          'info'
        );
      },
      
      // 播放音频预览
      playPreview: function(previewUrl, trackName) {
        if (!previewUrl) {
          this.showNotification(
            this.currentLanguage === 'zh' ? '无法播放，预览链接不可用' : 'Cannot play, preview link unavailable',
            'error'
          );
          return;
        }
        
        // 停止当前播放的音频
        if (this.currentAudio) {
          this.currentAudio.pause();
          this.currentAudio = null;
        }
        
        // 创建新音频对象
        const audio = new Audio(previewUrl);
        this.currentAudio = audio;
        
        // 开始播放
        audio.play().then(() => {
          this.showNotification(
            this.currentLanguage === 'zh' ? '正在播放: ' + (trackName || '音乐') : 'Now playing: ' + (trackName || 'music'),
            'info'
          );
        }).catch(error => {
          console.error('播放音频出错:', error);
          this.showNotification(
            this.currentLanguage === 'zh' ? '播放失败，请稍后再试' : 'Playback failed, please try again later',
            'error'
          );
        });
        
        // 播放结束时清理
        audio.onended = () => {
          this.currentAudio = null;
        };
      },
      
      // 处理图片加载错误
      handleImageError: function(event) {
        event.target.src = 'static/img/music-pattern.svg';
      },
      
      // 播放歌曲预览
      playSongPreview(previewUrl) {
        this.playPreview(previewUrl);
      },
      
      // 对单首歌曲评分
      rateSongItem(song, rating) {
        if (!song || !song.track_id) return;
        
        // 设置歌曲评分
        song.rating = rating;
        
        // 调用评分API
        this.rateSong(song.track_id, rating);
      },
      
      // 点赞歌曲
      likeSong(song) {
        if (!song || !song.track_id) return;
        
        this.submitFeedback(song.track_id, 'like');
        this.showNotification('感谢您的反馈！', 'success');
      },
      
      // 点踩歌曲
      dislikeSong(song) {
        if (!song || !song.track_id) return;
        
        this.submitFeedback(song.track_id, 'dislike');
        this.showNotification('感谢您的反馈！我们会改进推荐', 'info');
      },
      
      // 加载聊天历史
      loadChatHistory() {
        // 如果用户没有登录，不加载聊天历史
        if (!this.user.isLoggedIn) return;
        
        // 调用获取聊天历史的API
        this.getChatHistory();
      },
      
      // 移除通知
      removeNotification(index) {
        this.notifications.splice(index, 1);
      },
      
      // 获取通知图标
      getNotificationIcon(type) {
        switch (type) {
          case 'is-success':
            return 'fas fa-check-circle';
          case 'is-danger':
            return 'fas fa-exclamation-circle';
          case 'is-warning':
            return 'fas fa-exclamation-triangle';
          case 'is-info':
          default:
            return 'fas fa-info-circle';
        }
      },
      
      // 添加通知
      addNotification(message, type = 'is-info') {
        console.log("添加通知:", message, type);
        if (!this.notifications) {
          this.notifications = [];
        }
        this.notifications.push({
          message: message,
          type: type
        });
        
        // 同时更新单一通知对象，兼容旧代码
        this.notification = {
          message: message,
          type: type.replace('is-', ''),
          isVisible: true
        };
        
        // 3秒后自动移除通知
        setTimeout(() => {
          if (this.notifications && this.notifications.length > 0) {
            this.notifications.shift();
          }
          this.notification.isVisible = false;
        }, 3000);
      },
      
      // 加载用户评分记录
      loadUserRatings() {
        if (!this.user.isLoggedIn) return;
        
        this.isLoading = true;
        
        axios.get(`/api/user_ratings/${this.user.id}`)
          .then(response => {
            this.userRatings = response.data || {};
            console.log('已加载用户评分:', Object.keys(this.userRatings).length);
          })
          .catch(error => {
            console.error('加载用户评分失败:', error);
          })
          .finally(() => {
            this.isLoading = false;
          });
      },
      
      // 加载所有用户 (管理员功能)
      loadAllUsers() {
        if (!this.user.isDeveloper) {
          this.showNotification('只有开发者才能查看用户列表', 'warning');
          this.currentTab = 'home';
          return;
        }
        
        this.isLoading = true;
        
        axios.get(`/api/user/all?admin_id=${this.user.id}`)
          .then(response => {
            this.allUsers = response.data || [];
            console.log('已加载所有用户:', this.allUsers.length);
          })
          .catch(error => {
            console.error('加载用户列表失败:', error);
            this.showNotification('加载用户列表失败', 'error');
          })
          .finally(() => {
            this.isLoading = false;
          });
      },
      
      // 添加新用户 (管理员功能)
      addUser() {
        if (!this.user.isDeveloper) {
          this.showNotification('只有开发者才能添加用户', 'warning');
          return;
        }
        
        if (!this.newUser.username.trim()) {
          this.showNotification('请输入用户名', 'warning');
          return;
        }
        
        if (!this.newUser.password.trim()) {
          this.showNotification('请输入密码', 'warning');
          return;
        }
        
        this.isLoading = true;
        
        // 准备添加用户的数据
        const userData = {
          admin_id: this.user.id,
          username: this.newUser.username,
          password: this.newUser.password,
          email: this.newUser.email,
          is_developer: this.newUser.isDeveloper
        };
        
        axios.post('/api/user/register', userData)
          .then(response => {
            console.log('添加用户成功:', response.data);
            this.showNotification('添加用户成功', 'success');
            
            // 重置表单
            this.newUser = {
              username: '',
              email: '',
              password: '',
              isDeveloper: false
            };
            
            // 重新加载用户列表
            this.loadAllUsers();
          })
          .catch(error => {
            console.error('添加用户失败:', error);
            
            // 显示错误消息
            if (error.response && error.response.data && error.response.data.error) {
              this.showNotification(error.response.data.error, 'error');
            } else {
              this.showNotification('添加用户失败，请重试', 'error');
            }
          })
          .finally(() => {
            this.isLoading = false;
          });
      },
      
      // 编辑用户 (管理员功能)
      editUser(user) {
        this.editingUser = { ...user };
        
        // 这里可以打开一个编辑模态框
        // 为简化起见，我们直接在控制台中显示一条消息
        console.log('编辑用户:', this.editingUser);
        this.showNotification('编辑用户功能待实现', 'info');
      },
      
      // 删除用户 (管理员功能)
      deleteUser(user) {
        if (user.id === 'dev-001') {
          this.showNotification('不能删除主开发者账号', 'warning');
          return;
        }
        
        if (confirm(`确定要删除用户 ${user.username} 吗？`)) {
          this.isLoading = true;
          
          axios.delete(`/api/user/delete?admin_id=${this.user.id}&user_id=${user.id}`)
            .then(response => {
              console.log('删除用户成功:', response.data);
              this.showNotification('删除用户成功', 'success');
              
              // 从列表中移除该用户
              this.allUsers = this.allUsers.filter(u => u.id !== user.id);
            })
            .catch(error => {
              console.error('删除用户失败:', error);
              this.showNotification('删除用户失败，请重试', 'error');
            })
            .finally(() => {
              this.isLoading = false;
            });
        }
      },
      
      /**
       * 用户登出
       */
      logout: function() {
        console.log("执行登出操作");
        // 调用logoutUser方法
        this.logoutUser();
        
        // 清除所有相关存储
        localStorage.removeItem('user');
        localStorage.removeItem('user_session');
        localStorage.removeItem('userId');
        localStorage.removeItem('username');
        localStorage.removeItem('email');
        localStorage.removeItem('isLoggedIn');
        localStorage.removeItem('isDeveloper');
        
        // 重置用户相关字段
        this.username = '';
        this.email = '';
        this.password = '';
        
        // 添加登出成功通知
        this.addNotification(
          this.currentLanguage === 'zh' ? '已成功退出登录' : 'Successfully logged out',
          'is-success'
        );
        
        console.log("登出完成，用户状态：", this.user);
      }
    }
  });
  
  // 将事件总线暴露给全局，以便组件间通信
  window.EventBus = EventBus;
  
  // 添加Vue全局错误处理
  Vue.config.errorHandler = function(err, vm, info) {
    console.error('Vue错误:', err);
    console.error('组件:', vm);
    console.error('信息:', info);
  };
}); 