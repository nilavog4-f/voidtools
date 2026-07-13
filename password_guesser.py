#!/usr/bin/env python3
"""
Password Guess Checker (CLI)
-----------------------------
Run this yourself, locally, in your own terminal:

    python3 password_guesser.py

Everything happens on your machine. Nothing is sent anywhere, saved to
disk, or logged. It never touches any real account, login page, or
service -- it only prints candidate guesses to your terminal so you can
compare them against your own password by eye.

Flow:
  1. You type in a few personal details -- the kind of stuff an attacker
     can find on social media in five minutes. Leave anything blank to skip.
  2. Optionally add more detail categories (family, places, hobbies, etc.)
  3. The script builds a list of realistic guesses mirroring real cracking
     wordlists: nicknames, leet substitutions, seasonal combos, keyboard
     patterns, natural-language phrases, special-char formulas, and more.
  4. It shows you ONE guess at a time. Press y+Enter if it matches your
     real password; press Enter (or n) to move on.
  5. A final result screen tells you how you fared and what to do next.
"""

import argparse
import os
import re
import sys
import time


# ─────────────────────────────────────────────────────────────────────────────
#  Terminal capability detection  (color + Unicode auto-downgrade)
# ─────────────────────────────────────────────────────────────────────────────

def _is_tty():
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


def _supports_color():
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("FORCE_COLOR") is not None:
        return True
    if not _is_tty():
        return False
    if sys.platform == "win32":
        try:
            import ctypes
            k32 = ctypes.windll.kernel32
            handle = k32.GetStdHandle(-11)
            mode = ctypes.c_uint32()
            if not k32.GetConsoleMode(handle, ctypes.byref(mode)):
                return False
            if not k32.SetConsoleMode(handle, mode.value | 0x0004):
                return False
        except Exception:
            return False
    return True


def _supports_unicode():
    enc = (getattr(sys.stdout, "encoding", None) or "").lower()
    if "utf" not in enc:
        return False
    try:
        "\u2554\u2550\u2588\u2713\u2717\u25b8\u25cf\u2502\u2500".encode(enc)
    except Exception:
        return False
    return True


COLOR   = _supports_color()
UNICODE = _supports_unicode()
ANIMATE = _is_tty() and os.environ.get("NO_ANIMATION") is None

_ANSI_RE = re.compile(r"\033\[[0-9;]*m")


def visible_len(s: str) -> int:
    """Length of s after stripping ANSI escape codes."""
    return len(_ANSI_RE.sub("", s))


def truncate_ansi(text: str, max_visible: int) -> str:
    """Truncate text to at most max_visible printable characters while
    keeping ANSI escape sequences intact (never slicing through one)."""
    result: list[str] = []
    vis = 0
    i   = 0
    while i < len(text):
        if text[i] == "\033" and i + 1 < len(text) and text[i + 1] == "[":
            # consume the whole escape sequence
            j = i + 2
            while j < len(text) and (text[j].isdigit() or text[j] == ";"):
                j += 1
            result.append(text[i : j + 1])   # include terminating letter
            i = j + 1
        else:
            if vis >= max_visible:
                break
            result.append(text[i])
            vis += 1
            i   += 1
    return "".join(result)


# ─────────────────────────────────────────────────────────────────────────────
#  ANSI color helpers
# ─────────────────────────────────────────────────────────────────────────────

def _c(code):
    return f"\033[{code}m" if COLOR else ""


RESET   = _c("0")
BOLD    = _c("1")
DIM     = _c("2")
ITALIC  = _c("3")

RED     = _c("91")
GREEN   = _c("92")
YELLOW  = _c("93")
BLUE    = _c("94")
MAGENTA = _c("95")
CYAN    = _c("96")
WHITE   = _c("97")
GRAY    = _c("90")
ORANGE  = _c("33")


# ─────────────────────────────────────────────────────────────────────────────
#  Box-drawing glyphs
# ─────────────────────────────────────────────────────────────────────────────

if UNICODE:
    TL, TR, BL, BR    = "\u2554", "\u2557", "\u255a", "\u255d"   # ╔ ╗ ╚ ╝
    H,  V             = "\u2550", "\u2551"                        # ═ ║
    ML, MR            = "\u2560", "\u2563"                        # ╠ ╣
    HTL, HTR, HBL, HBR = "\u250c","\u2510","\u2514","\u2518"     # ┌ ┐ └ ┘
    LH, LV            = "\u2500", "\u2502"                        # ─ │
    BLOCK, LIGHT_BLOCK = "\u2588", "\u2591"                       # █ ░
    MID_BLOCK         = "\u2593"                                  # ▓
    CHECK, CROSS      = "\u2713", "\u2717"                        # ✓ ✗
    ARROW, DOT, BULLET = "\u25b8", "\u25cf", "\u2022"             # ▸ ● •
    LOCK              = "\U0001f512"  if sys.platform != "win32" else "#"
