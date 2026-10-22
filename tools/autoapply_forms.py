"""autoapply_forms.py: fill one Greenhouse, Ashby or Lever application form (Ascend 2.0 automatic apply).

Called by tools/autoapply.py, never on its own. Needs Playwright with Chromium; Playwright is imported
inside fill() so the rules below stay importable (and tested) without it.

  fill(url, answers, resume_pdf, submit, shots_dir) -> {"result", "reason", "unfilled", "shots"}

result is "submitted" (the confirmation was seen), "filled" (a dry run: nothing clicked and the résumé not
attached, since attaching can upload it), "stopped" (nothing
was sent: a visible CAPTCHA, a sign-in page, a page off the allowed hosts, a required question the user's
answers do not cover, or an error shown on submit) or "unclear" (submit was clicked and no confirmation
appeared).

Answers come only from the user: the profile's contact fields, data/apply-answers.json and the answer bank
(data/answer-bank.json), whose entries match a form's question by the user's own wording. Essays, legal
agreements and company-specific questions are never answered from anything else, so a form that requires
one stops. Nothing here tries to get past a bot check: a visible challenge stops the job, and an invisible
one is left to decide on its own.
"""

import re
from pathlib import Path
from urllib.parse import urlparse

ALLOWED_HOSTS = {"job-boards.greenhouse.io", "boards.greenhouse.io", "jobs.ashbyhq.com", "jobs.lever.co"}
NAV_TIMEOUT_MS = 45000
SETTLE_MS = 2500

# Order matters: sponsorship questions mention work, and "Preferred name" is a first name.
RULES = [
    (r"\bsponsor", "sponsorship"),
    (r"authori[sz]ed to work|work authori[sz]ation|eligible to work|right to work|legally (able|permitted) to work", "work_authorization"),
    (r"^(legal )?first name|^preferred (first )?name|^given name", "first_name"),
    (r"^(legal )?(last|family) name|^surname", "last_name"),
    (r"^(full |legal )?name$", "name"),
    (r"\be-?mail\b", "email"),
    (r"\bphone\b|\bmobile\b", "phone"),
    (r"linkedin", "linkedin"),
    (r"github", "github"),
    (r"^(personal |other )?website|portfolio", "website"),
    (r"\bcity\b", "city"),
    (r"postal code|zip ?code|\bzip\b", "postal_code"),
    (r"^(current )?location\b|where are you (currently )?(located|based)", "location"),
    (r"current (company|employer)", "current_company"),
    (r"salary|compensation expectation|expected (compensation|pay)|desired pay", "salary_expectation"),
    (r"start date|earliest .*start|when can you start|available to start|notice period", "start_date"),
    (r"^country\b", "country"),
    (r"how did you (hear|find|learn)|where did you (hear|find|learn)", "how_heard"),
    (r"\brelocat", "relocation"),
    (r"^gender\b|gender identity", "gender"),
    (r"hispanic|latin[oa]", "hispanic"),
    (r"^race\b|\bethnicit", "race"),
    (r"veteran", "veteran"),
    (r"disabilit", "disability"),
    (r"pronoun", "pronouns"),
]
CONFIRM = re.compile(r"thank you for (applying|your application|your interest)|thanks for applying|"
                     r"application (has been |was )?(successfully )?(submitted|received)|"
                     r"we('ve| have) received your application", re.I)
SUBMIT_ERROR = re.compile(r"flagged as (possible )?spam|could not be submitted|there was an (error|issue)|"
                          r"please (fill|complete|correct)|is required|try again", re.I)
CHALLENGE = re.compile(r"recaptcha.*bframe|hcaptcha.*challenge|challenges\.cloudflare\.com|turnstile|"
                       r"challenge expires|captcha challenge", re.I)


AUTH_WITHOUT_SPONSOR = re.compile(r"(authori[sz]ed|eligible|legally (able|permitted)) to work.*without .*sponsor", re.I)


def _yes_no(v):
    if isinstance(v, bool):
        return v
    w = norm(v).split()
    return {"yes": True, "no": False}.get(w[0]) if w else None


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", str(s or "").lower())).strip()


def _label(s):
    return re.sub(r"\s+", " ", re.sub(r"[*✱]", " ", str(s or ""))).strip()


