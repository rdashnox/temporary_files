const fallbackDashboardData = {
    summary: {
        revenue: 1845000,
        revenueTrend: '+12.8% vs last month',
        ordersToday: 486,
        pendingApprovals: 17,
        riskAlerts: 4,
    },
    bi: {
        financialPerformance: [
            { label: 'Revenue', value: 1845000, max: 2200000 },
            { label: 'Gross Profit', value: 690000, max: 2200000 },
            { label: 'Operating Cost', value: 410000, max: 2200000 },
            { label: 'Marketing Spend', value: 120000, max: 2200000 },
        ],
    },
    orders: {
        statuses: [
            { label: 'New', count: 132, hint: 'Awaiting validation' },
            { label: 'Paid', count: 184, hint: 'Payment confirmed' },
            { label: 'Packed', count: 91, hint: 'Warehouse queue' },
            { label: 'Shipped', count: 62, hint: 'Tracking active' },
            { label: 'Exception', count: 17, hint: 'Needs review' },
        ],
    },
    reports: {
        jobs: [
            { name: 'Revenue Summary - June', status: 'Ready' },
            { name: 'Marketing ROI export', status: 'Running' },
            { name: 'Cash Flow Forecast', status: 'Queued' },
        ],
    },
    access: {
        roles: [
            { role: 'Executive', bi: 'Yes', orders: 'Yes', finance: 'Yes', planning: 'Yes', admin: 'Limited' },
            { role: 'Finance Manager', bi: 'Yes', orders: 'Limited', finance: 'Yes', planning: 'Yes', admin: 'No' },
            { role: 'Operations Staff', bi: 'Limited', orders: 'Yes', finance: 'No', planning: 'Limited', admin: 'No' },
            { role: 'Marketing Analyst', bi: 'Yes', orders: 'Limited', finance: 'Limited', planning: 'No', admin: 'No' },
        ],
    },
    marketing: {
        funnel: [
            { label: 'Visitors', value: 48500, percent: 100 },
            { label: 'Product Views', value: 21800, percent: 45 },
            { label: 'Cart Adds', value: 6200, percent: 13 },
            { label: 'Checkout Started', value: 3600, percent: 7 },
            { label: 'Paid Orders', value: 1480, percent: 3 },
        ],
        channels: [
            { label: 'Paid Social', roi: '3.8x', spend: '₱48K' },
            { label: 'Email', roi: '7.2x', spend: '₱9K' },
            { label: 'Search', roi: '4.4x', spend: '₱31K' },
            { label: 'Referral', roi: '5.1x', spend: '₱12K' },
        ],
    },
};

const currencyFormatter = new Intl.NumberFormat('en-PH', {
    style: 'currency',
    currency: 'PHP',
    maximumFractionDigits: 0,
});

const numberFormatter = new Intl.NumberFormat('en-PH');

const formatStatusClass = (status) => status.toLowerCase().replace(/\s+/g, '-');

const setText = (id, value) => {
    const element = document.getElementById(id);
    if (element) {
        element.textContent = value;
    }
};

const renderSummary = (summary) => {
    setText('kpiRevenue', currencyFormatter.format(summary.revenue));
    setText('kpiRevenueTrend', summary.revenueTrend);
    setText('kpiOrders', numberFormatter.format(summary.ordersToday));
    setText('kpiApprovals', numberFormatter.format(summary.pendingApprovals));
    setText('kpiRisks', numberFormatter.format(summary.riskAlerts));
};

const renderRevenueChart = (items) => {
    const container = document.getElementById('revenueChart');
    container.innerHTML = '';

    items.forEach((item) => {
        const width = Math.max(4, Math.round((item.value / item.max) * 100));
        const row = document.createElement('div');
        row.className = 'bar-row';
        row.innerHTML = `
            <span>${item.label}</span>
            <div class="bar-track" aria-hidden="true"><div class="bar-fill" style="width: ${width}%"></div></div>
            <strong>${currencyFormatter.format(item.value)}</strong>
        `;
        container.appendChild(row);
    });
};

const renderOrderBoard = (statuses) => {
    const container = document.getElementById('orderBoard');
    container.innerHTML = '';

    statuses.forEach((status) => {
        const card = document.createElement('article');
        card.className = 'order-status-card';
        card.innerHTML = `
            <span>${status.label}</span>
            <strong>${numberFormatter.format(status.count)}</strong>
            <small>${status.hint}</small>
        `;
        container.appendChild(card);
    });
};

const renderReportQueue = (jobs) => {
    const container = document.getElementById('reportQueue');
    container.innerHTML = '';

    jobs.forEach((job) => {
        const item = document.createElement('li');
        const statusClass = formatStatusClass(job.status);
        item.innerHTML = `
            <span>${job.name}</span>
            <span class="job-status ${statusClass}">${job.status}</span>
        `;
        container.appendChild(item);
    });
};