else:
    TL, TR, BL, BR    = "+", "+", "+", "+"
    H,  V             = "=", "|"
    ML, MR            = "+", "+"
    HTL, HTR, HBL, HBR = "+","+","+","+"
    LH, LV            = "-", "|"
    BLOCK, LIGHT_BLOCK, MID_BLOCK = "#", ".", "+"
    CHECK, CROSS      = "v", "x"
    ARROW, DOT, BULLET = ">", "*", "-"
    LOCK              = "#"

WIDTH = 70


def style(text, *codes):
    if not COLOR:
        return text
    return f"{''.join(codes)}{text}{RESET}"


def rule(char=H, color=GRAY):
    print(style(char * WIDTH, color))


def thin_rule(color=GRAY):
    print(style(LH * WIDTH, color))


def box_top(color=CYAN, double=True):
    c = (TL, TR, H) if double else (HTL, HTR, LH)
    print(style(c[0] + c[2] * (WIDTH - 2) + c[1], color))


def box_bottom(color=CYAN, double=True):
    c = (BL, BR, H) if double else (HBL, HBR, LH)
    print(style(c[0] + c[2] * (WIDTH - 2) + c[1], color))


def box_mid(color=CYAN):
    print(style(ML + H * (WIDTH - 2) + MR, color))


def box_line(text="", color=CYAN, align="center", double=True):
    vc    = V if double else LV
    inner = WIDTH - 4                     # 2 border chars + 2 padding spaces
    vl    = visible_len(text)
    # ANSI-safe truncation — never slice through an escape sequence
    if vl > inner:
        text = truncate_ansi(text, inner)
        vl   = visible_len(text)

    pad_total = inner - vl
    if align == "center":
        left  = pad_total // 2
        right = pad_total - left
    elif align == "left":
        left, right = 0, pad_total
    else:  # right
        left, right = pad_total, 0

    border = style(vc, color)
    print(border + " " + " " * left + text + " " * right + " " + border)


def type_out(text, delay=0.010):
    if not ANIMATE:
        print(text)
        return
    for ch in text:
        sys.stdout.write(ch)
        sys.stdout.flush()
        time.sleep(delay)
    print()


def progress_bar(current, total, width=32):
    pct    = int(100 * current / total) if total else 100
    filled = int(width * current / total) if total else width
    if pct < 40:
        bar_color = CYAN
    elif pct < 75:
        bar_color = YELLOW
    else:
        bar_color = GREEN
    bar    = style(BLOCK * filled, bar_color) + style(LIGHT_BLOCK * (width - filled), GRAY)
    pct_s  = style(f"{pct:>3}%", BOLD, WHITE)
    nums   = style(f"{current:,}/{total:,}", DIM)
    return f"{bar}  {pct_s}  {nums}"


def spinner_frame(i: int) -> str:
    frames = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"] if UNICODE else ["|","/","-","\\"]
    return style(frames[i % len(frames)], CYAN, BOLD)


def banner():
    print()
    # Top decorative line
    if UNICODE:
        grad = [CYAN, CYAN, WHITE, WHITE, CYAN, CYAN]
        pieces = []
        seg = (WIDTH) // len(grad)
        for i, col in enumerate(grad):
            pieces.append(style("▓" * seg, col))
        print("  " + "".join(pieces))
    else:
        print(style("  " + "=" * WIDTH, CYAN))

    print()
    box_top(CYAN)
    box_line(color=CYAN)
    box_line(style(f"  {LOCK}  PASSWORD  GUESS  CHECKER  {LOCK}  ", BOLD, WHITE), color=CYAN)
    box_line(style("personal-detail attack simulator", DIM, CYAN), color=CYAN)
    box_line(color=CYAN)
    box_bottom(CYAN)
    print()

    checks = [
        ("100% local", "nothing transmitted, saved, or logged"),
        ("Realistic patterns", "same techniques real cracking tools use"),
        ("Human combinations", "names, dates, phrases, leet, symbols & more"),
    ]
    for label, desc in checks:
        l = style(f" {CHECK} ", GREEN, BOLD)
        lb = style(label, BOLD, WHITE)
        ds = style(f"  —  {desc}", DIM)
        type_out(f"  {l}{lb}{ds}", delay=0.006)
    print()


def section(title, color=MAGENTA):
    print()
    inner = f"  {ARROW}  {title}  "
    pad   = max(0, WIDTH - len(inner) - 2)
    if COLOR:
        print(f"  {style(f' {ARROW}  {title} ', BOLD, color)}  "
              + style(LH * pad, GRAY))
    else:
        print(f"  {ARROW} {title}")
        thin_rule(GRAY)


def subheading(text):
    print()
    print(f"  {style(DOT, CYAN)}  {style(text, BOLD, WHITE)}")
    print(style(f"  {'·' * (WIDTH - 4)}", GRAY))


# ─────────────────────────────────────────────────────────────────────────────
#  Guess generation
# ─────────────────────────────────────────────────────────────────────────────

