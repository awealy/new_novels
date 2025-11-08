
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
                id: 1,
                title: "剑来",
                author: "烽火戏诸侯",
                description: "少年陈平安的修仙之路，从一个小山村开始，逐渐揭开世界的秘密。",
                tags: ["玄幻", "仙侠", "武侠"],
                cover: "📖",
                path: "novels/sword",
                chapters: [
                    { title: "第一章 少年与剑", file: "chapter1.md" },
                    { title: "第二章 青云试炼", file: "chapter2.md" }
                ],
                updateTime: "2023-11-08"
            },
            {
                id: 2,
                title: "全职高手",
                author: "蝴蝶蓝",
                description: "荣耀网游大神叶修被迫退役后的重返巅峰之路。",
                tags: ["游戏", "竞技", "都市"],
                cover: "🎮",
                path: "novels/professional",
                chapters: [
                    { title: "第一章 荣耀归来", file: "chapter1.md" }
                ],
                updateTime: "2023-11-07"
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
