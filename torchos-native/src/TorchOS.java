import java.util.Date;
import java.util.Enumeration;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.DataInputStream;
import java.io.DataOutputStream;
import java.io.IOException;
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

/** Local pocket workstation on stock OS7. No native network transport. */
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

    public static void main(String[] args) { new TorchOS().enterEventDispatcher(); }
    public TorchOS() { data = store.load(); pushScreen(new Home()); }

    static int shortcut(char key) {
        if (key >= '1' && key <= '6') return key - '1';
        switch (Character.toLowerCase(key)) {
            case 't': return 0; case 'w': return 1; case 's': return 2;
            case 'd': return 3; case 'f': return 4; case 'm': return 5;
            case 'n': return 6; case 'c': return 7; case 'a': return 8;
            case 'p': return 9; case 'o': return 10; case '0': return 11;
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
        else pushScreen(new Detail(section));
    }
    private class Page extends MainScreen {
        Page(String title) {
            theme(this); setTitle(new Band(title, "TORCHOS CP002 / LOCAL", 24));
            setStatus(new Band("Back: previous screen", "Remote services: disconnected", 16));
            addMenuItem(new MenuItem("Back", 90, 1) { public void run() { onClose(); } });
        }
        public boolean onClose() { UiApplication.getUiApplication().popScreen(this); return true; }
    }
    private final class Home extends MainScreen {
        private final Band status = new Band("", "Offline / stock OS7", 16);
        private final Row[] rows = new Row[6];
        private int clockEvent;
        Home() {
            theme(this); setTitle(new Band("TorchOS", "POCKET WORKSTATION / CP002", 26));
            setStatus(new Band("1-6 primary / 0 More / N Notes", "Menu: secondary / O About / Back: Exit", 16));
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
        public boolean onClose() { cancelInvokeLater(clockEvent); System.exit(0); return true; }
    }
    private final class More extends Page {
        More() {
            super("More / secondary");
            String[] names = {"Notes & Tasks", "CamDoor", "EchoVault / Tahani", "Project Monitor", "Settings / About"};
            for (int i = 0; i < names.length; i++) {
                final int index = i + 6;
                add(new Row(names[i], i == 0 ? "Local RMS notes and checklist" : "Offline / details", new Runnable() {
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
                    text(this, "TorchOS CP002 / 0.2.0\nNative BlackBerry OS7 shell, not Linux or replacement firmware.");
                    text(this, "Native transport not implemented. Gateway is a read-only contract prototype only; modern TLS on this handset is unverified. No pairing settings or remote execution.");
                    text(this, "Local terminal: help date about clear status history notes files. Notes, three tasks and three owner labels use a dedicated bounded RMS store. No terminal history persistence. " + store.error);
                    text(this, "Home: 1-6 / T W S D F M. N Notes, C CamDoor, A Archives, P Projects, O About, 0 More. Trackpad / Enter / touch activate. Terminal has a native keyboard menu. Files are read-only, permission dependent.");
            }
        }
    }

    static final class TerminalModel {
        static final int INPUT_LIMIT = 96, OUTPUT_LIMIT = 4096, HISTORY_LIMIT = 16;
        String output = "TorchOS local terminal. Type help. Remote services: disconnected.\n";
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
            if (command.equals("help")) result = "Local only: help date about clear status history notes files. No arguments or shell execution.";
            else if (command.equals("date")) result = "Local device clock: " + new Date().toString();
            else if (command.equals("about")) result = "TorchOS CP002 / stock OS7. Offline pocket workstation.";
            else if (command.equals("status")) result = "Local terminal ready. Remote services: disconnected. Native transport not implemented.";
            else if (command.equals("notes")) result = "Open Notes & Tasks from Home (N or More) for local RMS notes.";
            else if (command.equals("files")) result = "Open File Manager from Home (5) for read-only local folders; permission required.";
            else if (command.equals("history")) {
                StringBuffer b = new StringBuffer("Session history:");
                for (int i=0;i<historyCount;i++) b.append('\n').append(i+1).append(" ").append(history[i]);
                result = b.toString();
            } else result = "Rejected: only help date about clear status history notes files are allowed. No arguments or shell execution.";
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
        }
        private void submit() { command(input.getText()); }
        private void command(String value) { terminal.execute(value); output.setText(terminal.output); input.setText(""); input.setFocus(); }
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
            g.setFont(small); g.setColor(ACCENT);
            g.drawText(second, 16, primary.getHeight() + 9, Graphics.ELLIPSIS, getWidth() - 32);
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