LEET_MAP = {
    "a": ["a", "4", "@"],
    "b": ["b", "8"],
    "e": ["e", "3"],
    "i": ["i", "1", "!"],
    "l": ["l", "1"],
    "o": ["o", "0"],
    "s": ["s", "5", "$"],
    "t": ["t", "7"],
    "g": ["g", "9"],
    "z": ["z", "2"],
}

# Suffixes people actually append to make a simple word "complex"
COMMON_SUFFIXES = [
    "", "1", "2", "12", "123", "1234", "12345",
    "!", "!!", "!1", "!12", "!123",
    "1!", "1!!", "123!", "1234!",
    "01", "007", "99", "88", "69", "00", "786", "108", "420", "143",
    "@1", "@123", "#1", "#123", "#", "@",
    "2026", "2025", "2024", "2023", "2022", "2021", "2020",
    "4ever", "4life", "forever", "4u", "4me",
    "xo", "xx", "xoxo",
    "_1", "_123", ".1", ".123", "_", ".",
    "isme", "islife", "isking", "isqueen", "rocks", "rules",
]

COMMON_PREFIXES = [
    "", "the", "im", "its", "my", "i", "hey",
    "imy", "ilove", "ilovemy", "dear", "only",
]

# Human-natural word bridges used in compound passwords
BRIDGES = ["", "_", ".", "is", "my", "and", "4", "the", "n", "&"]

# Patterns humans think look "strong" because they use symbols
SPECIAL_WRAPPERS = [
    lambda w: f"{w}!",         lambda w: f"{w}!!",        lambda w: f"{w}@",
    lambda w: f"{w}#",         lambda w: f"{w}$",          lambda w: f"!{w}",
    lambda w: f"{w}@123",      lambda w: f"{w}!23",        lambda w: f"{w}_1",
    lambda w: f"{w}.1",        lambda w: f"_{w}_",         lambda w: f"{w}*",
    lambda w: f"{w}#1",        lambda w: f"#{w}1",         lambda w: f"{w}@1",
    lambda w: f"{w}@2024",     lambda w: f"{w}@2025",      lambda w: f"@{w}123",
    lambda w: f"{w}.123",      lambda w: f"{w}_123",       lambda w: f"123{w}",
    lambda w: f"{w}786",       lambda w: f"{w}143",        lambda w: f"{w}007",
    lambda w: f"[{w}]",        lambda w: f"({w})",         lambda w: f"{w}!@#",
]

# Keyboard walk patterns — attackers always try these
KEYBOARD_PATTERNS = [
    "qwerty", "qwerty1", "qwerty123", "qwerty!1",
    "qwertyuiop", "asdfgh", "asdfghjkl", "zxcvbn",
    "1q2w3e", "1q2w3e4r", "1qaz2wsx",
    "q1w2e3", "q1w2e3r4",
    "123abc", "abc123", "abc1234",
    "pass", "pass1", "pass123", "pass1234",
    "password", "password1", "password123", "p@ssw0rd",
    "letmein", "letmein1", "letmein123",
    "iloveyou", "iloveyou1",
    "welcome", "welcome1", "welcome123",
    "monkey", "monkey1", "monkey123",
    "dragon", "dragon1", "dragon123",
    "master", "master1", "master123",
    "111111", "222222", "123123", "321321",
    "000000", "696969", "121212",
]

# Seasonal + year combos (attackers know people love these)
CURRENT_YEAR   = 2024
SEASONS        = ["spring", "summer", "fall", "autumn", "winter"]
SEASON_YEARS   = [
    f"{s.capitalize()}{y}"
    for s in SEASONS
    for y in range(CURRENT_YEAR - 3, CURRENT_YEAR + 2)
]
SEASON_YEARS  += [
    f"{s.capitalize()}{str(y)[2:]}"
    for s in SEASONS
    for y in range(CURRENT_YEAR - 3, CURRENT_YEAR + 2)
]

# Months — used alone or combined
MONTHS = [
    "january","february","march","april","may","june",
    "july","august","september","october","november","december",
    "jan","feb","mar","apr","jun","jul","aug","sep","oct","nov","dec",
]

# Emotion/identity phrases attackers try
FILLER_PHRASES = [
    "iloveyou", "ihateyou", "imissyou", "foreveralone",
    "loveyou", "bestday", "mylife", "mybaby",
    "thebest", "number1", "numb3r1",
    "trustno1", "trust_no1",
]

def leet_variants(word: str, max_variants: int = 8) -> list[str]:
    lower    = word.lower()
    variants = [lower]
    seen     = {lower}
    for i, ch in enumerate(lower):
        if len(variants) >= max_variants:
            break
        for sub in LEET_MAP.get(ch, []):
            if sub == ch:
                continue
            swapped = lower[:i] + sub + lower[i + 1:]
            if swapped not in seen:
                seen.add(swapped)
                variants.append(swapped)
                if len(variants) >= max_variants:
                    break
    return variants


