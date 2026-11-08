import net.rim.device.api.ui.UiApplication;
import net.rim.device.api.ui.container.MainScreen;
import net.rim.device.api.browser.field2.BrowserField;
import net.rim.device.api.browser.field2.BrowserFieldConfig;
import net.rim.device.api.browser.field2.BrowserFieldRequest;

/** BlackBerry OS 7 native BrowserField2 shell for the S25 Hub. */
public final class S25Hub extends UiApplication {
    public static void main(String[] args) {
        S25Hub app = new S25Hub();
        app.enterEventDispatcher();
    }
    public S25Hub() { pushScreen(new HubScreen()); }
    private static final class HubScreen extends MainScreen {
        private final BrowserField browser;
        HubScreen() {
            super(MainScreen.NO_VERTICAL_SCROLL | MainScreen.NO_HORIZONTAL_SCROLL);
            setTitle("S25 Hub");
            BrowserFieldConfig config = new BrowserFieldConfig();
            config.setProperty(BrowserFieldConfig.JAVASCRIPT_ENABLED, Boolean.TRUE);
            config.setProperty(BrowserFieldConfig.ENABLE_COOKIES, Boolean.TRUE);
            config.setProperty(BrowserFieldConfig.NAVIGATION_MODE, BrowserFieldConfig.NAVIGATION_MODE_POINTER);
            browser = new BrowserField(config);
            add(browser);
            browser.requestContent(new BrowserFieldRequest("https://s25.fantest.win/"));
        }
        protected void makeMenu(net.rim.device.api.ui.component.Menu menu, int instance) {
            menu.add(new net.rim.device.api.ui.MenuItem("Reload", 100, 10) {
                public void run() { browser.requestContent(new BrowserFieldRequest("https://s25.fantest.win/")); }
            });
            super.makeMenu(menu, instance);
        }
    }
}
