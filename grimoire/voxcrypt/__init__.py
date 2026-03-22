# ═══════════════════════════════════════════════════════════════
#  GRIMOIRE v2.0 — voxcrypt/__init__.py
#  Steganography Engine + AES-grade Cipher
#
#  Developer  : Light
#  Alias      : Neok1ra
#  GitHub     : https://github.com/ne0k1r4
#  Tool       : GRIMOIRE — The Death Note of the digital world
#
#  Features:
#    LSB PNG/BMP encoding + HMAC integrity check
#    WAV audio LSB encoding
#    Zero-width character (ZWC) text stego
#    XOR-SHA256 stream cipher (AES-grade key)
#    Compress-before-encrypt (zlib)
# ═══════════════════════════════════════════════════════════════

import os, struct, hashlib, wave, zlib, hmac
from pathlib import Path
from datetime import datetime
from ..utils import C, section

BANNER = f"""
{C.RED}{C.BOLD}  ╔══════════════════════════════════════════════╗
  ║  V O X C R Y P T  v2.0  —  Stego Engine     ║
  ║  Developer: Light (Neok1ra)                  ║
  ╚══════════════════════════════════════════════╝{C.RESET}
  {C.DIM}LSB Image/Audio · ZWC Text · AES-cipher · HMAC integrity{C.RESET}
"""

MAGIC   = b"\xDE\xAD\xBE\xEF\xCA\xFE"   # 6-byte magic
VERSION = b"\x02"                          # format v2

ZWC_MAP = {"0": "\u200b", "1": "\u200c", " ": "\u200d"}
ZWC_RMAP= {v: k for k, v in ZWC_MAP.items()}


# ── Cipher ────────────────────────────────────────────────────

def _derive_key(passphrase: str) -> bytes:
    return hashlib.sha256(passphrase.encode()).digest()

def _keystream_block(key: bytes, counter: int) -> bytes:
    return hashlib.sha256(key + struct.pack(">Q", counter)).digest()

def _xor_cipher(data: bytes, key: bytes) -> bytes:
    out, blk, ctr = bytearray(len(data)), b"", 0
    for i, byte in enumerate(data):
        if i % 32 == 0:
            blk = _keystream_block(key, ctr); ctr += 1
        out[i] = byte ^ blk[i % 32]
    return bytes(out)

def _hmac_sign(data: bytes, key: bytes) -> bytes:
    return hmac.new(key, data, hashlib.sha256).digest()[:16]


# ── LSB PNG/BMP ───────────────────────────────────────────────

def lsb_hide(carrier_path: str, payload: bytes, output_path: str, passphrase: str = ""):
    with open(carrier_path, "rb") as f:
        carrier = bytearray(f.read())
    # validate
    is_png = carrier[:8] == b"\x89PNG\r\n\x1a\n"
    is_bmp = carrier[:2] == b"BM"
    if not (is_png or is_bmp):
        raise ValueError("Carrier must be PNG or BMP")
    offset = 8 if is_png else 54       # skip headers

    if passphrase:
        key     = _derive_key(passphrase)
        payload = zlib.compress(payload, level=9)
        payload = _xor_cipher(payload, key)
        sig     = _hmac_sign(payload, key)
        payload = sig + payload         # prepend 16-byte HMAC

    full    = MAGIC + VERSION + struct.pack(">I", len(payload)) + payload
    bits_n  = len(full) * 8
    usable  = len(carrier) - offset
    if bits_n > usable:
        raise ValueError(f"Carrier too small: need {bits_n} bits, have {usable}")

    bits = []
    for byte in full:
        for b in range(7, -1, -1): bits.append((byte >> b) & 1)
    for i, bit in enumerate(bits):
        carrier[offset + i] = (carrier[offset + i] & 0xFE) | bit

    with open(output_path, "wb") as f: f.write(bytes(carrier))
    return True


