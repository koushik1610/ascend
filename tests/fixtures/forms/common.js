// Fake ATS forms for tests/test_v2_autoapply_forms.py. Variants by query: captcha, essay, noconfirm, login.
const V = new URLSearchParams(location.search).get("variant") || "";
function addCaptcha() {
  const f = document.createElement("iframe");
  f.src = "about:blank#https://www.recaptcha.net/recaptcha/api2/bframe";
  f.title = "recaptcha challenge expires in two minutes";
  f.setAttribute("data-challenge", "recaptcha");
  f.style.cssText = "width:400px;height:400px;display:block";
  document.body.appendChild(f);
}
if (V === "captcha") addCaptcha();
if (V === "login") document.body.insertAdjacentHTML("afterbegin", '<label for="pw">Password</label><input id="pw" type="password">');
function values(form) {
  const out = {};
  form.querySelectorAll("input,select,textarea").forEach(el => {
    if (el.type === "file") out[el.name || el.id] = el.files.length ? el.files[0].name : "";
    else if (el.type === "radio" || el.type === "checkbox") { if (el.checked) out[el.name] = (out[el.name] ? out[el.name] + "|" : "") + el.value; }
    else out[el.name || el.id] = el.value;
  });
  document.querySelectorAll("[data-picked]").forEach(b => out[b.dataset.q] = b.dataset.picked);
  return out;
}
function missing(form) {
  const bad = [];
  form.querySelectorAll("[required]:not([data-skip])").forEach(el => {
    if (el.type === "radio") { if (!form.querySelector(`input[name="${el.name}"]:checked`)) bad.push(el.name); }
    else if (el.type === "file") { if (!el.files.length) bad.push(el.id || el.name); }
    else if (!el.value) bad.push(el.id || el.name);
  });
  document.querySelectorAll("[data-required-q]").forEach(c => { if (!c.dataset.picked) bad.push(c.dataset.q); });
  return [...new Set(bad)];
}
function submitTo(form, done) {
  form.addEventListener("submit", ev => {
    ev.preventDefault();
    const bad = missing(form);
    if (bad.length) { document.getElementById("err").textContent = "Please fill in: " + bad.join(", "); return; }
    if (V === "noconfirm") return;
    fetch("/record", {method: "POST", headers: {"Content-Type": "application/json"},
                      body: JSON.stringify({form: document.title, values: values(form)})}).then(done);
  });
}
// A combobox like Greenhouse's: type, then click an option.
function combobox(input, options) {
  const list = document.createElement("ul"); list.setAttribute("role", "listbox"); list.hidden = true;
  input.after(list);
  const show = () => {
    const q = input.value.toLowerCase();
    list.innerHTML = options.filter(o => o.toLowerCase().includes(q) || !q).map(o => `<li role="option">${o}</li>`).join("");
    list.hidden = false;
  };
  input.addEventListener("focus", show); input.addEventListener("input", show);
  list.addEventListener("click", ev => { const li = ev.target.closest("li"); if (!li) return; input.value = li.textContent; list.hidden = true; input.dataset.chosen = "1";
    const hidden = input.closest(".field").querySelector("input[data-skip]"); if (hidden && V !== "stuck") hidden.value = li.textContent; });
}
