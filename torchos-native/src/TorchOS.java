import java.util.Date;
import java.util.Enumeration;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import javax.microedition.io.StreamConnection;
import net.rim.device.api.system.ApplicationManager;
import javax.microedition.rms.RecordStore;
import javax.microedition.io.Connector;
import javax.microedition.io.file.FileConnection;
import javax.microedition.io.file.FileSystemRegistry;
import net.rim.device.api.system.DeviceInfo;
import net.rim.device.api.i18n.SimpleDateFormat;
import net.rim.device.api.ui.Field;
import net.rim.device.api.ui.FieldChangeListener;
import net.rim.device.api.ui.Font;
import net.rim.device.api.ui.FontFamily;
import net.rim.device.api.ui.Graphics;
import net.rim.device.api.ui.TouchEvent;
import net.rim.device.api.ui.VirtualKeyboard;
import net.rim.device.api.ui.UiApplication;
import net.rim.device.api.ui.component.ButtonField;
import net.rim.device.api.ui.component.Dialog;
import net.rim.device.api.ui.component.CheckboxField;
import net.rim.device.api.ui.component.EditField;
import net.rim.device.api.ui.MenuItem;
import net.rim.device.api.ui.component.RichTextField;
import net.rim.device.api.ui.container.MainScreen;
import net.rim.device.api.ui.decor.BackgroundFactory;

/** Pocket workstation on stock OS7. Optional TorchLink: app-local remote control of
 *  TorchOS's own screens from the paired Deck over Wi-Fi. No OS-wide input. */
public final class TorchOS extends UiApplication {
    private static final int BG = 0x101D28, INK = 0xEDF4F7, MUTED = 0xB9CBD6, ACCENT = 0x82E3C2;
    private static final String[] TITLES = {
        "Terminal", "Network Center", "Security Center", "Device Manager", "File Manager", "System Monitor"
    };
    private static final String[] HINTS = {
        "Local commands / offline", "Capabilities unavailable / no probes", "Safe local diagnostics",
        "Owner labels / remote offline", "Read-only local folders", "Battery / app runtime memory"
    };
    private final NoteStore store = new NoteStore();
    private final ReportStore reportStore = new ReportStore();
    private NoteData data;
    private final TerminalModel terminal = new TerminalModel();
    private final long started = System.currentTimeMillis();

    private final LinkStore linkStore = new LinkStore();
    private final Link link = new Link();
    private Terminal activeTerminal;
    static volatile String banner = "Remote: off";

    public static void main(String[] args) {
        boolean atBoot = ApplicationManager.getApplicationManager().inStartup();
        TorchOS app = new TorchOS();
        if (atBoot) {
            // Takeover: auto-run at boot. Owner can disable in Remote link settings.
            if (!app.linkStore.load().bootOpen) System.exit(0);
            app.foregroundAfterStartup(0);
        }
        app.enterEventDispatcher();
    }
    public TorchOS() { data = store.load(); pushScreen(new Home()); }
    private void foregroundAfterStartup(final int tries) {
        invokeLater(new Runnable() { public void run() {
            if (!ApplicationManager.getApplicationManager().inStartup()) requestForeground();
            else if (tries < 120) foregroundAfterStartup(tries + 1);
        } }, 1000, false);
    }
    /** Kill switch: leaving the foreground (lock screen, other app, Back) ends any remote session. */
    public void deactivate() { link.stop("TorchOS left the foreground"); }

