#!/usr/bin/env bash
# fl-aliases.sh — shell launchers for a multi-prefix Wine audio setup.
#
#   install:  cp examples/fl-aliases.sh ~/.fl-aliases
#             echo '[ -f ~/.fl-aliases ] && . ~/.fl-aliases' >> ~/.bashrc
#   then:     flhelp
#
# EDIT THE FIVE PREFIX PATHS BELOW to match your own layout. Everything else
# locates its .exe at call time with `find`, so you do not need to know or
# maintain install paths — measured at 11-76 ms per launch on an NVMe disk,
# and it survives installers that land somewhere unexpected (Arturia Software
# Center installs to "Program Files (x86)", not "Program Files").
#
# `wp` reads the wineserver socket at /tmp/.wine-$UID/server-<dev>-<inode>,
# derived from the prefix directory's device and inode. Do not be tempted to
# use `pgrep -f wineserver` instead: wineserver's argv contains no prefix, so
# that approach reports every prefix idle, including running ones.

# ---------------------------------------------------------------- prefixes ---
export WP_FL="$HOME/Image-Line"
export WP_NI="$HOME/.wine-ni"
export WP_ILOK="$HOME/.wine-ilok"
export WP_ARTURIA="$HOME/.wine-arturia"
export WP_SLATE="$HOME/.wine-slate"

_wp_resolve() {                       # short name -> prefix path
  case "$1" in
    fl|flstudio|image-line) printf '%s' "$WP_FL" ;;
    ni|kontakt|native)      printf '%s' "$WP_NI" ;;
    ilok|pace)              printf '%s' "$WP_ILOK" ;;
    arturia|asc|pigments)   printf '%s' "$WP_ARTURIA" ;;
    slate)                  printf '%s' "$WP_SLATE" ;;
    *)                      return 1 ;;
  esac
}

# ------------------------------------------------------------------ runners ---
_wrun() {                             # _wrun <prefix> <exe name> [args...]
  local pfx="$1" want="$2"; shift 2
  if [ ! -d "$pfx/drive_c" ]; then
    printf 'no prefix at %s\n' "$pfx" >&2; return 1
  fi
  local exe
  exe=$(find "$pfx/drive_c" -maxdepth 7 -type f -iname "$want" 2>/dev/null | head -1)
  if [ -z "$exe" ]; then
    printf '%s not found under %s\n' "$want" "$pfx/drive_c" >&2; return 1
  fi
  ( export WINEPREFIX="$pfx"; cd "$(dirname "$exe")" && wine "$exe" "$@" ) \
    >/dev/null 2>&1 &
  printf 'launched %s\n' "$(basename "$exe")"
}

_wrun_fg() {                          # same, but keep the log in the terminal
  local pfx="$1" want="$2"; shift 2
  local exe
  exe=$(find "$pfx/drive_c" -maxdepth 7 -type f -iname "$want" 2>/dev/null | head -1)
  [ -z "$exe" ] && { printf '%s not found\n' "$want" >&2; return 1; }
  ( export WINEPREFIX="$pfx"; cd "$(dirname "$exe")" && wine "$exe" "$@" )
}

# ------------------------------------------------------------------- the DAW ---
fl() {
  # audio setup first, then FL. -v keeps wine's log on screen.
  local fg=0; [ "$1" = "-v" ] && { fg=1; shift; }
  pw-metadata -n settings 0 clock.force-quantum 256 >/dev/null 2>&1
  if [ "$fg" = 1 ]; then
    _wrun_fg "$WP_FL" 'FL64.exe' "$@"
  else
    _wrun "$WP_FL" 'FL64.exe' "$@"
  fi
}

# --------------------------------------------------------- plugins & hosts ---
kontakt()  { _wrun "$WP_NI"      'Kontakt 8.exe' "$@"; }
access()   { _wrun "$WP_NI"      'Native Access.exe' "$@"; }
ilok()     { _wrun "$WP_ILOK"    'iLok License Manager.exe' "$@"; }
pigments() { _wrun "$WP_ARTURIA" 'Pigments*.exe' "$@"; }
asc()      { _wrun "$WP_ARTURIA" 'Arturia Software Center.exe' "$@"; }
slate()    { _wrun "$WP_SLATE"   'Complete Access Hub.exe' "$@"; }

# ------------------------------------------------------- prefix maintenance ---
_wp_live() {                          # 0 if this prefix has a live wineserver
  local p="$1" d i sock
  [ -d "$p" ] || return 2
  d=$(stat -c '%d' "$p" 2>/dev/null) || return 2
  i=$(stat -c '%i' "$p" 2>/dev/null) || return 2
  for base in "/tmp/.wine-$(id -u)" "${XDG_RUNTIME_DIR:-/nonexistent}/wine"; do
    sock="$base/server-$(printf '%x' "$d")-$(printf '%x' "$i")/socket"
    [ -S "$sock" ] && { printf '%s' "$sock"; return 0; }
  done
  return 1
}