def capitalizations(word: str) -> list[str]:
    """Common capitalisation patterns humans use."""
    w = word.lower()
    variants = [w]
    if w:
        variants.append(w.capitalize())              # Title
        variants.append(w.upper())                   # ALL CAPS
        variants.append(w[0].upper() + w[1:])       # First
    if len(w) > 1:
        variants.append(w[:-1] + w[-1].upper())     # lasT
        # alternating: hElLo  (less common but real)
        alt = "".join(c.upper() if i % 2 == 0 else c for i, c in enumerate(w))
        variants.append(alt)
    return list(dict.fromkeys(variants))             # deduplicated, order preserved


def extract_years(date_str: str) -> list[str]:
    if not date_str:
        return []
    m = re.search(r"(19|20)\d{2}", date_str)
    if not m:
        return []
    full = m.group(0)
    return [full, full[2:]]


def extract_date_digits(date_str: str) -> list[str]:
    if not date_str:
        return []
    out = set()
    digits_only = re.sub(r"[^0-9]", "", date_str)
    if len(digits_only) >= 4:
        out.add(digits_only)
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", date_str)
    if m:
        yyyy, mm, dd = m.groups()
        out.update({
            mm + dd,
            dd + mm,
            mm + dd + yyyy[2:],
            dd + mm + yyyy[2:],
            yyyy + mm + dd,
            mm + dd + yyyy,
        })
    m2 = re.search(r"(\d{1,2})[\/\-\.](\d{1,2})", date_str)
    if m2:
        a, b = m2.group(1).zfill(2), m2.group(2).zfill(2)
        out.update({a + b, b + a})
    return list(out)