    static int shortcut(char key) {
        if (key >= '1' && key <= '6') return key - '1';
        switch (Character.toLowerCase(key)) {
            case 't': return 0; case 'w': return 1; case 's': return 2;
            case 'd': return 3; case 'f': return 4; case 'm': return 5;
            case 'n': return 6; case 'c': return 7; case 'a': return 8;
            case 'p': return 9; case 'o': return 10; case '0': return 11; case 'r': return 12;
            default: return -1;
        }
    }
    private static void theme(MainScreen screen) {
        screen.getMainManager().setBackground(BackgroundFactory.createSolidBackground(BG));
        screen.setFont(Font.getDefault().derive(Font.PLAIN, 20));
    }
    private static RichTextField text(MainScreen screen, String value) {
        RichTextField field = new RichTextField(value, Field.NON_FOCUSABLE) {
            public void paint(Graphics g) { g.setColor(INK); super.paint(g); }
        };
        field.setPadding(8, 16, 8, 16); screen.add(field); return field;
    }
    private static void button(MainScreen screen, String label, final Runnable action) {
        ButtonField button = new ButtonField(label, ButtonField.CONSUME_CLICK);
        button.setChangeListener(new FieldChangeListener() {
            public void fieldChanged(Field field, int context) { action.run(); }
        });
        screen.add(button);
    }
    private void open(int section) {
        if (section == 0) pushScreen(new Terminal());
        else if (section == 4) pushScreen(new Files(null, 0));
        else if (section == 5) pushScreen(new SystemMonitor());
        else if (section == 6) pushScreen(new Notes());
        else if (section == 11) pushScreen(new More());
        else if (section == 12) pushScreen(new RemoteLink());
        else pushScreen(new Detail(section));
    }
    private class Page extends MainScreen {
        Page(String title) {
            theme(this); setTitle(new Band(title, "TORCHOS 0.3 / LOCAL", 24));
            setStatus(new Band("Back: previous screen", null, 16));
            addMenuItem(new MenuItem("Back", 90, 1) { public void run() { onClose(); } });
        }
        public boolean onClose() { UiApplication.getUiApplication().popScreen(this); return true; }
    }
    private final class Home extends MainScreen {
        private final Band status = new Band("", "Offline / stock OS7", 16);
        private final Row[] rows = new Row[6];
        private int clockEvent;
        Home() {
            theme(this); setTitle(new Band("TorchOS", "POCKET WORKSTATION / 0.3", 26));
            setStatus(new Band("1-6 primary / 0 More / R Remote", null, 16));
            add(status);
            for (int i = 0; i < rows.length; i++) {
                final int index = i;
                rows[i] = new Row((i + 1) + "  " + TITLES[i], HINTS[i], new Runnable() {
                    public void run() { open(index); }
                }); add(rows[i]);
            }
            // Secondary navigation is both touchable and available in the native menu.
            add(new Row("0  More", "Notes / CamDoor / Archives / Projects", new Runnable() {
                public void run() { open(11); }
            }));
            if (store.error.length() > 0) text(this, store.error);
            rows[0].setFocus();
            addMenuItem(new MenuItem("More / secondary modules", 90, 9) { public void run() { open(11); } });
            addMenuItem(new MenuItem("Notes & Tasks", 95, 9) { public void run() { open(6); } });
            addMenuItem(new MenuItem("Settings / About", 100, 10) { public void run() { open(10); } });
            addMenuItem(new MenuItem("Remote link (Deck)", 105, 10) { public void run() { open(12); } });
            addMenuItem(new MenuItem("Exit TorchOS", 200, 20) { public void run() { link.stop("exit"); cancelInvokeLater(clockEvent); System.exit(0); } });
            updateClock(); clockEvent = invokeLater(new Runnable() {
                public void run() { updateClock(); }
            }, 30000, true);
        }
        private void updateClock() { status.update(new SimpleDateFormat("EEE dd MMM  HH:mm").format(new Date())); }
        protected boolean keyChar(char key, int flags, int time) {
            int section = shortcut(key);
            if (section >= 0) { if (section < rows.length) rows[section].setFocus(); open(section); return true; }
            return super.keyChar(key, flags, time);
        }
        /** Takeover shell: Back keeps TorchOS resident; Menu > Exit TorchOS quits. */
        public boolean onClose() { link.stop("TorchOS sent to background"); requestBackground(); return true; }
    }
    private final class More extends Page {
        More() {
            super("More / secondary");
            String[] names = {"Notes & Tasks", "CamDoor", "EchoVault / Tahani", "Project Monitor", "Settings / About", "Remote link (Deck)"};
            for (int i = 0; i < names.length; i++) {
                final int index = i + 6;
                add(new Row(names[i], i == 0 ? "Local RMS notes and checklist" : i == 6 ? "Pair / start / stop Deck control" : "Offline / details", new Runnable() {
                    public void run() { open(index); }
                }));
            }
        }
    }
    private static String battery() {
        try { int level = DeviceInfo.getBatteryLevel();
            return level >= 0 && level <= 100 ? "Local battery: " + level + "%" : "Local battery unavailable";
        } catch (Exception e) { return "Local battery unavailable"; }
    }
    private String runtimeStatus() {
        return battery() + "\nJava app runtime memory (not total system RAM):\nFree " + Runtime.getRuntime().freeMemory()
            + " / allocated " + Runtime.getRuntime().totalMemory() + " bytes\nApp elapsed: "
            + ((System.currentTimeMillis() - started) / 1000) + " seconds";
    }
    private final class Detail extends Page {
        Detail(int section) {
            super(section < 6 ? TITLES[section] : section == 7 ? "CamDoor" : section == 8 ? "EchoVault / Tahani" : section == 9 ? "Project Monitor" : "Settings / About");
            switch (section) {
                case 1:
                    text(this, "Network capabilities unavailable. No verified local radio diagnostics in CP002. No probes or network settings changes.");
                    text(this, "Abu Jamal Wi-Fi\nNot connected\nSaved project name only.\nVPN health\nNot connected\nNo tunnel checks."); break;
                case 2:
                    text(this, "Safe local diagnostics\n" + runtimeStatus());
                    text(this, "RMS: " + (store.error.length() == 0 ? "available; saves checked individually" : store.error));
                    text(this, "Checksums disabled: no hashing workflow implemented. No scans, exploitation or security settings changes."); break;
                case 3:
                    text(this, battery());
                    for (int i = 0; i < data.labels.length; i++) text(this, "Owner label " + (i+1) + ": " + (data.labels[i].length() == 0 ? "(empty)" : data.labels[i]) + "\nOffline / remote status unavailable");
                    text(this, "Edit saved owner labels in Notes & Tasks. Labels do not discover or pair devices.");
                    text(this, "S25\nNot connected\nSteam Deck\nNot connected\nMASTER-PC\nNot connected\nNo remote controls."); break;
                case 5:
                    text(this, runtimeStatus()); text(this, "Snapshot on opening this page; reopen to refresh. Total system RAM and CPU load unavailable."); break;
                case 7:
                    text(this, "CamDoor\nNot connected\nXiaomi C301\nNot connected\nNo camera feed or camera controls."); break;
                case 8:
                    text(this, "EchoVault\nNot connected\nTahani family memories\nNot connected\nNo private archive data bundled or synchronized."); break;
                case 9:
                    text(this, "Project Monitor\nOffline / remote project status unavailable. No gateway transport, project polling or remote actions."); break;
                default:
                    text(this, "TorchOS 0.3.0\nNative BlackBerry OS7 shell, not Linux or replacement firmware. Starts at boot (can be disabled in Remote link).");
                    text(this, "TorchLink: optional, owner-started Wi-Fi session from the paired Deck. Controls TorchOS screens only (open, back, home, allowlisted terminal commands). HMAC-SHA256 authenticated, not encrypted. Ends on lock, background, timeout or Stop.");
                    text(this, "Local terminal: help date about clear status history notes files. Notes, three tasks and three owner labels use a dedicated bounded RMS store. No terminal history persistence. " + store.error);
                    text(this, "Home: 1-6 / T W S D F M. N Notes, C CamDoor, A Archives, P Projects, O About, 0 More. Trackpad / Enter / touch activate. Terminal has a native keyboard menu. Files are read-only, permission dependent.");
            }
        }
    }

