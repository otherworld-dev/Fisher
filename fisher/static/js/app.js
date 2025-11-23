// Fisher Web App JavaScript

let currentReport = null;

// Initialize app when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    checkApiStatus();
    setupEventListeners();
});

// Check API configuration status
async function checkApiStatus() {
    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        const statusBadge = document.getElementById('statusBadge');
        const configuredMarketplaces = data.configured_marketplaces;

        if (configuredMarketplaces.length > 0) {
            statusBadge.className = 'status-badge connected';
            statusBadge.innerHTML = `
                <span class="status-text">✓ Connected: ${configuredMarketplaces.map(m => m.toUpperCase()).join(', ')}</span>
            `;
        } else {
            statusBadge.className = 'status-badge error';
            statusBadge.innerHTML = `
                <span class="status-text">⚠ No APIs Configured</span>
            `;
        }
    } catch (error) {
        console.error('Error checking API status:', error);
        const statusBadge = document.getElementById('statusBadge');
        statusBadge.className = 'status-badge error';
        statusBadge.innerHTML = '<span class="status-text">⚠ Error checking status</span>';
    }
}

// Setup event listeners
function setupEventListeners() {
    const searchForm = document.getElementById('searchForm');
    searchForm.addEventListener('submit', handleSearch);

    const exportBtn = document.getElementById('exportBtn');
    exportBtn.addEventListener('click', exportResults);

    const viewApiStatusBtn = document.getElementById('viewApiStatus');
    viewApiStatusBtn.addEventListener('click', showApiStatusModal);

    const closeModalBtn = document.getElementById('closeModal');
    closeModalBtn.addEventListener('click', closeApiStatusModal);

    // Close modal when clicking outside
    const modal = document.getElementById('apiStatusModal');
    modal.addEventListener('click', function(e) {
        if (e.target === modal) {
            closeApiStatusModal();
        }
    });
}

// Handle search form submission
async function handleSearch(e) {
    e.preventDefault();

    const searchBtn = document.getElementById('searchBtn');
    const btnText = searchBtn.querySelector('.btn-text');
    const btnLoader = searchBtn.querySelector('.btn-loader');

    // Show loading state
    searchBtn.disabled = true;
    btnText.style.display = 'none';
    btnLoader.style.display = 'inline';

    showSection('loadingSection');
    hideSection('resultsSection');
    hideSection('errorSection');

    // Collect form data
    const formData = {
        keywords: document.getElementById('keywords').value,
        marketplaces: getSelectedMarketplaces(),
        category: document.getElementById('category').value || null,
        min_price: parseFloat(document.getElementById('minPrice').value) || null,
        max_price: parseFloat(document.getElementById('maxPrice').value) || null,
        condition: document.getElementById('condition').value || null,
        max_results: parseInt(document.getElementById('maxResults').value) || 50,
        sort_by: document.getElementById('sortBy').value,
        top_n: parseInt(document.getElementById('topN').value) || 20
    };

    try {
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || 'Search failed');
        }

        currentReport = data.report;
        displayResults(data);

    } catch (error) {
        console.error('Search error:', error);
        showError(error.message || 'An error occurred during search');
    } finally {
        // Reset button state
        searchBtn.disabled = false;
        btnText.style.display = 'inline';
        btnLoader.style.display = 'none';
    }
}

// Get selected marketplaces from multi-select
function getSelectedMarketplaces() {
    const select = document.getElementById('marketplaces');
    const selected = Array.from(select.selectedOptions).map(option => option.value);
    return selected.join(',');
}

// Display search results
function displayResults(data) {
    hideSection('loadingSection');
    showSection('resultsSection');

    const report = data.report;

    // Display insights
    displayInsights(report.insights);

    // Display products
    displayProducts(report.top_products);
}

// Display insights panel
function displayInsights(insights) {
    const insightsPanel = document.getElementById('insightsPanel');

    let html = '<h3>Analysis Insights</h3>';
    html += '<div class="insights-grid">';

    // Total products
    if (insights.total_products !== undefined) {
        html += `
            <div class="insight-card">
                <div class="insight-label">Total Products</div>
                <div class="insight-value">${insights.total_products}</div>
            </div>
        `;
    }

    // Price analysis
    if (insights.price_analysis) {
        const price = insights.price_analysis;
        if (price.avg_price !== null) {
            html += `
                <div class="insight-card">
                    <div class="insight-label">Avg Price</div>
                    <div class="insight-value">$${price.avg_price.toFixed(2)}</div>
                </div>
                <div class="insight-card">
                    <div class="insight-label">Price Range</div>
                    <div class="insight-value">$${price.min_price.toFixed(2)} - $${price.max_price.toFixed(2)}</div>
                </div>
                <div class="insight-card">
                    <div class="insight-label">Median Price</div>
                    <div class="insight-value">$${price.median_price.toFixed(2)}</div>
                </div>
            `;
        }
    }

    // Top categories
    if (insights.top_categories && Object.keys(insights.top_categories).length > 0) {
        const topCategory = Object.entries(insights.top_categories)[0];
        html += `
            <div class="insight-card">
                <div class="insight-label">Top Category</div>
                <div class="insight-value" style="font-size: 1rem;">${topCategory[0]} (${topCategory[1]})</div>
            </div>
        `;
    }

    html += '</div>';
    insightsPanel.innerHTML = html;
}

