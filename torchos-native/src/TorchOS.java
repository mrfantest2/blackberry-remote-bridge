import java.util.Date;
import net.rim.device.api.i18n.SimpleDateFormat;
import net.rim.device.api.ui.Field;
import net.rim.device.api.ui.FieldChangeListener;
import net.rim.device.api.ui.Font;
import net.rim.device.api.ui.Graphics;
import net.rim.device.api.ui.TouchEvent;
import net.rim.device.api.ui.UiApplication;
import net.rim.device.api.ui.component.CheckboxField;
import net.rim.device.api.ui.component.EditField;
import net.rim.device.api.ui.MenuItem;
import net.rim.device.api.ui.component.RichTextField;
import net.rim.device.api.ui.container.MainScreen;
import net.rim.device.api.ui.decor.BackgroundFactory;

/** Offline launcher preview on stock OS 7. No transport or device-control code. */
public final class TorchOS extends UiApplication {
    private static final int BG = 0x101D28;
    private static final int INK = 0xEDF4F7;
    private static final int MUTED = 0xB9CBD6;
    private static final int ACCENT = 0x82E3C2;
    private static final String[] TITLES = {
        "Devices", "Camera", "Archives", "Network", "Notes & Tasks"
    };
    private static final String[] HINTS = {
        "S25 / Steam Deck / MASTER-PC", "CamDoor / Xiaomi C301",
        "EchoVault / Tahani memories", "Abu Jamal Wi-Fi / VPN health",
        "Local draft / session checklist"
    };
    private String note = "";
    private final boolean[] tasks = new boolean[3];

    public static void main(String[] args) {
        new TorchOS().enterEventDispatcher();
    }

    public TorchOS() { pushScreen(new Home()); }

    // Pure mapping also exercised on the host JVM without loading BlackBerry UI.
    static int shortcut(char key) {
        if (key >= '1' && key <= '5') return key - '1';
        switch (Character.toLowerCase(key)) {
            case 'd': return 0;
            case 'c': return 1;
            case 'a': return 2;
            case 'w': return 3;
            case 'n': return 4;
            case '6': case 's': return 5;
            default: return -1;
        }
    }

    private static void theme(MainScreen screen) {
        screen.getMainManager().setBackground(BackgroundFactory.createSolidBackground(BG));
        screen.setFont(Font.getDefault().derive(Font.PLAIN, 22));
    }

    private static void text(MainScreen screen, String value) {
        RichTextField field = new RichTextField(value, Field.NON_FOCUSABLE) {
            public void paint(Graphics g) { g.setColor(INK); super.paint(g); }
        };
        field.setPadding(10, 16, 10, 16);
        screen.add(field);
    }

    private void open(int section) {
        if (section == 4) pushScreen(new Notes());
        else pushScreen(new Detail(section));
    }

    private final class Home extends MainScreen {
        private final Band status = new Band("", "Offline / Preview", 18);
        private final Row[] rows = new Row[5];
        private int clockEvent;

        Home() {
            super();
            theme(this);
            setTitle(new Band("TorchOS", "NATIVE SHELL  0.1", 28));
            setStatus(new Band("1-5 or D C A W N / S Settings", "Menu: Settings / About  |  Back: Exit", 18));
            add(status);
            add(new Band("Your space. Within reach.", "External services: Not connected", 22));
            for (int i = 0; i < rows.length; i++) {
                final int index = i;
                rows[i] = new Row((i + 1) + "  " + TITLES[i], HINTS[i], new Runnable() {
                    public void run() { open(index); }
                });
                add(rows[i]);
            }
            rows[0].setFocus();
            addMenuItem(new MenuItem("Settings / About", 100, 10) {
                public void run() { open(5); }
            });
            updateClock();
            clockEvent = invokeLater(new Runnable() {
                public void run() { updateClock(); }
            }, 30000, true);
        }

        private void updateClock() {
            status.update(new SimpleDateFormat("EEE dd MMM  HH:mm").format(new Date()));
        }

        protected boolean keyChar(char key, int flags, int time) {
            int section = shortcut(key);
            if (section >= 0) {
                if (section < rows.length) rows[section].setFocus();
                open(section);
                return true;
            }
            return super.keyChar(key, flags, time);
        }

        public boolean onClose() {
            cancelInvokeLater(clockEvent);
            System.exit(0);
            return true;
        }
    }

