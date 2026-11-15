/**
 * TorchLink v1 protocol core: CLDC 1.1 only (no RIM crypto API, no signing).
 *
 * App-local remote control of TorchOS's OWN screens from the paired Steam
 * Deck. No OS-wide input, no EventInjector, no shell. Transport-agnostic:
 * TorchOS supplies the socket; this class only builds and verifies lines.
 *
 * Wire (ASCII lines, '\n', max 512 bytes, '|' separated):
 *   phone -> deck  HELLO|1|<pn>|<mac("TL1|HELLO|"+pn)>
 *   deck  -> phone WELCOME|1|<dn>|<mac("TL1|WELCOME|"+pn+"|"+dn)>
 *   deck  -> phone CMD|<seq>|<op>|<arg>|<mac("TL1|CMD|"+pn+"|"+dn+"|"+seq+"|"+op+"|"+arg)>
 *   phone -> deck  ACK|<seq>|<OK|ERR>|<msg>|<mac("TL1|ACK|"+pn+"|"+dn+"|"+seq+"|"+st+"|"+msg)>
 * mac = lowercase hex HMAC-SHA256(pairing key). pn/dn = 32 lowercase hex.
 * seq must be exactly previous+1, starting at 1. Any MAC/sequence/format
 * failure closes the session (fail closed). Reference: companion/torchlink.py
 */
final class TorchLinkCore {
    static final int MAX_LINE = 512, KEY_BYTES = 20, RUN_LIMIT = 96, MSG_LIMIT = 160;
    static final long SESSION_MS = 600000L, IDLE_MS = 90000L;
    static final int MAX_COMMANDS = 500;
    static final String[] OPS = {"HOME", "OPEN", "BACK", "RUN", "STATUS", "BYE"};

    private TorchLinkCore() {}

    // ---- SHA-256 / HMAC-SHA256 (FIPS 180-4, RFC 2104) ----
    private static final int[] K = {
        0x428a2f98,0x71374491,0xb5c0fbcf,0xe9b5dba5,0x3956c25b,0x59f111f1,0x923f82a4,0xab1c5ed5,
        0xd807aa98,0x12835b01,0x243185be,0x550c7dc3,0x72be5d74,0x80deb1fe,0x9bdc06a7,0xc19bf174,
        0xe49b69c1,0xefbe4786,0x0fc19dc6,0x240ca1cc,0x2de92c6f,0x4a7484aa,0x5cb0a9dc,0x76f988da,
        0x983e5152,0xa831c66d,0xb00327c8,0xbf597fc7,0xc6e00bf3,0xd5a79147,0x06ca6351,0x14292967,
        0x27b70a85,0x2e1b2138,0x4d2c6dfc,0x53380d13,0x650a7354,0x766a0abb,0x81c2c92e,0x92722c85,
        0xa2bfe8a1,0xa81a664b,0xc24b8b70,0xc76c51a3,0xd192e819,0xd6990624,0xf40e3585,0x106aa070,
        0x19a4c116,0x1e376c08,0x2748774c,0x34b0bcb5,0x391c0cb3,0x4ed8aa4a,0x5b9cca4f,0x682e6ff3,
        0x748f82ee,0x78a5636f,0x84c87814,0x8cc70208,0x90befffa,0xa4506ceb,0xbef9a3f7,0xc67178f2
    };
    private static int rotr(int x, int n) { return (x >>> n) | (x << (32 - n)); }

    static byte[] sha256(byte[] msg) {
        int[] h = {0x6a09e667,0xbb67ae85,0x3c6ef372,0xa54ff53a,0x510e527f,0x9b05688c,0x1f83d9ab,0x5be0cd19};
        long bitLen = (long) msg.length * 8L;
        int padded = ((msg.length + 9 + 63) / 64) * 64;
        byte[] m = new byte[padded];
        System.arraycopy(msg, 0, m, 0, msg.length);
        m[msg.length] = (byte) 0x80;
        for (int i = 0; i < 8; i++) m[padded - 1 - i] = (byte) (bitLen >>> (8 * i));
        int[] w = new int[64];
        for (int off = 0; off < padded; off += 64) {
            for (int t = 0; t < 16; t++) {
                int j = off + t * 4;
                w[t] = ((m[j] & 0xff) << 24) | ((m[j+1] & 0xff) << 16) | ((m[j+2] & 0xff) << 8) | (m[j+3] & 0xff);
            }
            for (int t = 16; t < 64; t++) {
                int s0 = rotr(w[t-15], 7) ^ rotr(w[t-15], 18) ^ (w[t-15] >>> 3);
                int s1 = rotr(w[t-2], 17) ^ rotr(w[t-2], 19) ^ (w[t-2] >>> 10);
                w[t] = w[t-16] + s0 + w[t-7] + s1;
            }
            int a=h[0], b=h[1], c=h[2], d=h[3], e=h[4], f=h[5], g=h[6], hh=h[7];
            for (int t = 0; t < 64; t++) {
                int t1 = hh + (rotr(e,6) ^ rotr(e,11) ^ rotr(e,25)) + ((e & f) ^ (~e & g)) + K[t] + w[t];
                int t2 = (rotr(a,2) ^ rotr(a,13) ^ rotr(a,22)) + ((a & b) ^ (a & c) ^ (b & c));
                hh = g; g = f; f = e; e = d + t1; d = c; c = b; b = a; a = t1 + t2;
            }
            h[0]+=a; h[1]+=b; h[2]+=c; h[3]+=d; h[4]+=e; h[5]+=f; h[6]+=g; h[7]+=hh;
        }
        byte[] out = new byte[32];
        for (int i = 0; i < 8; i++) {
            out[i*4] = (byte) (h[i] >>> 24); out[i*4+1] = (byte) (h[i] >>> 16);
            out[i*4+2] = (byte) (h[i] >>> 8); out[i*4+3] = (byte) h[i];
        }
        return out;
    }

