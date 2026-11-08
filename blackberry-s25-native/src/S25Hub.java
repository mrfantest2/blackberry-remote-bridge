import net.rim.device.api.ui.UiApplication;
import net.rim.device.api.ui.Ui;
import net.rim.device.api.ui.Field;
import net.rim.device.api.ui.FieldChangeListener;
import net.rim.device.api.ui.component.ButtonField;
import net.rim.device.api.ui.component.LabelField;
import net.rim.device.api.ui.component.Dialog;
import net.rim.device.api.ui.container.MainScreen;
import java.io.InputStream;
import java.io.ByteArrayOutputStream;
import javax.microedition.io.Connector;
import javax.microedition.io.HttpConnection;

/** Native BlackBerry OS 7 interface; no BrowserField or web page. */
public final class S25Hub extends UiApplication {
    private static final String BASE = "https://s25.fantest.win";
    private static final int LIMIT = 4096;
    public static void main(String[] args) { S25Hub app = new S25Hub(); app.enterEventDispatcher(); }
    public S25Hub() { pushScreen(new HomeScreen()); }
    private static String fetch(String path) throws Exception {
        HttpConnection connection = null;
        InputStream input = null;
        try {
            connection = (HttpConnection)Connector.open(BASE + path, Connector.READ, true);
            connection.setRequestMethod(HttpConnection.GET);
            connection.setRequestProperty("Accept", "application/json");
            connection.setRequestProperty("Cache-Control", "no-store");
            int code = connection.getResponseCode();
            if (code == 401 || code == 403) return "Pairing required";
            if (code != 200) return "Server response: " + code;
            String type = connection.getHeaderField("Content-Type");
            if (type == null || type.toLowerCase().indexOf("application/json") < 0) return "Native API unavailable";
            input = connection.openInputStream();
            ByteArrayOutputStream output = new ByteArrayOutputStream();
            byte[] buffer = new byte[512]; int count;
            while ((count = input.read(buffer)) != -1) {
                if (output.size() + count > LIMIT) return "Response too large";
                output.write(buffer, 0, count);
            }
            return new String(output.toByteArray(), "UTF-8");
        } finally {
            if (input != null) try { input.close(); } catch (Exception ignored) {}
            if (connection != null) try { connection.close(); } catch (Exception ignored) {}
        }
    }
    private static final class HomeScreen extends MainScreen {
        private final LabelField state = new LabelField("Not connected");
        HomeScreen() {
            super(MainScreen.NO_VERTICAL_SCROLL);
            setTitle("S25 Remote Hub");
            add(new LabelField("Samsung Galaxy S25"));
            add(state);
            addButton("Check connection", "/api/native/v1/status");
            addButton("Battery", "/api/native/v1/battery");
            addButton("Device information", "/api/native/v1/device");
            add(new LabelField("Commands require a paired S25 native API."));
        }
        private void addButton(String title, final String path) {
            ButtonField button = new ButtonField(title, ButtonField.CONSUME_CLICK);
            button.setChangeListener(new FieldChangeListener() {
                public void fieldChanged(Field field, int context) { request(path); }
            });
            add(button);
        }
        private void request(final String path) {
            state.setText("Connecting...");
            new Thread(new Runnable() {
                public void run() {
                    String result;
                    try { result = fetch(path); }
                    catch (Exception ex) { result = "Connection failed"; }
                    final String message = result;
                    UiApplication.getUiApplication().invokeLater(new Runnable() {
                        public void run() { state.setText(message); }
                    });
                }
            }).start();
        }
        public boolean onClose() { Dialog.alert("S25 Remote Hub closed"); return super.onClose(); }
    }
}
