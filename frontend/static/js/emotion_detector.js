/**
 * 情感检测模块
 * 用于分析用户的情感状态并用于音乐推荐
 */

class EmotionDetector {
    constructor() {
        // 预定义的情感状态映射
        this.emotions = {
            "高兴": { valence: 0.8, energy: 0.7 },
            "平静": { valence: 0.6, energy: 0.3 },
            "悲伤": { valence: 0.2, energy: 0.3 },
            "愤怒": { valence: 0.3, energy: 0.8 },
            "兴奋": { valence: 0.7, energy: 0.9 },
            "放松": { valence: 0.6, energy: 0.2 },
            "焦虑": { valence: 0.4, energy: 0.7 }
        };
        
        // 简单的关键词匹配规则（前端简易实现）
        this.keywords = {
            "高兴": ["开心", "快乐", "欢乐", "高兴", "愉快", "喜悦", "好心情"],
            "平静": ["平静", "安宁", "祥和", "舒适", "安心", "平和"],
            "悲伤": ["难过", "伤心", "悲伤", "痛苦", "低落", "郁闷", "失落", "沮丧"],
            "愤怒": ["生气", "愤怒", "气愤", "恼火", "烦躁", "暴躁", "发怒"],
            "兴奋": ["兴奋", "激动", "振奋", "热血", "活力", "精神"],
            "放松": ["放松", "惬意", "休闲", "慵懒", "轻松", "自在"],
            "焦虑": ["焦虑", "紧张", "担心", "忧虑", "不安", "恐惧"]
        };
    }
    
    // 前端简单的情感分析（关键词匹配）
    analyzeLocally(text) {
        if (!text || text.trim() === '') {
            return { emotion: "平静", valence: 0.5, energy: 0.5 };
        }
        
        let matches = {};
        for (let emotion in this.keywords) {
            matches[emotion] = 0;
            this.keywords[emotion].forEach(keyword => {
                if (text.includes(keyword)) {
                    matches[emotion] += 1;
                }
            });
        }
        
        // 找出匹配度最高的情感
        let maxEmotion = "平静"; // 默认是平静
        let maxCount = 0;
        
        for (let emotion in matches) {
            if (matches[emotion] > maxCount) {
                maxCount = matches[emotion];
                maxEmotion = emotion;
            }
        }
        
        // 如果没有匹配，返回中性
        if (maxCount === 0) {
            return { emotion: "平静", valence: 0.5, energy: 0.5 };
        }
        
        return {
            emotion: maxEmotion,
            valence: this.emotions[maxEmotion].valence,
            energy: this.emotions[maxEmotion].energy
        };
    }
    
    // 使用后端API分析情感
    async detectFromText(text) {
        try {
            // 如果有后端API，使用以下代码
            // const response = await axios.post('/api/detect_emotion', { text });
            // return response.data;
            
            // 在没有后端API的情况下，使用前端简单的关键词匹配
            return this.analyzeLocally(text);
        } catch (error) {
            console.error('情感检测失败:', error);
            // 失败时返回中性情绪
            return { emotion: "平静", valence: 0.5, energy: 0.5 };
        }
    }
    
    // 根据音乐风格猜测情感
    mapGenreToEmotion(genre) {
        const genreToEmotion = {
            "流行": { emotion: "高兴", valence: 0.7, energy: 0.6 },
            "摇滚": { emotion: "愤怒", valence: 0.4, energy: 0.8 },
            "电子": { emotion: "兴奋", valence: 0.6, energy: 0.9 },
            "嘻哈": { emotion: "兴奋", valence: 0.6, energy: 0.7 },
            "古典": { emotion: "平静", valence: 0.7, energy: 0.3 },
            "爵士": { emotion: "放松", valence: 0.6, energy: 0.4 },
            "蓝调": { emotion: "悲伤", valence: 0.3, energy: 0.4 },
            "民谣": { emotion: "平静", valence: 0.5, energy: 0.3 }
        };
        
        return genreToEmotion[genre] || { emotion: "平静", valence: 0.5, energy: 0.5 };
    }
    
    // 生成情感相关的推荐理由
    generateRecommendationReason(emotion) {
        const reasons = {
            "高兴": [
                "这首欢快的歌曲能够延续你愉悦的心情",
                "听听这首活力满满的曲子，让快乐加倍",
                "这首歌的旋律轻快，正适合你现在的好心情"
            ],
            "平静": [
                "这首平和的曲子能让你保持内心的宁静",
                "这种舒缓的节奏很适合你当前平静的状态",
                "让这首歌帮你维持这份安宁"
            ],
            "悲伤": [
                "这首歌能够理解你的悲伤，给你一些共鸣",
                "有时候，听听能懂你的歌曲也是一种安慰",
                "这首略带忧伤的曲子，或许能陪你度过这段情绪"
            ],
            "愤怒": [
                "这首有力的歌曲可以帮你宣泄情绪",
                "强劲的节奏能够配合你当前的激烈心情",
                "这首歌的能量或许能帮你释放一些压力"
            ],
            "兴奋": [
                "这首节奏强劲的歌曲很配你现在兴奋的状态",
                "保持这份热情吧，这首歌会让你更加振奋",
                "这种充满活力的曲子正适合你的兴奋情绪"
            ],
            "放松": [
                "这首轻柔的歌曲会帮你更好地放松心情",
                "慵懒时刻，配上这样的曲子再合适不过",
                "让这首歌的旋律带你进入更舒适的状态"
            ],
            "焦虑": [
                "这首平缓的歌曲可以帮你缓解紧张情绪",
                "听听这首曲子，它能帮你找回一些平静",
                "这种舒缓的旋律设计用来安抚焦躁的心情"
            ]
        };
        
        const emotionReasons = reasons[emotion] || reasons["平静"];
        return emotionReasons[Math.floor(Math.random() * emotionReasons.length)];
    }
} 