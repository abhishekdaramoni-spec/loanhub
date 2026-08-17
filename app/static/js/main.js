document.addEventListener('DOMContentLoaded', () => {
    // -------------------------------------------------------------
    // 1. DARK/LIGHT THEME SWITCHER
    // -------------------------------------------------------------
    const themeToggle = document.getElementById('theme-toggle');
    const getPreferredTheme = () => {
        const storedTheme = localStorage.getItem('theme');
        if (storedTheme) return storedTheme;
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    };

    const setTheme = (theme) => {
        document.documentElement.setAttribute('data-theme', theme);
        localStorage.setItem('theme', theme);
        
        // Update theme toggle icon/text
        if (themeToggle) {
            const icon = themeToggle.querySelector('i');
            if (theme === 'dark') {
                icon.className = 'fas fa-sun text-warning';
            } else {
                icon.className = 'fas fa-moon';
            }
        }
    };

    // Initialize Theme
    setTheme(getPreferredTheme());

    if (themeToggle) {
        themeToggle.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme');
            setTheme(currentTheme === 'dark' ? 'light' : 'dark');
        });
    }

    // -------------------------------------------------------------
    // 2. ANIMATED STATISTICS COUNTERS
    // -------------------------------------------------------------
    const counters = document.querySelectorAll('.counter-value');
    if (counters.length > 0) {
        const animateCounters = () => {
            counters.forEach(counter => {
                const targetText = counter.getAttribute('data-target');
                const numericPart = parseFloat(targetText.replace(/[^\d.]/g, ''));
                const suffix = targetText.replace(/[\d.]/g, '');
                
                let count = 0;
                const speed = 100; // lower is faster
                const increment = numericPart / speed;
                
                const updateCount = () => {
                    count += increment;
                    if (count < numericPart) {
                        counter.innerText = (suffix === '%' || suffix.startsWith('.') ? count.toFixed(1) : Math.ceil(count)) + suffix;
                        setTimeout(updateCount, 15);
                    } else {
                        counter.innerText = targetText;
                    }
                };
                updateCount();
            });
        };

        // Trigger on visibility
        const observerOptions = { threshold: 0.5 };
        const counterObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    animateCounters();
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        const counterSection = document.querySelector('.statistics-section');
        if (counterSection) {
            counterObserver.observe(counterSection);
        } else {
            // Trigger immediately if section not found
            animateCounters();
        }
    }

    // -------------------------------------------------------------
    // 3. SCROLL REVEAL ANIMATIONS
    // -------------------------------------------------------------
    const revealElements = document.querySelectorAll('.reveal');
    if (revealElements.length > 0) {
        const revealObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('animate-fade-in-up');
                    entry.target.style.opacity = '1';
                }
            });
        }, { threshold: 0.1 });

        revealElements.forEach(el => {
            el.style.opacity = '0';
            revealObserver.observe(el);
        });
    }

    // -------------------------------------------------------------
    // 4. AUTO-SAVE FORM DRAFT
    // -------------------------------------------------------------
    const autoSaveForm = document.querySelector('.auto-save-form');
    const draftIndicator = document.querySelector('.draft-indicator');
    
    if (autoSaveForm) {
        const formId = autoSaveForm.getAttribute('id') || 'loansphere_form';
        
        // Load Draft
        const loadFormDraft = () => {
            const savedData = localStorage.getItem(`draft_${formId}`);
            if (savedData) {
                const data = JSON.parse(savedData);
                Object.keys(data).forEach(name => {
                    const field = autoSaveForm.querySelector(`[name="${name}"]`);
                    // Skip files and passwords
                    if (field && field.type !== 'file' && field.type !== 'password' && field.type !== 'hidden') {
                        field.value = data[name];
                    }
                });
                if (draftIndicator) {
                    draftIndicator.style.display = 'inline-flex';
                    draftIndicator.innerHTML = '<i class="fas fa-check-circle"></i> Loaded draft progress';
                }
            }
        };

        // Save Draft
        const saveFormDraft = () => {
            const formData = new FormData(autoSaveForm);
            const data = {};
            formData.forEach((value, key) => {
                // Ignore file objects, CSRF, and passwords
                if (!(value instanceof File) && key !== 'csrf_token' && !key.includes('password')) {
                    data[key] = value;
                }
            });
            localStorage.setItem(`draft_${formId}`, JSON.stringify(data));
            if (draftIndicator) {
                draftIndicator.style.display = 'inline-flex';
                draftIndicator.innerHTML = '<i class="fas fa-save"></i> Draft saved automatically';
            }
        };

        // Load immediately
        loadFormDraft();

        // Listen for changes
        autoSaveForm.addEventListener('input', () => {
            saveFormDraft();
        });

        // Clear draft on submit
        autoSaveForm.addEventListener('submit', () => {
            localStorage.removeItem(`draft_${formId}`);
        });
    }

    // -------------------------------------------------------------
    // 5. TOAST NOTIFICATION TRIGGER HELPER
    // -------------------------------------------------------------
    window.showToast = (message, type = 'success') => {
        const toastContainer = document.querySelector('.toast-container-custom');
        if (!toastContainer) return;

        const toastId = 'toast_' + Date.now();
        const iconClass = type === 'success' ? 'fa-check-circle text-success' : 
                          type === 'danger' ? 'fa-times-circle text-danger' : 
                          type === 'warning' ? 'fa-exclamation-triangle text-warning' : 'fa-info-circle text-info';

        const toastHtml = `
            <div id="${toastId}" class="toast align-items-center border-0 show glass-panel shadow" role="alert" aria-live="assertive" aria-atomic="true" style="margin-bottom:10px;">
                <div class="d-flex">
                    <div class="toast-body d-flex align-items-center gap-2">
                        <i class="fas ${iconClass} fs-5"></i>
                        <span>${message}</span>
                    </div>
                    <button type="button" class="btn-close me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
                </div>
            </div>
        `;

        toastContainer.insertAdjacentHTML('beforeend', toastHtml);
        const toastElement = document.getElementById(toastId);
        
        // Auto-remove after 4 seconds
        setTimeout(() => {
            if (toastElement) {
                toastElement.classList.remove('show');
                setTimeout(() => toastElement.remove(), 300);
            }
        }, 4000);

        // Bind close button manually
        toastElement.querySelector('.btn-close').addEventListener('click', () => {
            toastElement.remove();
        });
    };

    // -------------------------------------------------------------
    // 6. NOTIFICATION MARK AS READ HANDLER
    // -------------------------------------------------------------
    const notifBellItems = document.querySelectorAll('.notification-item-dismiss');
    const csrfTokenMeta = document.querySelector('meta[name="csrf-token"]');
    
    notifBellItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const notifId = item.getAttribute('data-id');
            const token = csrfTokenMeta ? csrfTokenMeta.getAttribute('content') : '';

            fetch(`/notifications/read/${notifId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': token
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    item.closest('.dropdown-item').style.opacity = '0.5';
                    // Update main unread counter if exists
                    const badge = document.querySelector('.navbar .badge');
                    if (badge) {
                        let currentCount = parseInt(badge.innerText);
                        if (currentCount > 1) {
                            badge.innerText = currentCount - 1;
                        } else {
                            badge.remove();
                        }
                    }
                }
            })
            .catch(err => console.error(err));
        });
    });

    // -------------------------------------------------------------
    // 7. LOAN FAVORITING TOGGLER
    // -------------------------------------------------------------
    const favButtons = document.querySelectorAll('.fav-toggle');
    favButtons.forEach(btn => {
        btn.addEventListener('click', (e) => {
            e.preventDefault();
            const loanId = btn.getAttribute('data-id');
            const token = csrfTokenMeta ? csrfTokenMeta.getAttribute('content') : '';

            fetch(`/favorites/toggle/${loanId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': token
                }
            })
            .then(res => res.json())
            .then(data => {
                if (data.success) {
                    const icon = btn.querySelector('i');
                    if (data.action === 'added') {
                        icon.className = 'fas fa-heart text-danger';
                        window.showToast('Added to favorites!', 'success');
                    } else {
                        icon.className = 'far fa-heart';
                        window.showToast('Removed from favorites.', 'info');
                    }
                }
            })
            .catch(err => console.error(err));
        });
    });
});
