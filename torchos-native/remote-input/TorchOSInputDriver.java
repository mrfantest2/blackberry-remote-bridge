import net.rim.device.api.applicationcontrol.ApplicationPermissions;
import net.rim.device.api.applicationcontrol.ApplicationPermissionsManager;
import net.rim.device.api.system.Characters;
import net.rim.device.api.system.EventInjector;
import net.rim.device.api.ui.UiApplication;

/**
 * SIGNED-API ADAPTER ONLY: not installed on a handset.
 * A future receiver must verify the HMAC, session, expiry, replay, input
 * schema, and rate limit before calling dispatch. No receiver, network
 * listener, pairing key, or background service is bundled here.
 */
final class TorchOSInputDriver {
    private static final long MAX_SESSION_MS = 300000L;
    private boolean armed;
    private long until;

    synchronized boolean armFromPhone(boolean userConfirmed) {
        disarm();
        if (!userConfirmed || !foreground() || !hasPermission()) return false;
        armed = true;
        until = System.currentTimeMillis() + MAX_SESSION_MS;
        return true;
    }

    synchronized void disarm() {
        armed = false;
        until = 0L;
    }

    synchronized boolean isArmed() {
        if (!armed || System.currentTimeMillis() >= until
                || !foreground() || !hasPermission()) {
            disarm();
            return false;
        }
        return true;
    }

    private boolean foreground() {
        UiApplication app = UiApplication.getUiApplication();
        return app != null && app.isForeground();
    }

    private boolean hasPermission() {
        try {
            return ApplicationPermissionsManager.getInstance().getPermission(
                ApplicationPermissions.PERMISSION_INPUT_SIMULATION
            ) == ApplicationPermissions.VALUE_ALLOW;
        } catch (RuntimeException denied) {
            return false;
        }
    }

    /** Only call after trusted phone-side authorization and validated HMAC. */
    synchronized void dispatch(String op, String value,
                               int x1, int y1, int x2, int y2) {
        if (!isArmed()) throw new SecurityException("Input disabled");
        if ("NAV".equals(op)) {
            if ("SELECT".equals(value)) {
                EventInjector.invokeEvent(new EventInjector.NavigationEvent(
                    EventInjector.NavigationEvent.NAVIGATION_CLICK, 0, 0, 0));
                EventInjector.invokeEvent(new EventInjector.NavigationEvent(
                    EventInjector.NavigationEvent.NAVIGATION_UNCLICK, 0, 0, 0));
            } else if ("BACK".equals(value)) {
                emit(Characters.ESCAPE);
            } else if ("HOME".equals(value)) {
                // No system-wide input until lock-screen detection is verified.
                throw new SecurityException("System-wide control disabled");
            } else {
                int dx = 0, dy = 0;
                if ("UP".equals(value)) dy = -1;
                else if ("DOWN".equals(value)) dy = 1;
                else if ("LEFT".equals(value)) dx = -1;
                else if ("RIGHT".equals(value)) dx = 1;
                else throw new IllegalArgumentException("Unknown navigation");
                EventInjector.invokeEvent(new EventInjector.NavigationEvent(
                    EventInjector.NavigationEvent.NAVIGATION_MOVEMENT, dx, dy, 0));
            }
        } else if ("KEY".equals(op)) {
            if (value == null) throw new IllegalArgumentException("Null key");
            char key;
            if ("ENTER".equals(value)) key = Characters.ENTER;
            else if ("BACKSPACE".equals(value)) key = Characters.BACKSPACE;
            else if ("ESCAPE".equals(value)) key = Characters.ESCAPE;
            else if ("TAB".equals(value)) key = Characters.TAB;
            else if ("SPACE".equals(value)) key = Characters.SPACE;
            else if (value.length() == 1 && value.charAt(0) >= 32
                    && value.charAt(0) <= 126) key = value.charAt(0);
            else throw new IllegalArgumentException("Unknown key");
            emit(key);
        } else if ("TAP".equals(op)) {
            check(x1, y1);
            tap(x1, y1);
        } else if ("SWIPE".equals(op)) {
            check(x1, y1);
            check(x2, y2);
            if (x1 == x2 && y1 == y2) throw new IllegalArgumentException("Empty swipe");
            EventInjector.invokeEvent(new EventInjector.TouchEvent(
                EventInjector.TouchEvent.DOWN, x1, y1, -1, -1, -1));
            for (int step = 1; step <= 6; step++) {
                int x = x1 + (x2 - x1) * step / 6;
                int y = y1 + (y2 - y1) * step / 6;
                EventInjector.invokeEvent(new EventInjector.TouchEvent(
                    EventInjector.TouchEvent.MOVE, x, y, -1, -1, -1));
            }
            EventInjector.invokeEvent(new EventInjector.TouchEvent(
                EventInjector.TouchEvent.UP, x2, y2, -1, -1, -1));
        } else {
            throw new IllegalArgumentException("Unknown operation");
        }
    }

    private void check(int x, int y) {
        if (x < 0 || x >= 480 || y < 0 || y >= 640)
            throw new IllegalArgumentException("Point outside screen");
    }

    private void emit(char key) {
        EventInjector.invokeEvent(new EventInjector.KeyCodeEvent(
            EventInjector.KeyCodeEvent.KEY_DOWN, key, 0));
        EventInjector.invokeEvent(new EventInjector.KeyCodeEvent(
            EventInjector.KeyCodeEvent.KEY_UP, key, 0));
    }

    private void tap(int x, int y) {
        EventInjector.invokeEvent(new EventInjector.TouchEvent(
            EventInjector.TouchEvent.DOWN, x, y, -1, -1, -1));
        EventInjector.invokeEvent(new EventInjector.TouchEvent(
            EventInjector.TouchEvent.CLICK, x, y, -1, -1, -1));
        EventInjector.invokeEvent(new EventInjector.TouchEvent(
            EventInjector.TouchEvent.UNCLICK, x, y, -1, -1, -1));
        EventInjector.invokeEvent(new EventInjector.TouchEvent(
            EventInjector.TouchEvent.UP, x, y, -1, -1, -1));
    }
}