def answer_for(label, answers):
    """The user's own answer to a form question, or None."""
    text = norm(_label(label))
    if not text:
        return None
    for b in answers.get("_bank") or []:
        q = norm(b.get("question"))
        if q and (q == text or (len(q) >= 12 and q in text)):
            return str(b.get("answer"))
    # "Authorized to work ... without sponsorship" asks both at once: Yes only when the user is authorized
    # and needs no sponsorship. The sponsorship rule alone would answer it backwards.
    if AUTH_WITHOUT_SPONSOR.search(text):
        auth, spon = _yes_no(answers.get("work_authorization")), _yes_no(answers.get("sponsorship"))
        if auth is False or spon is True:
            return "No"
        return "Yes" if auth is True and spon is False else None
    name = str(answers.get("name") or "").split()
    derived = {"first_name": name[0] if name else None, "last_name": name[-1] if len(name) > 1 else None}
    for rx, key in RULES:
        if re.search(rx, text):
            v = answers.get(key, derived.get(key))
            if isinstance(v, bool):
                v = "Yes" if v else "No"
            return None if v in (None, "") else str(v)
    return None


def pick(answer, options):
    """The option that says the user's answer, or None. Never a guess between two."""
    a = norm(answer)
    opts = [(o, norm(o)) for o in options if norm(o)]
    exact = [o for o, n in opts if n == a]
    if exact:
        return exact[0]
    if a in ("yes", "no"):
        first = [o for o, n in opts if n.split()[0] == a]
        return first[0] if len(first) == 1 else None
    pref = [o for o, n in opts if n.startswith(a + " ") or a.startswith(n + " ")]
    return pref[0] if len(pref) == 1 else None


COLLECT = r"""
() => {
  const txt = el => (el ? (el.innerText || el.textContent || '') : '').replace(/\s+/g, ' ').trim();
  const vis = el => { const r = el.getBoundingClientRect(), s = getComputedStyle(el);
                      return s.visibility !== 'hidden' && s.display !== 'none' && r.width >= 4 && r.height >= 4 && s.opacity !== '0'; };
  const box = el => el.closest('.application-question, [class*="fieldEntry"], fieldset, [role=radiogroup], [role=group], .field, .form-group, [class*="question"]');
  const qText = c => { if (!c) return ''; const l = c.querySelector('.application-label, legend, label:not(:has(input)), label');
                       return txt(l); };
  const labelOf = el => {
    if (el.id) { const l = document.querySelector(`label[for="${CSS.escape(el.id)}"]`); if (l) return txt(l); }
    const lb = el.getAttribute('aria-labelledby');
    if (lb) { const t = lb.split(/\s+/).map(i => txt(document.getElementById(i))).join(' ').trim(); if (t) return t; }
    if (el.getAttribute('aria-label')) return el.getAttribute('aria-label');
    const q = qText(box(el)); if (q) return q;
    const w = el.closest('label'); if (w) return txt(w);
    return el.placeholder || '';
  };
  // A required mark can be in the text, in a class, or drawn by CSS (Ashby's red asterisk is ::after).
  const marked = l => !!l && ([l, ...l.querySelectorAll('*')].some(e => /required/i.test(e.className && e.className.baseVal !== undefined ? e.className.baseVal : e.className || ''))
                     || [l, ...l.querySelectorAll('*')].some(e => ['::after', '::before'].some(p => /[*✱]/.test(getComputedStyle(e, p).content || ''))));
  const labelEl = el => (el.id && document.querySelector(`label[for="${CSS.escape(el.id)}"]`)) ||
                        (box(el) && box(el).querySelector('.application-label, legend, label')) || el.closest('label');
  const required = (el, label) => !!(el.required || el.getAttribute('aria-required') === 'true' || /[*✱]/.test(label) || marked(labelEl(el)));
  const out = []; let n = 0; const groups = new Set();
  const mark = el => { const id = 'q' + (n++); el.setAttribute('data-ascend', id); return id; };
  for (const el of document.querySelectorAll('input, select, textarea')) {
    const type = (el.type || '').toLowerCase();
    if (['hidden', 'submit', 'button', 'search', 'password', 'image', 'reset'].includes(type)) continue;
    if (/recaptcha|h-captcha|cf-turnstile/i.test(el.name || el.id)) continue;
    if (type === 'file') { const label = labelOf(el);
      out.push({id: mark(el), kind: 'file', label, required: required(el, label), name: el.name || '', elid: el.id || ''}); continue; }
    // A combobox's own input can be a couple of pixels wide (react-select): judge it by its control.
    const shown = el.getAttribute('role') === 'combobox' ? vis(el.closest('[class*="control"], [class*="container"]') || el.parentElement) : vis(el);
    if (!shown && type !== 'radio' && type !== 'checkbox') continue;
    // Ashby keeps a hidden checkbox behind its Yes / No buttons: the buttons are the question.
    const yesNo = c => c && [...c.querySelectorAll('button')].some(b => /^(yes|no)$/i.test(txt(b)) && vis(b));
    if ((type === 'checkbox' || type === 'radio') && !vis(el) && yesNo(box(el))) continue;
    if (type === 'radio' || type === 'checkbox') {
      const c = box(el); const key = (el.name || '') + '|' + (c ? (c.dataset.ascendBox || (c.dataset.ascendBox = 'b' + n)) : '');
      if (groups.has(key)) continue; groups.add(key);
      const members = [...document.querySelectorAll('input[type="' + type + '"]')].filter(x => (x.name || '') === (el.name || '') && box(x) === c);
      const id = mark(el);
      const options = members.map((m, i) => { m.setAttribute('data-ascend-opt', id + '-' + i); return txt(m.closest('label')) || m.value; });
      let label = members.length > 1 ? (qText(c) || labelOf(el)) : labelOf(el);
      out.push({id, kind: type, label, options, required: members.some(m => required(m, label)), name: el.name || '', elid: el.id || ''});
      continue;
    }
    const label = labelOf(el);
    const kind = el.tagName === 'SELECT' ? 'select' : (el.getAttribute('role') === 'combobox' ? 'combobox' : 'text');
    out.push({id: mark(el), kind, label, required: required(el, label), name: el.name || '', elid: el.id || '',
              options: kind === 'select' ? [...el.options].map(o => o.text) : undefined});
  }
  const btnBoxes = new Set();
  for (const b of document.querySelectorAll('button')) {
    if (!/^(yes|no)$/i.test(txt(b)) || !vis(b)) continue;
    const c = box(b) || b.parentElement.parentElement; if (!c || btnBoxes.has(c)) continue; btnBoxes.add(c);
    const id = 'q' + (n++); c.setAttribute('data-ascend', id);
    const btns = [...c.querySelectorAll('button')].filter(x => vis(x));
    btns.forEach((x, i) => x.setAttribute('data-ascend-opt', id + '-' + i));
    const label = qText(c);
    out.push({id, kind: 'buttons', label, options: btns.map(txt), required: /[*✱]/.test(label) || marked(c.querySelector('label, legend, .application-label'))});
  }
  return out;
}
"""

