(() => {
  const menuButton = document.querySelector(".mobile-menu");
  const nav = document.querySelector(".main-nav");
  menuButton?.addEventListener("click", () => {
    const open = nav.classList.toggle("open");
    menuButton.setAttribute("aria-expanded", String(open));
  });
  nav?.querySelectorAll("a").forEach(link => link.addEventListener("click", () => {
    nav.classList.remove("open");
    menuButton?.setAttribute("aria-expanded", "false");
  }));

  const themeButton = document.querySelector(".theme-toggle");
  const savedTheme = (() => {
    try { return localStorage.getItem("pocketso-theme"); } catch { return null; }
  })();
  if (savedTheme === "light") document.body.classList.add("light");
  function updateThemeLabel() {
    const light = document.body.classList.contains("light");
    themeButton?.setAttribute("aria-label", light ? "Switch to dark theme" : "Switch to light theme");
    themeButton?.setAttribute("title", light ? "Switch to dark theme" : "Switch to light theme");
    const glyph = themeButton?.querySelector(".theme-glyph");
    if (glyph) glyph.textContent = light ? "☼" : "◐";
  }
  themeButton?.addEventListener("click", () => {
    document.body.classList.toggle("light");
    try { localStorage.setItem("pocketso-theme", document.body.classList.contains("light") ? "light" : "dark"); } catch {}
    updateThemeLabel();
  });
  updateThemeLabel();
  const year = document.getElementById("year");
  if (year) year.textContent = new Date().getFullYear();
})();
