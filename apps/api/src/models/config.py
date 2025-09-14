from typing import Dict, List, Literal
from pydantic import BaseModel, Field

BaseDomain = Literal['go2.video', 'go2.reviews', 'go2.tools']


class SafetySettings(BaseModel):
    """Safety configuration settings"""
    enable_safe_browsing: bool = True
    blacklist_domains: List[str] = Field(default_factory=list)
    blacklist_keywords: List[str] = Field(default_factory=list)


class PlanLimits(BaseModel):
    """Plan limits configuration"""
    free: Dict[str, int] = Field(default_factory=lambda: {"custom_codes": 5})
    paid: Dict[str, int] = Field(default_factory=lambda: {"custom_codes": 100})


class ConfigDocument(BaseModel):
    """Firestore document model for system configuration"""
    base_domains: List[BaseDomain] = Field(default_factory=lambda: ['go2.video', 'go2.reviews', 'go2.tools'])
    domain_suggestions: Dict[str, BaseDomain] = Field(default_factory=dict)
    safety_settings: SafetySettings = Field(default_factory=SafetySettings)
    plan_limits: PlanLimits = Field(default_factory=PlanLimits)


class BaseDomainsResponse(BaseModel):
    """Response model for base domains"""
    domains: List[BaseDomain]
    suggestions: Dict[str, BaseDomain] = Field(default_factory=dict)


class UpdateConfigRequest(BaseModel):
    """Request model for updating configuration"""
    base_domains: List[BaseDomain] = None
    domain_suggestions: Dict[str, BaseDomain] = None
    safety_settings: SafetySettings = None
    plan_limits: PlanLimits = None


class DomainConfigRequest(BaseModel):
    """Request model for domain configuration updates"""
    base_domains: List[BaseDomain]
    domain_suggestions: Dict[str, BaseDomain] = Field(default_factory=dict)