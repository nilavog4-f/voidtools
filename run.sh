#!/usr/bin/env bash
# ##############################################################
# ##                                                          ##
# ##   VOID OSINT  —  WSL / Kali Linux Edition               ##
# ##   ** Main Launcher / Tool Menu **                        ##
# ##                                                          ##
# ##   Usage  :  bash run.sh                                  ##
# ##   Requires:  Python 3.8+, pip3                           ##
# ##   Author  :  @lfw.k4rma_                                 ##
# ##                                                          ##
# ##############################################################

# ── Always run from the script's own directory ────────────────
cd "$(dirname "$(realpath "$0")")" 2>/dev/null \
  || cd "$(dirname "$0")"

# ── Color Palette ─────────────────────────────────────────────
R='\033[0;31m'   LR='\033[1;31m'
Y='\033[0;33m'   LY='\033[1;33m'
C='\033[0;36m'   LC='\033[1;36m'
G='\033[0;32m'   LG='\033[1;32m'
M='\033[0;35m'   LM='\033[1;35m'
W='\033[1;37m'   DIM='\033[2m'   RST='\033[0m'

OK="${LG}[✔]${RST}"
ERR="${LR}[✘]${RST}"
INF="${LC}[◈]${RST}"
WARN="${LY}[!]${RST}"
RUN="${LM}[➜]${RST}"

# ── Helpers ───────────────────────────────────────────────────
rule() {
  local char="${1:-─}" color="${2:-$DIM}"
  printf "${color}"
  printf '%*s' "$(tput cols 2>/dev/null || echo 72)" '' | tr ' ' "$char"
  printf "${RST}\n"
}