wp() {                                # list prefixes and whether they're running
  printf '%-10s %-34s %s\n' NAME PREFIX STATE
  local n p
  for n in fl ni ilok arturia slate; do
    p=$(_wp_resolve "$n")
    _wp_live "$p" >/dev/null
    case $? in
      0) printf '%-10s %-34s %s\n' "$n" "${p/#"$HOME"/\~}" 'LIVE' ;;
      1) printf '%-10s %-34s %s\n' "$n" "${p/#"$HOME"/\~}" 'idle' ;;
      *) printf '%-10s %-34s %s\n' "$n" "${p/#"$HOME"/\~}" 'absent' ;;
    esac
  done
}

wpkill() {                            # wpkill <name> [name...]   |   wpkill all
  local names="$*" n p
  [ -z "$names" ] && { echo 'usage: wpkill <fl|ni|ilok|arturia|slate|all> ...' >&2; return 1; }
  case " $names " in *" all "*) names='fl ni ilok arturia slate' ;; esac
  for n in $names; do
    p=$(_wp_resolve "$n") || { printf 'unknown prefix: %s\n' "$n" >&2; continue; }
    _wp_live "$p" >/dev/null
    case $? in
      0) WINEPREFIX="$p" wineserver -k 2>/dev/null; printf 'killed %s\n' "$n" ;;
      1) printf '%s already idle\n' "$n" ;;
      *) printf '%s absent\n' "$n" ;;
    esac
  done
}

wpcfg()    { local p; p=$(_wp_resolve "${1:?usage: wpcfg <name>}") \
             && WINEPREFIX="$p" winecfg; }
wpreg()    { local p; p=$(_wp_resolve "${1:?usage: wpreg <name>}") \
             && WINEPREFIX="$p" regedit; }
wptricks() { local p n="${1:?usage: wptricks <name> <verb...>}"; shift
             p=$(_wp_resolve "$n") && WINEPREFIX="$p" winetricks "$@"; }
wpshell()  { local p; p=$(_wp_resolve "${1:?usage: wpshell <name>}") \
             && printf 'WINEPREFIX=%s  (exit to leave)\n' "${p/#"$HOME"/\~}" \
             && WINEPREFIX="$p" bash; }
wpinstall() {                         # run an installer inside a prefix
  local n="${1:?usage: wpinstall <name> /path/to/setup.exe}"; shift
  local p; p=$(_wp_resolve "$n") || return 1
  WINEPREFIX="$p" wine "$@"
}

# ------------------------------------------------------------------- .fst ---
FLDB="$WP_FL/drive_c/users/$USER/Documents/Image-Line/FL Studio/Presets"

bridge()  { python3 "$HOME/fl-studio-linux/waves-bridge.py" "$@"; }
fstx()    { python3 "$HOME/fl-studio-linux/tools/fst-inspect.py" "$@"; }
fldb()    { cd "$FLDB/Plugin database" || return 1; pwd; }

flbackup() {
  local out="$HOME/fl-backups/fl-presets-$(date +%Y%m%d-%H%M).tar.gz"
  mkdir -p "$HOME/fl-backups" || return 1
  tar -czf "$out" -C "$(dirname "$FLDB")" "$(basename "$FLDB")" || return 1
  printf '%s  (%s)\n' "$out" "$(du -h "$out" | cut -f1)"
}

# -------------------------------------------------------------------- help ---
flhelp() { cat <<'EOF'
LAUNCH
  fl [-v]            FL Studio   (-v keeps the wine log on screen)
  kontakt            Kontakt 8 standalone
  access             Native Access
  ilok               iLok License Manager
  pigments           Pigments standalone
  asc                Arturia Software Center
  slate              Complete Access Hub

PREFIXES            names: fl  ni  ilok  arturia  slate
  wp                 list prefixes + LIVE/idle (reads the wineserver socket)
  wpkill  <name>…    wineserver -k  (takes several, or "all")
  wpcfg   <name>     winecfg
  wpreg   <name>     regedit
  wptricks <name> …  winetricks, e.g.  wptricks slate -q win10
  wpshell <name>     subshell with WINEPREFIX set
  wpinstall <name> setup.exe

.FST / PLUGIN DB
  bridge …           waves-bridge.py — the id-2 transplant
  fstx …             fst-inspect.py  — events | records | flags | diff
  fldb               cd to the live Plugin database
  flbackup           tar the whole Presets tree to ~/fl-backups

  $FLDB is the live Presets path. The ~/Documents/Image-Line tree is the
  stale one FL never reads — never patch there.
EOF
}