    static final class TerminalModel {
        static final int INPUT_LIMIT = 96, OUTPUT_LIMIT = 4096, HISTORY_LIMIT = 16;
        String output = "TorchOS local terminal. Type help.\n";
        final String[] history = new String[HISTORY_LIMIT];
        int historyCount, cursor;
        String draft = "";
        String execute(String raw) {
            cursor = historyCount;
            draft = "";
            if (raw == null || raw.length() > INPUT_LIMIT) return append("Rejected: input limit is 96 characters.\n");
            for (int i=0;i<raw.length();i++) { char c = raw.charAt(i); if (c < 0x20 || c == 0x7F) return append("Rejected: control characters are not allowed.\n"); }
            String command = raw.trim();
            if (command.length() > 0) {
                if (historyCount == HISTORY_LIMIT) { for (int i=1;i<historyCount;i++) history[i-1]=history[i]; historyCount--; }
                history[historyCount++] = command;
            }
            cursor = historyCount;
            String result;
            if (command.equals("clear")) { output = ""; return ""; }
            if (command.equals("help")) result = "Local only: help date about clear status history notes files remote. No arguments or shell execution.";
            else if (command.equals("date")) result = "Local device clock: " + new Date().toString();
            else if (command.equals("about")) result = "TorchOS 0.3 / stock OS7 pocket workstation. Not replacement firmware.";
            else if (command.equals("status")) result = "Local terminal ready. " + banner + ". TorchLink controls TorchOS screens only.";
            else if (command.equals("notes")) result = "Open Notes & Tasks from Home (N or More) for local RMS notes.";
            else if (command.equals("files")) result = "Open File Manager from Home (5) for read-only local folders; permission required.";
            else if (command.equals("remote")) result = banner + ". Pair and start from More > Remote link.";
            else if (command.equals("history")) {
                StringBuffer b = new StringBuffer("Session history:");
                for (int i=0;i<historyCount;i++) b.append('\n').append(i+1).append(" ").append(history[i]);
                result = b.toString();
            } else result = "Rejected: only help date about clear status history notes files remote are allowed. No arguments or shell execution.";
            append("local> " + command + "\n" + result + "\n"); return result;
        }
        private String append(String value) {
            output += value;
            if (output.length() > OUTPUT_LIMIT) output = output.substring(output.length() - OUTPUT_LIMIT);
            return value;
        }
        private String boundedDraft(String value) {
            if (value == null) return "";
            return value.length() > INPUT_LIMIT ? value.substring(0, INPUT_LIMIT) : value;
        }
        String previous(String currentInput) {
            if (cursor >= historyCount) draft = boundedDraft(currentInput);
            if (cursor > 0) cursor--;
            return cursor < historyCount ? history[cursor] : draft;
        }
        String next(String currentInput) {
            if (cursor < historyCount) {
                cursor++;
                if (cursor < historyCount) return history[cursor];
                return draft;
            }
            draft = boundedDraft(currentInput);
            return draft;
        }
        String previous() { return previous(""); }
        String next() { return next(""); }
    }
    private final class Terminal extends Page {
        private final RichTextField output;
        private final EditField input;
        Terminal() {
            super("Terminal / offline");
            output = new RichTextField(terminal.output, Field.FOCUSABLE | Field.READONLY) {
                public void paint(Graphics g) { g.setColor(ACCENT); super.paint(g); }
            };
            output.setPadding(8, 16, 8, 16); add(output);
            try { output.setFont(FontFamily.forName("BBAlpha Mono").getFont(Font.PLAIN, 18)); }
            catch (Exception e) { /* local default font remains usable */ }
            input = new EditField("local> ", "", TerminalModel.INPUT_LIMIT, Field.EDITABLE) {
                protected boolean keyChar(char key, int flags, int time) {
                    if (key == '\n' || key == '\r') { submit(); return true; }
                    return super.keyChar(key, flags, time);
                }
            };
            input.setBackground(BackgroundFactory.createSolidBackground(0xFFFFFF)); add(input);
            button(this, "Run", new Runnable() { public void run() { submit(); } });
            button(this, "Previous command", new Runnable() { public void run() { input.setText(terminal.previous(input.getText())); input.setFocus(); } });
            button(this, "Next command", new Runnable() { public void run() { input.setText(terminal.next(input.getText())); input.setFocus(); } });
            button(this, "Help", new Runnable() { public void run() { command("help"); } });
            button(this, "Clear", new Runnable() { public void run() { command("clear"); } });
            addMenuItem(new MenuItem("Show keyboard", 80, 1) {
                public void run() {
                    input.setFocus(); VirtualKeyboard keyboard = getVirtualKeyboard();
                    if (keyboard != null) keyboard.setVisibility(VirtualKeyboard.SHOW);
                    else Dialog.alert("Software keyboard unavailable on this device.");
                }
            });
            input.setFocus();
            activeTerminal = this;
        }
        private void submit() { command(input.getText()); }
        void command(String value) { terminal.execute(value); output.setText(terminal.output); input.setText(""); input.setFocus(); }
        public boolean onClose() { if (activeTerminal == this) activeTerminal = null; return super.onClose(); }
    }

