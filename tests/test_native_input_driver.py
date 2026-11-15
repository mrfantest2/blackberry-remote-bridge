"""Host-doubles for the signed BlackBerry EventInjector adapter.

Tests compilation/execution without a handset or privileged APIs. CI uses
Java 8; on the Steam Deck the fallback JDK8 toolchain is selected.
"""
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
ADAPTER = ROOT / "torchos-native/remote-input/TorchOSInputDriver.java"
SOURCES = {
    "net/rim/device/api/applicationcontrol/ApplicationPermissions.java": """
package net.rim.device.api.applicationcontrol;
public class ApplicationPermissions {
  public static final int PERMISSION_INPUT_SIMULATION=1, VALUE_ALLOW=1;
}""",
    "net/rim/device/api/applicationcontrol/ApplicationPermissionsManager.java": """
package net.rim.device.api.applicationcontrol;
public class ApplicationPermissionsManager {
  public static int permission=0;
  private static ApplicationPermissionsManager instance=new ApplicationPermissionsManager();
  public static ApplicationPermissionsManager getInstance(){return instance;}
  public int getPermission(int p){return permission;}
}""",
    "net/rim/device/api/system/Characters.java": """
package net.rim.device.api.system;
public interface Characters {
  char ENTER=13, BACKSPACE=8, ESCAPE=27, TAB=9, SPACE=32;
}""",
    "net/rim/device/api/ui/UiApplication.java": """
package net.rim.device.api.ui;
public class UiApplication {
  public static boolean active=true;
  private static UiApplication instance=new UiApplication();
  public static UiApplication getUiApplication(){return instance;}
  public boolean isForeground(){return active;}
}""",
    "net/rim/device/api/system/EventInjector.java": """
package net.rim.device.api.system;
public class EventInjector {
  public static int events=0;
  public static void invokeEvent(Object e){events++;}
  public static class NavigationEvent {
    public static final int NAVIGATION_CLICK=1, NAVIGATION_UNCLICK=2, NAVIGATION_MOVEMENT=3;
    public NavigationEvent(int event,int x,int y,int flags) {}
  }
  public static class KeyCodeEvent {
    public static final int KEY_DOWN=1, KEY_UP=2;
    public KeyCodeEvent(int event,char key,int flags) {}
  }
  public static class TouchEvent {
    public static final int DOWN=1, UP=2, MOVE=3, CLICK=4, UNCLICK=5;
    public TouchEvent(int event,int x,int y,int a,int b,int c) {}
  }
}""",
    "InputDriverHostHarness.java": """
import net.rim.device.api.applicationcontrol.*;
import net.rim.device.api.ui.*;
import net.rim.device.api.system.*;
public class InputDriverHostHarness {
  static void assertTrue(boolean okay) {
    if (!okay) throw new AssertionError("Host gate check failed");
  }
  static void denied(TorchOSInputDriver d, String op, String value,
                     int x,int y,int x2,int y2) {
    int before=EventInjector.events;
    try { d.dispatch(op,value,x,y,x2,y2);
      throw new AssertionError("Unauthorized input accepted");
    } catch (SecurityException expected) {}
    assertTrue(before==EventInjector.events);
  }
  static void bad(TorchOSInputDriver d, String op, String value,
                  int x,int y,int x2,int y2) {
    int before=EventInjector.events;
    try { d.dispatch(op,value,x,y,x2,y2);
      throw new AssertionError("Invalid input accepted");
    } catch (IllegalArgumentException expected) {}
    assertTrue(before==EventInjector.events);
  }
  public static void main(String[] args) {
    TorchOSInputDriver d=new TorchOSInputDriver();
    assertTrue(!d.isArmed());
    denied(d,"KEY","a",0,0,0,0);
    assertTrue(!d.armFromPhone(false));
    assertTrue(!d.armFromPhone(true)); // permission missing
    ApplicationPermissionsManager.permission=ApplicationPermissions.VALUE_ALLOW;
    UiApplication.active=false;
    assertTrue(!d.armFromPhone(true)); // not foreground
    UiApplication.active=true;
    assertTrue(d.armFromPhone(true));
    d.dispatch("NAV","UP",0,0,0,0);
    d.dispatch("NAV","SELECT",0,0,0,0);
    d.dispatch("NAV","BACK",0,0,0,0);
    d.dispatch("KEY","a",0,0,0,0);
    d.dispatch("KEY","ENTER",0,0,0,0);
    d.dispatch("TAP","",479,639,0,0);
    d.dispatch("SWIPE","",0,0,479,639);
    assertTrue(EventInjector.events==21);
    bad(d,"KEY","CTRL+ALT+DEL",0,0,0,0);
    bad(d,"TAP","",480,10,0,0);
    bad(d,"SWIPE","",2,2,2,2);
    denied(d,"NAV","HOME",0,0,0,0);
    UiApplication.active=false;
    denied(d,"KEY","b",0,0,0,0);
    assertTrue(!d.isArmed());
    UiApplication.active=true;
    assertTrue(d.armFromPhone(true));
    ApplicationPermissionsManager.permission=0;
    denied(d,"KEY","b",0,0,0,0);
    ApplicationPermissionsManager.permission=ApplicationPermissions.VALUE_ALLOW;
    assertTrue(d.armFromPhone(true));
    d.disarm();
    denied(d,"KEY","b",0,0,0,0);
    System.out.println("PASS: native input host gate, controls and kill switch");
  }
}""",
}


class NativeInputDriverTests(unittest.TestCase):
    def test_driver_with_stub_blackberry_apis(self):
        java_home = os.environ.get("JDK8_HOME") or os.environ.get("JAVA_HOME")
        if not java_home:
            fallback = Path("/home/SD/BlackBerryBridge/toolchains/jdk8")
            if (fallback / "bin/javac").exists():
                java_home = str(fallback)
        javac = str(Path(java_home) / "bin/javac") if java_home else shutil.which("javac")
        java = str(Path(java_home) / "bin/java") if java_home else shutil.which("java")
        if not (javac and java):
            self.fail("Java toolchain unavailable; CI must provision Java 8")
        with tempfile.TemporaryDirectory(prefix="torchos-input-host-") as directory:
            work = Path(directory)
            for name, content in SOURCES.items():
                target = work / name
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(content)
            files = [str(work / name) for name in SOURCES] + [str(ADAPTER)]
            compile_result = subprocess.run(
                [javac, "-source", "7", "-target", "7", "-d", str(work)] + files,
                capture_output=True, text=True, timeout=25,
            )
            self.assertEqual(compile_result.returncode, 0, compile_result.stderr)
            result = subprocess.run(
                [java, "-cp", str(work), "InputDriverHostHarness"],
                capture_output=True, text=True, timeout=15,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("PASS:", result.stdout)


if __name__ == "__main__":
    unittest.main()
