import re
import os
from urllib.parse import urlparse
from pop_pay.core.models import PaymentIntent, GuardrailPolicy


def _tokenize(s: str) -> set:
    return set(re.split(r'[\s\-_./]+', s.lower()))


def _match_vendor(vendor_name: str, allowed_categories: list, page_domain: str = "") -> bool:
    """Unified vendor matching used by both GuardrailEngine and request_purchaser_info MCP tool."""
    vendor_lower = vendor_name.lower()
    vendor_tokens = _tokenize(vendor_name)
    allowed_lower = [c.lower() for c in allowed_categories]
    page_domain_tokens = {
        tok for tok in re.split(r'[\s\-_./]+', page_domain.lower().removeprefix("www."))
        if tok and len(tok) >= 4
    } if page_domain else set()

    return (
        vendor_lower in allowed_lower
        or any(tok in allowed_lower for tok in vendor_tokens)
        or any(
            _tokenize(cat) - {''} <= vendor_tokens
            for cat in allowed_lower
        )
        or bool(page_domain and any(
            _tokenize(cat) - {''} <= page_domain_tokens
            for cat in allowed_lower
        ))
    )


from pop_pay.engine.known_processors import KNOWN_PAYMENT_PROCESSORS  # noqa: F401

KNOWN_VENDOR_DOMAINS = {
    "aws": ["amazonaws.com", "aws.amazon.com"],
    "amazon": ["amazon.com", "amazon.co.uk", "amazon.co.jp"],
    "github": ["github.com"],
    "cloudflare": ["cloudflare.com"],
    "openai": ["openai.com", "platform.openai.com"],
    "stripe": ["stripe.com", "dashboard.stripe.com"],
    "anthropic": ["anthropic.com", "claude.ai"],
    "google": ["google.com", "cloud.google.com", "console.cloud.google.com"],
    "microsoft": ["microsoft.com", "azure.microsoft.com", "portal.azure.com"],
    "wikipedia": ["wikipedia.org", "wikimedia.org", "donate.wikimedia.org"],
    "digitalocean": ["digitalocean.com", "cloud.digitalocean.com"],
    "heroku": ["heroku.com", "dashboard.heroku.com"],
    "vercel": ["vercel.com", "app.vercel.com"],
    "netlify": ["netlify.com", "app.netlify.com"],
}


class GuardrailEngine:
    async def evaluate_intent(self, intent: PaymentIntent, policy: GuardrailPolicy) -> tuple[bool, str]:
        # Rule 1: Vendor/Category check
        vendor_allowed = _match_vendor(intent.target_vendor, policy.allowed_categories)

        if not vendor_allowed:
            return False, "Vendor not in allowed categories"

        # Rule 2: Hallucination/Loop detection
        if policy.block_hallucination_loops:
            reasoning_lower = intent.reasoning.lower()
            loop_keywords = ["retry", "failed again", "loop", "ignore previous", "stuck"]

            for keyword in loop_keywords:
                if keyword in reasoning_lower:
                    return False, "Hallucination or infinite loop detected in reasoning"

            # Rule 3: Injection pattern detection
            injection_patterns = [
                r'\{.*".*".*:',                         # JSON-like structure
                r'output\s*:',                           # "output:" pattern
                r'you are now',                          # role injection
                r'ignore (all |previous |your |the )',   # instruction override
                r'already (approved|authorized|confirmed)',  # false pre-approval
                r'system (says|has|override)',            # system impersonation
            ]
            for pattern in injection_patterns:
                if re.search(pattern, reasoning_lower):
                    return False, "Potential prompt injection detected in reasoning"

            # User-defined extra keywords from env
            extra_keywords_raw = os.getenv("POP_EXTRA_BLOCK_KEYWORDS", "")
            extra_keywords = [kw.strip().lower() for kw in extra_keywords_raw.split(",") if kw.strip()]
            for keyword in extra_keywords:
                if keyword in reasoning_lower:
                    return False, f"Blocked by custom keyword policy: '{keyword}'"

        # Rule 4: page_url domain cross-validation
        if intent.page_url:
            parsed = urlparse(intent.page_url)
            netloc = parsed.netloc.lower()
            # Strip www. prefix
            if netloc.startswith("www."):
                netloc = netloc[4:]

            vendor_tokens_for_domain = _tokenize(intent.target_vendor)
            for known_vendor, known_domains in KNOWN_VENDOR_DOMAINS.items():
                if known_vendor in vendor_tokens_for_domain:
                    # Vendor matches a known entry — validate domain
                    domain_ok = any(
                        netloc == d or netloc.endswith("." + d)
                        for d in known_domains
                    )
                    if not domain_ok:
                        return False, "Page URL domain does not match expected vendor domain"
                    break

        return True, "Approved"
