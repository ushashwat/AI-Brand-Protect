"""Brand signal data models and LLM response schemas."""

from enum import Enum
from pydantic import BaseModel, ConfigDict


class ScanRequest(BaseModel):
    """Inbound request model for the /scan API endpoint."""

    company_name: str
    official_domains: list[str]


class AssetType(str, Enum):
    logo = "logo"
    favicon = "favicon"
    product_image = "product_image"


class Asset(BaseModel):
    """Visual brand assets like logos and favicons."""

    model_config = ConfigDict(frozen=True)
    url: str
    asset_type: AssetType
    source_page: str
    description: str | None = None


class DomainInfo(BaseModel):
    """Information regarding official and discovered domains."""

    model_config = ConfigDict(frozen=True)
    domain: str
    registrant_org: str | None = None
    is_confirmed_owned: bool = False


class Person(BaseModel):
    """Key executive or personnel associated with the brand."""

    model_config = ConfigDict(frozen=True)
    name: str
    role: str
    source_url: str


class BrandProfile(BaseModel):
    """Aggregated output model containing all discovered brand intelligence."""

    model_config = ConfigDict(frozen=True)
    company_name: str
    official_domains: list[str]
    discovered_domains: list[DomainInfo]
    visual_assets: list[Asset]
    keywords: list[str]
    key_people: list[Person]
    social_links: list[str]


class DomainResponse(BaseModel):
    domains: list[str]


class KeywordResponse(BaseModel):
    keywords: list[str]


class PeopleResponse(BaseModel):
    people: list[Person]


class SocialResponse(BaseModel):
    social_urls: list[str]
