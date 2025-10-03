/**
 * AVICAST Modern User Management System
 * Dynamic UI/UX Enhancements
 */

class AVICASTModernSystem {
    constructor() {
        this.sidebarVisible = true;
        this.init();
    }

    init() {
        document.addEventListener('DOMContentLoaded', () => {
            this.initSidebarToggle();
            this.forceDashboardStyles();
            this.enhanceAnimations();
            this.enhanceInteractions();
            this.enhanceForms();
            this.enhanceNavigation();
            this.addProgressIndicators();
            this.addTooltips();
            this.initResponsiveLayout();
            console.log('🚀 AVICAST Modern System initialized');
            console.log('🔍 Debug Info:');
            console.log('- Sidebar:', document.getElementById('nav-sidebar') ? 'Found' : 'Not Found');
            console.log('- Content:', document.getElementById('content') ? 'Found' : 'Not Found');
            console.log('- Hamburger Button:', document.getElementById('header-hamburger') ? 'Found' : 'Not Found');
            console.log('- Header:', document.getElementById('header') ? 'Found' : 'Not Found');
            console.log('- User Tools:', document.getElementById('user-tools') ? 'Found' : 'Not Found');
        });
    }

    initSidebarToggle() {
        const sidebar = document.getElementById('nav-sidebar');
        const content = document.getElementById('content');
        const hamburgerButton = document.getElementById('header-hamburger');

        if (!sidebar || !content) {
            console.log('Sidebar or content not found');
            return;
        }

        console.log('Found sidebar and content:', sidebar, content);
        console.log('Found hamburger button:', hamburgerButton);

        // Set initial state
        this.updateSidebarState(sidebar, content);

        // Listen for hamburger button clicks
        if (hamburgerButton) {
            console.log('Adding click listener to hamburger button');
            hamburgerButton.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation();
                console.log('Hamburger button clicked, toggling sidebar');
                this.toggleSidebar(sidebar, content);
            });
        } else {
            console.log('Hamburger button not found');
        }

        // Handle responsive behavior
        this.handleResponsiveToggle();

        // Mark hamburger button as initialized
        if (hamburgerButton) {
            hamburgerButton.setAttribute('data-initialized', 'true');
            console.log('Hamburger button initialized successfully');
        }
    }

    toggleSidebar(sidebar, content) {
        this.sidebarVisible = !this.sidebarVisible;
        this.updateSidebarState(sidebar, content);
        
        // Store preference
        localStorage.setItem('avicast-sidebar-visible', this.sidebarVisible.toString());
    }

    updateSidebarState(sidebar, content) {
        console.log('Updating sidebar state to:', this.sidebarVisible ? 'visible' : 'hidden');

        if (this.sidebarVisible) {
            sidebar.setAttribute('data-hidden', 'false');
            sidebar.style.display = 'block';
            sidebar.style.visibility = 'visible';
            content.setAttribute('data-sidebar-hidden', 'false');
            console.log('Sidebar set to visible');
        } else {
            sidebar.setAttribute('data-hidden', 'true');
            sidebar.style.display = 'none';
            sidebar.style.visibility = 'hidden';
            content.setAttribute('data-sidebar-hidden', 'true');
            console.log('Sidebar set to hidden');
        }

        // Force layout recalculation
        sidebar.offsetHeight;
        content.offsetHeight;
    }

    handleResponsiveToggle() {
        const mediaQuery = window.matchMedia('(max-width: 768px)');
        
        const handleMediaChange = (e) => {
            const sidebar = document.getElementById('nav-sidebar');
            const content = document.getElementById('content');
            
            if (e.matches) {
                // Mobile: Hide sidebar by default
                this.sidebarVisible = false;
                this.updateSidebarState(sidebar, content);
            } else {
                // Desktop: Restore saved preference or show by default
                const savedState = localStorage.getItem('avicast-sidebar-visible');
                this.sidebarVisible = savedState !== null ? savedState === 'true' : true;
                this.updateSidebarState(sidebar, content);
            }
        };

        mediaQuery.addListener(handleMediaChange);
        handleMediaChange(mediaQuery);
    }

    initResponsiveLayout() {
        // Add viewport meta tag if not present
        if (!document.querySelector('meta[name="viewport"]')) {
            const viewportMeta = document.createElement('meta');
            viewportMeta.name = 'viewport';
            viewportMeta.content = 'width=device-width, initial-scale=1.0';
            document.head.appendChild(viewportMeta);
        }

        // Add overflow hidden to body and html to prevent horizontal scroll
        document.documentElement.style.overflowX = 'hidden';
        document.body.style.overflowX = 'hidden';
    }

    forceDashboardStyles() {
        // Force apply modern styles to dashboard cards
        const modules = document.querySelectorAll('.module');
        modules.forEach(module => {
            module.style.cssText = `
                background: linear-gradient(145deg, #ffffff 0%, #f8fafc 100%) !important;
                border-radius: 16px !important;
                box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08), 0 3px 10px rgba(0, 0, 0, 0.05) !important;
                border: 1px solid rgba(226, 232, 240, 0.8) !important;
                overflow: hidden !important;
                transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
                position: relative !important;
                max-width: none !important;
                min-width: 280px !important;
                width: auto !important;
                height: auto !important;
            `;
        });

        // Force apply styles to headers
        const moduleHeaders = document.querySelectorAll('.module h3');
        moduleHeaders.forEach(header => {
            header.style.cssText = `
                background: linear-gradient(135deg, #1e40af 0%, #3b82f6 50%, #1e3a8a 100%) !important;
                color: white !important;
                padding: 1.25rem 1.5rem !important;
                margin: 0 !important;
                font-size: 1.125rem !important;
                font-weight: 700 !important;
                letter-spacing: 0.025em !important;
                position: relative !important;
                display: flex !important;
                align-items: center !important;
                gap: 0.75rem !important;
                text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1) !important;
            `;
        });

        // Force apply styles to action buttons - 20% smaller
        const actionButtons = document.querySelectorAll('.actions-cell .addlink, .actions-cell .changelink');
        actionButtons.forEach(button => {
            button.style.cssText = `
                background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%) !important;
                color: white !important;
                border: none !important;
                border-radius: 6px !important;
                padding: 0.4rem 0.8rem !important;
                font-weight: 600 !important;
                font-size: 0.64rem !important;
                text-decoration: none !important;
                display: inline-flex !important;
                align-items: center !important;
                justify-content: center !important;
                gap: 0.2rem !important;
                transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
                box-shadow: 0 1.5px 3px rgba(30, 64, 175, 0.2) !important;
                margin: 0.125rem !important;
                min-width: 64px !important;
                max-width: 80px !important;
                text-transform: uppercase !important;
                letter-spacing: 0.04em !important;
                width: auto !important;
                height: auto !important;
                position: relative !important;
                flex-shrink: 0 !important;
            `;
        });

        // Make Add buttons green - 20% smaller
        const addButtons = document.querySelectorAll('.actions-cell .addlink');
        addButtons.forEach(button => {
            button.style.background = 'linear-gradient(135deg, #059669 0%, #10b981 100%) !important';
            button.style.boxShadow = '0 1.5px 3px rgba(5, 150, 105, 0.2) !important';
        });

        console.log('🎨 Dashboard styles forced applied');
    }

    enhanceAnimations() {
        // Professional, subtle animations only
        const dashboardCards = document.querySelectorAll('.module, .stat-item');
        dashboardCards.forEach((card, index) => {
            card.style.animationDelay = `${index * 50}ms`;
            card.classList.add('professional-fade-in');
        });

        // Minimal, professional transitions
        const interactiveElements = document.querySelectorAll('button, a, .module, .stat-item');
        interactiveElements.forEach(element => {
            element.style.transition = 'all 0.2s ease';
        });
    }

    enhanceInteractions() {
        // Enhanced table row interactions
        const tableRows = document.querySelectorAll('.results tbody tr');
        tableRows.forEach(row => {
            row.addEventListener('mouseenter', () => {
                row.style.transform = 'translateX(4px) scale(1.002)';
                row.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.1)';
            });

            row.addEventListener('mouseleave', () => {
                row.style.transform = 'translateX(0) scale(1)';
                row.style.boxShadow = 'none';
            });
        });

        // Button hover enhancements
        const buttons = document.querySelectorAll('.button, .default, input[type="submit"]');
        buttons.forEach(button => {
            button.addEventListener('mouseenter', () => {
                button.style.transform = 'translateY(-2px)';
            });

            button.addEventListener('mouseleave', () => {
                button.style.transform = 'translateY(0)';
            });

            button.addEventListener('mousedown', () => {
                button.style.transform = 'translateY(0) scale(0.98)';
            });

            button.addEventListener('mouseup', () => {
                button.style.transform = 'translateY(-2px) scale(1)';
            });
        });

        // Card hover effects
        const cards = document.querySelectorAll('.module');
        cards.forEach(card => {
            card.addEventListener('mouseenter', () => {
                card.style.transform = 'translateY(-4px)';
                card.style.boxShadow = '0 12px 24px rgba(0, 0, 0, 0.15)';
            });

            card.addEventListener('mouseleave', () => {
                card.style.transform = 'translateY(0)';
                card.style.boxShadow = '0 1px 3px rgba(0, 0, 0, 0.1)';
            });
        });
    }

    enhanceForms() {
        // Form validation enhancements
        const inputs = document.querySelectorAll('input, select, textarea');
        inputs.forEach(input => {
            // Add floating label effect
            if (input.type !== 'hidden' && input.type !== 'submit') {
                this.addFloatingLabel(input);
            }

            // Add validation styling
            input.addEventListener('blur', () => {
                this.validateField(input);
            });

            input.addEventListener('input', () => {
                this.clearValidationState(input);
            });
        });

        // Form submission with loading state
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', (e) => {
                this.addLoadingState(form);
            });
        });
    }

    addFloatingLabel(input) {
        const wrapper = document.createElement('div');
        wrapper.className = 'avic-input-wrapper';
        wrapper.style.position = 'relative';
        
        const label = input.previousElementSibling;
        if (label && label.tagName === 'LABEL') {
            label.style.position = 'absolute';
            label.style.top = input.value ? '0' : '50%';
            label.style.left = '12px';
            label.style.transform = input.value ? 'translateY(-50%) scale(0.85)' : 'translateY(-50%)';
            label.style.transition = 'all 0.2s ease';
            label.style.pointerEvents = 'none';
            label.style.color = '#64748b';
            label.style.backgroundColor = '#ffffff';
            label.style.padding = '0 4px';
            label.style.zIndex = '1';

            input.addEventListener('focus', () => {
                label.style.top = '0';
                label.style.transform = 'translateY(-50%) scale(0.85)';
                label.style.color = '#1e40af';
            });

            input.addEventListener('blur', () => {
                if (!input.value) {
                    label.style.top = '50%';
                    label.style.transform = 'translateY(-50%)';
                    label.style.color = '#64748b';
                }
            });
        }
    }

    validateField(input) {
        const isValid = input.checkValidity();
        
        if (!isValid) {
            input.style.borderColor = '#dc2626';
            input.style.boxShadow = '0 0 0 3px rgba(220, 38, 38, 0.1)';
        } else {
            input.style.borderColor = '#059669';
            input.style.boxShadow = '0 0 0 3px rgba(5, 150, 105, 0.1)';
        }
    }

    clearValidationState(input) {
        input.style.borderColor = '#e2e8f0';
        input.style.boxShadow = 'none';
    }

    addLoadingState(form) {
        form.classList.add('loading');
        
        const submitButton = form.querySelector('input[type="submit"], .button, .default');
        if (submitButton) {
            const originalText = submitButton.textContent || submitButton.value;
            
            if (submitButton.tagName === 'INPUT') {
                submitButton.value = 'Processing...';
            } else {
                submitButton.textContent = 'Processing...';
            }
            
            submitButton.disabled = true;
            submitButton.style.opacity = '0.7';
            
            // Add spinner
            const spinner = document.createElement('span');
            spinner.innerHTML = '⏳';
            spinner.style.marginRight = '8px';
            submitButton.prepend(spinner);
        }
    }

    enhanceNavigation() {
        // Smooth scroll for internal links
        const internalLinks = document.querySelectorAll('a[href^="#"]');
        internalLinks.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(link.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({
                        behavior: 'smooth',
                        block: 'start'
                    });
                }
            });
        });

        // Active navigation highlighting
        const navLinks = document.querySelectorAll('#nav-sidebar a');
        const currentPath = window.location.pathname;
        
        navLinks.forEach(link => {
            if (link.getAttribute('href') === currentPath) {
                link.style.backgroundColor = '#1e40af';
                link.style.color = 'white';
                link.style.borderLeftColor = '#ffffff';
            }
        });
    }

    addProgressIndicators() {
        // Add progress bars for long operations
        const progressBar = document.createElement('div');
        progressBar.id = 'avic-progress-bar';
        progressBar.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 0%;
            height: 3px;
            background: linear-gradient(90deg, #1e40af, #1e3a8a);
            transition: width 0.3s ease;
            z-index: 9999;
            display: none;
        `;
        document.body.appendChild(progressBar);

        // Show progress on form submissions
        const forms = document.querySelectorAll('form');
        forms.forEach(form => {
            form.addEventListener('submit', () => {
                this.showProgress();
            });
        });
    }

    showProgress() {
        const progressBar = document.getElementById('avic-progress-bar');
        progressBar.style.display = 'block';
        
        let progress = 0;
        const interval = setInterval(() => {
            progress += Math.random() * 15;
            if (progress > 90) progress = 90;
            
            progressBar.style.width = progress + '%';
            
            if (progress >= 90) {
                clearInterval(interval);
            }
        }, 200);

        // Complete on page unload
        window.addEventListener('beforeunload', () => {
            progressBar.style.width = '100%';
            setTimeout(() => {
                progressBar.style.display = 'none';
                progressBar.style.width = '0%';
            }, 300);
        });
    }

    addTooltips() {
        // Add tooltips to action buttons
        const actionButtons = document.querySelectorAll('.addlink, .changelink, .deletelink');
        actionButtons.forEach(button => {
            const tooltip = document.createElement('div');
            tooltip.className = 'avic-tooltip';
            tooltip.textContent = button.textContent.trim();
            tooltip.style.cssText = `
                position: absolute;
                background: #1e293b;
                color: white;
                padding: 0.5rem 0.75rem;
                border-radius: 0.375rem;
                font-size: 0.75rem;
                font-weight: 500;
                opacity: 0;
                pointer-events: none;
                transition: opacity 0.2s ease;
                z-index: 1000;
                white-space: nowrap;
                transform: translateY(-100%);
                margin-top: -0.5rem;
            `;

            button.style.position = 'relative';
            button.appendChild(tooltip);

            button.addEventListener('mouseenter', () => {
                tooltip.style.opacity = '1';
            });

            button.addEventListener('mouseleave', () => {
                tooltip.style.opacity = '0';
            });
        });
    }

    // Public method to refresh enhancements (useful for AJAX content)
    refresh() {
        this.enhanceInteractions();
        this.enhanceForms();
        this.addTooltips();
    }
}

// Initialize the modern system
window.AVICASTModern = new AVICASTModernSystem();

// Make refresh method globally available
window.refreshAVICASTEnhancements = () => {
    window.AVICASTModern.refresh();
};
