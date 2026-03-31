"""
Tests for TOCTOU domain verification in PopBrowserInjector.inject_payment_info().

The TOCTOU guard must fire BEFORE any CDP connection is attempted, so the
mismatch test never tries to connect to CDP at all.
"""
import pytest
from unittest.mock import MagicMock


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
