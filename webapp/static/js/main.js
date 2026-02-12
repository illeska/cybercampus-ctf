/* --------------------------------------------------------
   CyberCampus CTF
-------------------------------------------------------- */

document.addEventListener("DOMContentLoaded", () => {
  initAnimations();
  initRipple();
  initFlashMessages();
});

// 1. ANIMATION D'APPARITION (Simp)
function initAnimations() {
  const elements = document.querySelectorAll(
    '.challenge-card, .home-block, form, .card, .section-large, .animated-title, .challenge-info-block, .action-card'
  );
  
  elements.forEach((el, index) => {
    el.style.opacity = '0';
    el.style.transform = 'translateY(15px)';
    el.style.transition = 'opacity 0.6s ease-out, transform 0.6s ease-out';
    
    setTimeout(() => {
      el.style.opacity = '1';
      el.style.transform = 'translateY(0)';
    }, index * 50 + 50);
  });
}

// 2. EFFET RIPPLE
function initRipple() {
  document.addEventListener("click", e => {
    const btn = e.target.closest(".btn, .nav-btn, .challenge-btn, .primary-btn, .submit-btn, .env-btn, .back-btn-modern");
    if (!btn) return;

    const ripple = document.createElement("span");
    ripple.className = "ripple";
    
    const rect = btn.getBoundingClientRect();
    const size = Math.max(rect.width, rect.height);
    const x = e.clientX - rect.left - size / 2;
    const y = e.clientY - rect.top - size / 2;

    ripple.style.width = ripple.style.height = `${size}px`;
    ripple.style.left = `${x}px`;
    ripple.style.top = `${y}px`;
    
    btn.appendChild(ripple);
    setTimeout(() => ripple.remove(), 600);
  });
}

// 3. NOTIFICATIONS FLASH
function initFlashMessages() {
  const errors = document.querySelectorAll(".error");
  const container = document.querySelector(".flash-container") || createFlashContainer();

  errors.forEach(err => {
    if (err.textContent.trim()) {
      showFlash(err.textContent, "danger");
      err.style.display = 'none'; 
    }
  });

  setTimeout(() => {
    document.querySelectorAll(".flash").forEach(f => dismissFlash(f));
  }, 4000);
}

function createFlashContainer() {
  const div = document.createElement("div");
  div.className = "flash-container top";
  document.body.prepend(div);
  return div;
}

function showFlash(msg, type = "info") {
  const container = document.querySelector(".flash-container") || createFlashContainer();
  const notif = document.createElement("div");
  notif.className = `flash ${type}`;
  notif.textContent = msg;
  notif.style.opacity = "0";
  notif.style.transform = "translateY(-10px)";
  notif.style.transition = "all 0.3s ease";
  
  container.appendChild(notif);
  
  requestAnimationFrame(() => {
    notif.style.opacity = "1";
    notif.style.transform = "translateY(0)";
  });

  setTimeout(() => dismissFlash(notif), 4000);
}

function dismissFlash(el) {
  el.style.opacity = "0";
  el.style.transform = "translateY(-10px)";
  setTimeout(() => el.remove(), 300);
}

const style = document.createElement("style");
style.textContent = `
  .ripple {
    position: absolute; border-radius: 50%;
    background: rgba(255,255,255,0.3);
    transform: scale(0); animation: rippleAnim 0.6s linear;
    pointer-events: none;
  }
  @keyframes rippleAnim { to { transform: scale(4); opacity: 0; } }
  .btn, .nav-btn, .challenge-btn, .primary-btn, .back-btn-modern {
    position: relative; overflow: hidden;
  }
`;
document.head.appendChild(style);


function togglePasswordVisibility(fieldId, button) {
  const passwordInput = document.getElementById(fieldId);
  const eyeSlash = button.querySelector('.eye-slash');
  const eyePupil = button.querySelector('.eye-pupil');

  if (passwordInput.type === 'password') {
    passwordInput.type = 'text';
    eyeSlash.style.display = 'block';
    eyePupil.style.opacity = '0.5';
    button.classList.add('active');
  } else {
    passwordInput.type = 'password';
    eyeSlash.style.display = 'none';
    eyePupil.style.opacity = '1';
    button.classList.remove('active');
  }
}

function closeBanner() {
    const banner = document.getElementById('beta-banner');
    if (banner) {
        banner.style.opacity = '0';
        banner.style.transform = 'translateY(-100%)';
        sessionStorage.setItem('beta-closed', 'true'); // S'en souvient pour la session
        setTimeout(() => banner.style.display = 'none', 300);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (sessionStorage.getItem('beta-closed') === 'true') {
        const banner = document.getElementById('beta-banner');
        if (banner) banner.style.display = 'none';
    }
});