    static final class NoteData {
        String note = "";
        final boolean[] tasks = new boolean[3];
        final String[] labels = {"", "", ""};
    }
    static final class NoteCodec {
        static byte[] encode(NoteData value) throws IOException {
            if (value == null || value.note == null || value.note.length() > 512) throw new IOException("Note limit");
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            DataOutputStream out = new DataOutputStream(bytes);
            out.writeInt(0x544F5332); out.writeByte(1); out.writeUTF(value.note);
            for (int i=0;i<3;i++) out.writeByte(value.tasks[i] ? 1 : 0);
            for (int i=0;i<3;i++) {
                if (value.labels[i] == null || value.labels[i].length() > 40) throw new IOException("Label limit");
                out.writeUTF(value.labels[i]);
            }
            out.flush(); byte[] result = bytes.toByteArray();
            if (result.length > 2048) throw new IOException("Record limit"); return result;
        }
        static NoteData decode(byte[] bytes) throws IOException {
            if (bytes == null || bytes.length > 2048) throw new IOException("Record limit");
            DataInputStream in = new DataInputStream(new ByteArrayInputStream(bytes));
            if (in.readInt() != 0x544F5332 || in.readUnsignedByte() != 1) throw new IOException("Record version");
            NoteData result = new NoteData(); result.note = in.readUTF();
            if (result.note.length() > 512) throw new IOException("Note limit");
            for (int i=0;i<3;i++) { int flag = in.readUnsignedByte(); if (flag > 1) throw new IOException("Task flag"); result.tasks[i] = flag == 1; }
            for (int i=0;i<3;i++) { result.labels[i] = in.readUTF(); if (result.labels[i].length() > 40) throw new IOException("Label limit"); }
            if (in.available() != 0) throw new IOException("Trailing data"); return result;
        }
    }
    static final class NoteStore {
        String error = "";
        private boolean blocked;
        NoteData load() {
            RecordStore rms = null;
            try {
                rms = RecordStore.openRecordStore("TorchOS_CP002", true);
                int records = rms.getNumRecords();
                if (records == 0) return new NoteData();
                if (records != 1) throw new IOException("Unexpected records");
                if (rms.getRecordSize(1) > 2048) throw new IOException("Record limit");
                return NoteCodec.decode(rms.getRecord(1));
            } catch (Exception e) { blocked = true; error = "Persistence error: notes unavailable. Existing store preserved; saves blocked this session."; return new NoteData(); }
            finally { if (rms != null) try { rms.closeRecordStore(); } catch (Exception e) { blocked = true; error = "Persistence error: store close failed; saves blocked this session."; } }
        }
        boolean save(NoteData value) {
            if (blocked) return false;
            byte[] bytes;
            try { bytes = NoteCodec.encode(value); }
            catch (Exception e) { error = "Persistence error: invalid draft. Existing notes preserved; edit and retry."; return false; }
            RecordStore rms = null; boolean saved = false;
            try {
                rms = RecordStore.openRecordStore("TorchOS_CP002", true);
                int records = rms.getNumRecords();
                if (records == 0) rms.addRecord(bytes, 0, bytes.length);
                else if (records == 1) {
                    if (rms.getRecordSize(1) > 2048) throw new IOException("Record limit");
                    NoteCodec.decode(rms.getRecord(1));
                    rms.setRecord(1, bytes, 0, bytes.length);
                } else throw new IOException("Unexpected records");
                error = ""; saved = true;
            } catch (Exception e) { blocked = true; error = "Persistence error: save failed; existing notes state unconfirmed; saves blocked this session."; }
            finally { if (rms != null) try { rms.closeRecordStore(); } catch (Exception e) { blocked = true; error = "Persistence error: store close failed; save unconfirmed; saves blocked this session."; saved = false; } }
            return saved;
        }
    }
    private final class Notes extends Page {
        private final EditField draft;
        private final EditField[] labels = new EditField[3];
        private final CheckboxField[] checks = new CheckboxField[3];
        private final RichTextField message;
        Notes() {
            super("Notes & Tasks");
            message = text(this, store.error.length() == 0 ? "Local RMS / Save or Back to persist. 512-character draft." : store.error);
            draft = new EditField("Draft: ", data.note, 512, Field.EDITABLE);
            draft.setBackground(BackgroundFactory.createSolidBackground(0xFFFFFF)); add(draft);
            String[] names = {"Plan device pairing", "Review archive access", "Check integration roadmap"};
            for (int i=0;i<3;i++) {
                checks[i] = new CheckboxField(names[i], data.tasks[i]) {
                    public void paint(Graphics g) { g.setColor(INK); super.paint(g); }
                }; add(checks[i]);
                labels[i] = new EditField("Owner label " + (i+1) + ": ", data.labels[i], 40, Field.EDITABLE);
                labels[i].setBackground(BackgroundFactory.createSolidBackground(0xFFFFFF)); add(labels[i]);
            }
            button(this, "Save", new Runnable() { public void run() { saveDraft(); } });
            addMenuItem(new MenuItem("Back without saving", 100, 2) { public void run() { UiApplication.getUiApplication().popScreen(Notes.this); } });
            draft.setFocus();
        }
        private boolean saveDraft() {
            data.note = draft.getText();
            for (int i=0;i<3;i++) { data.tasks[i] = checks[i].getChecked(); data.labels[i] = labels[i].getText(); }
            boolean saved = store.save(data); message.setText(saved ? "Saved locally in TorchOS RMS." : store.error); return saved;
        }
        public boolean onClose() { if (!saveDraft()) { Dialog.alert(store.error); return false; } return super.onClose(); }
    }

