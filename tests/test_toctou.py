"""
Tests for TOCTOU domain verification in PopBrowserInjector.inject_payment_info().

The TOCTOU guard must fire BEFORE any CDP connection is attempted, so the
mismatch test never tries to connect to CDP at all.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.mark.asyncio
async def test_toctou_domain_mismatch_blocks_injection():
    """TOCTOU: injection blocked when page domain doesn't match approved vendor."""
    from pop_pay.injector import PopBrowserInjector

    injector = PopBrowserInjector(state_tracker=MagicMock())
    # wikipedia approved, but page_url is attacker.com
    result = await injector.inject_payment_info(
        seal_id="test-seal",
        page_url="https://attacker.com/fake-checkout",
        card_number="4111111111111111",
        cvv="123",
        expiration_date="12/28",
        approved_vendor="wikipedia",
        cdp_url="http://localhost:9222",  # won't actually connect — blocked before CDP
    )
    assert result["card_filled"] is False
    assert "domain_mismatch" in result.get("blocked_reason", "")


@pytest.mark.asyncio
async def test_toctou_matching_domain_proceeds():
    """TOCTOU: same domain passes the guard (CDP connection still mocked to fail gracefully)."""
    from pop_pay.injector import PopBrowserInjector

    injector = PopBrowserInjector(state_tracker=MagicMock())
    # wikipedia approved, page_url also wikipedia — guard passes, CDP fails (not running)
    result = await injector.inject_payment_info(
        seal_id="test-seal",
        page_url="https://en.wikipedia.org/wiki/donate",
        card_number="4111111111111111",
        cvv="123",
        expiration_date="12/28",
        approved_vendor="wikipedia",
        cdp_url="http://localhost:19999",  # nothing running here
    )
    # Guard passed — result depends on CDP (not running = card_filled False, but NOT blocked_reason)
    assert "domain_mismatch" not in result.get("blocked_reason", "")


# ---------------------------------------------------------------------------
# R1/F1 regression tests — validate-here / inject-there
# ---------------------------------------------------------------------------
#
# Bypass vector A: a compromised agent calls inject with page_url="" to
#   silently skip the domain guard entirely (the guard used to `return None`
#   for an empty page_url, meaning "not blocked").
# Bypass vector B: the agent supplies a legitimate, approved page_url, but the
#   shared CDP browser already has a DIFFERENT (attacker-controlled) tab open
#   that `_find_best_page` resolves to instead — the original code validated
#   the caller-supplied page_url string but injected into whatever page was
#   actually resolved, with no equality check between the two.
#
# Both vectors must result in card_filled=False and NO fields ever filled.

@pytest.mark.asyncio
async def test_toctou_empty_page_url_blocks_injection():
    """Bypass vector A: empty page_url must abort (no silent skip) whenever a
    vendor is being enforced — this must happen BEFORE any CDP connection."""
    from pop_pay.injector import PopBrowserInjector

    injector = PopBrowserInjector(state_tracker=MagicMock())
    result = await injector.inject_payment_info(
        seal_id="test-seal",
        page_url="",  # compromised-agent bypass attempt
        card_number="4111111111111111",
        cvv="123",
        expiration_date="12/28",
        approved_vendor="wikipedia",
        cdp_url="http://localhost:9222",  # must never actually be dialed
    )
    assert result["card_filled"] is False
    assert result.get("blocked_reason") == "empty_page_url"


@pytest.mark.asyncio
async def test_toctou_empty_page_url_blocks_billing_injection():
    """Same bypass vector A, but through the inject_billing_only entry point."""
    from pop_pay.injector import PopBrowserInjector

    injector = PopBrowserInjector(state_tracker=MagicMock())
    result = await injector.inject_billing_only(
        page_url="",
        approved_vendor="wikipedia",
        cdp_url="http://localhost:9222",
    )
    assert result["billing_filled"] is False
    assert result.get("blocked_reason") == "empty_page_url"


