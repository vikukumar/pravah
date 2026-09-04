from datetime import datetime, timezone
from typing import Any, Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.exceptions import NotFoundException
from app.models.cms import (
    CMSBlock,
    CMSPage,
    Form,
    FormField,
    FormSubmission,
    SEOConfiguration,
)

DEFAULT_CMS_PAGES = [
    {
        "title": "Terms & Conditions",
        "slug": "terms",
        "is_system": True,
        "is_published": True,
        "blocks": [
            {
                "block_type": "hero",
                "name": "Terms Header",
                "content": {"heading": "Terms & Conditions", "subheading": "Effective Date: January 1, 2026. Please read our operational and SaaS usage terms carefully."},
                "display_order": 0,
            },
            {
                "block_type": "custom_html",
                "name": "Terms Content",
                "content": {
                    "html": "<h3>1. Acceptance of Terms</h3><p>By registering, accessing, or using the PRAVAH platform, you agree to be bound by these Terms and Conditions.</p><h3>2. Multi-Tenant Account Security</h3><p>You are responsible for safeguarding your credentials and enabling two-factor authentication.</p><h3>3. Social Platform Compliance</h3><p>All automated publishing must comply with official third-party social media developer terms.</p>"
                },
                "display_order": 1,
            },
        ],
        "seo": {
            "meta_title": "Terms & Conditions | PRAVAH",
            "meta_description": "Legal terms of service and agreement for the PRAVAH AI social media operating system.",
        },
    },
    {
        "title": "Privacy Policy",
        "slug": "privacy",
        "is_system": True,
        "is_published": True,
        "blocks": [
            {
                "block_type": "hero",
                "name": "Privacy Header",
                "content": {"heading": "Privacy Policy", "subheading": "Your data privacy and tenant isolation are our foundational priorities."},
                "display_order": 0,
            },
            {
                "block_type": "custom_html",
                "name": "Privacy Content",
                "content": {
                    "html": "<h3>1. Data Minimization</h3><p>PRAVAH only collects information strictly required to authenticate your identity, manage social connections, and execute automation.</p><h3>2. Token Encryption</h3><p>All OAuth tokens, provider API keys, and payment credentials are encrypted at rest using AES-256 / Fernet encryption.</p><h3>3. Data Retention and Deletion</h3><p>Users may export or request complete deletion of their account and organization data at any time.</p>"
                },
                "display_order": 1,
            },
        ],
        "seo": {
            "meta_title": "Privacy Policy | PRAVAH",
            "meta_description": "Learn how PRAVAH protects and encrypts your organization's data.",
        },
    },
    {
        "title": "Refund Policy",
        "slug": "refund",
        "is_system": True,
        "is_published": True,
        "blocks": [
            {
                "block_type": "hero",
                "name": "Refund Header",
                "content": {"heading": "Refund Policy", "subheading": "Transparent billing and subscription cancellation policy."},
                "display_order": 0,
            },
            {
                "block_type": "custom_html",
                "name": "Refund Content",
                "content": {
                    "html": "<p>We offer a 30-day Free Trial on all new installations. Subscriptions can be cancelled at any time before the next billing cycle. Refund requests for annual commitments are evaluated on a pro-rata basis within 14 days of purchase.</p>"
                },
                "display_order": 1,
            },
        ],
        "seo": {
            "meta_title": "Refund Policy | PRAVAH",
            "meta_description": "Subscription refund and cancellation guidelines for PRAVAH.",
        },
    },
    {
        "title": "Cookie Policy",
        "slug": "cookie-policy",
        "is_system": True,
        "is_published": True,
        "blocks": [
            {
                "block_type": "hero",
                "name": "Cookie Header",
                "content": {"heading": "Cookie Policy", "subheading": "We use strictly necessary cookies for session security and CSRF protection."},
                "display_order": 0,
            },
            {
                "block_type": "custom_html",
                "name": "Cookie Content",
                "content": {
                    "html": "<p>PRAVAH uses secure HttpOnly, SameSite cookies exclusively for maintaining your authenticated session and protecting your account against cross-site request forgery.</p>"
                },
                "display_order": 1,
            },
        ],
        "seo": {
            "meta_title": "Cookie Policy | PRAVAH",
            "meta_description": "Information about cookies and session storage used by PRAVAH.",
        },
    },
    {
        "title": "Security",
        "slug": "security",
        "is_system": True,
        "is_published": True,
        "blocks": [
            {
                "block_type": "hero",
                "name": "Security Header",
                "content": {"heading": "Security Architecture", "subheading": "Enterprise-grade protection, encrypted secrets, and strict multi-tenant isolation."},
                "display_order": 0,
            },
            {
                "block_type": "custom_html",
                "name": "Security Content",
                "content": {
                    "html": "<p>PRAVAH implements defense-in-depth with cryptographic token encryption, strict role-based access control (RBAC), multi-tenant boundary checks, immutable audit logging, rate limiting, and automated security scans.</p>"
                },
                "display_order": 1,
            },
        ],
        "seo": {
            "meta_title": "Security Architecture | PRAVAH",
            "meta_description": "Learn about the security principles and enterprise defenses of PRAVAH.",
        },
    },
    {
        "title": "Acceptable Use Policy",
        "slug": "acceptable-use",
        "is_system": True,
        "is_published": True,
        "blocks": [
            {
                "block_type": "hero",
                "name": "Acceptable Use Header",
                "content": {"heading": "Acceptable Use Policy", "subheading": "Ethical automation standards and platform integrity rules."},
                "display_order": 0,
            },
            {
                "block_type": "custom_html",
                "name": "AUP Content",
                "content": {
                    "html": "<p>Users must not use PRAVAH for spam campaigns, artificial engagement, fake followers, credential scraping, or unauthorized automation violating third-party social media policies.</p>"
                },
                "display_order": 1,
            },
        ],
        "seo": {
            "meta_title": "Acceptable Use Policy | PRAVAH",
            "meta_description": "Platform policies prohibiting spam, artificial engagement, and unauthorized automation.",
        },
    },
    {
        "title": "AI Policy",
        "slug": "ai-policy",
        "is_system": True,
        "is_published": True,
        "blocks": [
            {
                "block_type": "hero",
                "name": "AI Policy Header",
                "content": {"heading": "AI & Content Generation Policy", "subheading": "Responsible AI, human review, and transparent provenance."},
                "display_order": 0,
            },
            {
                "block_type": "custom_html",
                "name": "AI Policy Content",
                "content": {
                    "html": "<p>All AI-generated content is traceable to its model and prompt. Organizations are encouraged to configure human-in-the-loop review chains before automated publishing.</p>"
                },
                "display_order": 1,
            },
        ],
        "seo": {
            "meta_title": "AI & Content Policy | PRAVAH",
            "meta_description": "Guidelines and policies regarding responsible AI usage on PRAVAH.",
        },
    },
]

