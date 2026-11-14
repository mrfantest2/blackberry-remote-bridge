"""Host JVM tests for the *actual* native diagnostic ReportStore fragment."""
import subprocess
import unittest
from test_torchos import ROOT, BUILD, JDK, fragment


class ReportPersistence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        BUILD.mkdir(parents=True, exist_ok=True)
        source = (ROOT / 'tests/ReportHarness.java.in').read_text()
        source = source.replace('@@ReportStore@@', fragment('static final class ReportStore'))
        target = BUILD / 'ReportHarness.java'
        target.write_text(source)
        subprocess.run([str(JDK / 'bin/javac'), '-d', str(BUILD), str(target)], check=True)

    def run_mode(self, mode):
        result = subprocess.run(
            [str(JDK / 'bin/java'), '-cp', str(BUILD), 'ReportHarness', mode],
            text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        print(result.stdout.strip())

    def test_roundtrip_and_record_bounds(self): self.run_mode('roundtrip')
    def test_empty_report_roundtrip_and_limits(self): self.run_mode('empty')
    def test_corrupt_report_fails_closed(self): self.run_mode('corrupt')
    def test_io_and_close_failures_visible(self): self.run_mode('failure')

    def test_native_entry_has_report_controls(self):
        source = (ROOT / 'src/TorchOS.java').read_text()
        self.assertIn('pushScreen(new SystemMonitor())', source)
        self.assertIn('"Save local report"', source)
        self.assertIn('"View saved report"', source)
        self.assertIn('"TorchOS_CP002_Report"', source)
        self.assertNotIn('openOutputStream', source)


if __name__ == '__main__':
    unittest.main(verbosity=2)