STATE = r"""
() => {
  const vis = el => { const r = el.getBoundingClientRect(), s = getComputedStyle(el);
                      return s.visibility !== 'hidden' && s.display !== 'none' && r.width >= 100 && r.height >= 100 && r.bottom > 0 && r.top > -500; };
  const challenge = [...document.querySelectorAll('iframe')].some(f => vis(f) && CH.test((f.src || '') + ' ' + (f.title || '')));
  const password = [...document.querySelectorAll('input[type=password]')].some(p => p.offsetParent !== null);
  const invalid = [...document.querySelectorAll('input:invalid, select:invalid, textarea:invalid')].length;
  return {challenge, password, invalid, text: (document.body.innerText || '').slice(0, 20000), url: location.href};
}
""".replace("CH.test", "new RegExp(" + repr(CHALLENGE.pattern) + ", 'i').test")


def _act(page, q, ans):
    sel = f'[data-ascend="{q["id"]}"]'
    kind = q["kind"]
    if kind == "text":
        page.locator(sel).fill(ans)
        return True
    if kind == "select":
        choice = pick(ans, q.get("options") or [])
        if choice:
            page.locator(sel).select_option(label=choice)
        return bool(choice)
    if kind in ("radio", "checkbox", "buttons"):
        opts = q.get("options") or []
        if kind == "checkbox" and len(opts) == 1:
            if norm(ans) in ("yes", "true", "i agree", "agree"):
                page.locator(f'[data-ascend-opt="{q["id"]}-0"]').check(force=True)
                return True
            return False
        choice = pick(ans, opts)
        if choice is None:
            return False
        target = page.locator(f'[data-ascend-opt="{q["id"]}-{opts.index(choice)}"]')
        if kind == "buttons":
            target.click()
        else:
            target.check(force=True)
        return True
    if kind == "combobox":
        box = page.locator(sel)
        box.click()
        page.wait_for_timeout(400)
        for typed in ("", ans.split()[0] if ans.split() else ans):
            if typed:
                box.fill(typed)
                page.wait_for_timeout(500)
            options = page.locator('[role="option"]:visible')
            texts = [t.strip() for t in options.all_inner_texts()]
            choice = pick(ans, texts)
            if choice:
                options.nth(texts.index(choice)).click()
                return True
        box.press("Escape")
        return False
    return False


