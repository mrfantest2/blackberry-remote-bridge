import pathlib
import unittest
from urllib.parse import urlsplit

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = (ROOT / 'src' / 'S25Hub.java').read_text()

class NativeContractTests(unittest.TestCase):
    def test_native_ui_not_webview(self):
        self.assertIn('extends UiApplication', SRC)
        self.assertIn('extends MainScreen', SRC)
        self.assertIn('new ButtonField', SRC)
        self.assertNotIn('new BrowserField', SRC)
    def test_https_only(self):
        self.assertIn('https://s25.fantest.win', SRC)
        self.assertNotIn('http://s25.fantest.win', SRC)
    def test_read_only(self):
        self.assertIn('HttpConnection.GET', SRC)
        self.assertNotIn('HttpConnection.POST', SRC)
        self.assertNotIn('HttpConnection.DELETE', SRC)
    def test_reject_html(self):
        self.assertIn('application/json', SRC)
        self.assertIn('Native API unavailable', SRC)
    def test_auth_not_bypassed(self):
        self.assertIn('code == 401 || code == 403', SRC)
        self.assertNotIn('Authorization', SRC)
    def test_response_bound(self):
        self.assertIn('output.size() + count > LIMIT', SRC)
    def test_background_network(self):
        self.assertIn('new Thread(new Runnable()', SRC)
        self.assertIn('invokeLater(new Runnable()', SRC)

if __name__ == '__main__': unittest.main()
