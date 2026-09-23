/* ============================================================
   ISPGAYA Homepage — JavaScript
   Navigation, Carousel, Counters, Tabs, Scroll Animations
   ============================================================ */

document.addEventListener('DOMContentLoaded', () => {

  // ─── STICKY NAV + TOP BAR HIDE ────────────────────────────
  const mainNav = document.getElementById('main-nav');
  const topBar = document.getElementById('top-bar');
  let lastScrollY = 0;

  window.addEventListener('scroll', () => {
    const currentScrollY = window.scrollY;


    // Nav & Top Bar: add scrolled class
    if (mainNav) {
      if (currentScrollY > 60) {
        mainNav.classList.add('scrolled');
        if (topBar) topBar.classList.add('scrolled');
      } else {
        mainNav.classList.remove('scrolled');
        if (topBar) topBar.classList.remove('scrolled');
      }
    }

    lastScrollY = currentScrollY;
  }, { passive: true });


  // ─── HAMBURGER MENU (MOBILE) ──────────────────────────────
  const hamburger = document.getElementById('hamburger');
  const navMenu = document.getElementById('nav-menu');

  if (hamburger && navMenu) {
    hamburger.addEventListener('click', () => {
      hamburger.classList.toggle('active');
      navMenu.classList.toggle('active');
      document.body.style.overflow = navMenu.classList.contains('active') ? 'hidden' : '';
    });

    // Mobile dropdown toggle
    const navItems = navMenu.querySelectorAll('.main-nav__item');
    navItems.forEach(item => {
      const link = item.querySelector('.main-nav__link');
      if (link && item.querySelector('.main-nav__dropdown')) {
        link.addEventListener('click', (e) => {
          if (window.innerWidth <= 768) {
            e.preventDefault();
            // Close all others
            navItems.forEach(other => {
              if (other !== item) other.classList.remove('open');
            });
            item.classList.toggle('open');
          }
        });
      }
    });
  }


  // ─── HIGHLIGHTS CAROUSEL ──────────────────────────────────
  const track = document.getElementById('highlights-track');
  const dotsContainer = document.getElementById('highlights-dots');
  const prevBtn = document.querySelector('.highlights__arrow--prev');
  const nextBtn = document.querySelector('.highlights__arrow--next');

  if (track && dotsContainer) {
    let currentSlide = 0;
    const slides = track.querySelectorAll('.highlight-slide');
    const dots = dotsContainer.querySelectorAll('.highlights__dot');
    const totalSlides = slides.length;

    function goToSlide(index) {
      if (index < 0) index = totalSlides - 1;
      if (index >= totalSlides) index = 0;
      currentSlide = index;
      track.style.transform = `translateX(-${currentSlide * 100}%)`;
      dots.forEach((dot, i) => dot.classList.toggle('active', i === currentSlide));
    }

    if (prevBtn) prevBtn.addEventListener('click', () => goToSlide(currentSlide - 1));
    if (nextBtn) nextBtn.addEventListener('click', () => goToSlide(currentSlide + 1));

    dots.forEach(dot => {
      dot.addEventListener('click', () => goToSlide(parseInt(dot.dataset.slide)));
    });

    // Auto-play
    let autoPlay = setInterval(() => goToSlide(currentSlide + 1), 6000);

    // Pause on hover
    const carousel = document.querySelector('.highlights__carousel');
    if (carousel) {
      carousel.addEventListener('mouseenter', () => clearInterval(autoPlay));
      carousel.addEventListener('mouseleave', () => {
        autoPlay = setInterval(() => goToSlide(currentSlide + 1), 6000);
      });
    }
  }


  // ─── TESTIMONIALS CAROUSEL ────────────────────────────────
  const testimonialCards = document.querySelectorAll('.testimonial-card');
  const testimonialDots = document.querySelectorAll('.testimonials__dot');

  if (testimonialCards.length > 0 && testimonialDots.length > 0) {
    let currentTestimonial = 0;

    function showTestimonial(index) {
      testimonialCards.forEach((card, i) => card.classList.toggle('active', i === index));
      testimonialDots.forEach((dot, i) => dot.classList.toggle('active', i === index));
      currentTestimonial = index;
    }

    testimonialDots.forEach(dot => {
      dot.addEventListener('click', () => showTestimonial(parseInt(dot.dataset.testimonial)));
    });

    // Auto-rotate
    setInterval(() => {
      showTestimonial((currentTestimonial + 1) % testimonialCards.length);
    }, 7000);
  }


  // ─── NEWS/EVENTS TABS ─────────────────────────────────────
  const tabs = document.querySelectorAll('.news-events__tab');
  const panels = document.querySelectorAll('.news-events__panel');

  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      tabs.forEach(t => t.classList.remove('active'));
      panels.forEach(p => p.classList.remove('active'));
      tab.classList.add('active');
      const target = document.getElementById(tab.dataset.tab);
      if (target) target.classList.add('active');
    });
  });


  // ─── COUNTER ANIMATION ────────────────────────────────────
  function animateCounter(el) {
    const target = parseInt(el.dataset.target);
    const prefix = el.dataset.prefix || '';
    const suffix = el.dataset.suffix || '';
    const duration = 2000;
    const start = performance.now();

    function update(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // Ease out cubic
      const ease = 1 - Math.pow(1 - progress, 3);
      const current = Math.round(target * ease);

      // Build display string
      let display = '';
      if (prefix) display += prefix;
      if (target >= 1000) {
        display += current >= 1000 ? (current / 1000).toFixed(1) + 'k' : current;
      } else {
        display += current;
      }
      if (suffix) display += suffix;
      el.textContent = display;

      if (progress < 1) {
        requestAnimationFrame(update);
      }
    }

    requestAnimationFrame(update);
  }


  // ─── SCROLL ANIMATIONS (Intersection Observer) ────────────
  const observerOptions = { threshold: 0.15, rootMargin: '0px 0px -50px 0px' };

  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');

        // Trigger counter animation for stat cards
        if (entry.target.classList.contains('stat-card')) {
          const counter = entry.target.querySelector('.stat-card__number');
          if (counter && !counter.dataset.animated) {
            counter.dataset.animated = 'true';
            animateCounter(counter);
          }
        }

        observer.unobserve(entry.target);
      }
    });
  }, observerOptions);

  document.querySelectorAll('.fade-in').forEach(el => observer.observe(el));
  document.querySelectorAll('.stat-card').forEach(el => observer.observe(el));


  // ─── HERO PARTICLES ───────────────────────────────────────
  const particlesContainer = document.getElementById('hero-particles');
  if (particlesContainer) {
    for (let i = 0; i < 30; i++) {
      const particle = document.createElement('div');
      particle.className = 'hero__particle';
      particle.style.left = Math.random() * 100 + '%';
      particle.style.animationDuration = (Math.random() * 15 + 10) + 's';
      particle.style.animationDelay = Math.random() * 10 + 's';
      particle.style.width = (Math.random() * 3 + 2) + 'px';
      particle.style.height = particle.style.width;
      particlesContainer.appendChild(particle);
    }
  }


  // ─── SMOOTH SCROLL FOR ANCHOR LINKS ───────────────────────
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      const targetEl = document.querySelector(targetId);
      if (targetEl) {
        e.preventDefault();
        targetEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
        // Close mobile menu if open
        if (navMenu && navMenu.classList.contains('active')) {
          hamburger.classList.remove('active');
          navMenu.classList.remove('active');
          document.body.style.overflow = '';
        }
      }
    });
  });

});
