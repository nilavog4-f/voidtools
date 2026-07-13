#!/usr/bin/env bash
# ##############################################################
# ##                                                          ##
# ##   VOID OSINT  —  WSL / Kali Linux Edition               ##
# ##   ** Phone Number Deep Intelligence Scanner **           ##
# ##                                                          ##
# ##   Usage  :  bash run.sh                                  ##
# ##   Requires:  Python 3.8+, pip3, Kali/Debian             ##
# ##   Author  :  @lfw.k4rma_                                 ##
# ##                                                          ##
# ##############################################################

# ── Color Palette ─────────────────────────────────────────────────────────────
R='\033[0;31m'      # red
LR='\033[1;31m'     # light red
Y='\033[0;33m'      # yellow
LY='\033[1;33m'     # bright yellow
C='\033[0;36m'      # cyan
LC='\033[1;36m'     # bright cyan
G='\033[0;32m'      # green
LG='\033[1;32m'     # bright green
M='\033[0;35m'      # magenta
LM='\033[1;35m'     # bright magenta
W='\033[1;37m'      # white bold
DIM='\033[2m'
RST='\033[0m'

# ── Symbols ───────────────────────────────────────────────────────────────────
OK="${LG}[✔]${RST}"
ERR="${LR}[✘]${RST}"
INF="${LC}[◈]${RST}"
WARN="${LY}[!]${RST}"
RUN="${LM}[➜]${RST}"
DOT="${Y}•${RST}"

# ── Helper: horizontal rule ───────────────────────────────────────────────────
rule() {
  local char="${1:-─}" color="${2:-$DIM}"
  printf "${color}"
  printf '%*s' "$(tput cols 2>/dev/null || echo 72)" '' | tr ' ' "$char"
  printf "${RST}\n"
}