def lsb_reveal(stego_path: str, passphrase: str = "") -> bytes:
    with open(stego_path, "rb") as f:
        carrier = f.read()
    is_png = carrier[:8] == b"\x89PNG\r\n\x1a\n"
    is_bmp = carrier[:2] == b"BM"
    offset = 8 if is_png else (54 if is_bmp else 8)

    bits = [(carrier[offset + i] & 1) for i in range(len(carrier) - offset)]
    raw  = bytearray()
    for i in range(0, len(bits) - 7, 8):
        byte = 0
        for j in range(8): byte = (byte << 1) | bits[i + j]
        raw.append(byte)
    raw = bytes(raw)

    if not raw.startswith(MAGIC):
        raise ValueError("No GRIMOIRE payload found (wrong file or not stego?)")
    pos     = len(MAGIC) + 1   # skip magic + version byte
    length  = struct.unpack(">I", raw[pos:pos+4])[0]
    payload = raw[pos+4:pos+4+length]

    if passphrase:
        key  = _derive_key(passphrase)
        sig  = payload[:16]
        data = payload[16:]
        if not hmac.compare_digest(sig, _hmac_sign(data, key)):
            raise ValueError("HMAC integrity check FAILED — wrong passphrase or tampered payload")
        data    = _xor_cipher(data, key)
        payload = zlib.decompress(data)

    return payload


# ── WAV audio ─────────────────────────────────────────────────

def wav_hide(carrier_path: str, payload: bytes, output_path: str, passphrase: str = ""):
    with wave.open(carrier_path, "r") as w:
        params = w.getparams()
        frames = bytearray(w.readframes(w.getnframes()))
    if passphrase:
        key     = _derive_key(passphrase)
        payload = zlib.compress(payload, 9)
        payload = _xor_cipher(payload, key)
    full = MAGIC + VERSION + struct.pack(">I", len(payload)) + payload
    if len(full) * 8 > len(frames):
        raise ValueError("WAV too small for payload")
    bits = []
    for byte in full:
        for b in range(7, -1, -1): bits.append((byte >> b) & 1)
    for i, bit in enumerate(bits): frames[i] = (frames[i] & 0xFE) | bit
    with wave.open(output_path, "w") as w:
        w.setparams(params); w.writeframes(bytes(frames))
    return True


def wav_reveal(stego_path: str, passphrase: str = "") -> bytes:
    with wave.open(stego_path, "r") as w:
        frames = bytearray(w.readframes(w.getnframes()))
    bits = [(frames[i] & 1) for i in range(len(frames))]
    raw  = bytearray()
    for i in range(0, len(bits) - 7, 8):
        byte = 0
        for j in range(8): byte = (byte << 1) | bits[i + j]
        raw.append(byte)
    raw = bytes(raw)
    if not raw.startswith(MAGIC):
        raise ValueError("No GRIMOIRE payload in WAV")
    pos     = len(MAGIC) + 1
    length  = struct.unpack(">I", raw[pos:pos+4])[0]
    payload = raw[pos+4:pos+4+length]
    if passphrase:
        key     = _derive_key(passphrase)
        payload = _xor_cipher(payload, key)
        payload = zlib.decompress(payload)
    return payload


# ── ZWC text stego ────────────────────────────────────────────

def zwc_hide(cover: str, secret: str, passphrase: str = "") -> str:
    data = secret.encode()
    if passphrase:
        key  = _derive_key(passphrase)
        data = _xor_cipher(data, key)
    binary = "".join(f"{byte:08b}" for byte in data)
    zwc    = "".join(ZWC_MAP.get(bit, ZWC_MAP["0"]) for bit in binary)
    words  = cover.split(" ", 1)
    return words[0] + zwc + (" " + words[1] if len(words) > 1 else "")


def zwc_reveal(stego: str, passphrase: str = "") -> str:
    chars  = "".join(c for c in stego if c in ZWC_RMAP)
    if not chars: raise ValueError("No ZWC payload found")
    binary = "".join(ZWC_RMAP[c] for c in chars)
    raw    = bytes(int(binary[i:i+8], 2) for i in range(0, len(binary)-7, 8))
    if passphrase:
        key = _derive_key(passphrase)
        raw = _xor_cipher(raw, key)
    return raw.decode(errors="replace")


# ── Interactive ───────────────────────────────────────────────

