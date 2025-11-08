class NovelReader {
    constructor() {
        this.currentNovel = null;
        this.currentChapter = 0;
        this.totalChapters = 0;
        this.fontSize = 16;
        this.isDarkMode = false;
        this.init();
    }

    async init() {
        await this.loadNovelData();
        this.setupEventListeners();
        this.updateProgress();
        this.loadChapter();
    }

    async loadNovelData() {
        const urlParams = new URLSearchParams(window.location.search);
        const novelId = urlParams.get('novel');
        const chapterId = parseInt(urlParams.get('chapter')) || 1;

        try {
            // 加载小说列表
            const response = await fetch('novels.json');
            const data = await response.json();
            
            this.currentNovel = data.novels.find(n => n.id == novelId);
            this.currentChapter = chapterId - 1;
            this.totalChapters = this.currentNovel.chapters.length;

            this.updateUI();
            this.setupChapterSelect();
        } catch (error) {
            console.error('加载小说数据失败:', error);
        }
    }

    async loadChapter() {
        if (!this.currentNovel) return;

        const chapter = this.currentNovel.chapters[this.currentChapter];
        const contentElement = document.getElementById('novelContent');
        
        contentElement.innerHTML = `
            <div class="loading">
                <i class="fas fa-book-open fa-spin"></i>
                <p>正在加载章节内容...</p>
            </div>
        `;

        try {
            const response = await fetch(`${this.currentNovel.path}/${chapter.file}`);
            const markdownText = await response.text();
            
            // 使用Marked.js渲染Markdown
            const htmlContent = marked.parse(markdownText);
            contentElement.innerHTML = htmlContent;
            
            document.getElementById('chapterTitle').textContent = chapter.title;
            this.updateProgress();
            this.updateURL();
        } catch (error) {
            console.error('加载章节内容失败:', error);
            contentElement.innerHTML = `
                <div class="error">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>加载章节内容失败，请稍后重试</p>
                </div>
            `;
        }
    }

    updateUI() {
        if (this.currentNovel) {
            document.title = `${this.currentNovel.chapters[this.currentChapter].title} - ${this.currentNovel.title}`;
        }
    }

    setupChapterSelect() {
        const select = document.getElementById('chapterSelect');
        select.innerHTML = '';
        
        this.currentNovel.chapters.forEach((chapter, index) => {
            const option = document.createElement('option');
            option.value = index;
            option.textContent = chapter.title;
            option.selected = index === this.currentChapter;
            select.appendChild(option);
        });

        select.addEventListener('change', (e) => {
            this.currentChapter = parseInt(e.target.value);
            this.loadChapter();
        });
    }

    setupEventListeners() {
        // 章节导航
        document.getElementById('prevChapter').addEventListener('click', () => {
            if (this.currentChapter > 0) {
                this.currentChapter--;
                this.loadChapter();
            }
        });

        document.getElementById('nextChapter').addEventListener('click', () => {
            if (this.currentChapter < this.totalChapters - 1) {
                this.currentChapter++;
                this.loadChapter();
            }
        });

        // 字体大小调整
        document.getElementById('fontSmaller').addEventListener('click', () => {
            this.fontSize = Math.max(12, this.fontSize - 2);
            this.updateFontSize();
        });

        document.getElementById('fontLarger').addEventListener('click', () => {
            this.fontSize = Math.min(24, this.fontSize + 2);
            this.updateFontSize();
        });

        document.getElementById('fontReset').addEventListener('click', () => {
            this.fontSize = 16;
            this.updateFontSize();
        });

        // 暗色模式
        document.getElementById('darkModeToggle').addEventListener('click', () => {
            this.toggleDarkMode();
        });

        // 键盘导航
        document.addEventListener('keydown', (e) => {
            switch(e.key) {
                case 'ArrowLeft':
                    if (this.currentChapter > 0) {
                        this.currentChapter--;
                        this.loadChapter();
                    }
                    break;
                case 'ArrowRight':
                    if (this.currentChapter < this.totalChapters - 1) {
                        this.currentChapter++;
                        this.loadChapter();
                    }
                    break;
            }
        });

        // 滚动进度
        window.addEventListener('scroll', () => {
            this.updateProgress();
        });
    }

    updateFontSize() {
        document.getElementById('novelContent').style.fontSize = `${this.fontSize}px`;
    }

    toggleDarkMode() {
        this.isDarkMode = !this.isDarkMode;
        document.body.classList.toggle('dark-mode', this.isDarkMode);
        
        const icon = document.querySelector('#darkModeToggle i');
        icon.className = this.isDarkMode ? 'fas fa-sun' : 'fas fa-moon';
    }

    updateProgress() {
        const scrollTop = window.scrollY;
        const windowHeight = window.innerHeight;
        const docHeight = document.documentElement.scrollHeight;
        
        const scrollPercent = (scrollTop / (docHeight - windowHeight)) * 100;
        document.querySelector('.progress').style.width = `${scrollPercent}%`;
        
        // 更新页码信息（简化版）
        const currentPage = Math.floor(scrollTop / windowHeight) + 1;
        const totalPages = Math.ceil(docHeight / windowHeight);
        document.getElementById('currentPage').textContent = currentPage;
        document.getElementById('totalPages').textContent = totalPages;
    }

    updateURL() {
        const newUrl = `${window.location.pathname}?novel=${this.currentNovel.id}&chapter=${this.currentChapter + 1}`;
        window.history.replaceState({}, '', newUrl);
    }
}

// 初始化阅读器
document.addEventListener('DOMContentLoaded', () => {
    window.reader = new NovelReader();
});