# ── Helper: center text ───────────────────────────────────────────────────────
center() {
  local text="$1"
  local plain
  plain=$(echo -e "$text" | sed 's/\x1B\[[0-9;]*m//g')
  local width len pad
  width=$(tput cols 2>/dev/null || echo 72)
  len=${#plain}
  pad=$(( (width - len) / 2 ))
  printf "%${pad}s" ""
  echo -e "$text"
}

# ── Helper: spinner while running a command ───────────────────────────────────
spin() {
  local label="$1" ; shift
  local frames=('⠋' '⠙' '⠹' '⠸' '⠼' '⠴' '⠦' '⠧' '⠇' '⠏')
  "$@" &>/tmp/_void_cmd_out & local pid=$!
  local i=0
  while kill -0 "$pid" 2>/dev/null; do
    printf "\r  ${LY}${frames[$i]}${RST}  ${DIM}%s${RST}   " "$label"
    i=$(( (i + 1) % ${#frames[@]} ))
    sleep 0.08
  done
  wait "$pid" ; local rc=$?
  printf "\r\033[2K"
  return $rc
}

# ══════════════════════════════════════════════════════════════════════════════
clear

# ## BANNER ####################################################################
echo ""
rule "═" "$LY"
echo ""
echo -e "${LY}"
center "██╗   ██╗ ██████╗ ██╗██████╗      ██████╗ ███████╗██╗███╗   ██╗████████╗"
center "██║   ██║██╔═══██╗██║██╔══██╗    ██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝"
center "██║   ██║██║   ██║██║██║  ██║    ██║   ██║███████╗██║██╔██╗ ██║   ██║   "
center "╚██╗ ██╔╝██║   ██║██║██║  ██║    ██║   ██║╚════██║██║██║╚██╗██║   ██║   "
center " ╚████╔╝ ╚██████╔╝██║██████╔╝    ╚██████╔╝███████║██║██║ ╚████║   ██║   "
center "  ╚═══╝   ╚═════╝ ╚═╝╚═════╝      ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝  "
echo -e "${RST}"
center "${DIM}** Phone Number Deep Intelligence  •  WSL / Kali Linux Edition **${RST}"
center "${DIM}by @lfw.k4rma_  •  FOR AUTHORIZED USE ONLY${RST}"
echo ""
rule "═" "$LY"
echo ""

# ## ENVIRONMENT CHECKS ########################################################
echo -e "  ${W}ENVIRONMENT CHECKS${RST}"
echo ""

# -- WSL detection
if grep -qi microsoft /proc/version 2>/dev/null; then
  echo -e "  ${OK}  Running inside WSL  ${DIM}(Windows Subsystem for Linux)${RST}"
else
  echo -e "  ${INF}  WSL not detected — running native Linux"
fi

# -- Kali detection
if [ -f /etc/os-release ] && grep -qi kali /etc/os-release 2>/dev/null; then
  echo -e "  ${OK}  OS  ${DIM}→${RST}  ${LR}Kali Linux${RST} detected"
else
  distro=$(. /etc/os-release 2>/dev/null && echo "$NAME" || echo "Unknown")
  echo -e "  ${WARN}  OS  ${DIM}→${RST}  ${W}${distro}${RST}  ${DIM}(not Kali — tool may still work)${RST}"
fi

echo ""
rule "─" "$DIM"
echo ""

# ## DEPENDENCY CHECKS #########################################################
echo -e "  ${W}DEPENDENCIES${RST}"
echo ""

# -- Python 3 check
if ! command -v python3 &>/dev/null; then
  echo -e "  ${ERR}  Python3 not found"
  echo -e "  ${DIM}    Fix  :  sudo apt update && sudo apt install python3 python3-pip -y${RST}"
  echo ""
  exit 1
fi
PY_VER=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "  ${OK}  Python  ${DIM}→${RST}  ${LG}${PY_VER}${RST}"

# -- pip3 check
if ! command -v pip3 &>/dev/null; then
  echo -e "  ${WARN}  pip3 not found — installing..."
  sudo apt install python3-pip -y -qq &>/dev/null \
    && echo -e "  ${OK}  pip3 installed" \
    || { echo -e "  ${ERR}  pip3 install failed — run: sudo apt install python3-pip -y"; echo ""; exit 1; }
else
  PIP_VER=$(pip3 --version 2>&1 | awk '{print $2}')
  echo -e "  ${OK}  pip3    ${DIM}→${RST}  ${LG}${PIP_VER}${RST}"
fi

echo ""
rule "─" "$DIM"
echo ""

# ## PACKAGE INSTALL ###########################################################
echo -e "  ${W}INSTALLING REQUIREMENTS${RST}"
echo ""

if [ -f requirements.txt ]; then
  spin "Resolving packages…" \
    pip3 install -r requirements.txt -q --break-system-packages \
      || pip3 install -r requirements.txt -q
  if [ $? -eq 0 ]; then
    echo -e "  ${OK}  All packages ready"
  else
    echo -e "  ${WARN}  Some packages may have failed — attempting fallback"
    echo -e "       ${DIM}Run manually:  pip3 install requests rich pyfiglet ddgs phonenumbers beautifulsoup4${RST}"
  fi
else
  echo -e "  ${WARN}  requirements.txt not found — installing core deps directly"
  spin "Installing core dependencies…" \
    pip3 install requests rich pyfiglet ddgs phonenumbers beautifulsoup4 -q --break-system-packages \
      || pip3 install requests rich pyfiglet ddgs phonenumbers beautifulsoup4 -q
  echo -e "  ${OK}  Core packages installed"
fi

echo ""
rule "─" "$DIM"
echo ""

# ## LAUNCH ####################################################################
echo -e "  ${RUN}  ${W}Launching DEEP SCAN…${RST}"
echo ""
rule "═" "$LY"
echo ""

python3 osint2.py

# ## EXIT ######################################################################
EXIT_CODE=$?
echo ""
rule "═" "$LY"
if [ $EXIT_CODE -eq 0 ]; then
  echo ""
  center "${LG}** Scan complete **${RST}"
else
  echo ""
  center "${LR}** Exited with code ${EXIT_CODE} **${RST}"
fi
echo ""