    // Only direct children of OS-supplied roots/folders; no user-entered paths or URL escapes.
    static boolean safeChild(String child) {
        if (child == null || child.length() == 0 || child.length() > 255) return false;
        String name = child.endsWith("/") ? child.substring(0, child.length()-1) : child;
        if (name.length() == 0 || name.equals(".") || name.equals("..")) return false;
        for (int i=0;i<name.length();i++) {
            char c = name.charAt(i);
            if (c < 32 || c == 127 || c == '/' || c == '\\' || c == ':' || c == '%' || c == '?' || c == '#') return false;
        }
        return true;
    }
    private final class Files extends Page {
        Files(final String url, final int depth) {
            super("File Manager / read-only");
            text(this, "Local folder listing only. No writes, delete, rename or file content reads. Permission dependent. Up to 64 entries / 8 levels. Back goes up.");
            FileConnection connection = null;
            try {
                Enumeration entries;
                if (url == null) entries = FileSystemRegistry.listRoots();
                else { connection = (FileConnection) Connector.open(url, Connector.READ); entries = connection.list(); }
                int count = 0;
                while (entries.hasMoreElements() && count < 64) {
                    final String name = (String) entries.nextElement();
                    count++;
                    if (!safeChild(name)) continue;
                    if (name.endsWith("/")) {
                        final String next = url == null ? "file:///" + name : url + name;
                        if (depth >= 8) text(this, name + " (folder depth limit reached)");
                        else add(new Row(name, "Read-only folder", new Runnable() {
                            public void run() { pushScreen(new Files(next, depth+1)); }
                        }));
                    } else text(this, name + " (read-only; content not opened)");
                }
                if (count == 0) text(this, "No accessible entries.");
                if (entries.hasMoreElements()) text(this, "Listing limited to 64 entries.");
            } catch (Exception e) { text(this, "Files unavailable: permission denied or JSR75 listing unsupported. No files changed."); }
            finally { if (connection != null) try { connection.close(); } catch (Exception e) { text(this, "Read-only connection close failed."); } }
        }
    }
    /** Bounded standalone RMS record for the most recent local diagnostics snapshot. */
    static final class ReportStore {
        private static final String NAME = "TorchOS_CP002_Report";
        private static final int MAGIC = 0x54524F53;
        private static final int LIMIT = 1024;
        String error = "";
        private boolean blocked;

        static String decode(byte[] bytes) throws IOException {
            if (bytes == null || bytes.length < 7 || bytes.length > LIMIT) throw new IOException("Report length");
            DataInputStream in = new DataInputStream(new ByteArrayInputStream(bytes));
            if (in.readInt() != MAGIC || in.readUnsignedByte() != 1) throw new IOException("Report version");
            String report = in.readUTF();
            if (report.length() > 384 || in.available() != 0) throw new IOException("Report contents");
            return report;
        }
        String load() {
            RecordStore rms = null;
            String report = "No locally saved diagnostic report.";
            try {
                rms = RecordStore.openRecordStore(NAME, true);
                int count = rms.getNumRecords();
                if (count == 1) {
                    if (rms.getRecordSize(1) > LIMIT) throw new IOException("Report size");
                    report = decode(rms.getRecord(1));
                } else if (count != 0) throw new IOException("Report record count");
            } catch (Exception e) {
                blocked = true;
                error = "Report storage error; existing records preserved. Saves blocked until restart.";
            } finally {
                if (rms != null) try { rms.closeRecordStore(); }
                catch (Exception e) { blocked = true; error = "Report close error; saves blocked."; }
            }
            return blocked ? error : report;
        }
        boolean save(String report) {
            if (blocked) return false;
            RecordStore rms = null;
            boolean saved = false;
            try {
                if (report == null || report.length() > 384) throw new IOException("Report limit");
                ByteArrayOutputStream bytes = new ByteArrayOutputStream();
                DataOutputStream out = new DataOutputStream(bytes);
                out.writeInt(MAGIC); out.writeByte(1); out.writeUTF(report); out.flush();
                byte[] data = bytes.toByteArray();
                if (data.length > LIMIT) throw new IOException("Report bytes limit");
                rms = RecordStore.openRecordStore(NAME, true);
                int count = rms.getNumRecords();
                if (count == 0) rms.addRecord(data, 0, data.length);
                else if (count == 1) {
                    if (rms.getRecordSize(1) > LIMIT) throw new IOException("Existing report too large");
                    decode(rms.getRecord(1)); // Reject corrupt data before any write.
                    rms.setRecord(1, data, 0, data.length);
                } else throw new IOException("Unexpected report records");
                error = "";
                saved = true;
            } catch (Exception e) {
                blocked = true;
                error = "Report save failed; existing report state unconfirmed; saves blocked until restart.";
            } finally {
                if (rms != null) try { rms.closeRecordStore(); }
                catch (Exception e) { blocked = true; error = "Report close error; save unconfirmed."; }
            }
            return saved && !blocked;
        }
    }

