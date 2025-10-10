// Effet ripple sur clic
document.addEventListener("click", e => {
  if (!e.target.classList.contains("btn")) return;
  const btn = e.target;
  const ripple = document.createElement("span");
  ripple.className = "ripple";
  ripple.style.left = `${e.offsetX}px`;
  ripple.style.top = `${e.offsetY}px`;
  btn.appendChild(ripple);
  setTimeout(() => ripple.remove(), 600);
});

// Glow + fade global
window.addEventListener("load", () => {
  document.body.style.opacity = "1";
});

// Disparition automatique des flashs
setTimeout(() => {
  document.querySelectorAll(".flash").forEach(f => {
    f.style.transition = "opacity 0.8s";
    f.style.opacity = "0";
    setTimeout(() => f.remove(), 800);
  });
}, 3000);

// Style dynamique pour effet ripple
const style = document.createElement("style");
style.textContent = `
  .ripple {
    position:absolute;
    border-radius:50%;
    background:rgba(255,255,255,0.4);
    width:100px;height:100px;
    transform:scale(0);
    animation:rippleEffect 0.6s linear;
    pointer-events:none;
  }
  @keyframes rippleEffect {to{transform:scale(4);opacity:0;}}
`;
document.head.appendChild(style);

// --- Convertir les erreurs de formulaire en notifications flash ---
document.addEventListener("DOMContentLoaded", () => {
  const errors = document.querySelectorAll(".error");
  errors.forEach(err => {
    if (err.textContent.trim() !== "") {
      const notif = document.createElement("div");
      notif.className = "flash danger";
      notif.textContent = err.textContent;
      document.querySelector(".flash-container")?.appendChild(notif);
    }
  });
});

