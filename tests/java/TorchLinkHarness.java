import java.io.BufferedReader;
import java.io.InputStreamReader;

/** Host-only driver for TorchLinkCore. Line protocol on stdin/stdout. */
public class TorchLinkHarness {
    static byte[] unhex(String s) {
        byte[] b = new byte[s.length() / 2];
        for (int i = 0; i < b.length; i++) b[i] = (byte) Integer.parseInt(s.substring(2*i, 2*i+2), 16);
        return b;
    }
    public static void main(String[] a) throws Exception {
        BufferedReader in = new BufferedReader(new InputStreamReader(System.in, "US-ASCII"));
        String mode = in.readLine();
        if (mode.equals("VECTORS")) {
            String line;
            while ((line = in.readLine()) != null) {
                String[] p = line.split(" ", -1);
                if (p[0].equals("SHA")) System.out.println(TorchLinkCore.hex(TorchLinkCore.sha256(unhex(p[1]))));
                else if (p[0].equals("HMAC")) System.out.println(TorchLinkCore.hex(TorchLinkCore.hmac(unhex(p[1]), unhex(p[2]))));
                else if (p[0].equals("CODE")) { byte[] k = TorchLinkCore.pairingKey(line.substring(5)); System.out.println(k == null ? "null" : TorchLinkCore.hex(k)); }
                else if (p[0].equals("HOST")) System.out.println(TorchLinkCore.validHost(p[1]));
                else if (p[0].equals("OP")) System.out.println(TorchLinkCore.validOp(p[1], line.substring(4 + p[1].length())));
            }
            return;
        }
        TorchLinkCore.Session s = new TorchLinkCore.Session(unhex(mode), unhex(in.readLine()), 0L);
        System.out.println(s.hello());
        String line;
        while ((line = in.readLine()) != null) {
            int sp = line.indexOf(' ');
            long now = Long.parseLong(line.substring(0, sp));
            String body = line.substring(sp + 1);
            if (body.startsWith("WELCOME")) {
                System.out.println(s.welcome(body, now) ? "OPEN" : "CLOSED " + s.reason);
            } else {
                TorchLinkCore.Command c = s.accept(body, now);
                if (c == null) System.out.println("CLOSED " + s.reason);
                else System.out.println("CMD " + c.op + " " + c.arg + " " + s.ack(c.seq, true, "did " + c.op));
            }
            System.out.flush();
        }
    }
}
