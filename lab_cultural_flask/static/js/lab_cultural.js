/* ============================================================
   Laboratório Cultural — JavaScript
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {

    // ---- Sticky Navigation ----
    const mainNav = document.querySelector('.main-nav');
    const topBar = document.querySelector('.top-bar');
    let topBarHeight = topBar ? topBar.offsetHeight : 0;

    function handleScroll() {
        if (window.scrollY > 20) {
            mainNav?.classList.add('scrolled');
            topBar?.classList.add('scrolled');
        } else {
            mainNav?.classList.remove('scrolled');
            topBar?.classList.remove('scrolled');
        }
    }
    window.addEventListener('scroll', handleScroll, { passive: true });
    handleScroll();

    // ---- Mobile Menu ----
    const hamburger = document.querySelector('.main-nav__hamburger');
    const mobileMenu = document.querySelector('.main-nav__menu');

    if (hamburger && mobileMenu) {
        hamburger.addEventListener('click', () => {
            hamburger.classList.toggle('active');
            mobileMenu.classList.toggle('active');
            document.body.style.overflow = mobileMenu.classList.contains('active') ? 'hidden' : '';
        });
    }

    // ---- Scroll Animations (Intersection Observer) ----
    const fadeObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('visible');
                fadeObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.08, rootMargin: '0px 0px -60px 0px' });

    document.querySelectorAll('.fade-in').forEach(el => fadeObserver.observe(el));

    // ---- Hero Particles (apenas na página principal do Lab. Cultural) ----
    const particlesContainer = document.querySelector('.lc-hero__particles');
    if (particlesContainer) {
        for (let i = 0; i < 20; i++) {
            const p = document.createElement('div');
            p.style.cssText = `
        position:absolute;
        width:${Math.random() * 4 + 1}px;
        height:${Math.random() * 4 + 1}px;
        background:rgba(255,255,255,${Math.random() * 0.15 + 0.05});
        border-radius:50%;
        left:${Math.random() * 100}%;
        animation:lc-float ${Math.random() * 15 + 8}s linear infinite;
        animation-delay:${Math.random() * 10}s;
      `;
            particlesContainer.appendChild(p);
        }

        const style = document.createElement('style');
        style.textContent = `
      @keyframes lc-float {
        0% { transform: translateY(100vh) rotate(0deg); opacity:0; }
        10% { opacity:1; }
        90% { opacity:1; }
        100% { transform: translateY(-10vh) rotate(360deg); opacity:0; }
      }
    `;
        document.head.appendChild(style);
    }

    // ---- Auto-dismiss Flash Messages ----
    function dismissFlash(flash) {
        if (!flash) return;
        flash.style.transition = 'opacity 0.5s, transform 0.5s';
        flash.style.opacity = '0';
        flash.style.transform = 'translateX(40px)';
        setTimeout(() => {
            if (flash.parentNode) flash.remove();
        }, 500);
    }

    const flashes = document.querySelectorAll('.flash, .bo-flash');
    flashes.forEach(flash => {
        // Auto dismiss after 5s
        setTimeout(() => dismissFlash(flash), 5000);
        
        // Ensure close button works if present (already has onclick in some templates, but let's be safe)
        const closeBtn = flash.querySelector('.flash-close');
        if (closeBtn) {
            closeBtn.onclick = (e) => {
                e.preventDefault();
                dismissFlash(flash);
            };
        }
    });

    // ---- Backoffice Sidebar Toggle (mobile) ----
    const sidebarToggle = document.getElementById('sidebar-toggle');
    const sidebar = document.querySelector('.bo-sidebar');
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', () => {
            sidebar.style.display = sidebar.style.display === 'flex' ? 'none' : 'flex';
        });
    }

    // ---- Smooth Scroll ----
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            const targetId = this.getAttribute('href');
            if (targetId === '#') return;
            const target = document.querySelector(targetId);
            if (target) {
                e.preventDefault();
                const offset = 90;
                const top = target.getBoundingClientRect().top + window.scrollY - offset;
                window.scrollTo({ top, behavior: 'smooth' });
            }
        });
    });

    // ---- Validação de formulários do frontoffice (filtros) ----
    const filtrosForm = document.getElementById('filtros-form');
    if (filtrosForm) {
        const dateInputs = filtrosForm.querySelectorAll('input[type="date"]');
        dateInputs.forEach(input => {
            input.addEventListener('change', () => {
                filtrosForm.submit();
            });
        });
    }

});
