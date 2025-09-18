// --- Global variable to store all student data ---
let allStudents = [];

document.addEventListener("DOMContentLoaded", () => {
    const darkModeToggle = document.getElementById('darkModeToggle');
    const body = document.body;
    const applyTheme = (theme) => {
        if (theme === 'dark') {
            body.classList.add('dark-mode');
            darkModeToggle.checked = true;
        } else {
            body.classList.remove('dark-mode');
            darkModeToggle.checked = false;
        }
    };
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme) {
        applyTheme(savedTheme);
    }
    darkModeToggle.addEventListener('change', () => {
        if (darkModeToggle.checked) {
            localStorage.setItem('theme', 'dark');
            applyTheme('dark');
        } else {
            localStorage.setItem('theme', 'light');
            applyTheme('light');
        }
    });

    if (document.getElementById('student-grid')) {
        const isMentorDashboard = window.location.pathname.includes('mentor_dashboard');

        if (!isMentorDashboard) {
            fetchStatistics();
            fetchMentorStats();
            document.getElementById('show-student-view').addEventListener('click', () => {
                document.getElementById('student-view').style.display = 'block';
                document.getElementById('mentor-view').style.display = 'none';
                document.getElementById('show-student-view').classList.add('active');
                document.getElementById('show-mentor-view').classList.remove('active');
            });
            document.getElementById('show-mentor-view').addEventListener('click', () => {
                document.getElementById('student-view').style.display = 'none';
                document.getElementById('mentor-view').style.display = 'block';
                document.getElementById('show-student-view').classList.remove('active');
                document.getElementById('show-mentor-view').classList.add('active');
            });
        }
        
        fetchStudents(isMentorDashboard);

        const filterSelect = document.getElementById('riskFilter');
        if (filterSelect) {
            filterSelect.addEventListener('change', (event) => {
                renderStudentGrid(event.target.value);
            });
        }
    }
});

let radarChartInstance = null;
let doughnutChartInstance = null;

async function fetchStatistics() {
    const response = await fetch('/api/statistics');
    const stats = await response.json();
    document.getElementById('stats-cards').innerHTML = `
        <div class="col-md-3 mb-3"><div class="card stat-card total" data-risk="All"><div class="card-body d-flex justify-content-between align-items-center"><div><h5 class="card-title">Total Students</h5><p class="card-text fs-2 fw-bold">${stats.total}</p></div><i class="fas fa-users icon"></i></div></div></div>
        <div class="col-md-3 mb-3"><div class="card stat-card high-risk" data-risk="High Risk"><div class="card-body d-flex justify-content-between align-items-center"><div><h5 class="card-title">High Risk</h5><p class="card-text fs-2 fw-bold">${stats.high_risk}</p></div><i class="fas fa-exclamation-triangle icon"></i></div></div></div>
        <div class="col-md-3 mb-3"><div class="card stat-card medium-risk" data-risk="Medium Risk"><div class="card-body d-flex justify-content-between align-items-center"><div><h5 class="card-title">Medium Risk</h5><p class="card-text fs-2 fw-bold">${stats.medium_risk}</p></div><i class="fas fa-exclamation-circle icon"></i></div></div></div>
        <div class="col-md-3 mb-3"><div class="card stat-card low-risk" data-risk="Low Risk"><div class="card-body d-flex justify-content-between align-items-center"><div><h5 class="card-title">Low Risk</h5><p class="card-text fs-2 fw-bold">${stats.low_risk}</p></div><i class="fas fa-check-circle icon"></i></div></div></div>
    `;
    setupRiskFilterButtons(false);
}

