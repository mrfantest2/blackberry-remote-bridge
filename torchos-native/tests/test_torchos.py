"""Source/config checks plus actual Java fragments run against host-only UI doubles."""
import os
from pathlib import Path
import re
import subprocess
import unittest
from unittest import mock
import xml.etree.ElementTree as ET
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / 'src/TorchOS.java').read_text()
HTML = (ROOT / 'preview/index.html').read_text()
BUILD = ROOT / 'build/host-tests'


def resolve_jdk():
    """Honor explicit JDK 8 first, then CI's JAVA_HOME, then the Deck fallback."""
    return Path(os.environ.get('JDK8_HOME') or os.environ.get('JAVA_HOME')
                or '/home/SD/BlackBerryBridge/toolchains/jdk8')


JDK = resolve_jdk()


class JdkSelection(unittest.TestCase):
    def test_explicit_jdk8_home_wins(self):
        with mock.patch.dict(os.environ, {
            'JDK8_HOME': '/tmp/jdk8-override', 'JAVA_HOME': '/tmp/java-home'
        }):
            self.assertEqual(resolve_jdk(), Path('/tmp/jdk8-override'))

    def test_java_home_fallback(self):
        with mock.patch.dict(os.environ, {
            'JDK8_HOME': '', 'JAVA_HOME': '/tmp/java-home'
        }):
            self.assertEqual(resolve_jdk(), Path('/tmp/java-home'))

    def test_default_when_neither_set(self):
        with mock.patch.dict(os.environ, {
            'JDK8_HOME': '', 'JAVA_HOME': ''
        }):
            self.assertEqual(resolve_jdk(), Path('/home/SD/BlackBerryBridge/toolchains/jdk8'))


def fragment(marker):
    start = SRC.index(marker)
    opening = SRC.index('{', start)
    depth = 1
    end = opening + 1
    while depth:
        depth += (SRC[end] == '{') - (SRC[end] == '}')
        end += 1
    return SRC[start:end]


class HostBehavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        BUILD.mkdir(parents=True, exist_ok=True)
        harness = (ROOT / 'tests/HostHarness.java.in').read_text()
        for name, marker in [('SHORTCUT', 'static int shortcut('),
                             ('BAND', 'private static final class Band'),
                             ('ROW', 'private static final class Row')]:
            harness = harness.replace('@@' + name + '@@', fragment(marker))
        (BUILD / 'HostHarness.java').write_text(harness)
        subprocess.run([str(JDK / 'bin/javac'), '-d', str(BUILD),
                        str(BUILD / 'HostHarness.java')], check=True)

    def run_mode(self, mode):
        result = subprocess.run([str(JDK / 'bin/java'), '-cp', str(BUILD),
                                 'HostHarness', mode], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        print(result.stdout.strip())

    def test_all_character_shortcuts(self):
        self.run_mode('shortcuts')

    def test_touch_boundaries_and_cancel(self):
        self.run_mode('touch')

    def test_trackpad_enter_space_activation(self):
        self.run_mode('activation')

    def test_portrait_layout_budget(self):
        self.run_mode('layout')


class Contracts(unittest.TestCase):
    def test_native_entry_and_six_home_rows(self):
        self.assertIn('extends UiApplication', SRC)
        self.assertIn('extends MainScreen', SRC)
        self.assertIn('enterEventDispatcher()', SRC)
        titles = re.findall(r'"([^\"]+)"', re.search(r'TITLES = \{(.*?)\};', SRC, re.S)[1])
        self.assertEqual(titles, ['Terminal', 'Network Center', 'Security Center', 'Device Manager', 'File Manager', 'System Monitor'])
        self.assertIn('rows[0].setFocus()', SRC)
        self.assertIn('new Row[6]', SRC)

    def test_every_external_item_disconnected(self):
        items = ['S25', 'Steam Deck', 'MASTER-PC', 'CamDoor', 'Xiaomi C301',
                 'EchoVault', 'Tahani family memories', 'Abu Jamal Wi-Fi', 'VPN health']
        for item in items:
            self.assertIn(item + r'\nNot connected', SRC)
        self.assertNotRegex(SRC, r'Local battery: \d{1,3}%')

    def test_no_network_or_security_bypass_apis(self):
        imports = re.findall(r'^import (.*);', SRC, re.M)
        allowed = ('java.util.', 'java.io.', 'net.rim.device.api.ui.',
                   'net.rim.device.api.i18n.SimpleDateFormat', 'net.rim.device.api.system.DeviceInfo',
                   'javax.microedition.rms.RecordStore', 'javax.microedition.io.Connector',
                   'javax.microedition.io.file.', 'javax.microedition.io.StreamConnection',
                   'net.rim.device.api.system.ApplicationManager')
        self.assertTrue(all(i.startswith(allowed) for i in imports), imports)
        for forbidden in ['HttpConnection', 'BrowserField', 'ServerSocket', 'SocketConnection', 'PersistentStore',
                          'ApplicationPermissions', 'EventInjector', 'https://', 'http://', 'interface=cellular',
                          'socket://:', 'ApplicationManager.getApplicationManager().launch']:
            self.assertNotIn(forbidden, SRC)
        # Exactly two connections: read-only file listing and ONE outbound Wi-Fi TorchLink socket.
        self.assertEqual(SRC.count('Connector.open('), 2)
        self.assertEqual(SRC.count('"socket://"'), 1)
        self.assertIn(';deviceside=true;interface=wifi;', SRC)
        self.assertIn('Connector.open(target, Connector.READ_WRITE, true)', SRC)

    def test_torchlink_safety_gates(self):
        # Kill switch on background/lock, remote cannot reach pairing screen, owner-only start.
        self.assertIn('public void deactivate() { link.stop(', SRC)
        self.assertIn('if (section == 12) { result[1] = "Remote link screen cannot be opened remotely"', SRC)
        self.assertIn('if (!isForeground()) return "TorchOS must be in the foreground."', SRC)
        self.assertIn('if (!isForeground()) { result[1] = "TorchOS not in foreground"', SRC)
        self.assertIn('requestBackground()', SRC)
        self.assertIn('if (!app.linkStore.load().bootOpen) System.exit(0);', SRC)
        self.assertIn('session.accept(readLine(in)', SRC)
        self.assertNotIn('Dialog.ask', SRC.split('private final class Link implements Runnable')[1].split('private void setBanner(')[0])

    def test_persistent_notes_and_task_state(self):
        self.assertIn('new EditField("Draft: ", data.note, 512', SRC)
        self.assertIn('data.note = draft.getText()', SRC)
        self.assertIn('data.tasks[i] = checks[i].getChecked()', SRC)
        self.assertIn('new boolean[3]', SRC)
        self.assertIn('RecordStore.openRecordStore("TorchOS_CP002", true)', SRC)
        self.assertNotIn('S25Hub', SRC)
        self.assertIn('Persistence error:', SRC)

    def test_settings_back_and_clock_lifecycle(self):
        self.assertIn('new MenuItem("Settings / About"', SRC)
        self.assertIn('new SimpleDateFormat("EEE dd MMM  HH:mm").format(new Date())', SRC)
        self.assertIn('30000, true', SRC)
        self.assertIn('cancelInvokeLater(clockEvent)', SRC)
        self.assertEqual(SRC.count('popScreen(this)'), 1)
        self.assertIn('System.exit(0)', SRC)

    def test_packaging_identity(self):
        alx = ET.parse(ROOT / 'TorchOS.alx')
        app = alx.find('application')
        self.assertEqual(app.attrib['id'], 'TorchOS')
        self.assertEqual(app.findtext('version'), '0.3.0')
        self.assertEqual(app.findtext('fileset/directory'), 'build')
        self.assertEqual(app.findtext('fileset/files/file'), 'TorchOS.cod')
        rapc = (ROOT / 'TorchOS.rapc').read_text()
        self.assertIn('MicroEdition-Profile: MIDP-2.0', rapc)
        self.assertIn('MicroEdition-Configuration: CLDC-1.1', rapc)
        self.assertIn('MIDlet-1: TorchOS,,TorchOS', rapc)
        self.assertIn('MIDlet-Version: 0.3.0', rapc)
        self.assertIn('RIM-MIDlet-Flags-1: 1', rapc)  # takeover: auto-run at boot
        self.assertNotIn('S25Hub', rapc)

    def test_build_uses_real_tools_and_local_outputs(self):
        script = (ROOT / 'build.sh').read_text()
        self.assertIn('-jar "$JDE_HOME/rapc.jar"', script)
        self.assertIn('import=$JDE_HOME/net_rim_api.jar', script)
        self.assertIn('"$ROOT/src/TorchOS.java"', script)
        self.assertIn('cd "$ROOT/build"', script)
        self.assertIn('export TMPDIR="$ROOT/build/tmp"', script)
        self.assertIn('set -euo pipefail', script)
        self.assertNotRegex(script, r'\b(?:curl|wget|sudo|bjavaloader|javaloader|usb|push)\b')
        self.assertNotIn('-nopreverify', script)
        subprocess.run(['bash', '-n', str(ROOT / 'build.sh')], check=True)

    def test_source_trackable_artifacts_ignored(self):
        result = subprocess.run(['git', 'check-ignore', '--no-index', str(ROOT / 'src/TorchOS.java')],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        result = subprocess.run(['git', 'check-ignore', '--no-index', str(ROOT / 'build/TorchOS.cod')],
                                capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_preview_is_offline_and_labeled(self):
        class Inspect(HTMLParser):
            def __init__(self):
                super().__init__(); self.external = []; self.home_buttons = 0
            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                for name in ['src', 'href', 'action']:
                    if name in attrs:
                        self.external.append(attrs[name])
                if tag == 'button' and attrs.get('data-page') in ['0', '1', '2', '3', '4', '5']:
                    self.home_buttons += 1
        parser = Inspect(); parser.feed(HTML)
        self.assertEqual(parser.external, [])
        self.assertEqual(parser.home_buttons, 6)
        self.assertIn("connect-src 'none'", HTML)
        self.assertIn('width:480px;height:640px', HTML)
        self.assertIn('this is not on-device code', HTML)
        self.assertNotRegex(HTML, r'\b(?:fetch|XMLHttpRequest|WebSocket|sendBeacon)\s*\(')


if __name__ == '__main__':
    unittest.main(verbosity=2)
