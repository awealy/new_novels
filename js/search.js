// 增强搜索功能
class AdvancedSearch {
    constructor() {
        this.index = null;
        this.novels = [];
        this.init();
    }

    async init() {
        await this.loadNovels();
        this.buildSearchIndex();
        this.setupSearchListeners();
    }

    async loadNovels() {
        try {
            const response = await fetch('novels.json');
            const data = await response.json();
            this.novels = data.novels;
        } catch (error) {
            console.error('加载小说数据失败:', error);
        }
    }

    buildSearchIndex() {
        // 简单的搜索索引实现
        this.index = this.novels.map((novel, id) => ({
            id: id,
            title: novel.title,
            author: novel.author,
            description: novel.description,
            tags: novel.tags.join(' '),
            content: `${novel.title} ${novel.author} ${novel.description} ${novel.tags.join(' ')}`
        }));
    }

    setupSearchListeners() {
        const searchInput = document.getElementById('searchInput');
        const heroSearch = document.getElementById('heroSearch');

        // 防抖搜索
        const debouncedSearch = this.debounce((query) => {
            this.performSearch(query);
        }, 300);

        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                debouncedSearch(e.target.value);
            });
        }

        if (heroSearch) {
            heroSearch.addEventListener('input', (e) => {
                debouncedSearch(e.target.value);
            });
        }

        // 回车搜索
        if (searchInput) {
            searchInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.performSearch(e.target.value);
                }
            });
        }

        if (heroSearch) {
            heroSearch.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.performSearch(e.target.value);
                    window.performSearch();
                }
            });
        }
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }

    performSearch(query) {
        if (!query.trim()) {
            this.displayResults(this.novels);
            return;
        }

        const results = this.simpleSearch(query);
        this.displayResults(results);
    }

    simpleSearch(query) {
        const lowerQuery = query.toLowerCase();
        return this.novels.filter(novel => {
            const searchableText = `
                ${novel.title} 
                ${novel.author} 
                ${novel.description} 
                ${novel.tags.join(' ')}
            `.toLowerCase();

            return searchableText.includes(lowerQuery);
        });
    }

    displayResults(results) {
        const grid = document.getElementById('novelGrid');
        if (!grid) return;

        if (results.length === 0) {
            grid.innerHTML = `
                <div class="no-results" style="grid-column: 1/-1; text-align: center; padding: 2rem;">
                    <i class="fas fa-search" style="font-size: 3rem; color: #ccc; margin-bottom: 1rem;"></i>
                    <p>没有找到匹配的小说</p>
                </div>
            `;
            return;
        }

        // 更新小说网格显示
        const novelApp = window.novelApp;
        if (novelApp) {
            novelApp.filteredNovels = results;
            novelApp.renderNovels();
        }
    }
}

// 初始化搜索功能
document.addEventListener('DOMContentLoaded', () => {
    window.advancedSearch = new AdvancedSearch();
});
