/* ============================================
   ISPGaya Website - Main JavaScript
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {
  
  // ---- Sticky Navigation ----
  const mainNav = document.querySelector('.main-nav');
  const topBar = document.querySelector('.top-bar');
  let topBarHeight = topBar ? topBar.offsetHeight : 0;
  
  function handleScroll() {
    if (window.scrollY > topBarHeight + 20) {
      mainNav.classList.add('scrolled');
      topBar?.classList.add('hidden');
    } else {
      mainNav.classList.remove('scrolled');
      topBar?.classList.remove('hidden');
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
  
  // ---- Mobile Dropdown Toggle ----
  const navItems = document.querySelectorAll('.main-nav__item');
  
  navItems.forEach(item => {
    const link = item.querySelector('.main-nav__link');
    if (link && window.innerWidth <= 768) {
      link.addEventListener('click', (e) => {
        if (item.querySelector('.main-nav__dropdown')) {
          e.preventDefault();
          item.classList.toggle('open');
        }
      });
    }
  });
  
  // Re-bind on resize
  window.addEventListener('resize', () => {
    if (window.innerWidth > 768) {
      navItems.forEach(item => item.classList.remove('open'));
      if (mobileMenu) mobileMenu.classList.remove('active');
      if (hamburger) hamburger.classList.remove('active');
      document.body.style.overflow = '';
    }
  });
  
  // ---- Highlights Carousel ----
  const highlightsTrack = document.querySelector('.highlights__track');
  const highlightSlides = document.querySelectorAll('.highlight-slide');
  const highlightDots = document.querySelectorAll('.highlights__dot');
  const prevArrow = document.querySelector('.highlights__arrow--prev');
  const nextArrow = document.querySelector('.highlights__arrow--next');
  let currentHighlight = 0;
  let highlightInterval;
  
  function goToHighlight(index) {
    if (!highlightsTrack || highlightSlides.length === 0) return;
    currentHighlight = (index + highlightSlides.length) % highlightSlides.length;
    highlightsTrack.style.transform = `translateX(-${currentHighlight * 100}%)`;
    highlightDots.forEach((dot, i) => {
      dot.classList.toggle('active', i === currentHighlight);
    });
  }
  
  function startHighlightAutoplay() {
    highlightInterval = setInterval(() => {
      goToHighlight(currentHighlight + 1);
    }, 5000);
  }
  
  function stopHighlightAutoplay() {
    clearInterval(highlightInterval);
  }
  
  if (highlightSlides.length > 0) {
    highlightDots.forEach((dot, i) => {
      dot.addEventListener('click', () => {
        stopHighlightAutoplay();
        goToHighlight(i);
        startHighlightAutoplay();
      });
    });
    
    if (prevArrow) {
      prevArrow.addEventListener('click', () => {
        stopHighlightAutoplay();
        goToHighlight(currentHighlight - 1);
        startHighlightAutoplay();
      });
    }
    
    if (nextArrow) {
      nextArrow.addEventListener('click', () => {
        stopHighlightAutoplay();
        goToHighlight(currentHighlight + 1);
        startHighlightAutoplay();
      });
    }
    
    startHighlightAutoplay();
  }
  
  // ---- Counter Animation ----
  const statCards = document.querySelectorAll('.stat-card__number');
  let countersAnimated = false;
  
  function animateCounters() {
    if (countersAnimated) return;
    
    statCards.forEach(card => {
      const target = parseInt(card.getAttribute('data-target'));
      const prefix = card.getAttribute('data-prefix') || '';
      const suffix = card.getAttribute('data-suffix') || '';
      const duration = 2000;
      const startTime = performance.now();
      
      function update(currentTime) {
        const elapsed = currentTime - startTime;
        const progress = Math.min(elapsed / duration, 1);
        
        // Easing function
        const eased = 1 - Math.pow(1 - progress, 4);
        const current = Math.floor(eased * target);
        
        card.innerHTML = `${prefix ? `<span class="prefix">${prefix}</span>` : ''}${current}${suffix ? `<span class="suffix">${suffix}</span>` : ''}`;
        
        if (progress < 1) {
          requestAnimationFrame(update);
        }
      }
      
      requestAnimationFrame(update);
    });
    
    countersAnimated = true;
  }
  
  // ---- Scroll-triggered Animations ----
  const observerOptions = {
    root: null,
    rootMargin: '0px 0px -80px 0px',
    threshold: 0.1
  };
  
  const fadeObserver = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        entry.target.classList.add('visible');
        fadeObserver.unobserve(entry.target);
      }
    });
  }, observerOptions);
  
  document.querySelectorAll('.fade-in, .fade-in-left, .fade-in-right').forEach(el => {
    fadeObserver.observe(el);
  });
  
  // Stats counter observer
  const statsSection = document.querySelector('.stats');
  if (statsSection) {
    const statsObserver = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          animateCounters();
          statsObserver.unobserve(entry.target);
        }
      });
    }, { threshold: 0.3 });
    
    statsObserver.observe(statsSection);
  }
  
  // ---- News/Events Tabs ----
  const tabs = document.querySelectorAll('.news-events__tab');
  const panels = document.querySelectorAll('.news-events__panel');
  
  tabs.forEach(tab => {
    tab.addEventListener('click', () => {
      const target = tab.getAttribute('data-tab');
      
      tabs.forEach(t => t.classList.remove('active'));
      panels.forEach(p => p.classList.remove('active'));
      
      tab.classList.add('active');
      document.getElementById(target)?.classList.add('active');
    });
  });
  
  // ---- Testimonials Carousel ----
  const testimonialCards = document.querySelectorAll('.testimonial-card');
  const testimonialDots = document.querySelectorAll('.testimonials__dot');
  let currentTestimonial = 0;
  let testimonialInterval;
  
  function goToTestimonial(index) {
    if (testimonialCards.length === 0) return;
    currentTestimonial = (index + testimonialCards.length) % testimonialCards.length;
    
    testimonialCards.forEach((card, i) => {
      card.style.display = i === currentTestimonial ? 'block' : 'none';
      card.style.opacity = i === currentTestimonial ? '1' : '0';
    });
    
    testimonialDots.forEach((dot, i) => {
      dot.classList.toggle('active', i === currentTestimonial);
    });
  }
  
  function startTestimonialAutoplay() {
    testimonialInterval = setInterval(() => {
      goToTestimonial(currentTestimonial + 1);
    }, 6000);
  }
  
  if (testimonialCards.length > 0) {
    goToTestimonial(0);
    
    testimonialDots.forEach((dot, i) => {
      dot.addEventListener('click', () => {
        clearInterval(testimonialInterval);
        goToTestimonial(i);
        startTestimonialAutoplay();
      });
    });
    
    startTestimonialAutoplay();
  }
  
  // ---- Hero Particles ----
  const particlesContainer = document.querySelector('.hero__particles');
  if (particlesContainer) {
    for (let i = 0; i < 25; i++) {
      const particle = document.createElement('div');
      particle.classList.add('hero__particle');
      particle.style.left = `${Math.random() * 100}%`;
      particle.style.width = `${Math.random() * 4 + 2}px`;
      particle.style.height = particle.style.width;
      particle.style.animationDuration = `${Math.random() * 15 + 10}s`;
      particle.style.animationDelay = `${Math.random() * 10}s`;
      particlesContainer.appendChild(particle);
    }
  }
  
  // ---- Smooth Scroll ----
  document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function (e) {
      const targetId = this.getAttribute('href');
      if (targetId === '#') return;
      
      e.preventDefault();
      const targetEl = document.querySelector(targetId);
      if (targetEl) {
        const offset = 80;
        const top = targetEl.getBoundingClientRect().top + window.scrollY - offset;
        window.scrollTo({ top, behavior: 'smooth' });
      }
    });
  });
  
});
