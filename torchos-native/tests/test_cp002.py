"""Execute production model/codec/store with host RMS doubles; never device QA."""
import subprocess
import unittest
from test_torchos import ROOT, SRC, BUILD, JDK, fragment


class CP002Behavior(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        BUILD.mkdir(parents=True, exist_ok=True)
        harness = (ROOT / 'tests/CP002Harness.java.in').read_text()
        for name in ['TerminalModel', 'NoteData', 'NoteCodec', 'NoteStore']:
            harness = harness.replace('@@' + name + '@@', fragment('static final class ' + name))
        harness = harness.replace('@@CHILD@@', fragment('static boolean safeChild('))
        (BUILD / 'CP002Harness.java').write_text(harness)
        subprocess.run([str(JDK / 'bin/javac'), '-d', str(BUILD), str(BUILD / 'CP002Harness.java')], check=True)

    def run_mode(self, mode):
        result = subprocess.run([str(JDK / 'bin/java'), '-cp', str(BUILD), 'CP002Harness', mode], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        print(result.stdout.strip())

    def test_terminal_allowlist_offline_and_injection(self): self.run_mode('terminal')
    def test_terminal_control_characters_rejected_before_trim(self): self.run_mode('controls')
    def test_terminal_history_and_output_bounds(self): self.run_mode('bounds')
    def test_terminal_history_draft_preservation(self): self.run_mode('history_draft')
    def test_terminal_rejected_submission_resets_browsing(self): self.run_mode('history_rejected_reset')
    def test_rms_roundtrip_and_corrupt_bounds(self): self.run_mode('codec')
    def test_rms_failure_visible_and_no_corrupt_overwrite(self): self.run_mode('store')
    def test_rms_revalidates_record_after_successful_load(self): self.run_mode('store_revalidate')
    def test_rms_storage_and_close_failures_block_later_saves(self): self.run_mode('store_fail_closed')
    def test_file_child_traversal_rejection(self): self.run_mode('files')


def without_link(src):
    """Source minus the TorchLink socket session class (its stream is a Wi-Fi socket, not a file)."""
    start = src.index('    private final class Link implements Runnable {')
    end = src.index('    private void setBanner(', start)
    src = src[:start] + src[end:]
    # Sidecar: Bluetooth serial (btspp) stream to the ESP32, not a file.
    start = src.index('    private final class Sidecar extends Page {')
    end = src.index('    /** Owner-only, on-device pairing', start)
    return src[:start] + src[end:]


class CP002Contracts(unittest.TestCase):
    def test_file_api_is_read_only_and_bounded(self):
        self.assertIn('FileSystemRegistry.listRoots()', SRC)
        self.assertIn('Connector.open(url, Connector.READ)', SRC)
        self.assertIn('count < 64', SRC)
        self.assertIn('depth >= 8', SRC)
        for method in ['openOutputStream', '.delete(', '.rename(', '.mkdir(', '.create(', '.setWritable(']:
            self.assertNotIn(method, without_link(SRC))
        # Output streams exist only for the TorchLink Wi-Fi socket and Sidecar Bluetooth link, never files.
        self.assertEqual(SRC.count('openOutputStream'), 2)
        self.assertIn('out = c.openOutputStream();', SRC)

    def test_terminal_native_editable_and_keyboard(self):
        for token in ['new EditField("local> "', 'Field.FOCUSABLE | Field.READONLY', 'TerminalModel.INPUT_LIMIT', 'VirtualKeyboard.SHOW', '"Previous command"', '"Next command"', '"Help"', '"Clear"', '"Run"']:
            self.assertIn(token, SRC)
        self.assertNotIn('exec(', SRC)
        self.assertNotIn('HttpConnection', SRC)

    def test_diagnostics_honest(self):
        for token in ['DeviceInfo.getBatteryLevel()', 'Runtime.getRuntime().freeMemory()', 'app runtime', 'Checksums disabled', 'Network capabilities unavailable', 'HMAC-SHA256 authenticated, not encrypted', 'Controls TorchOS screens only']:
            self.assertIn(token, SRC)


if __name__ == '__main__': unittest.main(verbosity=2)
