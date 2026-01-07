// Global variables
let bsrChart = null;
let currentTimeRange = '30'; // Default to 30 days
let currentWorksheet = ''; // Current selected worksheet (empty = first/default)
let crosshairX = null; // X position of crosshair line
let isCrosshairFixed = false; // Whether crosshair is fixed (clicked)

// Helper function to get time range text
function getTimeRangeText(range) {
    const rangeMap = {
        '1': '24 Hours',
        '7': '7 Days',
        '30': '30 Days',
        '90': '90 Days',
        '365': '1 Year',
        'all': 'All Time'
    };
    return rangeMap[range] || `${range} Days`;
}

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    console.log('🚀 Initializing application...');
    console.log('Current time range:', currentTimeRange);
    console.log('Current worksheet:', currentWorksheet);
    
    try {
        // Initialize worksheets first (async), then load data
        initializeWorksheets().then(() => {
            console.log('✅ Worksheets initialized. Current worksheet:', currentWorksheet);
            initializeTimeFilters();
            updateChartTitle();
            updateRankingsTitle();
            
            // Load data after worksheets are loaded and default is set
            setTimeout(function() {
                console.log('📊 Loading chart and rankings for worksheet:', currentWorksheet);
                loadChart();
                loadRankings();
            }, 200);
        }).catch(error => {
            console.error('❌ Error initializing worksheets:', error);
            // Still try to load with default worksheet name
            currentWorksheet = 'Crime Fiction - US'; // Fallback default
            initializeTimeFilters();
            updateChartTitle();
            updateRankingsTitle();
            setTimeout(function() {
                console.log('📊 Loading chart and rankings with fallback worksheet');
                loadChart();
                loadRankings();
            }, 200);
        });
    } catch (error) {
        console.error('❌ Error initializing application:', error);
    }
});

// Initialize worksheet filters sidebar
async function initializeWorksheets() {
    console.log('📂 initializeWorksheets() called');
    try {
        const response = await fetch('/api/worksheets');
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const worksheets = await response.json();
        console.log('✅ Worksheets received:', worksheets);
        
        const worksheetList = document.getElementById('worksheetList');
        if (!worksheetList) {
            console.error('❌ worksheetList element not found!');
            return;
        }
        worksheetList.innerHTML = '';
        
        if (worksheets.length === 0) {
            worksheetList.innerHTML = '<div style="padding: 12px; color: #999; font-size: 0.9rem;">No worksheets found</div>';
            return;
        }
        
        // Set default worksheet to first one if not set
        if (!currentWorksheet && worksheets.length > 0) {
            currentWorksheet = worksheets[0];
            console.log(`📂 Default worksheet set to: ${currentWorksheet}`);
        }
        
        // Update selection immediately after setting default
        if (currentWorksheet) {
            updateWorksheetSelection();
        }
        
        // Add worksheets
        worksheets.forEach(worksheet => {
            const item = document.createElement('div');
            item.className = 'worksheet-item' + (currentWorksheet === worksheet ? ' active' : '');
            item.textContent = worksheet;
            item.addEventListener('click', function() {
                console.log(`📂 Worksheet selected: ${worksheet}`);
                currentWorksheet = worksheet;
                updateWorksheetSelection();
                // Destroy existing chart before loading new data
                if (bsrChart) {
                    console.log('🗑️ Destroying existing chart for worksheet change');
                    bsrChart.destroy();
                    bsrChart = null;
                }
                // Reset crosshair
                crosshairX = null;
                isCrosshairFixed = false;
                // Reload chart and rankings with new worksheet
                loadChart();
                loadRankings();
            });
            worksheetList.appendChild(item);
        });
        
        // Load data for default worksheet if set
        if (currentWorksheet) {
            console.log(`📂 Loading data for default worksheet: ${currentWorksheet}`);
        }
    } catch (error) {
        console.error('Error loading worksheets:', error);
    }
}

function updateWorksheetSelection() {
    const items = document.querySelectorAll('.worksheet-item');
    items.forEach(item => {
        if (item.textContent === currentWorksheet) {
            item.classList.add('active');
        } else {
            item.classList.remove('active');
        }
    });
    
    // Update chart title
    updateChartTitle();
    updateRankingsTitle();
}

