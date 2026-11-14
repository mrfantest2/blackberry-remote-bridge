"""Read-only CP004 evidence gates. No phone or network access; GitHub-hosted CI."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[2]
REPORT = ROOT / "docs" / "TORCHOS_CP004_FEASIBILITY_AUDIT_20261114.md"


class CP004ResearchPolicy(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = REPORT.read_text(encoding="utf-8")

    def test_retail_device_and_honest_identity(self):
        self.assertIn("BlackBerry Torch 9810", self.report)
        self.assertIn("BlackBerry OS 7", self.report)
        self.assertIn("does not satisfy this objective", self.report)

    def test_physical_change_is_no_go(self):
        self.assertRegex(self.report, r"NO-GO for physical OS replacement")
        self.assertIn("do not flash, unlock, install, repartition", self.report)
        self.assertIn("The BlackBerry is still off limits for experiments", self.report)

    def test_boot_and_recovery_are_independent_blockers(self):
        self.assertIn("G0 Device/recovery preservation", self.report)
        self.assertIn("G1 Independent boot", self.report)
        self.assertIn("G2 Board support", self.report)
        self.assertIn("G4 Safe real-device trial", self.report)
        self.assertIn("G5 Full replacement", self.report)
        self.assertIn("BLOCKED", self.report)

    def test_conflicting_chipset_identifiers_not_silently_resolved(self):
        self.assertIn("MSM8655", self.report)
        self.assertIn("MSM8255T", self.report)
        self.assertIn("Conflicting sources", self.report)

    def test_off_device_is_not_phone_boot(self):
        self.assertIn("QEMU's generic ARM machine is not a Torch 9810 emulator", self.report)
        self.assertIn("ALLOWED TO DEVELOP", self.report)
        self.assertIn("GitHub-hosted CI", self.report)

    def test_sources_are_cited_with_explicit_links(self):
        links = re.findall(r"https://[^\s)]+", self.report)
        self.assertGreaterEqual(len(links), 7)
        for domain in ("ifixit.com", "bbref.ca", "blackberry.com", "ubuntu.com"):
            self.assertTrue(any(domain in link for link in links), domain)

    def test_no_device_credentials_or_private_backup_contents(self):
        self.assertNotRegex(self.report, r"(?i)(?:ghp_|github_pat_|-----BEGIN PRIVATE KEY-----)")
        self.assertIn("not reread in this research run", self.report)


if __name__ == "__main__":
    unittest.main()