def _shot(page, shots, name, out):
    if not shots:
        return
    p = Path(shots) / name
    try:
        page.screenshot(path=str(p), full_page=True)
        out["shots"].append(str(p))
    except Exception:
        pass


def _fill(page, url, answers, resume, submit, shots, hosts, timeout):
    out = {"result": "stopped", "reason": "", "unfilled": [], "shots": [], "uploaded": False}
    page.goto(url, wait_until="domcontentloaded", timeout=NAV_TIMEOUT_MS)
    page.wait_for_timeout(SETTLE_MS)
    host = urlparse(page.url).hostname or ""
    if host not in hosts:
        out["reason"] = f"the application page is on {host}, not on the job board: apply on the company's site"
        return out
    st = page.evaluate(STATE)
    if st["password"]:
        out["reason"] = "the application asks you to sign in"
        return out
    if st["challenge"]:
        out["reason"] = "a CAPTCHA is showing"
        return out
    before = bool(CONFIRM.search(st["text"]))
    for q in page.evaluate(COLLECT):
        label = _label(q.get("label")) or q.get("name") or "an unlabeled field"
        if q["kind"] == "file":
            if re.search(r"resume|\bcv\b", f'{q.get("label")} {q.get("name")} {q.get("elid")}', re.I):
                if submit:          # attaching can upload the file before any submit: a dry run sends nothing
                    page.set_input_files(f'[data-ascend="{q["id"]}"]', resume)
                    out["uploaded"] = True
            elif q["required"]:
                out["unfilled"].append(label)
            continue
        ans = answer_for(q.get("label"), answers)
        if ans is None:
            if q["required"]:
                out["unfilled"].append(label)
            continue
        try:
            done = _act(page, q, ans)
        except Exception:
            done = False
        if not done and q["required"]:
            out["unfilled"].append(label)
    _shot(page, shots, "filled.png", out)
    if out["unfilled"]:
        out["reason"] = "questions your saved answers do not cover: " + "; ".join(out["unfilled"][:8])
        return out
    if not submit:
        out["result"] = "filled"
        return out
    button = page.locator("button:visible, input[type=submit]:visible").filter(
        has_text=re.compile(r"submit( your)?( application)?$", re.I))
    if button.count() == 0:
        button = page.locator('input[type=submit]:visible, button[type=submit]:visible')
    if button.count() == 0:
        out["reason"] = "no submit button found"
        return out
    start = page.url
    button.first.click()
    for _ in range(int(timeout * 2)):
        page.wait_for_timeout(500)
        try:
            st = page.evaluate(STATE)
        except Exception:       # the page is navigating
            continue
        moved = st["url"] != start and re.search(r"confirm|thank|success|submitted", st["url"], re.I)
        if moved or (CONFIRM.search(st["text"]) and not before):
            out["result"] = "submitted"
            _shot(page, shots, "confirmation.png", out)
            return out
        if st["challenge"]:
            out["reason"] = "a CAPTCHA appeared on submit"
            _shot(page, shots, "challenge.png", out)
            return out
    st = page.evaluate(STATE)
    err = SUBMIT_ERROR.search(st["text"])
    _shot(page, shots, "after-submit.png", out)
    if st["invalid"] and st["url"] == start:     # the browser refuses to send a form with an empty required field
        out["reason"] = f"the browser blocked the submit: {st['invalid']} required field(s) still empty"
        return out
    if err:
        out["reason"] = f"the form showed an error after submit: \"{st['text'][max(0, err.start() - 60):err.end() + 60].strip()}\""
        return out
    out["result"] = "unclear"
    out["reason"] = f"no confirmation within {timeout} seconds of submit"
    return out


def fill(url, answers, resume, submit, shots, hosts=None, timeout=30, headless=True):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        try:
            page = browser.new_context().new_page()     # a fresh context: no cookies kept between jobs
            return _fill(page, url, answers, resume, submit, shots, hosts or ALLOWED_HOSTS, timeout)
        finally:
            browser.close()