def _mock_playwright_with_page(page_url: str):
    """Build a mocked `playwright.async_api` module whose CDP browser has a
    single already-open page at `page_url`. Returns (module_patch_dict, mock_page).
    """
    mock_frame = MagicMock()
    mock_frame.url = page_url

    mock_page = MagicMock()
    mock_page.url = page_url
    mock_page.frames = [mock_frame]
    mock_page.bring_to_front = AsyncMock()

    mock_context = MagicMock()
    mock_context.pages = [mock_page]

    mock_browser = MagicMock()
    mock_browser.contexts = [mock_context]
    mock_browser.close = AsyncMock()

    mock_pw = MagicMock()
    mock_pw.chromium.connect_over_cdp = AsyncMock(return_value=mock_browser)

    class MockPlaywrightCtx:
        async def __aenter__(self):
            return mock_pw

        async def __aexit__(self, *args):
            pass

    mock_playwright_module = MagicMock()
    mock_playwright_module.async_api.async_playwright = MagicMock(return_value=MockPlaywrightCtx())

    return {
        "playwright": mock_playwright_module,
        "playwright.async_api": mock_playwright_module.async_api,
    }, mock_page


@pytest.mark.asyncio
async def test_toctou_find_best_page_mismatch_blocks_injection():
    """Bypass vector B: caller supplies a legitimate, approved page_url, but the
    shared CDP browser already has an attacker-controlled tab open that
    _find_best_page resolves to instead. Injection must abort with no fields
    filled — the resolved page's ACTUAL domain must be re-verified, not just
    the caller-supplied page_url string."""
    import sys
    from unittest.mock import patch
    from pop_pay.core.state import PopStateTracker

    tracker = PopStateTracker(db_path=":memory:")
    modules_patch, mock_page = _mock_playwright_with_page(
        "https://attacker.com/checkout"  # matches the "checkout" keyword — _find_best_page picks it
    )

    with patch.dict("sys.modules", modules_patch):
        from pop_pay.injector import PopBrowserInjector as Inj

        inj = Inj(tracker)
        with patch.object(inj, "_fill_across_frames", new=AsyncMock(return_value=True)) as mock_fill:
            result = await inj.inject_payment_info(
                seal_id="test-seal",
                page_url="https://en.wikipedia.org/wiki/donate",  # legitimate, approved
                card_number="4111111111111111",
                cvv="123",
                expiration_date="12/28",
                approved_vendor="wikipedia",
                cdp_url="http://localhost:9222",
            )

    assert result["card_filled"] is False
    assert "domain_mismatch" in result.get("blocked_reason", "")
    mock_fill.assert_not_called()  # no PAN/CVV ever handed to the fill path
    tracker.close()


@pytest.mark.asyncio
async def test_toctou_find_best_page_matching_domain_proceeds_to_fill():
    """Control case: when _find_best_page resolves to a page whose domain DOES
    match the approved vendor, injection proceeds normally (the new
    re-validation must not false-positive-block legitimate flows)."""
    import sys
    from unittest.mock import patch
    from pop_pay.core.state import PopStateTracker

    tracker = PopStateTracker(db_path=":memory:")
    modules_patch, mock_page = _mock_playwright_with_page(
        "https://en.wikipedia.org/wiki/donate"
    )

    with patch.dict("sys.modules", modules_patch):
        from pop_pay.injector import PopBrowserInjector as Inj

        inj = Inj(tracker)
        with patch.object(inj, "_fill_across_frames", new=AsyncMock(return_value=True)) as mock_fill:
            result = await inj.inject_payment_info(
                seal_id="test-seal",
                page_url="https://en.wikipedia.org/wiki/donate",
                card_number="4111111111111111",
                cvv="123",
                expiration_date="12/28",
                approved_vendor="wikipedia",
                cdp_url="http://localhost:9222",
            )

    assert result.get("blocked_reason", "") == ""
    assert result["card_filled"] is True
    mock_fill.assert_called_once()
    tracker.close()
