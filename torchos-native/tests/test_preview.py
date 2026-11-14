"""Run actual inline preview JS with a host DOM double; not browser/device QA."""
from pathlib import Path
import re
import subprocess
import unittest
from test_torchos import ROOT


class PreviewBehavior(unittest.TestCase):
    def run_harness(self, harness_name, target_name):
        html = (ROOT/'preview/index.html').read_text()
        script = re.search(r'<script>(.*?)</script>', html, re.S)[1]
        harness = (ROOT/'tests'/harness_name).read_text()
        build = ROOT/'build/host-tests'; build.mkdir(parents=True, exist_ok=True)
        target=build/target_name;target.write_text(harness.replace('/*@@SCRIPT@@*/', script))
        result=subprocess.run(['node',str(target)],capture_output=True,text=True)
        self.assertEqual(result.returncode,0,result.stdout+result.stderr)
        print(result.stdout.strip())

    def test_preview_terminal_navigation_notes_and_no_hardware_claims(self):
        html = (ROOT/'preview/index.html').read_text()
        for name in ['Terminal', 'Network Center', 'Security Center', 'Device Manager', 'File Manager', 'System Monitor', 'Notes &amp; Tasks', 'CamDoor', 'EchoVault', 'Project Monitor']:
            self.assertIn(name, html)
        self.run_harness('PreviewHarness.js', 'preview-test.js')

    def test_preview_control_character_rejection_parity(self):
        self.run_harness('PreviewControlHarness.js', 'preview-control-test.js')


if __name__=='__main__':unittest.main(verbosity=2)
