
// 小说数据和状态管理
class NovelApp {
    constructor() {
        this.novels = [];
        this.filteredNovels = [];
        this.currentFilter = 'all';
        this.init();
    }

    async init() {
        await this.loadNovels();
        this.renderNovels();
        this.setupEventListeners();
    }

    // 加载小说数据
    async loadNovels() {
        try {
            const response = await fetch('novels.json');
            const data = await response.json();
            this.novels = data.novels;
            this.filteredNovels = [...this.novels];
        } catch (error) {
            console.error('加载小说数据失败:', error);
            // 使用示例数据作为备用
            this.novels = this.getSampleData();
            this.filteredNovels = [...this.novels];
        }
    }

    // 示例数据
     getSampleData() {
         return [
             {
              "id": 1,
              "title": "周少&慕溪",
              "author": "***",
              "description": "暂无",
              "tags": ["校园", "同人", "青春", "双男"],
              "cover": "📖",
              "path": "novels/sword",
              "chapters": [
                {"title": "1-10", "file": "1-10.md"},
                {"title": "11-20", "file": "11-20.md"},
                {"title": "21-30", "file": "21-30.md"}
              ],
              "updateTime": "2025-10-24",
              "wordCount": 125000
            },
            {
              "id": 2,
              "title": "诡异陈萧",
              "author": "wyxrl",
              "description": "某天陈星宇掉进了一个神秘空间...",
              "tags": ["无限流", "双男", "恐怖", "热血"],
              "cover": "🎮",
              "path": "novels/professional",
              "chapters": [
                {"title": "第二章 深入工厂", "file": "第二章 深入工厂.md"},
                {"title": "第三章 主控室的危机", "file": "第三章 主控室的危机.md"},
                {"title": "第四章 绝境求生与神秘力量", "file": "第四章 绝境求生与神秘力量.md"},
                {"title": "第五章 新副本前奏：神秘小镇", "file": "第五章 新副本前奏：神秘小镇.md"},
                {"title": "第六章 月圆之夜的仪式", "file": "第六章 月圆之夜的仪式.md"}
                {"title": "第七章 神秘之门后的真相", "file": "第一章 神秘之门后的真相.md"},
              ],
              "updateTime": "2025-11-07",
              "wordCount": 98000
            },
             {
              "id": 3,
              "title": "漫漫消沉",
              "author": "爱装的wy",
              "description": "这是新人的第一个作品，可以支持一下吗？可能更新有点慢，双男主，非np【萧贺怊】×【陈俞】有副cp，攻会提前知道受的马甲，但受不知道 陈俞【女装大佬】开学第一天就和萧贺怊【外冷内热校霸】结下了梁子，没想到还被分到了同一个寝室..",
              "tags": ["都市", "双男", "青春", "甜宠","爽文"],
              "cover": "🎮",
              "path": "novels/cxy",
              "chapters": [
                {"title": "引子", "file": "引子.md"},
                {"title": "第 1 章 初识", "file": "第 1 章 初识.md"},
                {"title": "第 2 章 跑操", "file": "第 2 章 跑操.md"},
                {"title": "第 3 章 举报", "file": "第 3 章 举报.md"},
                {"title": "第 4 章 阅读节活动", "file": "第 4 章 阅读节活动.md"}
                {"title": "第 5 章 暗流涌动", "file": "第 5 章 暗流涌动.md"},
                {"title": "第 6 章：危机四伏与转机乍现", "file": "第 6 章：危机四伏与转机乍现.md"},
                {"title": "第 7 章：新的阴谋与困境", "file": "第 7 章：新的阴谋与困境.md"},
                {"title": "第 8 章：大赛前夕的暗潮", "file": "第 8 章：大赛前夕的暗潮.md"},
                {"title": "第 9 章：平静中的余波与新的契机", "file": "第 9 章：平静中的余波与新的契机.md"}
                {"title": "第 10 章：合作波折与意外转机", "file": "第 10 章：合作波折与意外转机.md"},
                {"title": "第 11 章：海外风云起", "file": "第 11 章：海外风云起.md"},
                {"title": "第 12 章：内外交困与破局之策", "file": "第 12 章：内外交困与破局之策.md"},
                {"title": "第 13 章：合作洽谈的波折与转机", "file": "第 13 章：合作洽谈的波折与转机.md"},
                {"title": "第 14 章：项目推进的挑战与成长", "file": "第 14 章：项目推进的挑战与成长.md"}
                {"title": "第 15 章：盛名之下的暗涌与抉择", "file": "第 15 章：盛名之下的暗涌与抉择.md"},
                {"title": "第 16 章：特殊教育领域的推广与突破", "file": "第 16 章：特殊教育领域的推广与突破.md"},
                {"title": "第 17 章：拓展普通教育市场的征程", "file": "第 17 章：拓展普通教育市场的征程.md"},
                {"title": "第 18 章：竞争中的突破与新挑战", "file": "第 18 章：竞争中的突破与新挑战.md"},
                {"title": "第 19 章：构建教育生态的坎坷之路", "file": "第 19 章：构建教育生态的坎坷之路.md"}
                {"title": "第 20 章：破局与升华.", "file": "第 20 章：破局与升华.md"}
              ],
              "updateTime": "2025-11-08",
              "wordCount": 71000
            }
         ];
     }