function updateChartTitle() {
    const chartTitle = document.getElementById('chartTitle');
    if (chartTitle) {
        const timeRangeText = getTimeRangeText(currentTimeRange);
        const worksheetText = currentWorksheet || 'All Sheets';
        // Title will be updated with actual book count when data loads
        chartTitle.textContent = `Average BSR - ${worksheetText} (${timeRangeText})`;
    }
}

function updateRankingsTitle() {
    const rankingsTitle = document.getElementById('rankingsTitle');
    if (rankingsTitle) {
        const worksheetText = currentWorksheet || 'All Sheets';
        rankingsTitle.textContent = `Book 1's Best Sellers - ${worksheetText}`;
    }
}

// Initialize time filter buttons
function initializeTimeFilters() {
    const timeFilterBtns = document.querySelectorAll('.time-filter-btn');
    timeFilterBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active class from all buttons
            timeFilterBtns.forEach(b => b.classList.remove('active'));
            // Add active class to clicked button
            this.classList.add('active');
            // Update current time range
            currentTimeRange = this.getAttribute('data-range');
            loadChart();
        });
    });
}

// Load and display chart
async function loadChart() {
    console.log('📊 loadChart() called');
    const container = document.querySelector('.chart-container');
    const chartTitleElement = document.getElementById('chartTitle');
    
    console.log('Container found:', !!container);
    console.log('Chart title element found:', !!chartTitleElement);
    
    if (!container) {
        console.error('❌ Chart container not found!');
        return;
    }
    
    // Update chart title based on time range and worksheet
    const timeRangeText = getTimeRangeText(currentTimeRange || '30');
    const worksheetText = currentWorksheet || 'All Sheets';
    if (chartTitleElement) {
        chartTitleElement.textContent = `Average BSR - ${worksheetText} (${timeRangeText})`;
    }
    
    // Show loading indicator
    const loadingHtml = '<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; color: #FF6B35;"><div style="border: 4px solid #f3f3f3; border-top: 4px solid #FF6B35; border-radius: 50%; width: 40px; height: 40px; animation: spin 1s linear infinite; margin-bottom: 10px;"></div><div>Loading chart data...</div></div><style>@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }</style>';
    container.innerHTML = loadingHtml;
    
    try {
        const worksheetParam = currentWorksheet ? `worksheet=${encodeURIComponent(currentWorksheet)}` : '';
        const rangeParam = `range=${currentTimeRange || '30'}`;
        // Add cache-busting parameter to ensure fresh data after BSR update
        const cacheBuster = `_=${Date.now()}`;
        // Build URL correctly: combine all parameters
        const params = [rangeParam, worksheetParam, cacheBuster].filter(p => p).join('&');
        const url = `/api/chart-data?${params}`;
        console.log('🌐 FETCHING FROM URL:', url);
        console.log('📅 Current time range:', currentTimeRange);
        console.log('📂 Current worksheet:', currentWorksheet);
        console.log('⚠️ IMPORTANT: If you see only 1 date, make sure you selected "All Time" button, not "30 Days"!');
        
        const startTime = performance.now();
        const response = await fetch(url, {
            cache: 'no-cache',
            headers: {
                'Cache-Control': 'no-cache'
            }
        });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        const fetchTime = performance.now() - startTime;
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Extract data once
        const totalBooks = data.total_books || 31;
        
        // CRITICAL DEBUG: Check what we actually received
        console.log('🔍 RAW API RESPONSE:', {
            hasDates: !!data.dates,
            datesType: typeof data.dates,
            isDatesArray: Array.isArray(data.dates),
            datesLength: data.dates ? data.dates.length : 'N/A',
            hasAverageBsr: !!data.average_bsr,
            averageBsrType: typeof data.average_bsr,
            isAverageBsrArray: Array.isArray(data.average_bsr),
            averageBsrLength: data.average_bsr ? data.average_bsr.length : 'N/A',
            firstDate: data.dates ? data.dates[0] : 'N/A',
            firstAverage: data.average_bsr ? data.average_bsr[0] : 'N/A',
            lastDate: data.dates && data.dates.length > 0 ? data.dates[data.dates.length - 1] : 'N/A',
            lastAverage: data.average_bsr && data.average_bsr.length > 0 ? data.average_bsr[data.average_bsr.length - 1] : 'N/A',
            ALL_DATES: data.dates ? data.dates : [],
            ALL_AVERAGES: data.average_bsr ? data.average_bsr : []
        });
        
        console.log('✅ Chart data received:', {
            datesCount: data.dates ? data.dates.length : 0,
            averageBsrCount: data.average_bsr ? data.average_bsr.length : 0,
            totalBooks: totalBooks,
            sampleDates: data.dates ? data.dates.slice(0, 5) : [],
            sampleAverages: data.average_bsr ? data.average_bsr.slice(0, 5) : []
        });
        
        // Update chart title with actual book count
        const timeRangeTextUpdated = getTimeRangeText(currentTimeRange || '30');
        if (chartTitleElement) {
            chartTitleElement.textContent = `Average BSR (${totalBooks} books, ${timeRangeTextUpdated})`;
            console.log('✅ Chart title updated');
        }
        
        if (!data.dates || data.dates.length === 0) {
            console.warn('No dates in chart data');
            if (container) {
                container.innerHTML = '<div class="error">No data available for the selected time range. Try selecting "All Time".</div>';
            }
            return;
        }
        
        // Restore canvas
        if (container) {
            container.innerHTML = '<canvas id="bsrChart"></canvas>';
        }
        const chartCtx = document.getElementById('bsrChart').getContext('2d');
        
        // Destroy existing chart if it exists
        if (bsrChart) {
            console.log('🗑️ Destroying existing chart');
            bsrChart.destroy();
            bsrChart = null;
        }
        
        // Prepare datasets - ensure data arrays match in length
        if (data.dates.length !== data.average_bsr.length) {
            console.error(`Data mismatch: ${data.dates.length} dates but ${data.average_bsr.length} BSR values`);
            const minLength = Math.min(data.dates.length, data.average_bsr.length);
            data.dates = data.dates.slice(0, minLength);
            data.average_bsr = data.average_bsr.slice(0, minLength);
        }
        
        // Filter out null/undefined values but keep dates aligned
        const validData = [];
        const validDates = [];
        const filteredOut = [];
        for (let i = 0; i < data.average_bsr.length; i++) {
            const bsrValue = data.average_bsr[i];
            const dateValue = data.dates[i];
            if (bsrValue !== null && bsrValue !== undefined && bsrValue !== '') {
                validData.push(bsrValue);
                validDates.push(dateValue);
            } else {
                filteredOut.push({ index: i, date: dateValue, bsr: bsrValue, reason: bsrValue === null ? 'null' : bsrValue === undefined ? 'undefined' : 'empty string' });
            }
        }
        
        console.log('📊 Data processing:', {
            totalDates: data.dates.length,
            totalAverages: data.average_bsr.length,
            validDataPoints: validData.length,
            validDatesCount: validDates.length,
            filteredOutCount: filteredOut.length,
            sampleValidData: validData.slice(0, 10),
            sampleValidDates: validDates.slice(0, 10),
            sampleFilteredOut: filteredOut.slice(0, 10),
            ALL_VALID_DATA: validData,
            ALL_VALID_DATES: validDates,
            allRawData: data.average_bsr ? data.average_bsr.map((val, idx) => ({ index: idx, date: data.dates[idx], bsr: val, type: typeof val, isNull: val === null, isUndefined: val === undefined, isEmpty: val === '' })) : []
        });
        
        // CRITICAL: Log if we're losing data
        if (data.dates.length > validData.length) {
            console.error(`❌ DATA LOSS DETECTED: ${data.dates.length} dates received but only ${validData.length} valid after filtering!`);
            console.error(`Filtered out ${filteredOut.length} entries:`, filteredOut);
        }
        
        // Check if we have data to display
        if (validData.length === 0) {
            console.warn('⚠️ No valid data points to display');
            if (container) {
                container.innerHTML = '<div class="error">No data available for the selected time range. Try selecting "All Time".</div>';
            }
            return;
        }
        
        // Warn if only one data point (chart won't show a line, just a point)
        if (validData.length === 1) {
            console.warn('⚠️ Only 1 data point available - chart will show a single point, not a line');
            console.log('💡 Tip: Select "All Time" or "1 Year" to see more historical data');
        }
        
        // Optimize for performance
        const showPoints = validData.length <= 50;
        const pointRadius = showPoints ? (validData.length > 30 ? 1 : 2) : 0;
        
        // Prepare datasets
        // Label shows average for all books
        const labelText = `Average BSR (${totalBooks} books)`;
        
        const datasets = [
            {
                label: labelText,
                data: [], // Will be set below after preparing chartData
                borderColor: '#667eea',
                backgroundColor: 'rgba(102, 126, 234, 0.1)',
                borderWidth: 2,
                fill: validData.length > 1 && validData.length <= 100,
                tension: validData.length <= 50 ? 0.4 : 0.1,
                pointRadius: pointRadius,
                pointHoverRadius: validData.length === 1 ? 8 : 4,
                pointHitRadius: validData.length === 1 ? 10 : 5,
                pointBackgroundColor: '#667eea',
                pointBorderColor: '#667eea',
                pointBorderWidth: 2
            }
        ];
        
        const renderStartTime = performance.now();
        
        // Verify Chart.js is loaded
        if (typeof Chart === 'undefined') {
            console.error('❌ Chart.js is not loaded!');
            if (container) {
                container.innerHTML = '<div class="error">Error: Chart.js library not loaded. Please refresh the page.</div>';
            }
            return;
        }
        
        // Verify date adapter for time scale
        if (validData.length > 1) {
            if (typeof Chart._adapters === 'undefined' || !Chart._adapters._date) {
                console.error('❌ Date adapter not loaded! Cannot use time scale.');
                if (container) {
                    container.innerHTML = '<div class="error">Error: Date adapter not loaded. Please refresh the page.</div>';
                }
                return;
            }
        }
        
        console.log('✅ Chart.js is loaded, creating chart...');
        console.log('Valid data points:', validData.length);
        console.log('Valid dates:', validDates.length);
        console.log('Sample data:', validData.slice(0, 5));
        console.log('Sample dates:', validDates.slice(0, 5));
        
        // Prepare data for Chart.js
        // Always use {x, y} format for consistency
        console.log('🔄 Starting chartData preparation:', {
            validDataLength: validData.length,
            validDatesLength: validDates.length,
            firstFewDates: validDates.slice(0, 5),
            firstFewValues: validData.slice(0, 5)
        });
        
        const chartData = validData.map((value, index) => {
            const dateStr = validDates[index];
            // For single point with category scale, use the date string as label
            if (validData.length === 1) {
                return { x: dateStr, y: value };
            } else {
                // For multiple points with time scale, convert to Date object
                let dateValue;
                if (dateStr.match(/^\d{4}-\d{2}-\d{2}$/)) {
                    // YYYY-MM-DD format - create Date object with time
                    dateValue = new Date(dateStr + 'T00:00:00');
                } else {
                    // Try to parse other formats
                    dateValue = new Date(dateStr);
                }
                
                // Validate date
                if (isNaN(dateValue.getTime())) {
                    console.error(`❌ Invalid date at index ${index}: "${dateStr}"`);
                    return null;
                }
                
                // Use Date object directly (adapter will handle it)
                return { x: dateValue, y: value };
            }
        }).filter(item => item !== null); // Remove any null entries
        
        console.log('🔄 After chartData preparation:', {
            chartDataLength: chartData.length,
            filteredOut: validData.length - chartData.length,
            sampleChartData: chartData.slice(0, 3).map(d => ({
                x: d.x instanceof Date ? d.x.toISOString() : d.x,
                y: d.y
            }))
        });
        
        if (chartData.length === 0) {
            console.error('❌ No valid chart data after processing');
            if (container) {
                container.innerHTML = '<div class="error">Error: No valid data points to display.</div>';
            }
            return;
        }
        
        datasets[0].data = chartData;
        
        console.log('📊 Chart data prepared:', {
            dataPoints: chartData.length,
            format: '{x, y} objects',
            sampleData: chartData.slice(0, 5),
            sampleDataLast: chartData.slice(-5),
            dateRange: chartData.length > 0 ? {
                first: chartData[0].x instanceof Date ? chartData[0].x.toISOString() : chartData[0].x,
                last: chartData[chartData.length - 1].x instanceof Date ? chartData[chartData.length - 1].x.toISOString() : chartData[chartData.length - 1].x
            } : null,
            yRange: validData.length > 0 ? {
                min: Math.min(...validData),
                max: Math.max(...validData)
            } : null,
            allDataPoints: chartData.length <= 20 ? chartData.map(d => ({
                x: d.x instanceof Date ? d.x.toISOString() : d.x,
                y: d.y
            })) : `Showing first 5 and last 5 of ${chartData.length} points`
        });
        
        // Verify we have multiple data points
        if (chartData.length === 1) {
            console.warn('⚠️ Only 1 data point available - chart will show a single point');
            console.log('💡 Tip: Select "All Time" or "1 Year" to see more historical data');
        } else {
            console.log(`✅ Chart will display ${chartData.length} data points`);
        }
        
        // Final verification before creating chart
        console.log('🔍 Final check before Chart.js creation:', {
            chartDataLength: chartData.length,
            datasetsLength: datasets.length,
            datasetsDataLength: datasets[0].data.length,
            firstDataPoint: datasets[0].data[0],
            lastDataPoint: datasets[0].data[datasets[0].data.length - 1],
            sampleData: datasets[0].data.slice(0, 5)
        });
        
        // Custom crosshair plugin to draw vertical line
        const crosshairPlugin = {
            id: 'crosshair',
            afterDraw: (chart) => {
                if (crosshairX === null) return;
                
                const ctx = chart.ctx;
                const chartArea = chart.chartArea;
                const xScale = chart.scales.x;
                
                // Convert X value to pixel position
                let xPixel;
                if (chart.data.datasets[0].data.length > 0) {
                    xPixel = xScale.getPixelForValue(crosshairX);
                } else {
                    return;
                }
                
                // Check if pixel is within chart area
                if (xPixel < chartArea.left || xPixel > chartArea.right) {
                    return;
                }
                
                // Draw vertical line
                ctx.save();
                ctx.strokeStyle = '#FF6B35';
                ctx.lineWidth = 2;
                ctx.setLineDash([5, 5]);
                ctx.beginPath();
                ctx.moveTo(xPixel, chartArea.top);
                ctx.lineTo(xPixel, chartArea.bottom);
                ctx.stroke();
                ctx.restore();
            }
        };
        
        bsrChart = new Chart(chartCtx, {
            type: 'line',
            data: {
                datasets: datasets
            },
            plugins: [crosshairPlugin],
            options: {
                responsive: true,
                maintainAspectRatio: false,
                animation: {
                    duration: 0
                },
                onHover: (event, activeElements) => {
                    if (!isCrosshairFixed && event.native && bsrChart) {
                        const canvasPosition = Chart.helpers.getRelativePosition(event.native, bsrChart);
                        const xScale = bsrChart.scales.x;
                        
                        // Check if mouse is within chart area
                        if (canvasPosition.x >= bsrChart.chartArea.left && 
                            canvasPosition.x <= bsrChart.chartArea.right) {
                            const xValue = xScale.getValueForPixel(canvasPosition.x);
                            crosshairX = xValue;
                            bsrChart.update('none');
                        }
                    }
                },
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
                    },
                    tooltip: {
                        enabled: true,
                        mode: 'index',
                        intersect: false,
                        filter: function(tooltipItem) {
                            return tooltipItem.parsed.y !== null;
                        },
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += '#' + context.parsed.y.toLocaleString();
                                }
                                return label;
                            }
                        }
                    },
                    zoom: {
                        zoom: {
                            wheel: {
                                enabled: true,
                                speed: 0.1
                            },
                            pinch: {
                                enabled: true
                            },
                            mode: 'x'
                        },
                        pan: {
                            enabled: true,
                            mode: 'x'
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: false,
                        reverse: true, // Lower rank is better
                        title: {
                            display: true,
                            text: 'Rank'
                        },
                        ticks: {
                            callback: function(value) {
                                return '#' + value.toLocaleString();
                            }
                        },
                        // Ensure the scale includes all data points
                        suggestedMin: validData.length > 0 ? Math.min(...validData) * 0.9 : undefined,
                        suggestedMax: validData.length > 0 ? Math.max(...validData) * 1.1 : undefined
                    },
                    x: {
                        type: validData.length === 1 ? 'category' : 'time',
                        time: validData.length === 1 ? undefined : {
                            parser: false, // Don't parse, dates are already Date objects
                            unit: 'day',
                            tooltipFormat: 'MMM d, yyyy',
                            displayFormats: {
                                day: 'MMM d, yyyy',
                                week: 'MMM d, yyyy',
                                month: 'MMM yyyy',
                                year: 'yyyy'
                            }
                        },
                        title: {
                            display: true,
                            text: 'Date'
                        },
                        ticks: {
                            maxRotation: 45,
                            minRotation: 45,
                            maxTicksLimit: validData.length === 1 ? 1 : (validData.length > 20 ? 20 : validData.length),
                            autoSkip: validData.length > 20
                        }
                    }
                },
                interaction: {
                    mode: 'nearest',
                    axis: 'x',
                    intersect: false
                }
            }
        });
        
        const renderTime = performance.now() - renderStartTime;
        const totalTime = performance.now() - startTime;
        console.log(`✅ Chart rendered in ${renderTime.toFixed(2)}ms | Total: ${totalTime.toFixed(2)}ms | Points: ${validData.length}`);
        
        // Verify chart data after creation
        setTimeout(() => {
            if (bsrChart && bsrChart.data && bsrChart.data.datasets && bsrChart.data.datasets[0]) {
                console.log(`📊 Chart data summary:`, {
                    totalDataPoints: bsrChart.data.datasets[0].data.length,
                    chartType: bsrChart.config.type,
                    xAxisType: bsrChart.scales.x ? bsrChart.scales.x.type : 'unknown',
                    yAxisType: bsrChart.scales.y ? bsrChart.scales.y.type : 'unknown',
                    xAxisMin: bsrChart.scales.x ? bsrChart.scales.x.min : 'unknown',
                    xAxisMax: bsrChart.scales.x ? bsrChart.scales.x.max : 'unknown',
                    firstDataPoint: bsrChart.data.datasets[0].data[0],
                    lastDataPoint: bsrChart.data.datasets[0].data[bsrChart.data.datasets[0].data.length - 1]
                });
            } else {
                console.error('❌ Chart data not accessible after creation');
            }
        }, 100);
        
                // Double click to reset zoom
                if (bsrChart && bsrChart.canvas) {
                    bsrChart.canvas.addEventListener('dblclick', function(e) {
                        e.preventDefault();
                        if (bsrChart && typeof bsrChart.resetZoom === 'function') {
                            bsrChart.resetZoom();
                        }
                        // Also reset crosshair
                        crosshairX = null;
                        isCrosshairFixed = false;
                        bsrChart.update('none');
                    });
                    
                    // Click to fix/unfix crosshair
                    bsrChart.canvas.addEventListener('click', function(e) {
                        const canvasPosition = Chart.helpers.getRelativePosition(e, bsrChart);
                        const xScale = bsrChart.scales.x;
                        const xValue = xScale.getValueForPixel(canvasPosition.x);
                        
                        if (isCrosshairFixed && crosshairX === xValue) {
                            // Unfix if clicking same position
                            isCrosshairFixed = false;
                            crosshairX = null;
                        } else {
                            // Fix crosshair at clicked position
                            isCrosshairFixed = true;
                            crosshairX = xValue;
                        }
                        bsrChart.update('none');
                    });
                    
                    // Mousemove to update crosshair position (if not fixed)
                    bsrChart.canvas.addEventListener('mousemove', function(e) {
                        if (!isCrosshairFixed && bsrChart) {
                            const canvasPosition = Chart.helpers.getRelativePosition(e, bsrChart);
                            const xScale = bsrChart.scales.x;
                            
                            // Check if mouse is within chart area
                            if (canvasPosition.x >= bsrChart.chartArea.left && 
                                canvasPosition.x <= bsrChart.chartArea.right) {
                                const xValue = xScale.getValueForPixel(canvasPosition.x);
                                crosshairX = xValue;
                                bsrChart.update('none');
                            } else {
                                // Hide crosshair if outside chart area
                                if (crosshairX !== null) {
                                    crosshairX = null;
                                    bsrChart.update('none');
                                }
                            }
                        }
                    });
                    
                    // Mouse leave to hide crosshair if not fixed
                    bsrChart.canvas.addEventListener('mouseleave', function() {
                        if (!isCrosshairFixed) {
                            crosshairX = null;
                            bsrChart.update('none');
                        }
                    });
                }
        
        console.log('✅ Chart created successfully with zoom/pan functionality');
        console.log('Chart data points:', bsrChart.data.datasets[0].data.length);
    } catch (error) {
        console.error('Error loading chart:', error);
        const container = document.querySelector('.chart-container');
        if (container) {
            container.innerHTML = `<div class="error">Error loading chart data: ${error.message}</div>`;
        }
    }
}