class CMSService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def seed_system_pages(self):
        for pdata in DEFAULT_CMS_PAGES:
            res = await self.db.execute(select(CMSPage).where(CMSPage.slug == pdata["slug"]))
            page = res.scalar_one_or_none()
            if not page:
                page = CMSPage(
                    title=pdata["title"],
                    slug=pdata["slug"],
                    is_system=pdata["is_system"],
                    is_published=pdata["is_published"],
                    published_at=datetime.now(timezone.utc),
                    version=1,
                )
                self.db.add(page)
                await self.db.flush()

                for b in pdata["blocks"]:
                    block = CMSBlock(
                        page_id=page.id,
                        block_type=b["block_type"],
                        name=b["name"],
                        content=b["content"],
                        display_order=b["display_order"],
                        is_visible=True,
                    )
                    self.db.add(block)

                if "seo" in pdata:
                    seo = SEOConfiguration(
                        page_id=page.id,
                        path=f"/{page.slug}",
                        meta_title=pdata["seo"]["meta_title"],
                        meta_description=pdata["seo"]["meta_description"],
                    )
                    self.db.add(seo)

        # Seed contact form
        contact_res = await self.db.execute(select(Form).where(Form.name == "contact_us"))
        if not contact_res.scalar_one_or_none():
            cform = Form(
                name="contact_us",
                title="Get in Touch",
                description="Have questions about PRAVAH? Reach out to our enterprise team.",
                is_active=True,
            )
            self.db.add(cform)
            await self.db.flush()

            fields = [
                ("name", "Your Name", "text", "Enter your full name", True, 0),
                ("email", "Email Address", "email", "name@company.com", True, 1),
                ("company", "Company / Agency", "text", "Your organization", False, 2),
                ("message", "How can we help?", "textarea", "Tell us about your requirements...", True, 3),
            ]
            for fname, flabel, ftype, fph, freq, forder in fields:
                ff = FormField(
                    form_id=cform.id,
                    field_name=fname,
                    field_label=flabel,
                    field_type=ftype,
                    placeholder=fph,
                    is_required=freq,
                    display_order=forder,
                )
                self.db.add(ff)

        await self.db.commit()

    async def get_page_by_slug(self, slug: str) -> Optional[CMSPage]:
        slug = slug.strip("/").lower()
        query = (
            select(CMSPage)
            .options(
                selectinload(CMSPage.blocks),
                selectinload(CMSPage.seo)
            )
            .where(CMSPage.slug == slug, CMSPage.is_published == True)
        )
        res = await self.db.execute(query)
        return res.scalar_one_or_none()

    async def submit_form(self, form_name: str, data: Dict[str, Any], ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> FormSubmission:
        res = await self.db.execute(select(Form).where(Form.name == form_name, Form.is_active == True))
        form = res.scalar_one_or_none()
        if not form:
            raise NotFoundException("Form not found or inactive")

        submission = FormSubmission(
            form_id=form.id,
            data=data,
            ip_address=ip_address,
            user_agent=user_agent,
            status="new",
        )
        self.db.add(submission)
        await self.db.commit()
        await self.db.refresh(submission)
        return submission