def _interactive():
    print(BANNER)
    print(f"  {C.DIM}Commands: hide | reveal | wav-hide | wav-reveal | zwc-hide | zwc-reveal | exit{C.RESET}\n")
    while True:
        try:
            raw = input(f"  {C.RED}voxcrypt>{C.RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  [Closing Voxcrypt]"); break
        if not raw: continue
        parts = raw.split(); cmd = parts[0].lower()
        if cmd in ("exit","quit","q"): break

        elif cmd == "hide":
            carrier = input(f"  {C.DIM}Carrier (PNG/BMP):{C.RESET} ").strip()
            src     = input(f"  {C.DIM}Payload file or text:{C.RESET} ").strip()
            output  = input(f"  {C.DIM}Output file:{C.RESET} ").strip()
            pw      = input(f"  {C.DIM}Passphrase (blank=none):{C.RESET} ").strip()
            try:
                payload = open(src,"rb").read() if os.path.isfile(src) else src.encode()
                lsb_hide(carrier, payload, output, pw)
                print(f"  {C.GREEN}[+] Hidden in {output} (HMAC + zlib + cipher){C.RESET}")
            except Exception as e: print(f"  {C.YELLOW}[!] {e}{C.RESET}")

        elif cmd == "reveal":
            stego = input(f"  {C.DIM}Stego file:{C.RESET} ").strip()
            pw    = input(f"  {C.DIM}Passphrase:{C.RESET} ").strip()
            out   = input(f"  {C.DIM}Save to file (blank=print):{C.RESET} ").strip()
            try:
                data = lsb_reveal(stego, pw)
                if out: open(out,"wb").write(data); print(f"  {C.GREEN}[+] Saved to {out}{C.RESET}")
                else: print(f"  {C.CYAN}[PAYLOAD]{C.RESET} {data.decode(errors='replace')}")
            except Exception as e: print(f"  {C.YELLOW}[!] {e}{C.RESET}")

        elif cmd == "wav-hide":
            carrier = input(f"  {C.DIM}WAV carrier:{C.RESET} ").strip()
            src     = input(f"  {C.DIM}Payload file or text:{C.RESET} ").strip()
            output  = input(f"  {C.DIM}Output WAV:{C.RESET} ").strip()
            pw      = input(f"  {C.DIM}Passphrase:{C.RESET} ").strip()
            try:
                payload = open(src,"rb").read() if os.path.isfile(src) else src.encode()
                wav_hide(carrier, payload, output, pw)
                print(f"  {C.GREEN}[+] Hidden in {output}{C.RESET}")
            except Exception as e: print(f"  {C.YELLOW}[!] {e}{C.RESET}")

        elif cmd == "wav-reveal":
            stego = input(f"  {C.DIM}Stego WAV:{C.RESET} ").strip()
            pw    = input(f"  {C.DIM}Passphrase:{C.RESET} ").strip()
            try:
                data = wav_reveal(stego, pw)
                print(f"  {C.CYAN}[PAYLOAD]{C.RESET} {data.decode(errors='replace')}")
            except Exception as e: print(f"  {C.YELLOW}[!] {e}{C.RESET}")

        elif cmd == "zwc-hide":
            cover  = input(f"  {C.DIM}Cover text:{C.RESET} ").strip()
            secret = input(f"  {C.DIM}Secret message:{C.RESET} ").strip()
            pw     = input(f"  {C.DIM}Passphrase:{C.RESET} ").strip()
            result = zwc_hide(cover, secret, pw)
            print(f"  {C.GREEN}[+] Stego text (copy everything below):{C.RESET}")
            print(f"  {result}")

        elif cmd == "zwc-reveal":
            stego = input(f"  {C.DIM}Stego text:{C.RESET} ").strip()
            pw    = input(f"  {C.DIM}Passphrase:{C.RESET} ").strip()
            try:
                msg = zwc_reveal(stego, pw)
                print(f"  {C.CYAN}[MESSAGE]{C.RESET} {msg}")
            except Exception as e: print(f"  {C.YELLOW}[!] {e}{C.RESET}")
        else:
            print(f"  {C.DIM}Commands: hide | reveal | wav-hide | wav-reveal | zwc-hide | zwc-reveal | exit{C.RESET}")

def cli_main(args): _interactive()
def launch(): _interactive()