center() {
  local text="$1"
  local plain; plain=$(echo -e "$text" | sed 's/\x1B\[[0-9;]*m//g')
  local width len pad
  width=$(tput cols 2>/dev/null || echo 72)
  len=${#plain}; pad=$(( (width - len) / 2 ))
  printf "%${pad}s" ""; echo -e "$text"
}

spin() {
  local label="$1"; shift
  local frames=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
  "$@" &>/tmp/_void_out & local pid=$! i=0
  while kill -0 "$pid" 2>/dev/null; do
    printf "\r  ${LY}${frames[$i]}${RST}  ${DIM}%s${RST}   " "$label"
    i=$(( (i + 1) % ${#frames[@]} )); sleep 0.08
  done
  wait "$pid"; local rc=$?; printf "\r\033[2K"; return $rc
}

# ── Banner ────────────────────────────────────────────────────
show_banner() {
  clear; echo ""
  rule "═" "$LC"
  echo ""
  echo -e "${LC}"
  center "██╗   ██╗ ██████╗ ██╗██████╗      ██████╗ ███████╗██╗███╗   ██╗████████╗"
  center "██║   ██║██╔═══██╗██║██╔══██╗    ██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝"
  center "██║   ██║██║   ██║██║██║  ██║    ██║   ██║███████╗██║██╔██╗ ██║   ██║   "
  center "╚██╗ ██╔╝██║   ██║██║██║  ██║    ██║   ██║╚════██║██║██║╚██╗██║   ██║   "
  center " ╚████╔╝ ╚██████╔╝██║██████╔╝    ╚██████╔╝███████║██║██║ ╚████║   ██║   "
  center "  ╚═══╝   ╚═════╝ ╚═╝╚═════╝      ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝  "
  echo -e "${RST}"
  center "${DIM}OSINT Toolkit  •  WSL / Kali Linux Edition  •  @lfw.k4rma_${RST}"
  echo ""
  rule "═" "$LC"
  echo ""
}

# ── Environment + dep check (runs once on startup) ────────────
startup_checks() {
  echo -e "  ${W}ENVIRONMENT${RST}\n"

  if grep -qi microsoft /proc/version 2>/dev/null; then
    echo -e "  ${OK}  WSL detected"
  else
    echo -e "  ${INF}  Native Linux"
  fi

  if grep -qi kali /etc/os-release 2>/dev/null; then
    echo -e "  ${OK}  Kali Linux"
  else
    distro=$(. /etc/os-release 2>/dev/null && echo "$NAME" || echo "Unknown")
    echo -e "  ${WARN}  ${distro}  ${DIM}(not Kali — tool may still work)${RST}"
  fi

  if ! command -v python3 &>/dev/null; then
    echo -e "  ${ERR}  Python3 not found"
    echo -e "       ${DIM}sudo apt update && sudo apt install python3 python3-pip -y${RST}"
    echo ""; exit 1
  fi
  PY_VER=$(python3 --version 2>&1 | awk '{print $2}')
  echo -e "  ${OK}  Python ${LG}${PY_VER}${RST}"

  echo ""
  rule "─" "$DIM"
  echo ""
  echo -e "  ${W}DEPENDENCIES${RST}\n"

  if [ -f requirements.txt ]; then
    spin "Installing requirements…" \
      pip3 install -r requirements.txt -q --break-system-packages 2>/dev/null \
      || pip3 install -r requirements.txt -q 2>/dev/null
    echo -e "  ${OK}  Packages ready"
  else
    spin "Installing core packages…" \
      pip3 install requests rich pyfiglet ddgs phonenumbers beautifulsoup4 flask -q \
           --break-system-packages 2>/dev/null \
      || pip3 install requests rich pyfiglet ddgs phonenumbers beautifulsoup4 flask -q 2>/dev/null
    echo -e "  ${OK}  Core packages installed"
  fi

  echo ""
  rule "═" "$LC"
  echo ""
}

# ── Tool menu ─────────────────────────────────────────────────
show_menu() {
  echo -e "  ${LC}SELECT A TOOL${RST}\n"

  echo -e "  ${LY}[1]${RST}  ${W}Phone Deep Scan${RST}        ${DIM}phone_deep.py   — carrier, breach, OSINT lookup${RST}"
  echo -e "  ${LY}[2]${RST}  ${W}Phone Intelligence${RST}     ${DIM}phone2.py       — full OSINT + AI phone framework${RST}"
  echo -e "  ${LY}[3]${RST}  ${W}IP Intelligence${RST}        ${DIM}ip_intel.py     — geo, ASN, VPN/Tor, port scan, DDG${RST}"
  echo -e "  ${LY}[4]${RST}  ${W}GeoTracker${RST}             ${DIM}geo.py          — Flask lure page, Cloudflare tunnel${RST}"
  echo -e "  ${LY}[5]${RST}  ${W}Phishing Kit${RST}           ${DIM}phishing.py     — credential capture server${RST}"
  echo -e "  ${LY}[6]${RST}  ${W}Password Guesser${RST}       ${DIM}password_guesser.py — social-data wordlist builder${RST}"
  echo -e "  ${LY}[7]${RST}  ${W}VOID-AI Chatbot${RST}        ${DIM}chatbot.py      — OpenRouter AI assistant${RST}"
  echo ""
  echo -e "  ${DIM}[Q]  Quit${RST}"
  echo ""
  rule "─" "$DIM"
  echo ""
}

launch() {
  local script="$1" label="$2"
  if [ ! -f "$script" ]; then
    echo -e "\n  ${ERR}  ${script} not found in $(pwd)\n"
    return
  fi
  echo ""
  rule "═" "$LY"
  echo -e "\n  ${RUN}  ${W}Launching ${label}…${RST}\n"
  rule "═" "$LY"
  echo ""
  python3 "$script"
  local rc=$?
  echo ""
  rule "═" "$LC"
  if [ $rc -eq 0 ]; then
    center "${LG}** ${label} exited cleanly **${RST}"
  else
    center "${LR}** ${label} exited with code ${rc} **${RST}"
  fi
  echo ""
  rule "═" "$LC"
  echo ""
  echo -e "  ${DIM}Press Enter to return to the menu…${RST}"
  read -r
}

# ── Main loop ─────────────────────────────────────────────────
show_banner
startup_checks

while true; do
  show_banner
  show_menu

  printf "  ${LC}◈${RST}  Choice: "
  read -r choice

  case "$choice" in
    1) launch "phone_deep.py"       "Phone Deep Scan"    ;;
    2) launch "phone2.py"           "Phone Intelligence" ;;
    3) launch "ip_intel.py"         "IP Intelligence"    ;;
    4) launch "geo.py"              "GeoTracker"         ;;
    5) launch "phishing.py"         "Phishing Kit"       ;;
    6) launch "password_guesser.py" "Password Guesser"   ;;
    7) launch "chatbot.py"          "VOID-AI Chatbot"    ;;
    q|Q|quit|exit)
      echo ""
      center "${DIM}** Session ended **${RST}"
      echo ""; exit 0 ;;
    *)
      echo -e "\n  ${WARN}  Invalid choice — enter 1-7 or Q\n"
      sleep 1 ;;
  esac
done
