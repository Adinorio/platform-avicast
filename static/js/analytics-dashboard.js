/**
 * AVICAST Analytics Dashboard - Chart Loading System
 * 
 * Features:
 * - Lazy loading with Intersection Observer
 * - Loading states (skeleton loaders)
 * - Error handling with retry
 * - Chart expansion modal
 * - Download functionality
 * - Performance optimized
 * 
 * Reference: docs/TECHNICAL_AUDIT_REPORT.md - Chart Loading UX
 */

class AnalyticsChartLoader {
  constructor() {
    this.charts = new Map();
    this.observers = new Map();
    this.init();
  }
  
  init() {
    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', () => this.setup());
    } else {
      this.setup();
    }
  }
  
  setup() {
    // Load non-lazy charts immediately
    this.loadImmediateCharts();
    
    // Setup Intersection Observer for lazy loading
    this.setupLazyLoading();
    
    // Setup chart expansion handlers
    this.setupExpansionHandlers();
    
    // Setup download handlers
    this.setupDownloadHandlers();
    
    // Initialize Bootstrap tooltips
    this.initTooltips();
  }
  
  /**
   * Load charts that should appear immediately (not lazy)
   */
  loadImmediateCharts() {
    const immediateCharts = document.querySelectorAll('.chart-container:not([data-lazy-load])');
    immediateCharts.forEach(container => {
      const chartId = container.getAttribute('data-chart-id');
      const endpoint = container.getAttribute('data-endpoint');
      if (chartId && endpoint) {
        this.loadChart(chartId, endpoint, container);
      }
    });
  }
  
  /**
   * Setup Intersection Observer for lazy loading charts when they become visible
   */
  setupLazyLoading() {
    const lazyCharts = document.querySelectorAll('.chart-container[data-lazy-load]');
    
    if (lazyCharts.length === 0) return;
    
    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const container = entry.target;
          const chartId = container.getAttribute('data-chart-id');
          const endpoint = container.getAttribute('data-endpoint');
          
          if (chartId && endpoint) {
            // Load chart when it becomes visible
            this.loadChart(chartId, endpoint, container);
            
            // Stop observing after load
            observer.unobserve(container);
          }
        }
      });
    }, {
      rootMargin: '50px', // Load 50px before entering viewport
      threshold: 0.1
    });
    
    lazyCharts.forEach(chart => observer.observe(chart));
  }
  
  /**
   * Load chart data and render
   */
  async loadChart(chartId, endpoint, container) {
    const loadingEl = container.querySelector('.chart-container__loading');
    const chartEl = container.querySelector('.chart-container__chart');
    const emptyEl = container.querySelector('.chart-container__empty');
    const errorEl = container.querySelector('.chart-container__error');
    
    try {
      // Show loading state
      this.showElement(loadingEl);
      this.hideElement(chartEl);
      this.hideElement(emptyEl);
      this.hideElement(errorEl);
      
      // Fetch chart data
      const response = await fetch(endpoint);
      
      if (!response.ok) {
        throw new Error(`HTTP error ${response.status}`);
      }
      
      const data = await response.json();
      
      // Check if data exists
      if (!data.chart || data.chart === 'null' || data.chart === null) {
        this.showEmptyState(loadingEl, emptyEl);
        return;
      }
      
      // Parse and render chart
      const chartData = JSON.parse(data.chart);
      
      await this.renderChart(chartId, chartData, chartEl);
      
      // Hide loading, show chart
      this.hideElement(loadingEl);
      this.showElement(chartEl);
      
      // Store chart reference
      this.charts.set(chartId, chartEl);
      
    } catch (error) {
      console.error(`Failed to load chart ${chartId}:`, error);
      this.showErrorState(loadingEl, errorEl, chartId, endpoint, container);
    }
  }
  
  /**
   * Render Plotly chart with optimal configuration
   */
  async renderChart(chartId, chartData, chartEl) {
    // Plotly configuration for better UX
    const config = {
      responsive: true,
      displayModeBar: true,
      modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d', 'autoScale2d'],
      displaylogo: false,
      toImageButtonOptions: {
        format: 'png',
        filename: `avicast_${chartId}_${new Date().toISOString().split('T')[0]}`,
        height: 1000,
        width: 1600,
        scale: 2
      }
    };
    
    // Layout improvements for accessibility and consistency
    const layout = {
      ...chartData.layout,
      font: {
        family: 'Inter, -apple-system, BlinkMacSystemFont, sans-serif',
        size: 14,
        color: '#495057'
      },
      paper_bgcolor: '#ffffff',
      plot_bgcolor: '#f8f9fa',
      margin: { t: 40, r: 20, b: 60, l: 60 },
      autosize: true,
      modebar: {
        bgcolor: 'rgba(255,255,255,0.9)',
        color: '#495057',
        activecolor: '#0d6efd'
      }
    };
    
    // Render chart
    await Plotly.newPlot(
      chartEl,
      chartData.data,
      layout,
      config
    );
    
    // Add accessibility attributes
    chartEl.setAttribute('role', 'img');
    chartEl.setAttribute('tabindex', '0');
  }
  
  /**
   * Show empty state when no data available
   */
  showEmptyState(loadingEl, emptyEl) {
    this.hideElement(loadingEl);
    this.showElement(emptyEl);
  }
  
  /**
   * Show error state with retry button
   */
  showErrorState(loadingEl, errorEl, chartId, endpoint, container) {
    this.hideElement(loadingEl);
    this.showElement(errorEl);
    
    // Find and setup retry button
    const retryBtn = errorEl.querySelector('button');
    if (retryBtn) {
      retryBtn.onclick = () => {
        this.loadChart(chartId, endpoint, container);
      };
    }
  }
  
  /**
   * Retry loading a specific chart
   */
  retryChart(chartId) {
    const container = document.querySelector(`[data-chart-id="${chartId}"]`);
    if (container) {
      const endpoint = container.getAttribute('data-endpoint');
      this.loadChart(chartId, endpoint, container);
    }
  }
  
  /**
   * Setup chart expansion handlers
   */
  setupExpansionHandlers() {
    const expandBtns = document.querySelectorAll('.chart-container__expand');
    expandBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const container = e.target.closest('.chart-container');
        this.expandChart(container);
      });
    });
  }
  
  /**
   * Expand chart in modal for better viewing
   */
  expandChart(container) {
    const chartId = container.getAttribute('data-chart-id');
    const titleEl = container.querySelector('.chart-container__title');
    
    if (!titleEl) {
      console.error('Chart container is missing .chart-container__title element');
      return;
    }
    
    const title = titleEl.textContent.trim();
    const chartEl = container.querySelector('.chart-container__chart');
    
    if (!chartEl || !chartEl.data) {
      console.warn('Chart not loaded yet');
      return;
    }
    
    // Create modal
    const modalHTML = `
      <div class="modal fade" id="chartModal-${chartId}" tabindex="-1" aria-labelledby="chartModalLabel" aria-hidden="true">
        <div class="modal-dialog modal-xl modal-fullscreen-lg-down">
          <div class="modal-content">
            <div class="modal-header">
              <h5 class="modal-title" id="chartModalLabel">${title}</h5>
              <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
              <div id="expanded-chart-${chartId}" style="height: 70vh;"></div>
            </div>
            <div class="modal-footer">
              <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
              <button type="button" class="btn btn-primary" onclick="window.analyticsCharts.downloadChart('expanded-chart-${chartId}')">
                <i class="fas fa-download me-2"></i>Download
              </button>
            </div>
          </div>
        </div>
      </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById(`chartModal-${chartId}`);
    if (existingModal) {
      existingModal.remove();
    }
    
    // Add modal to DOM
    document.body.insertAdjacentHTML('beforeend', modalHTML);
    
    // Get modal element
    const modalEl = document.getElementById(`chartModal-${chartId}`);
    const expandedChartEl = document.getElementById(`expanded-chart-${chartId}`);
    
    // Show modal
    const modal = new bootstrap.Modal(modalEl);
    modal.show();
    
    // Clone chart data to expanded view
    modalEl.addEventListener('shown.bs.modal', () => {
      Plotly.newPlot(
        expandedChartEl,
        chartEl.data,
        chartEl.layout,
        {
          responsive: true,
          displayModeBar: true,
          displaylogo: false
        }
      );
    });
    
    // Cleanup on close
    modalEl.addEventListener('hidden.bs.modal', () => {
      modalEl.remove();
    });
  }
  
  /**
   * Setup download handlers for charts
   */
  setupDownloadHandlers() {
    const downloadBtns = document.querySelectorAll('.chart-container__download');
    downloadBtns.forEach(btn => {
      btn.addEventListener('click', (e) => {
        const container = e.target.closest('.chart-container');
        const chartId = container.getAttribute('data-chart-id');
        const chartEl = container.querySelector('.chart-container__chart');
        
        if (chartEl && chartEl.data) {
          this.downloadChart(`chart-${chartId}`);
        }
      });
    });
  }
  
  /**
   * Download chart as PNG image
   */
  downloadChart(elementId) {
    const chartEl = document.getElementById(elementId);
    
    if (!chartEl || !chartEl.data) {
      console.warn('Chart not available for download');
      return;
    }
    
    Plotly.downloadImage(chartEl, {
      format: 'png',
      filename: `avicast_${elementId}_${new Date().toISOString().split('T')[0]}`,
      height: 1000,
      width: 1600,
      scale: 2
    });
  }
  
  /**
   * Initialize Bootstrap tooltips
   */
  initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
      return new bootstrap.Tooltip(tooltipTriggerEl);
    });
  }
  
  /**
   * Utility: Show element
   */
  showElement(el) {
    if (el) {
      el.style.display = '';
      el.removeAttribute('aria-hidden');
    }
  }
  
  /**
   * Utility: Hide element
   */
  hideElement(el) {
    if (el) {
      el.style.display = 'none';
      el.setAttribute('aria-hidden', 'true');
    }
  }
}

// Initialize on DOM ready
window.analyticsCharts = new AnalyticsChartLoader();

// Handle window resize (debounced)
let resizeTimer;
window.addEventListener('resize', () => {
  clearTimeout(resizeTimer);
  resizeTimer = setTimeout(() => {
    // Resize all loaded charts
    window.analyticsCharts.charts.forEach((chartEl, chartId) => {
      if (chartEl && chartEl.data) {
        Plotly.Plots.resize(chartEl);
      }
    });
  }, 250);
});

