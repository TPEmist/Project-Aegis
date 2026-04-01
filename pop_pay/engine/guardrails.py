import re
import os
from urllib.parse import urlparse
from pop_pay.core.models import PaymentIntent, GuardrailPolicy


def _tokenize(s: str) -> set:
    return set(re.split(r'[\s\-_./]+', s.lower()))


# ---------------------------------------------------------------------------
# Known third-party payment processors.
# When a checkout page redirects to one of these domains, the TOCTOU domain
# guard treats it as a pass — the vendor intent was already approved by the
# policy gate, and these processors are independently trusted infrastructure.
# Users can extend this list via POP_ALLOWED_PAYMENT_PROCESSORS in .env.
# To propose additions, open a PR at github.com/agentpayorg/project-aegis.
# ---------------------------------------------------------------------------
KNOWN_PAYMENT_PROCESSORS = {
    # ── Stripe ──
    "stripe.com",           # Stripe-hosted checkout & Payment Links
    "js.stripe.com",        # Stripe Elements (iframe injection)
    # ── Zoho ──
    "zohosecurepay.com",    # Zoho Payments / Zoho Commerce checkout
    # ── Square ──
    "squareup.com",         # Square POS & Square Online checkout
    "square.com",           # Square marketing domain (some checkout flows)
    # ── PayPal / Braintree ──
    "paypal.com",           # PayPal Checkout
    "braintreegateway.com", # Braintree (PayPal subsidiary)
    # ── Adyen ──
    "adyen.com",            # Adyen Drop-In & Components
    # ── Checkout.com ──
    "checkout.com",         # Checkout.com hosted pages
    # ── Paddle ──
    "paddle.com",           # Paddle (SaaS billing & checkout)
    # ── FastSpring ──
    "fastspring.com",       # FastSpring (software & digital goods)
    # ── Gumroad ──
    "gumroad.com",          # Gumroad (creators / digital products)
    # ── Recurly / Chargebee (subscription billing) ──
    "recurly.com",
    "chargebee.com",
    # ── Event & ticketing platforms ──
    "eventbrite.com",       # Eventbrite
    "ti.to",                # Tito (tech conferences: RailsConf, WWDC alt, etc.)
    "lu.ma",                # Luma (tech meetups & events)
    "universe.com",         # Universe ticketing
    # ── Other ──
    "2checkout.com",        # 2Checkout / Verifone
    "authorize.net",        # Authorize.net (AIM / SIM hosted forms)
}

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
        vendor_lower = intent.target_vendor.lower()
        vendor_tokens = _tokenize(intent.target_vendor)
        vendor_allowed = False

        for category in policy.allowed_categories:
            cat_lower = category.lower()
            cat_tokens = _tokenize(category)
            if vendor_tokens & cat_tokens or vendor_lower == cat_lower:
                vendor_allowed = True
                break

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
