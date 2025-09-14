from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field, EmailStr, ConfigDict, field_serializer

PlanType = Literal['free', 'paid']


class UserDocument(BaseModel):
    """Firestore document model for users"""
    email: EmailStr
    display_name: str = Field(..., min_length=1)
    plan_type: PlanType = 'free'
    custom_codes_used: int = Field(0, ge=0)
    custom_codes_reset_date: datetime
    created_at: datetime
    last_login: datetime
    is_admin: bool = False

    @field_serializer('custom_codes_reset_date', 'created_at', 'last_login')
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()


class UserProfileResponse(BaseModel):
    """Response model for user profile"""
    email: str
    display_name: str
    plan_type: PlanType
    custom_codes_used: int
    custom_codes_remaining: int
    custom_codes_reset_date: datetime
    created_at: datetime
    is_admin: bool

    @field_serializer('custom_codes_reset_date', 'created_at')
    def serialize_datetime(self, value: datetime) -> str:
        return value.isoformat()


class UpdateUserRequest(BaseModel):
    """Request model for updating user profile"""
    display_name: str = Field(..., min_length=1)


class PlanUpgradeRequest(BaseModel):
    """Request model for plan upgrade"""
    plan_type: PlanType