// Load and display rankings
async function loadRankings() {
    console.log('📚 loadRankings() called');
    const container = document.getElementById('rankingsContainer');
    
    console.log('Rankings container found:', !!container);
    
    if (!container) {
        console.error('❌ Rankings container not found!');
        return;
    }
    
    container.innerHTML = '<div class="loading">Loading rankings...</div>';
    
    try {
        // Ensure we have a worksheet name
        const worksheetName = currentWorksheet || 'Crime Fiction - US';
        const worksheetParam = `worksheet=${encodeURIComponent(worksheetName)}`;
        // Add cache-busting parameter to ensure fresh data after BSR update
        const cacheBuster = `_=${Date.now()}`;
        // Build URL correctly: combine all parameters
        const params = [worksheetParam, cacheBuster].join('&');
        const url = `/api/rankings?${params}`;
        console.log('📚 Fetching rankings from:', url);
        console.log('📂 Current worksheet:', worksheetName);
        
        let response;
        try {
            response = await fetch(url, {
                cache: 'no-cache',
                headers: {
                    'Cache-Control': 'no-cache',
                    'Accept': 'application/json'
                }
            });
        } catch (fetchError) {
            console.error('❌ Fetch error:', fetchError);
            console.error('❌ Error details:', {
                message: fetchError.message,
                name: fetchError.name,
                stack: fetchError.stack
            });
            container.innerHTML = `<div class="error">Network error: ${fetchError.message}. Please check if the server is running on port 5001.</div>`;
            return;
        }
        
        if (!response.ok) {
            const errorText = await response.text().catch(() => 'Unknown error');
            console.error(`❌ HTTP error! status: ${response.status}, body: ${errorText}`);
            throw new Error(`HTTP error! status: ${response.status}: ${errorText}`);
        }
        
        let rankings;
        try {
            rankings = await response.json();
        } catch (jsonError) {
            console.error('❌ JSON parse error:', jsonError);
            const responseText = await response.text().catch(() => 'Could not read response');
            console.error('❌ Response text:', responseText.substring(0, 500));
            throw new Error(`Failed to parse JSON response: ${jsonError.message}`);
        }
        console.log('✅ Rankings received:', rankings.length, 'books');
        
        // Log sample book data to debug BSR display
        if (rankings.length > 0) {
            console.log('📊 Sample book data:', {
                name: rankings[0].name,
                current_bsr: rankings[0].current_bsr,
                bsr_history_length: rankings[0].bsr_history?.length || 0,
                latest_bsr: rankings[0].bsr_history?.[rankings[0].bsr_history.length - 1]?.bsr || null
            });
        }
        
        if (rankings.error) {
            throw new Error(rankings.error);
        }
        
        if (rankings.length === 0) {
            container.innerHTML = '<div class="loading">No rankings available.</div>';
            return;
        }
        
        container.innerHTML = '';
        
        rankings.forEach((book, index) => {
            const card = createRankingCard(book, index + 1);
            container.appendChild(card);
        });
    } catch (error) {
        console.error('Error loading rankings:', error);
        container.innerHTML = '<div class="error">Error loading rankings. Please try again later.</div>';
    }
}

// Create a ranking card element
function createRankingCard(book, rank) {
    const card = document.createElement('div');
    card.className = 'ranking-card';
    
    // Use cover image from backend if available, otherwise use placeholder
    const coverImage = book.cover_image || '/static/images/placeholder-book.svg';
    
    card.innerHTML = `
        <div class="rank-badge">#${rank}</div>
        <div class="book-cover-container">
            <img src="${coverImage}" alt="${escapeHtml(book.name)}" class="book-cover" 
                 onerror="this.onerror=null; this.src='/static/images/placeholder-book.svg';">
        </div>
        <div class="book-info">
            <div class="book-title">${escapeHtml(book.name)}</div>
            <div class="book-author">${escapeHtml(book.author || 'Unknown Author')}</div>
            <div class="book-rank">Rank: #${book.current_bsr ? book.current_bsr.toLocaleString() : 'N/A'}</div>
        </div>
    `;
    
    // Make card clickable to open Amazon link
    card.style.cursor = 'pointer';
    card.addEventListener('click', function() {
        if (book.amazon_link) {
            window.open(book.amazon_link, '_blank');
        }
    });
    
    return card;
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// BSR update button removed - no longer needed
