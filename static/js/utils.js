// Utility functions for MeTruyenCV Downloader Web Interface

// Connection status management
class ConnectionManager {
    constructor() {
        this.isConnected = false;
        this.statusElement = null;
        this.init();
    }
    
    init() {
        // Create connection status indicator
        this.statusElement = document.createElement('div');
        this.statusElement.className = 'connection-status disconnected';
        this.statusElement.innerHTML = '<i class="bi bi-wifi-off me-1"></i>Disconnected';
        document.body.appendChild(this.statusElement);
        
        // Hide after 3 seconds initially
        setTimeout(() => {
            if (!this.isConnected) {
                this.statusElement.style.display = 'none';
            }
        }, 3000);
    }
    
    setConnected(connected) {
        this.isConnected = connected;
        this.statusElement.style.display = 'block';
        
        if (connected) {
            this.statusElement.className = 'connection-status connected';
            this.statusElement.innerHTML = '<i class="bi bi-wifi me-1"></i>Connected';
            
            // Hide after 2 seconds
            setTimeout(() => {
                this.statusElement.style.display = 'none';
            }, 2000);
        } else {
            this.statusElement.className = 'connection-status disconnected';
            this.statusElement.innerHTML = '<i class="bi bi-wifi-off me-1"></i>Disconnected';
        }
    }
}

// Progress tracking utilities
class ProgressTracker {
    constructor() {
        this.startTime = null;
        this.currentChapter = 0;
        this.totalChapters = 0;
        this.completedChapters = 0;
    }
    
    start(totalChapters) {
        this.startTime = new Date();
        this.totalChapters = totalChapters;
        this.currentChapter = 0;
        this.completedChapters = 0;
    }
    
    updateProgress(currentChapter, totalChapters) {
        this.currentChapter = currentChapter;
        this.totalChapters = totalChapters;
        this.completedChapters = currentChapter;
    }
    
    getElapsedTime() {
        if (!this.startTime) return 0;
        return Math.floor((new Date() - this.startTime) / 1000);
    }
    
    getEstimatedTimeRemaining() {
        if (!this.startTime || this.completedChapters === 0) return null;
        
        const elapsed = this.getElapsedTime();
        const avgTimePerChapter = elapsed / this.completedChapters;
        const remainingChapters = this.totalChapters - this.completedChapters;
        
        return Math.floor(avgTimePerChapter * remainingChapters);
    }
    
    getSpeed() {
        if (!this.startTime || this.completedChapters === 0) return 0;
        
        const elapsed = this.getElapsedTime();
        return (this.completedChapters / (elapsed / 60)).toFixed(1); // chapters per minute
    }
    
    getProgressPercentage() {
        if (this.totalChapters === 0) return 0;
        return Math.floor((this.completedChapters / this.totalChapters) * 100);
    }
}

// Local storage utilities
class StorageManager {
    static set(key, value) {
        try {
            localStorage.setItem(`metruyencv_${key}`, JSON.stringify(value));
        } catch (e) {
            console.warn('Failed to save to localStorage:', e);
        }
    }
    
    static get(key, defaultValue = null) {
        try {
            const item = localStorage.getItem(`metruyencv_${key}`);
            return item ? JSON.parse(item) : defaultValue;
        } catch (e) {
            console.warn('Failed to read from localStorage:', e);
            return defaultValue;
        }
    }
    
    static remove(key) {
        try {
            localStorage.removeItem(`metruyencv_${key}`);
        } catch (e) {
            console.warn('Failed to remove from localStorage:', e);
        }
    }
    
    static clear() {
        try {
            const keys = Object.keys(localStorage).filter(key => key.startsWith('metruyencv_'));
            keys.forEach(key => localStorage.removeItem(key));
        } catch (e) {
            console.warn('Failed to clear localStorage:', e);
        }
    }
}

// URL validation utilities
class URLValidator {
    static isValidMeTruyenCVUrl(url) {
        const validDomains = ['metruyencv.biz', 'metruyencv.com', 'metruyencv.info'];
        try {
            const urlObj = new URL(url);
            return validDomains.some(domain => urlObj.hostname.includes(domain)) &&
                   urlObj.pathname.includes('/truyen/');
        } catch (e) {
            return false;
        }
    }
    
