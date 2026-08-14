"""
WebDriver construction, in one place.

Both runners (core/test_runner.py and agents/executor.py) build their browser
here so a deployment only has to be configured once. Behaviour is driven by
config/settings.py, which reads the environment:

    HEADLESS        headless Chrome (REQUIRED on servers/containers/CI --
                    a machine with no display cannot open a visible window)
    WINDOW_WIDTH    viewport size; affects responsive layouts and therefore
    WINDOW_HEIGHT   which elements are visible to a locator
    DEFAULT_TIMEOUT implicit wait, in seconds -- how long Selenium keeps
                    retrying a locator before giving up

The implicit wait is what makes runs reliable on slower client hardware:
without it Selenium fails the instant an element isn't yet in the DOM.
"""

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

from ai_test_engine.config.settings import (
    DEFAULT_TIMEOUT,
    HEADLESS_MODE,
    PAGE_LOAD_TIMEOUT,
    WINDOW_SIZE,
)


def build_chrome_options(headless: bool = None) -> Options:
    """Assemble Chrome options from settings.

    Args:
        headless: Override ``settings.HEADLESS_MODE``. Leave as None to use
            the configured value.
    """
    if headless is None:
        headless = HEADLESS_MODE

    options = Options()
    if headless:
        # "new" is the supported headless mode in current Chrome; the old
        # --headless flag is deprecated and behaves differently.
        options.add_argument("--headless=new")

    width, height = WINDOW_SIZE
    options.add_argument(f"--window-size={width},{height}")

    # Required in containers: /dev/shm is typically 64MB there, and Chrome
    # crashes with "session deleted because of page crash" without this.
    options.add_argument("--disable-dev-shm-usage")
    # Chrome refuses to start as root (common in Docker) without --no-sandbox.
    options.add_argument("--no-sandbox")
    # Quieten the console on client machines.
    options.add_argument("--log-level=3")
    options.add_experimental_option("excludeSwitches", ["enable-logging"])

    return options


def create_driver(headless: bool = None):
    """Return a configured Chrome WebDriver.

    The caller owns the driver and must call ``quit()`` on it -- both runners
    do so in a ``finally`` block so a crash cannot leak a browser process.

    Args:
        headless: Override the configured headless setting.

    Raises:
        WebDriverException: If Chrome or a matching chromedriver is
            unavailable. On a headless server this usually means Chrome
            itself is not installed.
    """
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=build_chrome_options(headless),
    )
    # Retry a failing locator for up to DEFAULT_TIMEOUT seconds before raising.
    driver.implicitly_wait(DEFAULT_TIMEOUT)
    driver.set_page_load_timeout(PAGE_LOAD_TIMEOUT)
    return driver