// Display product cards
function displayProducts(products) {
    const resultsGrid = document.getElementById('resultsGrid');
    resultsGrid.innerHTML = '';

    if (!products || products.length === 0) {
        resultsGrid.innerHTML = '<p style="text-align: center; color: var(--text-secondary);">No products found</p>';
        return;
    }

    products.forEach((product, index) => {
        const card = createProductCard(product, index + 1);
        resultsGrid.appendChild(card);
    });
}

// Create a product card element
function createProductCard(product, rank) {
    const card = document.createElement('div');
    card.className = 'product-card';

    const priceStr = product.price !== null ? `${product.currency} ${product.price.toFixed(2)}` : 'N/A';
    const popularityScore = product.metrics?.popularity_score !== null ? product.metrics.popularity_score.toFixed(1) : 'N/A';

    let metricsHtml = '<div class="product-metrics">';

    if (product.metrics?.sales_count !== null && product.metrics?.sales_count !== undefined) {
        metricsHtml += `
            <div class="metric">
                <div class="metric-label">Sales</div>
                <div class="metric-value">${formatNumber(product.metrics.sales_count)}</div>
            </div>
        `;
    }

    if (product.metrics?.view_count !== null && product.metrics?.view_count !== undefined) {
        metricsHtml += `
            <div class="metric">
                <div class="metric-label">Views</div>
                <div class="metric-value">${formatNumber(product.metrics.view_count)}</div>
            </div>
        `;
    }

    if (product.metrics?.review_count !== null && product.metrics?.review_count !== undefined) {
        metricsHtml += `
            <div class="metric">
                <div class="metric-label">Reviews</div>
                <div class="metric-value">${formatNumber(product.metrics.review_count)}</div>
            </div>
        `;
    }

    if (product.metrics?.average_rating !== null && product.metrics?.average_rating !== undefined) {
        metricsHtml += `
            <div class="metric">
                <div class="metric-label">Rating</div>
                <div class="metric-value">${product.metrics.average_rating.toFixed(1)}/5.0</div>
            </div>
        `;
    }

    metricsHtml += '</div>';

    card.innerHTML = `
        <div class="product-rank">#${rank}</div>
        <div class="product-title">${escapeHtml(product.title)}</div>
        <div class="product-meta">
            <span class="product-marketplace">${product.marketplace.toUpperCase()}</span>
            <span class="product-price">${priceStr}</span>
        </div>
        ${metricsHtml}
        <div class="popularity-score">
            <div class="metric-label">Popularity Score</div>
            <div class="metric-value">${popularityScore}</div>
        </div>
    `;

    // Add click handler to open product URL
    if (product.product_url) {
        card.style.cursor = 'pointer';
        card.addEventListener('click', () => {
            window.open(product.product_url, '_blank');
        });
    }

    return card;
}

// Export results to JSON
function exportResults() {
    if (!currentReport) {
        alert('No results to export');
        return;
    }

    const dataStr = JSON.stringify(currentReport, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });

    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `fisher-results-${Date.now()}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

// Show API status modal
async function showApiStatusModal(e) {
    e.preventDefault();

    const modal = document.getElementById('apiStatusModal');
    const content = document.getElementById('apiStatusContent');

    content.innerHTML = '<p style="text-align: center;">Loading...</p>';
    modal.style.display = 'flex';

    try {
        const response = await fetch('/api/status');
        const data = await response.json();

        let html = '';
        for (const [marketplace, status] of Object.entries(data.status)) {
            const badgeClass = status.configured ? 'configured' : 'not-configured';
            const badgeText = status.configured ? '✓ Configured' : '✗ Not Configured';

            html += `
                <div class="api-status-item">
                    <span class="api-name">${marketplace.toUpperCase()}</span>
                    <span class="api-status-badge ${badgeClass}">${badgeText}</span>
                </div>
            `;
        }

        content.innerHTML = html;

    } catch (error) {
        content.innerHTML = '<p style="color: var(--error-color); text-align: center;">Error loading API status</p>';
    }
}

// Close API status modal
function closeApiStatusModal() {
    const modal = document.getElementById('apiStatusModal');
    modal.style.display = 'none';
}

// Show/hide sections
function showSection(sectionId) {
    document.getElementById(sectionId).style.display = 'block';
}

function hideSection(sectionId) {
    document.getElementById(sectionId).style.display = 'none';
}

// Show error message
function showError(message) {
    hideSection('loadingSection');
    hideSection('resultsSection');
    showSection('errorSection');

    const errorMessage = document.getElementById('errorMessage');
    errorMessage.textContent = message;
}

// Utility functions
function formatNumber(num) {
    if (num === null || num === undefined) return 'N/A';
    return num.toLocaleString();
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
