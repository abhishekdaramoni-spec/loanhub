document.addEventListener('DOMContentLoaded', () => {
    const loanAmountInput = document.getElementById('loanAmount');
    const interestRateInput = document.getElementById('interestRate');
    const loanTenureInput = document.getElementById('loanTenure');
    
    // Outputs
    const emiOutput = document.getElementById('monthlyEmi');
    const interestOutput = document.getElementById('totalInterest');
    const amountOutput = document.getElementById('totalAmount');
    
    const scheduleBody = document.getElementById('scheduleTableBody');
    const scheduleSection = document.getElementById('amortizationSection');
    
    let emiChart = null;

    const calculateEMI = () => {
        const principal = parseFloat(loanAmountInput.value);
        const annualRate = parseFloat(interestRateInput.value);
        const tenureMonths = parseInt(loanTenureInput.value);

        if (isNaN(principal) || isNaN(annualRate) || isNaN(tenureMonths) || principal <= 0 || annualRate <= 0 || tenureMonths <= 0) {
            return;
        }

        // Monthly Rate
        const r = (annualRate / 100) / 12;
        const n = tenureMonths;

        // Formula: P * r * (1+r)^n / ((1+r)^n - 1)
        const power = Math.pow(1 + r, n);
        const emi = (principal * r * power) / (power - 1);
        
        const totalAmount = emi * n;
        const totalInterest = totalAmount - principal;

        // Update Outputs
        emiOutput.innerText = emi.toLocaleString('en-IN', { maximumFractionDigits: 2, style: 'currency', currency: 'INR' });
        interestOutput.innerText = totalInterest.toLocaleString('en-IN', { maximumFractionDigits: 2, style: 'currency', currency: 'INR' });
        amountOutput.innerText = totalAmount.toLocaleString('en-IN', { maximumFractionDigits: 2, style: 'currency', currency: 'INR' });

        // Update Chart
        updateChart(principal, totalInterest);

        // Generate Schedule Table
        generateSchedule(principal, r, n, emi);
    };

    const updateChart = (principal, interest) => {
        const ctx = document.getElementById('emiChart').getContext('2d');
        
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        const labelColor = isDark ? '#F8FAFC' : '#2D3748';

        if (emiChart) {
            emiChart.destroy();
        }

        emiChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: ['Principal Amount', 'Total Interest'],
                datasets: [{
                    data: [principal, interest],
                    backgroundColor: ['#0056D2', '#00B894'],
                    borderWidth: 0
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            color: labelColor,
                            font: {
                                family: 'Poppins',
                                size: 12
                            }
                        }
                    }
                }
            }
        });
    };

    const generateSchedule = (principal, monthlyRate, tenure, emi) => {
        if (!scheduleBody) return;
        
        scheduleBody.innerHTML = '';
        let balance = principal;
        
        for (let i = 1; i <= tenure; i++) {
            const interest = balance * monthlyRate;
            let principalPaid = emi - interest;
            
            // Adjust balance offset on last month
            if (i === tenure) {
                principalPaid = balance;
                balance = 0;
            } else {
                balance -= principalPaid;
            }

            const row = `
                <tr>
                    <td>${i}</td>
                    <td>INR ${emi.toFixed(2)}</td>
                    <td>INR ${principalPaid.toFixed(2)}</td>
                    <td>INR ${interest.toFixed(2)}</td>
                    <td>INR ${Math.max(0, balance).toFixed(2)}</td>
                </tr>
            `;
            scheduleBody.insertAdjacentHTML('beforeend', row);
        }
        
        if (scheduleSection) {
            scheduleSection.style.display = 'block';
        }
    };

    // Event Listeners for Live updates
    if (loanAmountInput && interestRateInput && loanTenureInput) {
        [loanAmountInput, interestRateInput, loanTenureInput].forEach(input => {
            input.addEventListener('input', calculateEMI);
        });
        
        // Initial execution
        calculateEMI();
    }
});
