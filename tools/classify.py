#!/usr/bin/env python3
"""classify.py: sort employer mail into categories by rule, at zero tokens (Ascend 2.0, M1).

Most mail about a job application says one of a handful of things in a handful of ways, and the
sender is usually an applicant tracking system. Rules catch those for free. Only mail that still
looks job-related after every rule has missed is marked `needs_llm`, so a batch goes to Claude and
receipts, newsletters and family mail never cost a token.

Email content is UNTRUSTED DATA (reference/untrusted-content-policy.md). This module only matches
patterns against it. Nothing in a message is ever executed, fetched or followed.
"""

import re

CATEGORIES = ["acknowledgement", "rejection", "info-request", "assessment", "interview-invite",
              "status-update", "recruiter-inbound", "job-alert", "other"]

# Senders that only ever write about hiring: applicant tracking systems and assessment vendors.
ATS_DOMAINS = {"greenhouse.io", "greenhouse-mail.io", "lever.co", "ashbyhq.com", "myworkday.com",
               "workday.com", "smartrecruiters.com", "workable.com", "icims.com", "jobvite.com",
               "taleo.net", "successfactors.com", "bamboohr.com", "recruitee.com", "rippling.com",
               "codesignal.com", "hackerrank.com", "codility.com", "coderpad.io"}
ALERT_SENDERS = {"jobalerts-noreply@linkedin.com", "jobs-noreply@linkedin.com", "alert@indeed.com",
                 "alerts@indeed.com", "noreply@glassdoor.com", "alerts@glassdoor.com",
                 "alert@ziprecruiter.com"}


def _rx(*parts):
    return re.compile("|".join(parts), re.I)


# Checked in this order; the first category with a hit wins. Rejection comes first because most
# rejections open with a thank-you that would otherwise read as an acknowledgement.
RULES = [
    ("rejection", _rx(r"\bunfortunately\b", r"not (be )?moving forward", r"will not be (moving|proceeding)",
                      r"not be proceeding", r"decided to (move forward|proceed|pursue|go) with (other|another)",
                      r"pursue other candidates", r"\bother candidates\b", r"\bnot (been )?selected\b",
                      r"position has been filled", r"regret to inform", r"no longer (being )?considered")),
    ("assessment", _rx(r"\bassessment\b", r"coding challenge", r"take[- ]home", r"hackerrank", r"codesignal",
                       r"codility", r"coderpad", r"online test", r"technical exercise")),
    ("interview-invite", _rx(r"schedule (your |an |a |the )?(interview|call|time|chat)", r"share your availability",
                             r"send (me )?your availability", r"availability (for|using)", r"are you available",
                             r"calendly", r"/meeting/", r"book a time", r"invite you to interview",
                             r"interview invitation", r"phone screen",
                             r"set up (a|an) (technical |video |phone )?(interview|call)", r"video interview",
                             r"move you forward")),
    ("info-request", _rx(r"additional information", r"complete your application", r"action required",
                         r"verify your (email|identity)", r"questionnaire", r"remaining questions",
                         r"please (provide|complete|answer|confirm|respond)", r"could you (please )?provide")),
    ("acknowledgement", _rx(r"thank(s| you) for (applying|your application|your interest|submitting)",
                            r"received your application", r"application (has been |was )?(received|submitted)")),
    ("status-update", _rx(r"status of your application", r"application (status|update)", r"under review",
                          r"still reviewing", r"moved to the .{0,40}(stage|review)", r"update on your .{0,30}application")),
    ("recruiter-inbound", _rx(r"came across your (profile|work|background)", r"reaching out", r"your background",
                              r"role we're opening", r"open to (a )?(quick )?(chat|conversation|call|new roles)",
                              r"opportunity with", r"(great|strong) fit")),
]
# Interview wording only counts in a sentence that is not conditional ("If selected, a recruiter
# will contact you to schedule a call" is an acknowledgement's promise, not an invitation).
CONDITIONAL = re.compile(r"\b(if|should|once|when)\b", re.I)
JOBBY = re.compile(r"\b(application|applied|candidate|interview|recruit\w*|hiring|position|job offer)\b", re.I)


def sender(msg):
    m = re.search(r"[\w.+-]+@[\w.-]+", msg.get("from", "") or "")
    return m.group(0).lower() if m else ""


def sender_domain(msg):
    s = sender(msg)
    return s.split("@", 1)[1] if "@" in s else ""


def is_ats(msg):
    d = sender_domain(msg)
    return any(d == a or d.endswith("." + a) for a in ATS_DOMAINS)


def _text(msg):
    return f"{msg.get('subject', '') or ''}\n{msg.get('body_excerpt', '') or ''}"


def _interview_hit(text, rx):
    for sentence in re.split(r"(?<=[.!?\n])\s+", text):
        hit = rx.search(sentence)
        if hit and not CONDITIONAL.search(sentence[:hit.start()]):
            return hit
    return None


def classify_message(msg):
    """Rule verdict for one message: {category, confidence, rule, needs_llm}."""
    text = _text(msg)
    ats = is_ats(msg)
    if sender(msg) in ALERT_SENDERS:
        return {"category": "job-alert", "confidence": 0.95, "rule": "sender:alert", "needs_llm": False}
    for category, rx in RULES:
        if category == "recruiter-inbound" and ats:
            continue
        hit = _interview_hit(text, rx) if category == "interview-invite" else rx.search(text)
        if hit:
            return {"category": category, "confidence": 0.95 if ats else 0.85,
                    "rule": f"{category}:{hit.group(0).lower()[:40]}", "needs_llm": False}
    return {"category": "other", "confidence": 0.5, "rule": "none",
            "needs_llm": bool(ats or JOBBY.search(text))}