    static byte[] hmac(byte[] key, byte[] msg) {
        byte[] k = key.length > 64 ? sha256(key) : key;
        byte[] ipad = new byte[64 + msg.length], opad = new byte[64 + 32];
        for (int i = 0; i < 64; i++) {
            byte b = i < k.length ? k[i] : 0;
            ipad[i] = (byte) (b ^ 0x36); opad[i] = (byte) (b ^ 0x5c);
        }
        System.arraycopy(msg, 0, ipad, 64, msg.length);
        System.arraycopy(sha256(ipad), 0, opad, 64, 32);
        return sha256(opad);
    }

    // ---- encodings ----
    private static final String HEX = "0123456789abcdef";
    static String hex(byte[] b) {
        StringBuffer s = new StringBuffer(b.length * 2);
        for (int i = 0; i < b.length; i++) { s.append(HEX.charAt((b[i] >> 4) & 15)); s.append(HEX.charAt(b[i] & 15)); }
        return s.toString();
    }
    static boolean isHex(String s, int len) {
        if (s == null || s.length() != len) return false;
        for (int i = 0; i < len; i++) if (HEX.indexOf(s.charAt(i)) < 0) return false;
        return true;
    }
    /** Printable ASCII only (0x20..0x7e). Returns null otherwise. */
    static byte[] ascii(String s) {
        if (s == null) return null;
        byte[] out = new byte[s.length()];
        for (int i = 0; i < out.length; i++) {
            char c = s.charAt(i);
            if (c < 0x20 || c > 0x7e) return null;
            out[i] = (byte) c;
        }
        return out;
    }
    /** RFC 4648 base32 pairing code; spaces/dashes ignored, case-insensitive. Exactly 20 bytes or null. */
    static byte[] pairingKey(String code) {
        if (code == null) return null;
        final String A = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567";
        byte[] out = new byte[KEY_BYTES];
        int bits = 0, acc = 0, n = 0, chars = 0;
        for (int i = 0; i < code.length(); i++) {
            char c = code.charAt(i);
            if (c == ' ' || c == '-') continue;
            if (c >= 'a' && c <= 'z') c = (char) (c - 32);
            int v = A.indexOf(c);
            if (v < 0 || chars >= 32) return null;
            chars++;
            acc = (acc << 5) | v; bits += 5;
            if (bits >= 8) { bits -= 8; out[n++] = (byte) (acc >> bits); acc &= (1 << bits) - 1; }
        }
        return chars == 32 && n == KEY_BYTES ? out : null;
    }
    static boolean sameMac(String a, String b) {
        if (a == null || b == null || a.length() != b.length()) return false;
        int diff = 0;
        for (int i = 0; i < a.length(); i++) diff |= a.charAt(i) ^ b.charAt(i);
        return diff == 0;
    }
    /** Split on '|' into exactly n fields, else null. */
    static String[] fields(String line, int n) {
        if (line == null || line.length() == 0 || line.length() > MAX_LINE || ascii(line) == null) return null;
        String[] f = new String[n];
        int start = 0;
        for (int i = 0; i < n - 1; i++) {
            int bar = line.indexOf('|', start);
            if (bar < 0) return null;
            f[i] = line.substring(start, bar); start = bar + 1;
        }
        f[n - 1] = line.substring(start);
        return f[n - 1].indexOf('|') >= 0 ? null : f;
    }
    static String clean(String s, int limit) {
        if (s == null) return "-";
        StringBuffer b = new StringBuffer();
        for (int i = 0; i < s.length() && b.length() < limit; i++) {
            char c = s.charAt(i);
            b.append(c >= 0x20 && c <= 0x7e && c != '|' ? c : ' ');
        }
        return b.length() == 0 ? "-" : b.toString();
    }