def build_guesses(info: dict) -> list[tuple[str, str]]:
    """
    Build a realistic attacker-style dictionary from personal details.
    Returns list of (original_case_guess, human_readable_source_label).
    Deduplication uses lowercase keys so case variants are NOT collapsed —
    the user sees the exact capitalised form attackers would try.
    """
    # lowercase_key -> (original_case_guess, source)
    results: dict[str, tuple[str, str]] = {}
    words:   list[tuple[str, str]] = []   # (value, label)

    # ── collect word tokens ──────────────────────────────────────────────────
    full_name = info.get("full_name", "").strip()
    if full_name:
        parts = full_name.split()
        for p in parts:
            if p:
                words.append((p, "name part"))
        if len(parts) >= 2:
            words.append(("".join(parts), "full name"))
            words.append((parts[0][0] + parts[-1], "initial+last"))
            words.append((parts[-1] + parts[0][0], "last+initial"))
            if len(parts) >= 3:
                words.append((parts[0] + parts[-1], "first+last"))

    # ── custom free-form words ───────────────────────────────────────────────
    for custom_val in info.get("custom_words", []):
        if custom_val.strip():
            words.append((custom_val.strip(), "custom"))

    for key, label in [
        ("nickname",        "nickname"),
        ("pet_name",        "pet's name"),
        ("partner_name",    "partner's name"),
        ("city",            "city"),
        ("favorite_thing",  "favorite thing"),
        ("mother_name",     "mother's name"),
        ("father_name",     "father's name"),
        ("sibling_name",    "sibling's name"),
        ("child_name",      "child's name"),
        ("school",          "school name"),
        ("workplace",       "workplace"),
        ("street",          "street name"),
        ("car",             "car"),
        ("username",        "username / handle"),
        ("email_prefix",    "email prefix"),
        ("fav_color",       "favorite color"),
        ("fav_band",        "favorite band / artist"),
        ("fav_sport_team",  "sports team"),
        ("hobby",           "hobby"),
        ("phone_last4",     "phone last 4 digits"),
    ]:
        val = info.get(key, "").strip()
        if val:
            words.append((val, label))

    years       = (extract_years(info.get("birth_year", ""))
                 + extract_years(info.get("birth_date", ""))
                 + extract_years(info.get("anniversary", ""))
                 + extract_years(info.get("grad_year", "")))
    # deduplicate years while preserving order
    seen_y: set[str] = set()
    years = [y for y in years if not (y in seen_y or seen_y.add(y))]

    date_digits = (extract_date_digits(info.get("birth_date", ""))
                 + extract_date_digits(info.get("anniversary", "")))

    lucky = info.get("lucky_number", "").strip()
    phone4 = info.get("phone_last4", "").strip()
    extra_numbers = [x for x in [lucky, phone4] if x and x.isdigit()]

    def add(guess: str, source: str):
        k = guess.lower().strip()
        g = guess.strip()
        if k and len(k) >= 3 and k not in results:
            results[k] = (g, source)   # store original case for display

    # ── per-word patterns ────────────────────────────────────────────────────
    for value, source in words:
        base = value.strip()
        if not base:
            continue

        for cap in capitalizations(base):
            for leet in leet_variants(cap):
                # plain prefix × suffix grid
                for pfx in COMMON_PREFIXES:
                    for sfx in COMMON_SUFFIXES:
                        add(f"{pfx}{leet}{sfx}", source)

                # special-char wrappers (attackers know people think these help)
                for wrap in SPECIAL_WRAPPERS:
                    add(wrap(leet), source)
                    add(wrap(leet.capitalize()), source)

                # with years
                for year in years:
                    add(f"{leet}{year}",           f"{source} + year")
                    add(f"{year}{leet}",           f"year + {source}")
                    add(f"{leet.capitalize()}{year}!", f"{source} + year + !")
                    add(f"{leet}{year}!",          f"{source} + year + !")
                    add(f"{leet}@{year}",          f"{source} @year")

                # with date fragments
                for dd in date_digits:
                    add(f"{leet}{dd}",             f"{source} + birthday")
                    add(f"{dd}{leet}",             f"birthday + {source}")

                # with extra numbers
                for num in extra_numbers:
                    add(f"{leet}{num}",            f"{source} + lucky/phone")
                    add(f"{leet}#{num}",           f"{source} #number")

                # reversed word
                rev = leet[::-1]
                if rev != leet:
                    add(rev, f"{source} (reversed)")
                    for sfx in ["", "1", "123", "!"]:
                        add(f"{rev}{sfx}", f"{source} reversed{sfx}")

                # doubled (e.g. "maxmax", "dogdog123")
                doubled = leet + leet
                add(doubled, f"{source} doubled")
                add(f"{doubled}1",   f"{source} doubled+1")
                add(f"{doubled}!",   f"{source} doubled+!")

                # emotion / identity phrases — how real humans talk
                add(f"ilove{leet}",       f"i love {source}")
                add(f"ilovemy{leet}",     f"i love my {source}")
                add(f"ilovemy{leet}123",  f"i love my {source} 123")
                add(f"my{leet}",          f"my {source}")
                add(f"my{leet}123",       f"my {source} 123")
                add(f"my{leet}!",         f"my {source} !")
                add(f"only{leet}",        f"only {source}")
                add(f"dear{leet}",        f"dear {source}")
                add(f"{leet}forever",     f"{source} forever")
                add(f"{leet}4ever",       f"{source} 4ever")
                add(f"{leet}4ever!",      f"{source} 4ever !")
                add(f"{leet}4life",       f"{source} 4life")
                add(f"{leet}isthebest",   f"{source} isthebest")
                add(f"{leet}islife",      f"{source} islife")
                add(f"{leet}isking",      f"{source} isking")
                add(f"{leet}isqueen",     f"{source} isqueen")
                add(f"bestof{leet}",      f"best of {source}")
                add(f"{leet}only",        f"{source} only")
                add(f"{leet}isme",        f"{source} isme")
                add(f"{leet}ismylife",    f"{source} ismylife")
                add(f"{leet}rocks",       f"{source} rocks")
                add(f"{leet}rules",       f"{source} rules")
                # number sandwich — humans wrap words in numbers
                add(f"1{leet}1",          f"1 {source} 1")
                add(f"123{leet}",         f"123 {source}")
                add(f"007{leet}",         f"007 {source}")
                add(f"{leet}786",         f"{source} 786")
                add(f"{leet}143",         f"{source} 143")
                # dot / underscore natural separators
                add(f"my_{leet}",         f"my_{source}")
                add(f"my.{leet}",         f"my.{source}")
                add(f"{leet}_123",        f"{source}_123")
                add(f"{leet}.123",        f"{source}.123")
                # camelCase feel
                add(f"my{leet.capitalize()}",      f"my{source.title()}")
                add(f"my{leet.capitalize()}123",   f"my{source.title()}123")
                add(f"i{leet.capitalize()}",       f"i{source.title()}")

    # ── pairwise word combinations ───────────────────────────────────────────
    for i, (a, sa) in enumerate(words):
        # year combos — outside inner loop (bug fix)
        for year in years:
            add(f"{a}{year}",  f"{sa} + year")
            add(f"{a.capitalize()}{year}", f"{sa} cap + year")

        for j, (b, sb) in enumerate(words):
            if i == j:
                continue
            for bridge in BRIDGES:
                combo = f"{a}{bridge}{b}".strip()
                add(combo, f"{sa}+{sb}")
                add(combo.capitalize(), f"{sa}+{sb} cap")
                for sfx in ["", "1", "123", "!", "!1"]:
                    add(f"{combo}{sfx}", f"{sa}+{sb}")
            for year in years:
                add(f"{a}{b}{year}", f"{sa}+{sb}+year")

    # ── standalone date/year patterns ───────────────────────────────────────
    for year in years:
        add(year,            "year alone")
        add(f"{year}!",      "year!")
        add(f"!{year}",      "!year")
    for dd in date_digits:
        add(dd,              "birthday digits alone")

    # ── seasonal patterns ───────────────────────────────────────────────────
    for sv in SEASON_YEARS:
        add(sv, "season + year")
        add(f"{sv}!", "season + year + !")

    # ── month patterns ───────────────────────────────────────────────────────
    for month in MONTHS:
        for year in years:
            add(f"{month}{year}",            f"month + year")
            add(f"{month.capitalize()}{year}", f"month cap + year")

    # ── keyboard walks & common passwords ───────────────────────────────────
    for kw in KEYBOARD_PATTERNS:
        add(kw, "keyboard pattern / common password")

    # ── filler emotion phrases ───────────────────────────────────────────────
    for phrase in FILLER_PHRASES:
        add(phrase, "common phrase")
        for sfx in ["", "1", "123", "!"]:
            add(f"{phrase}{sfx}", "common phrase")

    return list(results.values())   # each value is (original_case_guess, source)