const renderRbacTable = (roles) => {
    const container = document.getElementById('rbacTable');
    container.innerHTML = '';

    const permissionClass = (value) => {
        if (value === 'Yes') return 'yes';
        if (value === 'Limited') return 'limited';
        return 'no';
    };

    roles.forEach((row) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td><strong>${row.role}</strong></td>
            <td><span class="permission-pill ${permissionClass(row.bi)}">${row.bi}</span></td>
            <td><span class="permission-pill ${permissionClass(row.orders)}">${row.orders}</span></td>
            <td><span class="permission-pill ${permissionClass(row.finance)}">${row.finance}</span></td>
            <td><span class="permission-pill ${permissionClass(row.planning)}">${row.planning}</span></td>
            <td><span class="permission-pill ${permissionClass(row.admin)}">${row.admin}</span></td>
        `;
        container.appendChild(tr);
    });
};

const renderFunnel = (stages) => {
    const container = document.getElementById('funnelChart');
    container.innerHTML = '';

    stages.forEach((stage) => {
        const item = document.createElement('div');
        item.className = 'funnel-stage';
        item.innerHTML = `
            <div class="funnel-stage-header">
                <strong>${stage.label}</strong>
                <span>${numberFormatter.format(stage.value)}</span>
            </div>
            <div class="bar-track" aria-hidden="true"><div class="funnel-fill" style="width: ${Math.max(3, stage.percent)}%"></div></div>
        `;
        container.appendChild(item);
    });
};

const renderChannels = (channels) => {
    const container = document.getElementById('channelList');
    container.innerHTML = '';

    channels.forEach((channel) => {
        const item = document.createElement('li');
        item.innerHTML = `
            <span><strong>${channel.label}</strong><br><small>Spend: ${channel.spend}</small></span>
            <span class="channel-roi">${channel.roi}</span>
        `;
        container.appendChild(item);
    });
};

const renderDashboard = (data) => {
    renderSummary(data.summary);
    renderRevenueChart(data.bi.financialPerformance);
    renderOrderBoard(data.orders.statuses);
    renderReportQueue(data.reports.jobs);
    renderRbacTable(data.access.roles);
    renderFunnel(data.marketing.funnel);
    renderChannels(data.marketing.channels);
    setText('lastUpdated', `Last updated: ${new Date().toLocaleString()}`);
};

const loadDashboardData = async () => {
    try {
        const response = await window.Auth.authFetch(`${window.APP_CONFIG.API_BASE_URL}/data/business-modules`);
        if (!response.ok) {
            throw new Error('Protected dashboard data failed to load.');
        }
        return await response.json();
    } catch (error) {
        console.warn('Using fallback dashboard data:', error);
        return fallbackDashboardData;
    }
};

const setupNavigationHighlight = () => {
    const links = Array.from(document.querySelectorAll('.nav-link'));
    const sections = links
        .map((link) => document.querySelector(link.getAttribute('href')))
        .filter(Boolean);

    const updateActiveLink = () => {
        let current = sections[0];
        sections.forEach((section) => {
            if (section.getBoundingClientRect().top <= 140) {
                current = section;
            }
        });
        links.forEach((link) => link.classList.toggle('active', link.getAttribute('href') === `#${current.id}`));
    };

    window.addEventListener('scroll', updateActiveLink, { passive: true });
    updateActiveLink();
};

const setupSearch = () => {
    const searchInput = document.getElementById('globalSearch');
    const sections = Array.from(document.querySelectorAll('.module-section'));

    searchInput.addEventListener('input', () => {
        const query = searchInput.value.trim().toLowerCase();
        sections.forEach((section) => {
            const keywords = `${section.dataset.moduleKeywords || ''} ${section.textContent}`.toLowerCase();
            section.classList.toggle('hidden-by-search', query && !keywords.includes(query));
        });
    });
};

const setupPeriodButtons = () => {
    const periodMultipliers = {
        today: 1,
        week: 6.4,
        month: 24.7,
    };

    document.querySelectorAll('.period-button').forEach((button) => {
        button.addEventListener('click', async () => {
            document.querySelectorAll('.period-button').forEach((item) => item.classList.remove('active'));
            button.classList.add('active');

            const data = await loadDashboardData();
            const multiplier = periodMultipliers[button.dataset.period] || 1;
            renderSummary({
                ...data.summary,
                revenue: Math.round(data.summary.revenue * multiplier),
                ordersToday: Math.round(data.summary.ordersToday * multiplier),
            });
        });
    });
};

const setupReportGenerator = () => {
    const button = document.getElementById('generateReportButton');
    const reportType = document.getElementById('reportType');
    const reportFormat = document.getElementById('reportFormat');

    button.addEventListener('click', () => {
        const queue = document.getElementById('reportQueue');
        const item = document.createElement('li');
        item.innerHTML = `
            <span>${reportType.value} (${reportFormat.value})</span>
            <span class="job-status queued">Queued</span>
        `;
        queue.prepend(item);
    });
};

const setupRefresh = () => {
    const refreshButton = document.getElementById('refreshButton');
    refreshButton.addEventListener('click', async () => {
        refreshButton.disabled = true;
        refreshButton.textContent = 'Refreshing...';
        const data = await loadDashboardData();
        renderDashboard(data);
        refreshButton.disabled = false;
        refreshButton.textContent = 'Refresh';
    });
};

document.addEventListener('DOMContentLoaded', () => {
    const dashboardMessage = document.getElementById('dashboardMessage');
    const logoutButton = document.getElementById('logoutButton');

    logoutButton.addEventListener('click', window.Auth.logout);

    window.Auth.requireAuth({
        onSuccess: async (authData) => {
            dashboardMessage.textContent = `Logged in as ${authData.authenticated_user}`;
            const data = await loadDashboardData();
            renderDashboard(data);
        },
        onFailure: () => {
            window.location.replace('index.html');
        },
    }).catch((error) => {
        dashboardMessage.textContent = 'Unable to validate your session. Please make sure the backend is running.';
        console.error('Dashboard token validation error:', error);
        renderDashboard(fallbackDashboardData);
    });

    setupNavigationHighlight();
    setupSearch();
    setupPeriodButtons();
    setupReportGenerator();
    setupRefresh();
});
