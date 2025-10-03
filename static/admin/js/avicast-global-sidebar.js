// AVICAST Global Sidebar Navigation System
document.addEventListener('DOMContentLoaded', function() {
    console.log('🏛️ AVICAST Global Sidebar System Initializing...');
    console.log('🔍 Body classes:', document.body.className);
    console.log('🔍 Has admin-interface class:', document.body.classList.contains('admin-interface'));
    
    // Only run on admin pages
    if (!document.body.classList.contains('admin-interface')) {
        console.log('❌ Not an admin page, skipping sidebar initialization');
        return;
    }
    
    console.log('✅ Admin page detected, proceeding with sidebar initialization');
    
    initGlobalSidebar();
    
    function initGlobalSidebar() {
        const header = document.getElementById('header');
        const userTools = document.getElementById('user-tools');
        const content = document.getElementById('content');
        
        console.log('🔍 Global element detection:', {
            header: !!header,
            userTools: !!userTools,
            content: !!content
        });
        
        if (!header || !userTools || !content) {
            console.warn('Required elements not found');
            return;
        }
        
        // Create professional hamburger button if it doesn't exist
        let navToggle = document.getElementById('nav-toggle');
        if (!navToggle) {
            navToggle = document.createElement('button');
            navToggle.id = 'nav-toggle';
            navToggle.className = 'nav-toggle-btn';
            navToggle.innerHTML = '<span class="nav-toggle-icon"></span>';
            navToggle.setAttribute('aria-label', 'Toggle navigation menu');
            navToggle.setAttribute('aria-expanded', 'true');
            
            // Add to header at the end (after logout button)
            userTools.appendChild(navToggle);
            console.log('✅ Created global navigation toggle');
        }
        
        // Wire our hamburger to Django's original toggle button
        const originalToggle = document.getElementById('toggle-nav-sidebar');
        if (originalToggle) {
            // Wire click-through
            navToggle.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                originalToggle.click();
            });
            console.log('🔗 Wired custom hamburger to original #toggle-nav-sidebar');

            // Ensure sidebar defaults to open on load
            const expanded = originalToggle.getAttribute('aria-expanded');
            if (expanded === 'false') {
                originalToggle.click();
                console.log('⬅️ Ensured sidebar opens on load via original toggle');
            }
        } else {
            console.warn('⚠️ Original #toggle-nav-sidebar not found — enabling fallback toggler');
            // Fallback: toggle visibility directly
            const contentEl = document.getElementById('content');
            let sidebar = document.getElementById('nav-sidebar');
            let isOpen = true;
            function applyState() {
                sidebar = document.getElementById('nav-sidebar');
                if (!sidebar) return;
                if (isOpen) {
                    sidebar.style.transform = 'translateX(0)';
                    sidebar.style.display = 'block';
                    sidebar.style.visibility = 'visible';
                    if (contentEl) {
                        contentEl.setAttribute('data-nav', 'open');
                        contentEl.setAttribute('data-sidebar-hidden', 'false');
                    }
                } else {
                    sidebar.style.transform = 'translateX(-100%)';
                    if (contentEl) {
                        contentEl.setAttribute('data-nav', 'closed');
                        contentEl.setAttribute('data-sidebar-hidden', 'true');
                    }
                }
            }
            navToggle.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                isOpen = !isOpen;
                applyState();
                console.log('🔁 Fallback sidebar toggled:', isOpen ? 'open' : 'closed');
            });
            // Apply initial state
            applyState();
        }

        // Initialize sidebar bindings (no DOM creation)
        initSidebar(navToggle, content);
        
        // Debug: Check if sidebar exists and has content
        setTimeout(() => {
            const sidebar = document.getElementById('nav-sidebar');
            console.log('🔍 Sidebar debug:', {
                exists: !!sidebar,
                innerHTML_length: sidebar ? sidebar.innerHTML.length : 0,
                style_display: sidebar ? sidebar.style.display : 'N/A',
                style_visibility: sidebar ? sidebar.style.visibility : 'N/A',
                style_transform: sidebar ? sidebar.style.transform : 'N/A',
                data_state: sidebar ? sidebar.getAttribute('data-state') : 'N/A',
                data_hidden: sidebar ? sidebar.getAttribute('data-hidden') : 'N/A',
                computed_display: sidebar ? getComputedStyle(sidebar).display : 'N/A',
                computed_position: sidebar ? getComputedStyle(sidebar).position : 'N/A',
                computed_z_index: sidebar ? getComputedStyle(sidebar).zIndex : 'N/A',
                computed_top: sidebar ? getComputedStyle(sidebar).top : 'N/A',
                computed_left: sidebar ? getComputedStyle(sidebar).left : 'N/A',
                computed_width: sidebar ? getComputedStyle(sidebar).width : 'N/A',
                computed_height: sidebar ? getComputedStyle(sidebar).height : 'N/A'
            });
            // Do not forcibly override Django's sidebar CSS here
        }, 1000);
    }
    
    function initSidebar(button, content) {
        // Bind to existing Django sidebar only; never create our own
        let sidebar = document.getElementById('nav-sidebar');
        if (!sidebar) {
            console.warn('⚠️ #nav-sidebar not found; skipping init to avoid duplicates');
            return;
        }
        
        // Prefer our own persisted state; fall back to Django's attribute
        const originalToggle = document.getElementById('toggle-nav-sidebar');
        let isOpen;
        const persisted = localStorage.getItem('avicast-nav-state');
        if (persisted === 'open' || persisted === 'closed') {
            isOpen = persisted === 'open';
        } else if (originalToggle) {
            const expanded = originalToggle.getAttribute('aria-expanded');
            isOpen = expanded === null ? true : expanded === 'true';
        } else {
            isOpen = true;
        }
        
        // Update sidebar state
        function updateSidebarState() {
            // Apply CSS/state regardless of Django JS presence
            sidebar.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
            button.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
            button.classList.toggle('closed', !isOpen);
            document.body.classList.toggle('avicast-sidebar-open', isOpen);
            document.body.classList.toggle('avicast-sidebar-closed', !isOpen);
            if (content) {
                content.setAttribute('data-nav', isOpen ? 'open' : 'closed');
                content.setAttribute('data-sidebar-hidden', isOpen ? 'false' : 'true');
            }
            localStorage.setItem('avicast-nav-state', isOpen ? 'open' : 'closed');
            // Best-effort sync with Django if available
            if (originalToggle) {
                const expanded = originalToggle.getAttribute('aria-expanded');
                const expandedBool = expanded === 'true';
                if (expandedBool !== isOpen) {
                    originalToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
                }
            }
            console.log('🔄 Sidebar state applied (isOpen):', isOpen);
        }
        
        // Apply initial state and observe changes from Django's script (if present)
        updateSidebarState();
        if (originalToggle) {
            const observer = new MutationObserver(() => {
                const expanded = originalToggle.getAttribute('aria-expanded');
                const expandedBool = expanded === 'true';
                if (expandedBool !== isOpen) {
                    isOpen = expandedBool;
                    updateSidebarState();
                }
            });
            observer.observe(originalToggle, { attributes: true, attributeFilter: ['aria-expanded'] });
        }
        
        console.log('✅ GLOBAL sidebar toggle initialized');
    }
    
    console.log('✅ AVICAST Global Sidebar System Ready');
});
