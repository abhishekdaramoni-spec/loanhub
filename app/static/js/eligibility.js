document.addEventListener('DOMContentLoaded', () => {
    const eligibilityForm = document.getElementById('eligibilityForm');
    const resultCard = document.getElementById('eligibilityResult');
    const csrfTokenMeta = document.querySelector('meta[name="csrf-token"]');

    if (eligibilityForm) {
        eligibilityForm.addEventListener('submit', (e) => {
            e.preventDefault();

            const age = document.getElementById('age').value;
            const income = document.getElementById('income').value;
            const creditScore = document.getElementById('credit_score').value;
            const existingEmi = document.getElementById('existing_emi').value;
            const employment = document.getElementById('employment').value;
            const token = csrfTokenMeta ? csrfTokenMeta.getAttribute('content') : '';

            // Loading spinner
            const submitBtn = eligibilityForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Calculating...';

            fetch('/eligibility', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': token
                },
                body: JSON.stringify({
                    age: age,
                    income: income,
                    credit_score: creditScore,
                    existing_emi: existingEmi,
                    employment: employment
                })
            })
            .then(res => res.json())
            .then(data => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;

                resultCard.style.display = 'block';
                resultCard.scrollIntoView({ behavior: 'smooth' });

                const badge = document.getElementById('eligibilityBadge');
                const reasonText = document.getElementById('eligibilityReason');
                const detailsSection = document.getElementById('eligibilityDetails');
                const recommendList = document.getElementById('recommendedLoansList');

                recommendList.innerHTML = '';

                if (data.eligible) {
                    badge.className = 'badge bg-success p-2 fs-5 mb-3';
                    badge.innerText = 'CONGRATULATIONS! YOU ARE ELIGIBLE';
                    reasonText.innerText = `Based on your credit profile, you have strong loan eligibility.`;
                    
                    detailsSection.innerHTML = `
                        <div class="row text-center mt-3 g-3">
                            <div class="col-md-6">
                                <div class="p-3 border rounded glass-panel">
                                    <span class="text-muted d-block small">Maximum Loan Amount Offered</span>
                                    <span class="fs-3 fw-bold text-primary">INR ${data.max_loan_amount.toLocaleString('en-IN')}</span>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="p-3 border rounded glass-panel">
                                    <span class="text-muted d-block small">Maximum EMI Allowed</span>
                                    <span class="fs-3 fw-bold text-success">INR ${data.max_emi.toLocaleString('en-IN')} / mo</span>
                                </div>
                            </div>
                            <div class="col-md-12">
                                <span class="text-muted d-block small">Interest Rate offered starting from</span>
                                <span class="fs-4 fw-bold text-gradient">${data.interest_rate_offered}% p.a.</span>
                            </div>
                        </div>
                    `;

                    // Populate recommendations
                    if (data.recommended_loans && data.recommended_loans.length > 0) {
                        recommendList.innerHTML = '<h5 class="mt-4 mb-3">Recommended Loans for You</h5>';
                        data.recommended_loans.forEach(loan => {
                            const card = `
                                <div class="card glass-card p-3 mb-2 d-flex flex-row justify-content-between align-items-center">
                                    <div>
                                        <h6 class="mb-0 fw-bold">${loan.name}</h6>
                                        <small class="text-muted">Interest rate: starting from ${loan.min_rate}% | Approval time: ${loan.approval_time}</small>
                                    </div>
                                    <a href="/loans/${loan.slug}" class="btn btn-sm btn-primary">Apply Now</a>
                                </div>
                            `;
                            recommendList.insertAdjacentHTML('beforeend', card);
                        });
                    }
                } else {
                    badge.className = 'badge bg-danger p-2 fs-5 mb-3';
                    badge.innerText = 'LOAN INELIGIBLE';
                    reasonText.innerText = data.reason;
                    detailsSection.innerHTML = '';
                }
            })
            .catch(err => {
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalText;
                console.error(err);
                window.showToast('Something went wrong during checking.', 'danger');
            });
        });
    }
});