async function fetchMentorStats() {
    try {
        const response = await fetch('/api/mentor_stats');
        const mentorStats = await response.json();
        const tableBody = document.getElementById('mentor-workload-table-body');
        tableBody.innerHTML = '';
        if (mentorStats.length === 0) {
            tableBody.innerHTML = `<tr><td colspan="5" class="text-center text-muted">No mentor data available.</td></tr>`;
            return;
        }
        mentorStats.forEach(mentor => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${mentor.mentor_name}</td>
                <td class="text-center">${mentor['Total Students']}</td>
                <td class="text-center text-danger">${mentor['High Risk']}</td>
                <td class="text-center text-warning">${mentor['Medium Risk']}</td>
                <td class="text-center text-success">${mentor['Low Risk']}</td>
            `;
            tableBody.appendChild(row);
        });
    } catch (error) {
        console.error("Error fetching mentor stats:", error);
        document.getElementById('mentor-workload-table-body').innerHTML = `<tr><td colspan="5" class="text-center text-danger">Failed to load mentor stats.</td></tr>`;
    }
}

async function fetchStudents(isMentor) {
    try {
        const endpoint = isMentor ? '/api/mentor_students' : '/api/students';
        const response = await fetch(endpoint);
        allStudents = await response.json();
        if (isMentor) {
            renderMentorStatsCards();
            setupRiskFilterButtons(true);
        }
        renderStudentGrid('All'); // Initial render
    } catch (error) {
        console.error("Error fetching students:", error);
        document.getElementById('student-grid').innerHTML = '<p class="text-center text-danger">Failed to load student data.</p>';
    }
}

function renderMentorStatsCards() {
    const cardsContainer = document.getElementById('mentor-stats-cards');
    if (allStudents.length === 0) {
        cardsContainer.innerHTML = '<p class="text-center text-muted">No students assigned to you.</p>';
        return;
    }

    const totalStudents = allStudents.length;
    const highRisk = allStudents.filter(s => s.risk_category === 'High Risk').length;
    const mediumRisk = allStudents.filter(s => s.risk_category === 'Medium Risk').length;
    const lowRisk = allStudents.filter(s => s.risk_category === 'Low Risk').length;

    cardsContainer.innerHTML = `
        <div class="col-md-3 mb-3"><div class="card stat-card total" data-risk="All"><div class="card-body d-flex justify-content-between align-items-center"><div><h5 class="card-title">My Total Students</h5><p class="card-text fs-2 fw-bold">${totalStudents}</p></div><i class="fas fa-users icon"></i></div></div></div>
        <div class="col-md-3 mb-3"><div class="card stat-card high-risk" data-risk="High Risk"><div class="card-body d-flex justify-content-between align-items-center"><div><h5 class="card-title">High Risk</h5><p class="card-text fs-2 fw-bold">${highRisk}</p></div><i class="fas fa-exclamation-triangle icon"></i></div></div></div>
        <div class="col-md-3 mb-3"><div class="card stat-card medium-risk" data-risk="Medium Risk"><div class="card-body d-flex justify-content-between align-items-center"><div><h5 class="card-title">Medium Risk</h5><p class="card-text fs-2 fw-bold">${mediumRisk}</p></div><i class="fas fa-exclamation-circle icon"></i></div></div></div>
        <div class="col-md-3 mb-3"><div class="card stat-card low-risk" data-risk="Low Risk"><div class="card-body d-flex justify-content-between align-items-center"><div><h5 class="card-title">Low Risk</h5><p class="card-text fs-2 fw-bold">${lowRisk}</p></div><i class="fas fa-check-circle icon"></i></div></div></div>
    `;
    setupRiskFilterButtons(true);
}

function renderStudentGrid(filterValue) {
    const grid = document.getElementById('student-grid');
    grid.innerHTML = '';

    const filteredStudents = filterValue === 'All' ?
        allStudents :
        allStudents.filter(student => student.risk_category === filterValue);

    if (filteredStudents.length === 0) {
        grid.innerHTML = `<p class="text-center p-4">No students found for the "${filterValue}" category.</p>`;
        return;
    }

    filteredStudents.forEach(student => {
        const riskClass = student.risk_category.replace(' ', '');
        const card = document.createElement('div');
        card.className = 'col-xl-2 col-lg-3 col-md-4 col-sm-6';
        card.innerHTML = `<div class="student-card risk-${riskClass.replace('Risk', '')}" data-bs-toggle="modal" data-bs-target="#studentModal" data-student='${JSON.stringify(student)}'><h6 class="student-name">${student.student_name}</h6><p class="student-id">${student.student_id}</p></div>`;
        new bootstrap.Popover(card.querySelector('.student-card'), {
            trigger: 'hover',
            placement: 'top',
            html: true,
            title: 'Quick Stats',
            content: `<div class="student-popover-content"><p><strong>CGPA:</strong> ${student.cgpa}</p><p><strong>Attendance:</strong> ${student.attendance}%</p><p><strong>Risk Score:</strong> ${student.final_risk_score.toFixed(2)}</p></div>`
        });
        grid.appendChild(card);
    });
}


const studentModal = document.getElementById('studentModal');
studentModal.addEventListener('show.bs.modal', event => {
    const card = event.relatedTarget;
    const student = JSON.parse(card.dataset.student);
    document.getElementById('modalStudentName').textContent = student.student_name;
    document.getElementById('modalStudentId').textContent = student.student_id;
    document.getElementById('modalMentorName').textContent = student.mentor_name;
    const riskColor = student.risk_category === 'High Risk' ? 'danger' : student.risk_category === 'Medium Risk' ? 'warning' : 'success';
    document.getElementById('modal-summary').innerHTML = `
        <p><strong>Final Risk Score:</strong> ${student.final_risk_score.toFixed(2)}</p>
        <p><strong>Risk Category:</strong> <span class="badge bg-${riskColor}">${student.risk_category}</span></p>
        <p><strong>Fees Due:</strong> ₹${new Intl.NumberFormat('en-IN').format(student.Fees_Amount_Due)}</p>
        <hr>
        <p><strong>Financial Risk:</strong> ${student.financial_risk} / 10</p>
        <p><strong>Attendance Risk:</strong> ${student.attendance_risk} / 10</p>
        <p><strong>Internals Risk:</strong> ${student.internals_risk} / 10</p>
        <p><strong>CGPA Risk:</strong> ${student.cgpa_risk} / 10</p>
    `;
    if (student.counselling_suggestions) {
        document.getElementById('suggestion-text').textContent = student.counselling_suggestions;
    }
    createRadarChart(student);
    createDoughnutChart(student);
});

function createRadarChart(student) {
    const ctx = document.getElementById('riskRadarChart').getContext('2d');
    if (radarChartInstance) { radarChartInstance.destroy(); }
    radarChartInstance = new Chart(ctx, {
        type: 'radar',
        data: {
            labels: ['Financial', 'Attendance', 'Internals', 'CGPA'],
            datasets: [{
                label: 'Risk Factors',
                data: [student.financial_risk, student.attendance_risk, student.internals_risk, student.cgpa_risk],
                backgroundColor: 'rgba(220, 53, 69, 0.2)',
                borderColor: 'rgba(220, 53, 69, 1)',
                borderWidth: 2,
                pointBackgroundColor: 'rgba(220, 53, 69, 1)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                title: {
                    display: true,
                    text: 'Risk Factor Analysis',
                    color: document.body.classList.contains('dark-mode') ? '#fff' : '#666'
                }
            },
            scales: {
                r: {
                    suggestedMin: 0,
                    suggestedMax: 10,
                    grid: {
                        color: document.body.classList.contains('dark-mode') ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.1)'
                    },
                    angleLines: {
                        color: document.body.classList.contains('dark-mode') ? 'rgba(255, 255, 255, 0.2)' : 'rgba(0, 0, 0, 0.1)'
                    },
                    pointLabels: {
                        color: document.body.classList.contains('dark-mode') ? '#fff' : '#666'
                    }
                }
            }
        }
    });
}

function createDoughnutChart(student) {
    const ctx = document.getElementById('riskCompositionChart').getContext('2d');
    const totalRisk = student.financial_risk + student.attendance_risk + student.internals_risk + student.cgpa_risk;
    const data = totalRisk > 0 ? [
        (student.financial_risk / totalRisk) * 100, (student.attendance_risk / totalRisk) * 100,
        (student.internals_risk / totalRisk) * 100, (student.cgpa_risk / totalRisk) * 100
    ] : [0, 0, 0, 0];
    if (doughnutChartInstance) { doughnutChartInstance.destroy(); }
    doughnutChartInstance = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Financial', 'Attendance', 'Internals', 'CGPA'],
            datasets: [{
                label: 'Risk Composition',
                data: data,
                backgroundColor: ['#0d6efd', '#ffc107', '#6c757d', '#198754'],
                borderColor: document.body.classList.contains('dark-mode') ? '#2a2a2a' : '#fff',
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        color: document.body.classList.contains('dark-mode') ? '#fff' : '#666'
                    }
                },
                title: {
                    display: true,
                    text: 'Risk Score Composition (%)',
                    color: document.body.classList.contains('dark-mode') ? '#fff' : '#666'
                }
            }
        }
    });
}

// Function to handle the filtering of students based on risk category
function setupRiskFilterButtons(isMentor) {
    const cardsContainer = isMentor ? document.getElementById('mentor-stats-cards') : document.getElementById('stats-cards');
    if (!cardsContainer) return;
    
    const filterButtons = cardsContainer.querySelectorAll('.stat-card');
    const riskFilterSelect = document.getElementById('riskFilter');

    filterButtons.forEach(button => {
        button.addEventListener('click', () => {
            const filterValue = button.dataset.risk;

            // Update the dropdown to reflect the selected filter
            if (riskFilterSelect) {
                riskFilterSelect.value = filterValue;
            }

            // Render the student grid with the new filter
            renderStudentGrid(filterValue);
        });
    });
}