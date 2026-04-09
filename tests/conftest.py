"""Shared fixtures for pop-pay test suite."""
import uuid
import pytest
from pop_pay.client import PopClient
from pop_pay.core.models import PaymentIntent, GuardrailPolicy, VirtualSeal
from pop_pay.providers.base import VirtualCardProvider


class MockProvider(VirtualCardProvider):
    """Provider that always issues a card (no real network call)."""

    async def issue_card(self, intent: PaymentIntent, policy: GuardrailPolicy) -> VirtualSeal:
        return VirtualSeal(
            seal_id=str(uuid.uuid4()),
            card_number="1234567812345678",
            cvv="123",
            expiration_date="12/26",
            authorized_amount=intent.requested_amount,
            status="Issued",
        )


@pytest.fixture
def mock_provider():
    return MockProvider()


@pytest.fixture
def default_policy():
    return GuardrailPolicy(
        allowed_categories=["cloud", "aws", "openai"],
        max_amount_per_tx=100.0,
        max_daily_budget=500.0,
        block_hallucination_loops=True,
    )


@pytest.fixture
def pop_client(mock_provider, default_policy):
    client = PopClient(mock_provider, default_policy, db_path=":memory:")
    yield client
    client.state_tracker.close()