    private final class SystemMonitor extends Page {
        private final RichTextField message;
        SystemMonitor() {
            super("System Monitor");
            text(this, runtimeStatus());
            text(this, "Local snapshot only. No network checks, personal files, or privileged diagnostics. One saved report at a time.");
            message = text(this, "Select Save local report or View saved report.");
            button(this, "Save local report", new Runnable() {
                public void run() {
                    String snapshot = "TorchOS CP002 / local\n" +
                        new SimpleDateFormat("yyyy-MM-dd HH:mm").format(new Date()) + "\n" +
                        runtimeStatus() + "\nNetwork: disabled / no remote commands";
                    boolean success = reportStore.save(snapshot);
                    message.setText(success ? "Saved locally in TorchOS Report RMS." : reportStore.error);
                }
            });
            button(this, "View saved report", new Runnable() {
                public void run() { message.setText(reportStore.load()); }
            });
        }
    }


    /** RMS record for TorchLink settings. The pairing key never leaves this store or the screen. */
    static final class LinkData {
        String host = ""; int port = 47810; byte[] key = null; boolean bootOpen = true; long counter;
    }
    static final class LinkStore {
        private static final String NAME = "TorchOS_Link";
        private static final int MAGIC = 0x544C4E4B;
        String error = "";
        static byte[] encode(LinkData d) throws IOException {
            if (d.host.length() > 15 || (d.key != null && d.key.length != TorchLinkCore.KEY_BYTES)) throw new IOException("Link limits");
            ByteArrayOutputStream bytes = new ByteArrayOutputStream();
            DataOutputStream out = new DataOutputStream(bytes);
            out.writeInt(MAGIC); out.writeByte(1); out.writeUTF(d.host); out.writeInt(d.port);
            out.writeByte(d.key == null ? 0 : d.key.length); if (d.key != null) out.write(d.key);
            out.writeBoolean(d.bootOpen); out.writeLong(d.counter); out.flush();
            return bytes.toByteArray();
        }
        static LinkData decode(byte[] b) throws IOException {
            if (b == null || b.length > 256) throw new IOException("Link record");
            DataInputStream in = new DataInputStream(new ByteArrayInputStream(b));
            if (in.readInt() != MAGIC || in.readUnsignedByte() != 1) throw new IOException("Link version");
            LinkData d = new LinkData(); d.host = in.readUTF(); d.port = in.readInt();
            int k = in.readUnsignedByte();
            if (k != 0 && k != TorchLinkCore.KEY_BYTES) throw new IOException("Link key");
            if (k > 0) { d.key = new byte[k]; in.readFully(d.key); }
            d.bootOpen = in.readBoolean(); d.counter = in.readLong();
            if (in.available() != 0) throw new IOException("Trailing data");
            return d;
        }
        LinkData load() {
            RecordStore rms = null;
            try {
                rms = RecordStore.openRecordStore(NAME, true);
                if (rms.getNumRecords() == 0) return new LinkData();
                if (rms.getNumRecords() != 1) throw new IOException("records");
                return decode(rms.getRecord(1));
            } catch (Exception e) { error = "Remote link settings unreadable; using defaults."; return new LinkData(); }
            finally { if (rms != null) try { rms.closeRecordStore(); } catch (Exception e) { } }
        }
        boolean save(LinkData d) {
            RecordStore rms = null;
            try {
                byte[] b = encode(d);
                rms = RecordStore.openRecordStore(NAME, true);
                if (rms.getNumRecords() == 0) rms.addRecord(b, 0, b.length); else rms.setRecord(1, b, 0, b.length);
                error = ""; return true;
            } catch (Exception e) { error = "Remote link settings save failed."; return false; }
            finally { if (rms != null) try { rms.closeRecordStore(); } catch (Exception e) { } }
        }
    }

    /** One owner-started outbound Wi-Fi session to the paired Deck. Every exit path closes it. */
    private final class Link implements Runnable {
        private Thread thread;
        private StreamConnection conn;
        private TorchLinkCore.Session session;
        private int watchdog = -1;
        String last = "Never started";