    static extractNovelName(url) {
        try {
            const urlObj = new URL(url);
            const pathParts = urlObj.pathname.split('/');
            const novelPart = pathParts.find(part => part && part !== 'truyen');
            return novelPart ? novelPart.replace(/-/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : '';
        } catch (e) {
            return '';
        }
    }
    
    static normalizeDomain(url) {
        // Convert any metruyencv domain to .biz (primary domain)
        return url.replace(/(metruyencv)\.(com|info)/g, '$1.biz');
    }
}

// Form utilities
class FormUtils {
    static validateChapterRange(startChapter, endChapter) {
        const start = parseInt(startChapter);
        const end = parseInt(endChapter);
        
        if (isNaN(start) || isNaN(end)) {
            return { valid: false, message: 'Chapter numbers must be valid integers' };
        }
        
        if (start < 1) {
            return { valid: false, message: 'Start chapter must be at least 1' };
        }
        
        if (end < start) {
            return { valid: false, message: 'End chapter must be greater than or equal to start chapter' };
        }
        
        if (end - start > 1000) {
            return { valid: false, message: 'Chapter range too large (max 1000 chapters)' };
        }
        
        return { valid: true };
    }
    
    static sanitizeInput(input) {
        return input.trim().replace(/[<>]/g, '');
    }
    
    static formatFileSize(bytes) {
        if (bytes === 0) return '0 Bytes';
        
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
    }
}

// Animation utilities
class AnimationUtils {
    static fadeIn(element, duration = 300) {
        element.style.opacity = '0';
        element.style.display = 'block';
        
        let start = null;
        function animate(timestamp) {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            
            element.style.opacity = Math.min(progress / duration, 1);
            
            if (progress < duration) {
                requestAnimationFrame(animate);
            }
        }
        
        requestAnimationFrame(animate);
    }
    
    static fadeOut(element, duration = 300) {
        let start = null;
        function animate(timestamp) {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            
            element.style.opacity = Math.max(1 - (progress / duration), 0);
            
            if (progress < duration) {
                requestAnimationFrame(animate);
            } else {
                element.style.display = 'none';
            }
        }
        
        requestAnimationFrame(animate);
    }
    
    static slideDown(element, duration = 300) {
        element.style.height = '0px';
        element.style.overflow = 'hidden';
        element.style.display = 'block';
        
        const targetHeight = element.scrollHeight;
        let start = null;
        
        function animate(timestamp) {
            if (!start) start = timestamp;
            const progress = timestamp - start;
            
            element.style.height = Math.min((progress / duration) * targetHeight, targetHeight) + 'px';
            
            if (progress < duration) {
                requestAnimationFrame(animate);
            } else {
                element.style.height = '';
                element.style.overflow = '';
            }
        }
        
        requestAnimationFrame(animate);
    }
    
    static pulse(element, duration = 1000) {
        element.style.animation = `pulse ${duration}ms infinite`;
        
        setTimeout(() => {
            element.style.animation = '';
        }, duration * 3);
    }
}

// Notification utilities
class NotificationManager {
    static requestPermission() {
        if ('Notification' in window && Notification.permission === 'default') {
            Notification.requestPermission();
        }
    }
    
    static show(title, options = {}) {
        if ('Notification' in window && Notification.permission === 'granted') {
            const notification = new Notification(title, {
                icon: '/static/img/icon.png',
                badge: '/static/img/badge.png',
                ...options
            });
            
            // Auto close after 5 seconds
            setTimeout(() => notification.close(), 5000);
            
            return notification;
        }
    }
    
    static showDownloadComplete(novelName, chaptersCount) {
        this.show('Download Complete!', {
            body: `${novelName} - ${chaptersCount} chapters downloaded`,
            tag: 'download-complete'
        });
    }
    
    static showDownloadError(error) {
        this.show('Download Error', {
            body: error,
            tag: 'download-error'
        });
    }
}

// Export utilities for global use
window.ConnectionManager = ConnectionManager;
window.ProgressTracker = ProgressTracker;
window.StorageManager = StorageManager;
window.URLValidator = URLValidator;
window.FormUtils = FormUtils;
window.AnimationUtils = AnimationUtils;
window.NotificationManager = NotificationManager;

// Initialize global instances
window.connectionManager = new ConnectionManager();
window.progressTracker = new ProgressTracker();

// Request notification permission on load
document.addEventListener('DOMContentLoaded', function() {
    NotificationManager.requestPermission();
});
