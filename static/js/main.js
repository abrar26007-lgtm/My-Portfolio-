'use strict';

// ── Hamburger menu ──
const hamburger = document.getElementById('hamburger');
const mobileMenu = document.getElementById('mobileMenu');
if (hamburger && mobileMenu) {
  hamburger.addEventListener('click', () => {
    mobileMenu.classList.toggle('open');
  }, { passive: true });
  document.querySelectorAll('.mobile-link').forEach(l =>
    l.addEventListener('click', () => mobileMenu.classList.remove('open'), { passive: true })
  );
}

// ── Active nav on scroll (throttled) ──
const sections = document.querySelectorAll('section[id]');
const navLinks = document.querySelectorAll('.nav-links a');
let scrollTicking = false;
window.addEventListener('scroll', () => {
  if (!scrollTicking) {
    requestAnimationFrame(() => {
      const y = window.scrollY + 100;
      sections.forEach(sec => {
        if (y >= sec.offsetTop && y < sec.offsetTop + sec.offsetHeight) {
          navLinks.forEach(a => { a.style.color = ''; a.style.background = ''; });
          const active = document.querySelector(`.nav-links a[href="#${sec.id}"]`);
          if (active) active.style.color = 'var(--accent)';
        }
      });
      scrollTicking = false;
    });
    scrollTicking = true;
  }
}, { passive: true });

// ── Contact form ──
const contactForm = document.getElementById('contactForm');
if (contactForm) {
  contactForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = document.getElementById('sendBtn');
    const msg = document.getElementById('formMsg');
    btn.textContent = 'Sending...';
    btn.disabled = true;
    try {
      // Get reCAPTCHA token
      const siteKey = document.querySelector('script[src*="recaptcha"]')
        ?.src?.match(/render=([^&]+)/)?.[1];
      if (siteKey && window.grecaptcha) {
        const token = await grecaptcha.execute(siteKey, { action: 'contact' });
        document.getElementById('recaptchaToken').value = token;
      }
      const res = await fetch('/contact', {
        method: 'POST',
        body: new FormData(contactForm)
      });
      const data = await res.json();
      msg.textContent = data.msg;
      msg.className = 'form-msg ' + (data.success ? 'success' : 'error');
      if (data.success) contactForm.reset();
    } catch {
      msg.textContent = 'Something went wrong. Try again.';
      msg.className = 'form-msg error';
    }
    btn.textContent = 'Send Message ✉';
    btn.disabled = false;
  });
}

// ── Scroll reveal (IntersectionObserver) ──
if ('IntersectionObserver' in window) {
  const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach(e => {
      if (e.isIntersecting) {
        e.target.style.opacity = '1';
        e.target.style.transform = 'translateY(0)';
        revealObserver.unobserve(e.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

  document.querySelectorAll('.skill-card, .project-card, .ach-card, .timeline-card').forEach(el => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(16px)';
    el.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
    el.style.willChange = 'opacity, transform';
    revealObserver.observe(el);
  });
}
