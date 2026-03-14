/**
 * VULNERABLE APPLICATION DISCLAIMER
 * Bottom sheet warning for security training environment
 */

(function() {
    'use strict';

    const DISCLAIMER_KEY = 'vulnbank_disclaimer_acknowledged';

    // Check if user already acknowledged
    if (localStorage.getItem(DISCLAIMER_KEY)) {
        return;
    }

    // Create bottom sheet disclaimer
    function createDisclaimer() {
        const sheet = document.createElement('div');
        sheet.id = 'vuln-disclaimer';
        sheet.innerHTML = `
            <div class="vuln-disclaimer-backdrop"></div>
            <div class="vuln-disclaimer-sheet" role="dialog" aria-labelledby="disclaimer-title">
                <div class="vuln-disclaimer-handle" aria-hidden="true"></div>
                <div class="vuln-disclaimer-content">
                    <div class="vuln-disclaimer-header">
                        <div class="vuln-disclaimer-icon">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path>
                                <line x1="12" y1="9" x2="12" y2="13"></line>
                                <line x1="12" y1="17" x2="12.01" y2="17"></line>
                            </svg>
                        </div>
                        <h3 id="disclaimer-title"> Heads up!</h3>
                        <button class="vuln-disclaimer-close" aria-label="Close" onclick="dismissVulnDisclaimer()">
                            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <line x1="18" y1="6" x2="6" y2="18"></line>
                                <line x1="6" y1="6" x2="18" y2="18"></line>
                            </svg>
                        </button>
                    </div>
                    <div class="vuln-disclaimer-body">
                        <p>This isn't a real bank. VulnBank was built with intentional security flaws for learning and practice.</p>
                        <p class="vuln-disclaimer-subtext">You'll find things like XSS, CSRF, SQL injection, and broken authentication—all on purpose.</p>
                        <p class="vuln-disclaimer-warning">Don't use any real passwords or personal info here.</p>
                    </div>
                    <div class="vuln-disclaimer-actions">
                        <button id="disclaimer-acknowledge" class="vuln-disclaimer-btn vuln-disclaimer-btn-primary">Got it</button>
                        <button onclick="dismissVulnDisclaimer()" class="vuln-disclaimer-btn vuln-disclaimer-btn-secondary">Remind me later</button>
                    </div>
                </div>
            </div>
        `;

        // Add styles
        const style = document.createElement('style');
        style.textContent = `
            #vuln-disclaimer {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                z-index: 99999;
                pointer-events: none;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            }
            .vuln-disclaimer-backdrop {
                position: absolute;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0, 0, 0, 0.4);
                backdrop-filter: blur(2px);
                opacity: 0;
                transition: opacity 0.3s ease;
                pointer-events: auto;
            }
            .vuln-disclaimer-sheet {
                position: absolute;
                bottom: 0;
                left: 0;
                right: 0;
                background: var(--bg, #1a1f2e);
                border-radius: 20px 20px 0 0;
                box-shadow: 0 -4px 24px rgba(0, 0, 0, 0.2);
                transform: translateY(100%);
                transition: transform 0.3s ease;
                pointer-events: auto;
                max-width: 600px;
                margin: 0 auto;
            }
            #vuln-disclaimer.visible .vuln-disclaimer-backdrop {
                opacity: 1;
            }
            #vuln-disclaimer.visible .vuln-disclaimer-sheet {
                transform: translateY(0);
            }
            .vuln-disclaimer-handle {
                width: 40px;
                height: 4px;
                background: var(--border, rgba(255,255,255,0.2));
                border-radius: 2px;
                margin: 8px auto;
            }
            .vuln-disclaimer-content {
                padding: 0 1.5rem 1.5rem;
            }
            .vuln-disclaimer-header {
                display: flex;
                align-items: flex-start;
                gap: 1rem;
                margin-bottom: 1rem;
            }
            .vuln-disclaimer-icon {
                flex-shrink: 0;
                width: 40px;
                height: 40px;
                background: rgba(0, 123, 255, 0.15);
                border-radius: 10px;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            .vuln-disclaimer-icon svg {
                width: 22px;
                height: 22px;
                color: #007BFF;
            }
            .vuln-disclaimer-header h3 {
                flex: 1;
                margin: 0;
                font-size: 1rem;
                font-weight: 600;
                color: var(--text-1, #e0e6ed);
            }
            .vuln-disclaimer-close {
                flex-shrink: 0;
                width: 28px;
                height: 28px;
                background: transparent;
                border: none;
                color: var(--text-3, rgba(255,255,255,0.5));
                cursor: pointer;
                border-radius: 6px;
                display: flex;
                align-items: center;
                justify-content: center;
                transition: background 0.2s;
            }
            .vuln-disclaimer-close:hover {
                background: rgba(255,255,255,0.1);
            }
            .vuln-disclaimer-body {
                color: var(--text-2, rgba(255,255,255,0.7));
                font-size: 0.875rem;
                line-height: 1.5;
            }
            .vuln-disclaimer-body p {
                margin: 0 0 0.75rem;
            }
            .vuln-disclaimer-subtext {
                opacity: 0.8;
            }
            .vuln-disclaimer-warning {
                background: rgba(255, 107, 107, 0.12);
                border-left: 3px solid #ff6b6b;
                padding: 0.75rem;
                border-radius: 6px;
                margin: 0;
            }
            .vuln-disclaimer-actions {
                display: flex;
                gap: 0.75rem;
                margin-top: 1.25rem;
            }
            .vuln-disclaimer-btn {
                flex: 1;
                padding: 0.75rem 1rem;
                font-size: 0.875rem;
                font-weight: 600;
                border-radius: 10px;
                cursor: pointer;
                transition: all 0.2s;
                border: none;
            }
            .vuln-disclaimer-btn-primary {
                background: #007BFF;
                color: #fff;
            }
            .vuln-disclaimer-btn-primary:hover {
                background: #0062CC;
            }
            .vuln-disclaimer-btn-secondary {
                background: transparent;
                color: var(--text-2, rgba(255,255,255,0.7));
                border: 1px solid var(--border, rgba(255,255,255,0.15));
            }
            .vuln-disclaimer-btn-secondary:hover {
                background: rgba(255,255,255,0.08);
            }
            @media (max-width: 600px) {
                .vuln-disclaimer-sheet {
                    border-radius: 16px 16px 0 0;
                }
                .vuln-disclaimer-content {
                    padding: 0 1rem 1rem;
                }
                .vuln-disclaimer-actions {
                    flex-direction: column;
                }
            }
        `;

        document.head.appendChild(style);
        document.body.appendChild(sheet);

        // Trigger animation
        requestAnimationFrame(() => {
            sheet.classList.add('visible');
        });

        // Handle acknowledge button
        document.getElementById('disclaimer-acknowledge').addEventListener('click', function() {
            localStorage.setItem(DISCLAIMER_KEY, 'true');
            dismissVulnDisclaimer();
        });
    }

    // Global dismiss function
    window.dismissVulnDisclaimer = function() {
        const sheet = document.getElementById('vuln-disclaimer');
        if (sheet) {
            sheet.classList.remove('visible');
            setTimeout(() => sheet.remove(), 300);
        }
    };

    // Wait for DOM to be ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', createDisclaimer);
    } else {
        createDisclaimer();
    }
})();