    /** One validated command handed to the UI. */
    static final class Command {
        final long seq; final String op, arg;
        Command(long seq, String op, String arg) { this.seq = seq; this.op = op; this.arg = arg; }
    }

    /** Phone-side session state machine. Not thread-safe; use from the link thread. */
    static final class Session {
        private final byte[] key;
        final String phoneNonce;
        private String deckNonce;
        private long seq, started, last;
        private int count;
        private boolean open, closed;
        String reason = "";

        Session(byte[] key, byte[] nonceSeed, long now) {
            if (key == null || key.length != KEY_BYTES) throw new IllegalArgumentException("pairing key");
            this.key = key;
            byte[] digest = sha256(nonceSeed);
            byte[] n = new byte[16];
            System.arraycopy(digest, 0, n, 0, 16);
            phoneNonce = hex(n);
            started = last = now;
        }
        private String mac(String text) { return hex(hmac(key, ascii(text))); }
        boolean isOpen() { return open && !closed; }
        boolean isClosed() { return closed; }
        void close(String why) { if (!closed) { closed = true; open = false; reason = why; } }

        String hello() { return "HELLO|1|" + phoneNonce + "|" + mac("TL1|HELLO|" + phoneNonce); }

        boolean welcome(String line, long now) {
            if (closed || open) { close("unexpected WELCOME"); return false; }
            String[] f = fields(line, 4);
            if (f == null || !f[0].equals("WELCOME") || !f[1].equals("1") || !isHex(f[2], 32) || !isHex(f[3], 64)) {
                close("malformed WELCOME"); return false;
            }
            if (f[2].equals(phoneNonce)) { close("reflected nonce"); return false; }
            if (!sameMac(f[3], mac("TL1|WELCOME|" + phoneNonce + "|" + f[2]))) { close("Deck authentication failed"); return false; }
            deckNonce = f[2]; open = true; started = last = now;
            return true;
        }

        /** Returns a validated command or null (session then closed, see reason). */
        Command accept(String line, long now) {
            if (!isOpen()) { close("session not open"); return null; }
            if (now - started > SESSION_MS) { close("session expired"); return null; }
            if (now - last > IDLE_MS) { close("idle timeout"); return null; }
            if (count >= MAX_COMMANDS) { close("command limit"); return null; }
            String[] f = fields(line, 5);
            if (f == null || !f[0].equals("CMD") || !isHex(f[4], 64)) { close("malformed command"); return null; }
            long n;
            try { n = Long.parseLong(f[1]); } catch (NumberFormatException e) { close("bad sequence"); return null; }
            if (!f[1].equals(Long.toString(n))) { close("bad sequence"); return null; }
            String expect = mac("TL1|CMD|" + phoneNonce + "|" + deckNonce + "|" + f[1] + "|" + f[2] + "|" + f[3]);
            if (!sameMac(f[4], expect)) { close("command MAC rejected"); return null; }
            if (n != seq + 1) { close("replayed or skipped sequence"); return null; }
            if (!validOp(f[2], f[3])) { close("command not allowed"); return null; }
            seq = n; count++; last = now;
            return new Command(n, f[2], f[3]);
        }

        String ack(long forSeq, boolean ok, String message) {
            String st = ok ? "OK" : "ERR";
            String msg = clean(message, MSG_LIMIT);
            return "ACK|" + forSeq + "|" + st + "|" + msg + "|"
                + mac("TL1|ACK|" + phoneNonce + "|" + deckNonce + "|" + forSeq + "|" + st + "|" + msg);
        }
    }

    static boolean validOp(String op, String arg) {
        if (op == null || arg == null || arg.length() == 0) return false;
        if (op.equals("OPEN")) {
            if (arg.length() > 2) return false;
            for (int i = 0; i < arg.length(); i++) if (arg.charAt(i) < '0' || arg.charAt(i) > '9') return false;
            int v = Integer.parseInt(arg);
            return v >= 0 && v <= 11 && Integer.toString(v).equals(arg);
        }
        if (op.equals("RUN")) return arg.length() <= RUN_LIMIT && ascii(arg) != null;
        for (int i = 0; i < OPS.length; i++) if (OPS[i].equals(op)) return arg.equals("-");
        return false;
    }

    /** Dotted IPv4 literal only (no DNS, no hostnames). */
    static boolean validHost(String h) {
        if (h == null || h.length() < 7 || h.length() > 15) return false;
        int parts = 0, val = -1;
        for (int i = 0; i <= h.length(); i++) {
            char c = i < h.length() ? h.charAt(i) : '.';
            if (c == '.') {
                if (val < 0 || val > 255) return false;
                parts++; val = -1;
            } else if (c >= '0' && c <= '9') {
                if (val == 0) return false; // no leading zeros
                val = (val < 0 ? 0 : val * 10) + (c - '0');
                if (val > 255) return false;
            } else return false;
        }
        return parts == 4;
    }
}
