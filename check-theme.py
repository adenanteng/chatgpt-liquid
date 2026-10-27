"""Check theme changes in Chromium without opening the personal app profile."""
from pathlib import Path
import subprocess
import tempfile

css = (Path(__file__).parent / 'glass.css').read_text()
with tempfile.TemporaryDirectory(prefix='chatgpt-glass-theme-') as directory:
    page = Path(directory) / 'test.html'
    page.write_text('''<!doctype html><style>
    [data-theme=light] { color-scheme: light; }
    [data-theme=dark] { color-scheme: dark; }
    </style><style>''' + css + '''</style>
    <div data-slate-sidebar-content><span>Foreground</span></div>
    <script>
    const sidebar = document.querySelector('[data-slate-sidebar-content]');
    for (const theme of ['light', 'dark', 'light']) {
      document.documentElement.dataset.theme = theme;
      const expectedBody = theme === 'light' ? 'rgba(255, 255, 255, 0.5)' : 'rgba(36, 36, 36, 0.5)';
      const expectedSidebar = theme === 'light' ? 'rgba(245, 245, 245, 0.2)' : 'rgba(30, 30, 30, 0.2)';
      if (getComputedStyle(document.body).backgroundColor !== expectedBody ||
          getComputedStyle(sidebar).backgroundColor !== expectedSidebar ||
          getComputedStyle(sidebar.firstElementChild).opacity !== '1') {
        throw new Error('Incorrect background or foreground opacity in ' + theme);
      }
    }
    document.body.textContent = 'THEME_CHECK_PASSED';
    </script>''')
    result = subprocess.run([
        '/opt/google/chrome/chrome', '--headless', '--no-sandbox', '--disable-gpu',
        '--no-first-run', '--disable-background-networking',
        '--user-data-dir=' + directory + '/profile', '--dump-dom', page.as_uri(),
    ], capture_output=True, text=True, timeout=30, check=True)
    assert '<body>THEME_CHECK_PASSED</body>' in result.stdout, result.stdout
print('Light → dark → light: background tints, alpha, and foreground opacity passed.')
