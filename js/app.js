// 小说数据和状态管理
class NovelApp {
    constructor() {
        this.novels = [];
        this.filteredNovels = [];
        this.currentFilter = 'all';
        this.isLoading = false;
        this.init();
    }

    async init() {
        try {
            await this.loadNovels();
            this.renderNovels();
            this.setupEventListeners();
            this.updateStats();
        } catch (error) {
            console.error('应用初始化失败:', error);
            this.showError('应用初始化失败，请刷新页面重试');
        }
    }

    // 增强的加载小说数据方法
    async loadNovels() {
        this.setLoading(true);

        try {
            const response = await fetch('novels.json');
            
            if (!response.ok) {
                throw new Error(`HTTP错误! 状态: ${response.status}`);
            }
            
            const text = await response.text();
            console.log('原始响应数据:', text.substring(0, 500) + '...');
            
            // 尝试修复常见的JSON格式错误
            const fixedText = this.tryFixJson(text);
            const data = JSON.parse(fixedText);
            
            // 数据验证
            if (!data.novels || !Array.isArray(data.novels)) {
                throw new Error('无效的数据结构: 缺少novels数组');
            }
            
            this.novels = data.novels.filter(novel => this.validateNovel(novel));
            this.filteredNovels = [...this.novels];
            
            console.log(`成功加载 ${this.novels.length} 本小说`);
            
        } catch (error) {
            console.error('加载小说数据失败:', error);
            this.showError(`数据加载失败: ${error.message}，使用示例数据继续运行`);
            
            // 使用示例数据作为备用
            this.novels = this.getSampleData();
            this.filteredNovels = [...this.novels];
        } finally {
            this.setLoading(false);
        }
    }

    // 尝试修复JSON格式错误
    tryFixJson(jsonString) {
        try {
            // 先尝试直接解析
            JSON.parse(jsonString);
            return jsonString;
        } catch (error) {
            console.warn('JSON解析失败，尝试修复...', error.message);

            let fixed = jsonString;

            // 修复1: 处理单引号
            fixed = fixed.replace(/(\w+):\s*'([^']*)'/g, '"$1": "$2"');

            // 修复2: 处理未加引号的属性名
            fixed = fixed.replace(/([{,]\s*)(\w+)(\s*:)/g, '$1"$2"$3');

            // 修复3: 移除尾随逗号
            fixed = fixed.replace(/,\s*([}\]])/g, '$1');

            // 修复4: 处理可能的多余字符
            fixed = fixed.replace(/[^\x20-\x7E\n\r\t]/g, '');

            console.log('修复后的JSON:', fixed.substring(0, 500) + '...');

            return fixed;
        }
    }

    // 小说数据验证
    validateNovel(novel) {
        const requiredFields = ['id', 'title', 'author', 'chapters'];
        const isValid = requiredFields.every(field => {
            const hasField = field in novel && novel[field] != null;
            if (!hasField) {
                console.warn(`小说数据缺少必要字段 "${field}":`, novel);
            }
            return hasField;
        });

        // 清理章节数据
        if (isValid && novel.chapters) {
            novel.chapters = novel.chapters.filter(chapter => 
                chapter && chapter.title && chapter.file
            );
        }

        return isValid;
    }

    // 设置加载状态
    setLoading(loading) {
        this.isLoading = loading;
        const loader = document.getElementById('loadingIndicator');
        if (loader) {
            loader.style.display = loading ? 'block' : 'none';
        }
    }

    // 显示错误信息
    showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.innerHTML = `
            <span>${message}</span>
            <button onclick="this.parentElement.remove()">×</button>
        `;
        errorDiv.style.cssText = `
            position: fixed; top: 20px; right: 20px; 
            background: #f8d7da; color: #721c24; padding: 12px; 
            border-radius: 4px; z-index: 1000; max-width: 400px;
            border: 1px solid #f5c6cb;
        `;
        document.body.appendChild(errorDiv);
        
        setTimeout(() => {
            if (errorDiv.parentElement) {
                errorDiv.remove();
            }
        }, 5000);
    }

    // 更新统计信息
    updateStats() {
        const statsDiv = document.getElementById('novelStats');
        if (!statsDiv) return;

        const totalNovels = this.novels.length;
        const totalWords = this.novels.reduce((sum, novel) => sum + (novel.wordCount || 0), 0);
        const totalChapters = this.novels.reduce((sum, novel) => sum + (novel.chapters?.length || 0), 0);

        statsDiv.innerHTML = `
            <div class="stat-item">
                <span class="stat-number">${totalNovels}</span>
                <span class="stat-label">本小说</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">${totalChapters}</span>
                <span class="stat-label">个章节</span>
            </div>
            <div class="stat-item">
                <span class="stat-number">${(totalWords / 10000).toFixed(1)}万</span>
                <span class="stat-label">字数</span>
            </div>
        `;
    }

    // 示例数据（保持不变）
    getSampleData() {
        return [
            // 示例数据
        ];
    }

    // 渲染小说列表（保持不变）
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
                    <div class="novel-meta">
                        <span>${novel.chapters?.length || 0}章</span>
                        <span>${((novel.wordCount || 0) / 10000).toFixed(1)}万字</span>
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

    // 显示小说详情（保持不变）
    async showNovelDetail(novelId) {
        const novel = this.novels.find(n => n.id === novelId);
        if (!novel) return;

        try {
            // 尝试加载额外的小说信息
            let novelInfo = { description: novel.description };
            try {
                const novelInfoResponse = await fetch(`${novel.path}/info.json`);
                if (novelInfoResponse.ok) {
                    novelInfo = await novelInfoResponse.json();
                }
            } catch (infoError) {
                console.warn('加载小说额外信息失败，使用基本信息:', infoError);
            }
            
            const modalContent = document.getElementById('modalContent');
            modalContent.innerHTML = `
                <h2>${novel.title}</h2>
                <div class="novel-meta">
                    <span>作者：${novel.author}</span>
                    <span>更新时间：${novel.updateTime}</span>
                    <span>字数：${((novel.wordCount || 0) / 10000).toFixed(1)}万</span>
                </div>
                <div class="novel-description">${novelInfo.description || novel.description}</div>
                <div class="chapter-list">
                    <h3>章节列表 (共${novel.chapters.length}章)</h3>
                    <ul>
                        ${novel.chapters.map((chapter, index) => `
                            <li>
                                <a href="reader.html?novel=${novel.id}&chapter=${index + 1}" 
                                   class="chapter-link">
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
            this.showError('加载小说详情失败: ' + error.message);
        }
    }

    // 设置事件监听器（保持不变）
    setupEventListeners() {
        // 筛选标签
        document.querySelectorAll('.filter-tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                document.querySelectorAll('.filter-tab').forEach(t => t.classList.remove('active'));
                e.target.classList.add('active');
                this.currentFilter = e.target.dataset.filter;
                this.filterNovels();
                this.updateStats();
            });
        });

        // 关闭模态框
        document.querySelector('.close')?.addEventListener('click', () => {
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

        // 添加键盘快捷键
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                document.getElementById('novelModal').style.display = 'none';
            }
        });
    }

    // 筛选小说（保持不变）
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

    // 处理搜索（保持不变）
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

// 初始化应用
document.addEventListener('DOMContentLoaded', () => {
    window.novelApp = new NovelApp();
    
    // 全局搜索函数
    window.performSearch = function() {
        const heroSearch = document.getElementById('heroSearch');
        if (heroSearch && heroSearch.value.trim()) {
            window.novelApp.handleSearch(heroSearch.value);
            document.getElementById('library')?.scrollIntoView({ behavior: 'smooth' });
        }
    };
});
