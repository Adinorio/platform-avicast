/**
 * AVICAST Admin Interface JavaScript
 * Handles navigation toggle and button text visibility fixes
 */

class AvicAdminInterface {
    constructor() {
        this.sidebar = null;
        this.content = null;
        this.header = null;
        
        this.init();
    }
    
    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.initElements();
            this.fixButtonTextVisibility();
            this.initSearchFilter();
        });
    }
    
    initElements() {
        this.sidebar = document.getElementById('nav-sidebar');
        this.content = document.getElementById('content');
        this.header = document.getElementById('header');
        
        // Hide original toggle button if it exists
        const originalToggleButton = document.getElementById('toggle-nav-sidebar');
        if (originalToggleButton) {
            originalToggleButton.style.display = 'none';
        }
    }
    
    fixButtonTextVisibility() {
        const buttonSelectors = [
            '.addlink',
            '.deletelink', 
            '.changelink',
            '.viewlink',
            '.historylink',
            '.button',
            '.default',
            'button',
            'input[type="submit"]'
        ];
        
        buttonSelectors.forEach(selector => {
            const buttons = document.querySelectorAll(selector);
            buttons.forEach(button => {
                this.applyButtonFixes(button);
            });
        });
    }
    
    applyButtonFixes(button) {
        // Ensure text is visible
        button.style.color = '#ffffff';
        button.style.setProperty('color', '#ffffff', 'important');
        
        // Fix child elements
        const children = button.querySelectorAll('*');
        children.forEach(child => {
            child.style.color = '#ffffff';
            child.style.setProperty('color', '#ffffff', 'important');
        });
        
        // Ensure proper text properties
        button.style.textIndent = '0';
        button.style.visibility = 'visible';
        button.style.opacity = '1';
        
        // Mark as fixed
        button.setAttribute('data-avic-fixed', 'true');
    }
    
    initSearchFilter() {
        const searchInput = document.getElementById('sidebar-quick-filter');
        if (!searchInput) return;
        
        searchInput.addEventListener('input', (e) => {
            this.filterNavigation(e.target.value);
        });
    }
    
    filterNavigation(searchTerm) {
        const modules = document.querySelectorAll('#nav-sidebar .module');
        const term = searchTerm.toLowerCase();
        
        modules.forEach(module => {
            const links = module.querySelectorAll('a');
            let hasVisibleLinks = false;
            
            links.forEach(link => {
                const text = link.textContent.toLowerCase();
                const shouldShow = text.includes(term);
                
                link.style.display = shouldShow ? 'block' : 'none';
                if (shouldShow) hasVisibleLinks = true;
            });
            
            // Show/hide entire module based on whether it has visible links
            module.style.display = hasVisibleLinks || term === '' ? 'block' : 'none';
        });
    }
}

// Initialize the admin interface
new AvicAdminInterface();