    private final class Detail extends MainScreen {
        Detail(int section) {
            theme(this);
            setTitle(new Band(section == 5 ? "Settings / About" : TITLES[section], "TORCHOS / PREVIEW", 26));
            setStatus(new Band("Back: Home", "Stock OS7 remains in control", 18));
            switch (section) {
                case 0:
                    text(this, "S25\nNot connected\nBattery and controls unavailable.");
                    text(this, "Steam Deck\nNot connected\nHost status and remote input unavailable.");
                    text(this, "MASTER-PC\nNot connected\nDesktop viewing and control unavailable.");
                    break;
                case 1:
                    text(this, "CamDoor\nNot connected\nNo camera feed or camera controls.");
                    text(this, "Xiaomi C301\nNot connected\nNo camera feed or camera controls.");
                    break;
                case 2:
                    text(this, "EchoVault\nNot connected\nArchive browsing and sync unavailable.");
                    text(this, "Tahani family memories\nNot connected\nNo private photos or records are bundled.");
                    break;
                case 3:
                    text(this, "Abu Jamal Wi-Fi\nNot connected\nSaved project name only; no SSID or signal reading.");
                    text(this, "VPN health\nNot connected\nNo tunnel probe or network settings changes.");
                    break;
                default:
                    text(this, "TorchOS Shell 0.1\nNative BlackBerry Java preview for OS 7.0.\nRuns on stock OS7; not replacement firmware.");
                    text(this, "Offline only. No pairing, network access, camera feed or remote control. External services: Not connected.");
                    text(this, "Keys: 1-5 / D C A W N open Home entries. 6 / S opens this page from Home. Trackpad moves focus; click, Enter or touch opens a row.");
                    text(this, "Notes and tasks live in app memory only and are lost on exit. There are no connection settings yet. Back returns Home; Back at Home exits.");
            }
        }
        public boolean onClose() { UiApplication.getUiApplication().popScreen(this); return true; }
    }

    private final class Notes extends MainScreen implements FieldChangeListener {
        private final EditField draft;
        private final CheckboxField[] checks = new CheckboxField[3];
        Notes() {
            theme(this);
            setTitle(new Band("Notes & Tasks", "LOCAL / SESSION ONLY", 26));
            setStatus(new Band("Back: Home / draft stays this session", "Exit discards draft and checklist", 18));
            text(this, "Local draft (512 characters). Lost on app exit.");
            draft = new EditField("Draft: ", note, 512, Field.EDITABLE);
            draft.setBackground(BackgroundFactory.createSolidBackground(0xFFFFFF));
            draft.setPadding(12, 16, 12, 16);
            draft.setChangeListener(this);
            add(draft);
            text(this, "Session checklist / local planning only");
            String[] labels = { "Plan device pairing", "Review archive access", "Check integration roadmap" };
            for (int i = 0; i < checks.length; i++) {
                checks[i] = new CheckboxField(labels[i], tasks[i]) {
                    public void paint(Graphics g) { g.setColor(INK); super.paint(g); }
                };
                checks[i].setPadding(10, 16, 10, 16);
                checks[i].setChangeListener(this);
                add(checks[i]);
            }
            draft.setFocus();
        }
        public void fieldChanged(Field field, int context) {
            note = draft.getText();
            for (int i = 0; i < checks.length; i++) {
                if (checks[i] != null) tasks[i] = checks[i].getChecked();
            }
        }
        public boolean onClose() { UiApplication.getUiApplication().popScreen(this); return true; }
    }

    /** Two compact, non-focusable lines; content height follows the selected font. */
    private static final class Band extends Field {
        String first;
        private final String second;
        private final Font primary;
        private final Font small = Font.getDefault().derive(Font.PLAIN, 18);
        Band(String first, String second, int size) {
            super(Field.NON_FOCUSABLE);
            this.first = first;
            this.second = second;
            primary = Font.getDefault().derive(Font.BOLD, size);
        }
        void update(String value) { first = value; invalidate(); }
        protected void layout(int width, int height) {
            setExtent(width, Math.min(height, primary.getHeight() + small.getHeight() + 18));
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
        private final Font primary = Font.getDefault().derive(Font.BOLD, 23);
        private final Font small = Font.getDefault().derive(Font.PLAIN, 18);
        Row(String title, String hint, Runnable action) {
            super(Field.FOCUSABLE | Field.USE_ALL_WIDTH);
            this.title = title; this.hint = hint; this.action = action;
        }
        protected void layout(int width, int height) {
            setExtent(width, Math.min(height, Math.max(64, primary.getHeight() + small.getHeight() + 18)));
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