        synchronized boolean active() { return thread != null; }
        synchronized String start() {
            if (thread != null) return "Session already running.";
            if (!isForeground()) return "TorchOS must be in the foreground.";
            LinkData d = linkStore.load();
            if (d.key == null) return "Not paired: enter the Deck pairing code first.";
            if (!TorchLinkCore.validHost(d.host) || d.port < 1024 || d.port > 65535) return "Set the Deck IPv4 address and port first.";
            d.counter++;
            if (!linkStore.save(d)) return linkStore.error;
            String seed = d.counter + "|" + System.currentTimeMillis() + "|" + Runtime.getRuntime().freeMemory()
                + "|" + new Object().hashCode() + "|" + Thread.currentThread().hashCode();
            session = new TorchLinkCore.Session(d.key, TorchLinkCore.ascii(seed), System.currentTimeMillis());
            final String url = "socket://" + d.host + ":" + d.port + ";deviceside=true;interface=wifi;ConnectionTimeout=15000";
            target = url;
            thread = new Thread(this); thread.start();
            setBanner("REMOTE: connecting to " + d.host);
            watchdog = invokeLater(new Runnable() { public void run() { check(); } }, 5000, true);
            return "Connecting to " + d.host + ":" + d.port + " over Wi-Fi...";
        }
        private String target;
        void check() {
            TorchLinkCore.Session s = session;
            if (s == null) return;
            long now = System.currentTimeMillis();
            if (!isForeground()) stop("TorchOS left the foreground");
            else if (s.isOpen() && (now - startedAt > TorchLinkCore.SESSION_MS)) stop("session expired");
        }
        private long startedAt;
        void stop(String why) {
            StreamConnection c;
            synchronized (this) {
                if (thread == null) return;
                thread = null; c = conn; conn = null;
                if (session != null) session.close(why);
                last = "Stopped: " + why;
            }
            if (watchdog >= 0) { cancelInvokeLater(watchdog); watchdog = -1; }
            if (c != null) try { c.close(); } catch (Exception e) { }
            setBanner("Remote: off");
        }
        private boolean current(Thread t) { synchronized (this) { return thread == t; } }
        public void run() {
            Thread me = Thread.currentThread();
            InputStream in = null; OutputStream out = null;
            try {
                StreamConnection c = (StreamConnection) Connector.open(target, Connector.READ_WRITE, true);
                synchronized (this) { if (thread != me) { c.close(); return; } conn = c; }
                in = c.openInputStream(); out = c.openOutputStream();
                send(out, session.hello());
                if (!session.welcome(readLine(in), System.currentTimeMillis())) { finish(me, session.reason); return; }
                startedAt = System.currentTimeMillis();
                setBanner("REMOTE CONTROL ACTIVE - Deck");
                while (current(me)) {
                    TorchLinkCore.Command cmd = session.accept(readLine(in), System.currentTimeMillis());
                    if (cmd == null) { finish(me, session.reason); return; }
                    final TorchLinkCore.Command fc = cmd;
                    final String[] result = {"ERR", "not run"};
                    invokeAndWait(new Runnable() { public void run() { dispatch(fc, result); } });
                    send(out, session.ack(cmd.seq, result[0].equals("OK"), result[1]));
                    if (cmd.op.equals("BYE")) { finish(me, "Deck ended session"); return; }
                }
            } catch (Exception e) {
                finish(me, "connection closed (" + e.getClass().getName() + ")");
            } finally {
                if (in != null) try { in.close(); } catch (Exception e) { }
                if (out != null) try { out.close(); } catch (Exception e) { }
            }
        }
        private void finish(Thread me, final String why) {
            if (!current(me)) return;
            invokeLater(new Runnable() { public void run() { stop(why); } });
        }
        private void send(OutputStream out, String line) throws IOException {
            byte[] b = TorchLinkCore.ascii(line);
            if (b == null) throw new IOException("non-ASCII frame");
            out.write(b); out.write('\n'); out.flush();
        }
        private String readLine(InputStream in) throws IOException {
            StringBuffer b = new StringBuffer();
            while (true) {
                int c = in.read();
                if (c < 0) throw new IOException("Deck disconnected");
                if (c == '\n') return b.toString();
                if (c < 0x20 || c > 0x7e || b.length() >= TorchLinkCore.MAX_LINE) throw new IOException("bad frame");
                b.append((char) c);
            }
        }
    }
    private void setBanner(final String text) {
        banner = text;
        invokeLater(new Runnable() { public void run() {
            net.rim.device.api.ui.Screen s = getActiveScreen(); if (s != null) s.invalidate();
        } });
    }
    /** Runs on the event thread. Only TorchOS's own navigation and terminal allowlist. */
    private void dispatch(TorchLinkCore.Command c, String[] result) {
        if (!isForeground()) { result[1] = "TorchOS not in foreground"; link.stop("TorchOS left the foreground"); return; }
        net.rim.device.api.ui.Screen top = getActiveScreen();
        if (c.op.equals("OPEN")) {
            int section = Integer.parseInt(c.arg);
            if (section == 12) { result[1] = "Remote link screen cannot be opened remotely"; return; }
            open(section); result[0] = "OK"; result[1] = "opened " + c.arg;
        } else if (c.op.equals("BACK")) {
            if (top instanceof Home || top instanceof RemoteLink) { result[1] = "nothing to go back to"; return; }
            ((MainScreen) top).onClose(); result[0] = "OK"; result[1] = "back";
        } else if (c.op.equals("HOME")) {
            int guard = 0;
            while (!(getActiveScreen() instanceof Home) && !(getActiveScreen() instanceof RemoteLink) && guard++ < 16)
                ((MainScreen) getActiveScreen()).onClose();
            result[0] = getActiveScreen() instanceof Home ? "OK" : "ERR"; result[1] = "home";
        } else if (c.op.equals("RUN")) {
            if (activeTerminal == null || getActiveScreen() != activeTerminal) open(0);
            activeTerminal.command(c.arg);
            result[0] = "OK"; result[1] = terminalTail();
        } else if (c.op.equals("STATUS") || c.op.equals("BYE")) {
            String name = top.getClass().getName();
            result[0] = "OK"; result[1] = "screen " + name.substring(name.lastIndexOf('$') + 1) + "; " + battery();
        }
    }
    private String terminalTail() {
        String o = terminal.output;
        int cut = o.lastIndexOf('\n', o.length() - 2);
        return o.substring(cut < 0 ? 0 : cut + 1).trim();
    }