# ─────────────────────────────────────────────────────────────────────────────
#  Interactive CLI helpers
# ─────────────────────────────────────────────────────────────────────────────

def prompt(label, hint=""):
    try:
        hint_part = style(f"  {hint}", DIM) if hint else ""
        if hint_part:
            print(hint_part)
        arrow     = style(ARROW, CYAN)
        colored   = (f"  {arrow} {style(label, CYAN)}{RESET}: "
                     if COLOR else f"  {ARROW} {label}: ")
        return input(colored).strip()
    except EOFError:
        return ""


def yes_no(label, default_yes=True) -> bool:
    hint = "[Y/n]" if default_yes else "[y/N]"
    try:
        arrow   = style(ARROW, YELLOW)
        colored = (f"  {arrow} {style(label, YELLOW)} {style(hint, DIM)}{RESET} "
                   if COLOR else f"  {ARROW} {label} {hint} ")
        ans = input(colored).strip().lower()
    except EOFError:
        return default_yes
    if ans in ("y", "yes"):
        return True
    if ans in ("n", "no"):
        return False
    return default_yes


def collect_custom_words(max_items: int = 100) -> list[str]:
    """
    Let the user type / paste any words or phrases, one per line.
    Type 'done' (or hit Ctrl-C / Ctrl-D) to finish.
    Returns a deduplicated list of non-empty strings.
    """
    print()
    print(style(f"  {ARROW} Type or paste anything — names, foods, words, phrases.", CYAN, BOLD))
    print(style( "    One item per line.  Type  done  when finished.", DIM))
    print(style(f"    You can add up to {max_items} items.\n", DIM))

    collected: list[str] = []
    seen: set[str] = set()

    while len(collected) < max_items:
        remaining = max_items - len(collected)
        count_hint = style(f"[{len(collected)}/{max_items}]", DIM)
        prompt_str = (
            f"  {style(ARROW, CYAN)} {count_hint} "
            f"{style('Enter item (or', DIM)} "
            f"{style('done', BOLD, YELLOW)}"
            f"{style('):', DIM)} "
        )
        try:
            raw = input(prompt_str).strip()
        except (EOFError, KeyboardInterrupt):
            break

        if raw.lower() == "done":
            break

        if not raw:
            continue

        key = raw.lower()
        if key in seen:
            print(style(f"    (already added — skipping)", DIM))
            continue

        seen.add(key)
        collected.append(raw)

        added_msg = style(f"    ✓  Added: {raw}", GREEN)
        if len(collected) == max_items:
            print(added_msg)
            print(style(f"\n  Reached the {max_items}-item limit — moving on.", YELLOW))
        else:
            print(added_msg)

    if collected:
        print()
        print(style(f"  {CHECK} {len(collected)} custom item(s) collected.", GREEN, BOLD))
    else:
        print(style("  No custom items added.", DIM))

    return collected


def numbered_menu(options: list[tuple[str, str]], multi=True) -> list[int]:
    """
    Display a numbered menu. Returns list of chosen 0-based indices.
    If multi=True, user can enter multiple numbers like "1 3 5" or "all".
    """
    print()
    for i, (title, desc) in enumerate(options, start=1):
        num   = style(f"  [{i:>2}]", BOLD, CYAN)
        ttl   = style(title, BOLD, WHITE)
        dsc   = style(f"  {desc}", DIM) if desc else ""
        print(f"{num}  {ttl}")
        if dsc:
            print(f"       {dsc}")
    print()
    all_msg  = "  all  " if multi else ""
    hint_str = style(f"Enter number(s) separated by spaces, {all_msg}or press Enter to skip: ", DIM)
    try:
        raw = input(hint_str).strip().lower()
    except EOFError:
        return []
    if not raw:
        return []
    if multi and raw == "all":
        return list(range(len(options)))
    chosen = []
    for tok in raw.split():
        if tok.isdigit():
            idx = int(tok) - 1
            if 0 <= idx < len(options) and idx not in chosen:
                chosen.append(idx)
    return chosen


# ─────────────────────────────────────────────────────────────────────────────
#  Strength analysis  (no real password ever enters this function)
# ─────────────────────────────────────────────────────────────────────────────

def strength_tips() -> list[str]:
    return [
        "Use a passphrase: 4 random words like 'violet-hammer-rogue-spoon'",
        "Enable a password manager (Bitwarden, 1Password) to use unique passwords everywhere",
        "Turn on two-factor authentication (2FA/TOTP) as a safety net",
        "Never reuse a password across sites — a breach on one site exposes all the others",
        "Aim for 16+ characters; length beats complexity every time",
    ]