    // 渲染小说列表
    renderNovels() {
        const grid = document.getElementById('novelGrid');
        if (!grid) return;

        if (this.filteredNovels.length === 0) {
            grid.innerHTML = '<div class="no-results">没有找到匹配的小说</div>';
            return;
        }

        grid.innerHTML = this.filteredNovels.map(novel => `
            <div class="novel-card" data-id="${novel.id}">
                <div class="novel-cover">${novel.cover}</div>
                <div class="novel-info">
                    <h3 class="novel-title">${novel.title}</h3>
                    <div class="novel-author">作者：${novel.author}</div>
                    <p class="novel-description">${novel.description}</p>
                    <div class="novel-tags">
                        ${novel.tags.map(tag => `<span class="novel-tag">${tag}</span>`).join('')}
                    </div>
                </div>
            </div>
        `).join('');

        // 添加点击事件
        document.querySelectorAll('.novel-card').forEach(card => {
            card.addEventListener('click', (e) => {
                const novelId = parseInt(card.dataset.id);
                this.showNovelDetail(novelId);
            });
        });
    }

    // 显示小说详情
    async showNovelDetail(novelId) {
        const novel = this.novels.find(n => n.id === novelId);
        if (!novel) return;

        try {
            // 加载小说详情信息
            const novelInfoResponse = await fetch(`${novel.path}/info.json`);
            const novelInfo = await novelInfoResponse.json();
            
            const modalContent = document.getElementById('modalContent');
            modalContent.innerHTML = `
                <h2>${novel.title}</h2>
                <div class="novel-meta">
                    <span>作者：${novel.author}</span>
                    <span>更新时间：${novel.updateTime}</span>
                </div>
                <div class="novel-description">${novelInfo.description || novel.description}</div>
                <div class="chapter-list">
                    <h3>章节列表</h3>
                    <ul>
                        ${novel.chapters.map((chapter, index) => `
                            <li>
                                <a href="reader.html?novel=${novel.id}&chapter=${index + 1}">
                                    ${chapter.title}
                                </a>
                            </li>
                        `).join('')}
                    </ul>
                </div>
                <button onclick="window.location.href='reader.html?novel=${novel.id}&chapter=1'" 
                        class="read-btn">开始阅读</button>
            `;

            document.getElementById('novelModal').style.display = 'block';
        } catch (error) {
            console.error('加载小说详情失败:', error);
        }
    }

    // 设置事件监听器
    setupEventListeners() {
        // 筛选标签
        document.querySelectorAll('.filter-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
                e.target.classList.add('active');
                this.currentFilter = e.target.dataset.filter;
                this.filterNovels();
            });
        });

        // 关闭模态框
        document.querySelector('.close').addEventListener('click', () => {
            document.getElementById('novelModal').style.display = 'none';
        });

        // 点击模态框外部关闭
        window.addEventListener('click', (e) => {
            const modal = document.getElementById('novelModal');
            if (e.target === modal) {
                modal.style.display = 'none';
            }
        });

        // 搜索功能
        const searchInput = document.getElementById('searchInput');
        const heroSearch = document.getElementById('heroSearch');
        
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.handleSearch(e.target.value);
            });
        }
        
        if (heroSearch) {
            heroSearch.addEventListener('input', (e) => {
                this.handleSearch(e.target.value);
            });
        }
    }

    // 筛选小说
    filterNovels() {
        if (this.currentFilter === 'all') {
            this.filteredNovels = [...this.novels];
        } else {
            this.filteredNovels = this.novels.filter(novel => 
                novel.tags.includes(this.currentFilter)
            );
        }
        this.renderNovels();
    }

    // 处理搜索
    handleSearch(query) {
        if (!query.trim()) {
            this.filteredNovels = [...this.novels];
        } else {
            const lowerQuery = query.toLowerCase();
            this.filteredNovels = this.novels.filter(novel =>
                novel.title.toLowerCase().includes(lowerQuery) ||
                novel.author.toLowerCase().includes(lowerQuery) ||
                novel.description.toLowerCase().includes(lowerQuery) ||
                novel.tags.some(tag => tag.toLowerCase().includes(lowerQuery))
            );
        }
        this.renderNovels();
    }
}

// 搜索功能
class SearchEngine {
    constructor(novels) {
        this.novels = novels;
        this.setupSearch();
    }

    setupSearch() {
        const searchBtn = document.getElementById('searchBtn');
        if (searchBtn) {
            searchBtn.addEventListener('click', () => {
                this.performSearch();
            });
        }
    }

    performSearch() {
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            const query = searchInput.value.trim();
            if (query) {
                this.search(query);
            }
        }
    }

    search(query) {
        const lowerQuery = query.toLowerCase();
        const results = this.novels.filter(novel =>
            novel.title.toLowerCase().includes(lowerQuery) ||
            novel.author.toLowerCase().includes(lowerQuery) ||
            novel.description.toLowerCase().includes(lowerQuery) ||
            novel.tags.some(tag => tag.toLowerCase().includes(lowerQuery))
        );
        
        this.displayResults(results, query);
    }

    displayResults(results, query) {
        // 在实际实现中，这里会更新UI显示搜索结果
        console.log(`搜索"${query}"找到${results.length}个结果:`, results);
    }
}

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.novelApp = new NovelApp();
    
    // 全局搜索函数
    window.performSearch = function() {
        const heroSearch = document.getElementById('heroSearch');
        if (heroSearch && heroSearch.value.trim()) {
            window.novelApp.handleSearch(heroSearch.value);
            document.getElementById('library').scrollIntoView({ behavior: 'smooth' });
        }
    };
});