    /** Owner-only, on-device pairing and session control. Never reachable over TorchLink. */
    private final class RemoteLink extends Page {
        private final EditField host, port, code;
        private final CheckboxField boot;
        private final RichTextField message;
        RemoteLink() {
            super("Remote link (Deck)");
            final LinkData d = linkStore.load();
            text(this, "Lets the paired Steam Deck control TorchOS screens over Wi-Fi: open pages, back, home and allowlisted terminal commands. Not other apps. Ends on Stop, lock, leaving TorchOS, 90 s idle or 10 min.");
            message = text(this, (d.key == null ? "Not paired." : "Paired.") + " " + link.last + " " + linkStore.error);
            host = new EditField("Deck IPv4: ", d.host, 15, Field.EDITABLE);
            port = new EditField("Port: ", Integer.toString(d.port), 5, Field.EDITABLE | EditField.FILTER_INTEGER);
            code = new EditField("Pairing code: ", "", 48, Field.EDITABLE);
            boot = new CheckboxField("Open TorchOS at boot", d.bootOpen) {
                public void paint(Graphics g) { g.setColor(INK); super.paint(g); }
            };
            EditField[] fs = {host, port, code};
            for (int i = 0; i < fs.length; i++) { fs[i].setBackground(BackgroundFactory.createSolidBackground(0xFFFFFF)); add(fs[i]); }
            add(boot);
            button(this, "Save settings / pair", new Runnable() { public void run() { save(); } });
            button(this, "Start remote session", new Runnable() { public void run() { message.setText(link.start()); } });
            button(this, "Stop remote session", new Runnable() { public void run() { link.stop("stopped on phone"); message.setText(link.last); } });
            button(this, "Forget pairing", new Runnable() { public void run() {
                link.stop("pairing removed"); LinkData x = linkStore.load(); x.key = null;
                message.setText(linkStore.save(x) ? "Pairing removed." : linkStore.error);
            } });
            host.setFocus();
        }
        private void save() {
            LinkData d = linkStore.load();
            String h = host.getText().trim();
            int p;
            try { p = Integer.parseInt(port.getText().trim()); } catch (Exception e) { p = -1; }
            if (!TorchLinkCore.validHost(h)) { message.setText("Invalid IPv4 address, e.g. 192.168.1.20"); return; }
            if (p < 1024 || p > 65535) { message.setText("Port must be 1024-65535."); return; }
            String c = code.getText().trim();
            if (c.length() > 0) {
                byte[] k = TorchLinkCore.pairingKey(c);
                if (k == null) { message.setText("Pairing code must be the 32 characters shown on the Deck."); return; }
                d.key = k;
            }
            d.host = h; d.port = p; d.bootOpen = boot.getChecked();
            code.setText("");
            message.setText(linkStore.save(d) ? (d.key == null ? "Saved. Not paired yet." : "Saved. Paired with Deck.") : linkStore.error);
        }
    }

    /** Two compact, non-focusable lines; content height follows the selected font. */
    private static final class Band extends Field {
        String first;
        private final String second;
        private final Font primary;
        private final Font small = Font.getDefault().derive(Font.PLAIN, 16);
        Band(String first, String second, int size) {
            super(Field.NON_FOCUSABLE);
            this.first = first;
            this.second = second;
            primary = Font.getDefault().derive(Font.BOLD, size);
        }
        void update(String value) { first = value; invalidate(); }
        protected void layout(int width, int height) {
            setExtent(width, Math.min(height, primary.getHeight() + small.getHeight() + 14));
        }
        protected void paint(Graphics g) {
            g.setColor(BG); g.fillRect(0, 0, getWidth(), getHeight());
            g.setFont(primary); g.setColor(INK);
            g.drawText(first, 16, 6, Graphics.ELLIPSIS, getWidth() - 32);
            g.setFont(small); g.setColor(second == null && banner.startsWith("REMOTE") ? 0xFFB347 : ACCENT);
            g.drawText(second == null ? banner : second, 16, primary.getHeight() + 9, Graphics.ELLIPSIS, getWidth() - 32);
        }
    }

    /** Native focus traversal, explicit trackpad / Enter / touch activation. */
    private static final class Row extends Field {
        private final String title;
        private final String hint;
        private final Runnable action;
        private boolean armed;
        private final Font primary = Font.getDefault().derive(Font.BOLD, 21);
        private final Font small = Font.getDefault().derive(Font.PLAIN, 16);
        Row(String title, String hint, Runnable action) {
            super(Field.FOCUSABLE | Field.USE_ALL_WIDTH);
            this.title = title; this.hint = hint; this.action = action;
        }
        protected void layout(int width, int height) {
            setExtent(width, Math.min(height, Math.max(60, primary.getHeight() + small.getHeight() + 14)));
        }
        protected void paint(Graphics g) {
            g.setColor(isFocus() ? 0x244B57 : BG);
            g.fillRect(0, 0, getWidth(), getHeight());
            if (isFocus()) { g.setColor(ACCENT); g.fillRect(0, 0, 5, getHeight()); }
            g.setFont(primary); g.setColor(INK);
            g.drawText(title, 16, 6, Graphics.ELLIPSIS, getWidth() - 32);
            g.setFont(small); g.setColor(MUTED);
            g.drawText(hint, 16, primary.getHeight() + 9, Graphics.ELLIPSIS, getWidth() - 32);
            g.setColor(0x2D414F); g.drawLine(16, getHeight() - 1, getWidth() - 16, getHeight() - 1);
        }
        protected void drawFocus(Graphics g, boolean on) { /* paint owns focus appearance */ }
        protected void onFocus(int direction) { super.onFocus(direction); invalidate(); }
        protected void onUnfocus() { armed = false; super.onUnfocus(); invalidate(); }
        protected boolean navigationClick(int status, int time) { action.run(); return true; }
        protected boolean keyChar(char key, int flags, int time) {
            if (key == '\n' || key == ' ') { action.run(); return true; }
            return super.keyChar(key, flags, time);
        }
        protected boolean touchEvent(TouchEvent event) {
            int x = event.getX(1), y = event.getY(1);
            boolean inside = x >= 0 && x < getWidth() && y >= 0 && y < getHeight();
            switch (event.getEvent()) {
                case TouchEvent.DOWN:
                    if (!inside) return false;
                    setFocus(); armed = true; return true;
                case TouchEvent.MOVE:
                    if (!inside) armed = false;
                    return armed;
                case TouchEvent.UP:
                    boolean activate = armed && inside;
                    armed = false;
                    if (activate) action.run();
                    return activate;
                default: return super.touchEvent(event);
            }
        }
    }
}