# ─────────────────────────────────────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Password Guess Checker")
    parser.add_argument("--list", action="store_true",
                        help="Print all generated guesses to stdout and exit (no interaction)")
    parser.add_argument("--no-keyboard", action="store_true",
                        help="Omit keyboard-walk and common-password guesses")
    args = parser.parse_args()

    start_time = time.time()
    banner()

    # ── Step 1: core personal details ────────────────────────────────────────
    section("STEP 1  —  TELL US A LITTLE ABOUT YOURSELF")
    print(style("  Leave any field blank to skip it.\n", DIM))

    info = {
        "full_name":    prompt("Full name",                 "e.g. John Smith"),
        "nickname":     prompt("Nickname",                  "e.g. Johnny, JJ"),
        "pet_name":     prompt("Pet's name"),
        "partner_name": prompt("Partner / significant other's name"),
        "birth_year":   prompt("Birth year",                "e.g. 1990"),
        "birth_date":   prompt("Birth date",                "e.g. 1990-05-12  or  05/12"),
        "city":         prompt("City or hometown"),
        "favorite_thing": prompt("Favorite team / show / thing"),
    }

    # ── Step 2: optional extras ───────────────────────────────────────────────
    section("STEP 2  —  WANT TO ADD MORE DETAIL?")
    print(style("  More info = more realistic guess list. All optional.\n", DIM))

    want_more = yes_no("Would you like to add anything else?", default_yes=True)

    if want_more:
        extra_menu = [
            ("Family members",       "parent, sibling, child — names people weave into passwords"),
            ("Important dates",      "anniversary, graduation year"),
            ("Places",               "school, workplace, street name"),
            ("Online identity",      "username / handle, email prefix"),
            ("Lucky number",         "a number with personal meaning"),
            ("Phone last 4 digits",  "commonly appended to weak passwords"),
            ("Favorites",            "favorite color, band/artist, sport team, hobby"),
            ("Car",                  "make or model — surprisingly common"),
        ]

        subheading("Select categories to fill in:")
        chosen = numbered_menu(extra_menu, multi=True)

        if 0 in chosen:   # family
            section("FAMILY MEMBERS", CYAN)
            info["mother_name"]  = prompt("Mother's name (or maiden name)")
            info["father_name"]  = prompt("Father's name")
            info["sibling_name"] = prompt("Sibling's name")
            info["child_name"]   = prompt("Child's name")

        if 1 in chosen:   # dates
            section("IMPORTANT DATES", CYAN)
            info["anniversary"] = prompt("Anniversary date", "e.g. 2015-06-20")
            info["grad_year"]   = prompt("Graduation year",   "e.g. 2008")

        if 2 in chosen:   # places
            section("PLACES", CYAN)
            info["school"]    = prompt("School name",    "e.g. Lincoln High")
            info["workplace"] = prompt("Workplace name", "e.g. Google, NHS")
            info["street"]    = prompt("Street name",    "e.g. Maple, Oak")

        if 3 in chosen:   # online identity
            section("ONLINE IDENTITY", CYAN)
            info["username"]     = prompt("Username / online handle")
            info["email_prefix"] = prompt("Email prefix (the part before @)")

        if 4 in chosen:   # lucky number
            section("LUCKY NUMBER", CYAN)
            info["lucky_number"] = prompt("Lucky / favourite number")

        if 5 in chosen:   # phone
            info["phone_last4"] = prompt("Last 4 digits of your phone number")

        if 6 in chosen:   # favorites
            section("FAVORITES", CYAN)
            info["fav_color"]      = prompt("Favorite color")
            info["fav_band"]       = prompt("Favorite band or artist")
            info["fav_sport_team"] = prompt("Favorite sports team")
            info["hobby"]          = prompt("A hobby or activity you love")

        if 7 in chosen:   # car
            info["car"] = prompt("Car make or model", "e.g. Honda, Mustang, Golf")

    # ── Step 2b: custom words ─────────────────────────────────────────────────
    section("STEP 2b  —  ADD YOUR OWN CUSTOM WORDS  (optional)")
    print(style("  Paste anything: foods, places, phrases, names — whatever you like.", DIM))
    want_custom = yes_no("Would you like to add custom words?", default_yes=True)
    if want_custom:
        info["custom_words"] = collect_custom_words(max_items=100)
    else:
        info["custom_words"] = []

    # ── build guesses ─────────────────────────────────────────────────────────
    section("STEP 3  —  BUILDING GUESS LIST")
    sys.stdout.write(style(f"  {ARROW} Generating combinations", CYAN))
    sys.stdout.flush()

    guesses = build_guesses(info)

    if args.no_keyboard:
        guesses = [(g, s) for g, s in guesses if s != "keyboard pattern / common password"]

    # Animate dots during generation (cosmetic; generation is fast)
    if ANIMATE:
        for _ in range(3):
            time.sleep(0.12)
            sys.stdout.write(style(".", CYAN))
            sys.stdout.flush()
    print()

    if not guesses:
        print(style("\n  No details entered — nothing to build guesses from. Exiting.", YELLOW))
        return

    if args.list:
        for g, _ in guesses:
            print(g)
        return

    # ── pre-run summary ───────────────────────────────────────────────────────
    print()
    box_top(BLUE)
    box_line(color=BLUE)
    box_line(style(f"✦  {len(guesses):,}  candidate guesses built  ✦", BOLD, WHITE), color=BLUE)
    box_line(style("from all the details you provided", DIM, CYAN), color=BLUE)
    box_line(color=BLUE)
    box_bottom(BLUE)

    section("STEP 4  —  CHECK EACH GUESS AGAINST YOUR REAL PASSWORD")
    print()
    kw = 12
    print(f"  {style(CHECK, GREEN, BOLD)}  {style('y', BOLD, GREEN):<{kw}}  →  {style('it matches — stop here', WHITE)}")
    print(f"  {style(CROSS, RED,   BOLD)}  {style('n  or Enter', RED):<{kw}}  →  {style('no match, next guess', DIM)}")
    print(f"  {style(ARROW, YELLOW,BOLD)}  {style('q', BOLD, YELLOW):<{kw}}  →  {style('quit early', DIM)}")
    print()
    try:
        input(style("  ─── Press Enter to begin ───", BOLD, CYAN))
    except EOFError:
        pass
    print()

    # ── main checking loop ────────────────────────────────────────────────────
    total    = len(guesses)
    w        = len(str(total))
    cracked  = False
    eof_quit = False

    # colour-code different source types so the eye can scan fast
    SOURCE_COLORS = {
        "custom":    MAGENTA,
        "name":      CYAN,
        "nickname":  CYAN,
        "pet":       YELLOW,
        "partner":   YELLOW,
        "city":      BLUE,
        "year":      ORANGE,
        "birthday":  ORANGE,
        "keyboard":  GRAY,
        "common":    GRAY,
    }

    def source_color(src: str) -> str:
        for key, col in SOURCE_COLORS.items():
            if key in src.lower():
                return col
        return WHITE

    for idx, (guess, source) in enumerate(guesses, start=1):
        # progress line
        bar = progress_bar(idx - 1, total)
        print(f"\n  {bar}")

        # guess display in a mini box
        sc   = source_color(source)
        cand = style(f"  {guess}  ", BOLD, WHITE)
        src  = style(f" {source} ", sc)
        thin_rule(GRAY)
        print(f"  {style(ARROW, CYAN)}  {cand}   {src}")
        thin_rule(GRAY)

        prompt_str = (
            f"  Match? "
            f"[{style('y', BOLD, GREEN)} = yes  "
            f"{style('n', RED)} = no  "
            f"{style('q', YELLOW)} = quit]: "
        )
        try:
            answer = input(prompt_str).strip().lower()
        except EOFError:
            eof_quit = True
            break

        if answer == "q":
            print(style("\n  Stopped early.", YELLOW))
            return

        if answer == "y":
            elapsed = time.time() - start_time
            print()
            box_top(RED)
            box_line(color=RED)
            box_line(style(f"{CROSS}  CRACKED  after {idx:,} guess{'es' if idx != 1 else ''}  {CROSS}",
                           BOLD, RED), color=RED)
            box_mid(RED)
            box_line(style(f"  Password :  {guess}", BOLD, YELLOW), color=RED, align="left")
            box_line(style(f"  Source   :  {source}", DIM),         color=RED, align="left")
            box_line(style(f"  Guesses  :  #{idx:,} of {total:,}", DIM), color=RED, align="left")
            box_line(style(f"  Time     :  {elapsed:.1f}s",   DIM), color=RED, align="left")
            box_line(color=RED)
            box_bottom(RED)
            print()
            print(style("  ⚠  This password is guessable from public info.", BOLD, RED))
            print(style("     Change it immediately — treat it as compromised.", WHITE))
            cracked = True
            break

    elapsed = time.time() - start_time

    if eof_quit and not cracked:
        print(style("\n  Input ended before all guesses were checked — result is inconclusive.", YELLOW))
        return

    if not cracked:
        print()
        box_top(GREEN)
        box_line(color=GREEN)
        box_line(style(f"{CHECK}  NONE OF {total:,} GUESSES MATCHED  {CHECK}", BOLD, GREEN), color=GREEN)
        box_mid(GREEN)
        box_line(style(f"  Guesses tried :  {total:,}", DIM),      color=GREEN, align="left")
        box_line(style(f"  Time taken    :  {elapsed:.1f}s", DIM), color=GREEN, align="left")
        box_line(color=GREEN)
        box_bottom(GREEN)
        print()
        print(style(f"  {CHECK} Good — your password isn't a direct personal-detail guess.", GREEN))
        print(style("    It could still fall to a full dictionary / brute-force attack.", DIM))

    # ── security tips ─────────────────────────────────────────────────────────
    print()
    subheading("Security tips")
    for tip in strength_tips():
        print(f"    {style(BULLET, CYAN)}  {style(tip, WHITE)}")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(style("\n\n  Stopped.", YELLOW))
        sys.exit(0)
