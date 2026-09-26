# """Macro event schemas for API requests/responses"""

# from pydantic import BaseModel, Field, validator
# from typing import Optional, List, Dict, Any
# from datetime import datetime
# from uuid import UUID


# class MacroSubscriptionCreate(BaseModel):
#     """Schema for creating a macro event subscription."""
#     user_id: UUID
#     event_type: str = Field(..., description="fed, cpi, gdp, employment, other")
#     subscribed: bool = True
#     impact_filter: str = Field(default="high", description="high, medium, low")

#     @validator('event_type')
#     def validate_event_type(cls, v):
#         valid_types = ['fed', 'cpi', 'gdp', 'employment', 'other']
#         if v not in valid_types:
#             raise ValueError(f'event_type must be one of: {", ".join(valid_types)}')
#         return v

#     @validator('impact_filter')
#     def validate_impact(cls, v):
#         valid_impacts = ['high', 'medium', 'low']
#         if v not in valid_impacts:
#             raise ValueError(f'impact_filter must be one of: {", ".join(valid_impacts)}')
#         return v


# class MacroSubscriptionUpdate(BaseModel):
#     """Schema for updating a macro event subscription."""
#     subscribed: Optional[bool] = None
#     impact_filter: Optional[str] = None

#     @validator('impact_filter')
#     def validate_impact(cls, v):
#         if v is not None:
#             valid_impacts = ['high', 'medium', 'low']
#             if v not in valid_impacts:
#                 raise ValueError(f'impact_filter must be one of: {", ".join(valid_impacts)}')
#         return v


# class MacroAlertCreate(BaseModel):
#     """Schema for creating a macro event alert."""
#     user_id: UUID
#     event_id: UUID
#     event_type: str
#     timing: str = Field(..., description="1d, 12h, 1h")
#     impact_filter: str = Field(default="high", description="high, medium, low")
#     name: Optional[str] = None
#     description: Optional[str] = None
#     notify_in_app: bool = True
#     notify_email: bool = True

#     @validator('event_type')
#     def validate_event_type(cls, v):
#         valid_types = ['fed', 'cpi', 'gdp', 'employment', 'other']
#         if v not in valid_types:
#             raise ValueError(f'event_type must be one of: {", ".join(valid_types)}')
#         return v

#     @validator('timing')
#     def validate_timing(cls, v):
#         valid_timings = ['1d', '12h', '1h']
#         if v not in valid_timings:
#             raise ValueError(f'timing must be one of: {", ".join(valid_timings)}')
#         return v


# class MacroAlertUpdate(BaseModel):
#     """Schema for updating a macro event alert."""
#     event_type: Optional[str] = None
#     timing: Optional[str] = None
#     impact_filter: Optional[str] = None
#     name: Optional[str] = None
#     description: Optional[str] = None
#     notify_in_app: Optional[bool] = None
#     notify_email: Optional[bool] = None
#     status: Optional[str] = None


# class MacroAlertResponse(BaseModel):
#     """Schema for macro event alert response."""
#     id: str
#     user_id: str
#     event_type: str
#     timing: str
#     impact_filter: str
#     status: str
#     created_at: str
#     updated_at: str
#     triggered_at: Optional[str]
#     notify_in_app: bool
#     notify_email: bool
#     name: Optional[str]
#     description: Optional[str]


# class MacroEventResponse(BaseModel):
#     """Schema for macro event response."""
#     id: str
#     event_id: str
#     event_type: str
#     event_name: str
#     description: Optional[str]
#     scheduled_at: str
#     timezone: str
#     impact: str
#     source: Optional[str]
#     url: Optional[str]

"""Macro event schemas for API requests/responses"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from uuid import UUID


class MacroSubscriptionCreate(BaseModel):
    """Schema for creating a macro event subscription."""
    user_id: UUID
    event_type: str = Field(
        ...,
        description="fed, cpi, gdp, employment, other"
    )
    subscribed: bool = True
    impact_filter: str = Field(
        default="high",
        description="high, medium, low"
    )
    timing: str = Field(
        default="1d",
        description="1d, 12h, 1h",
    )
    one_time: bool = True
    notify_in_app: bool = True
    notify_email: bool = False

    @validator('event_type')
    def validate_event_type(cls, v):
        valid_types = [
            'fed',
            'cpi',
            'gdp',
            'employment',
            'other'
        ]
        if v not in valid_types:
            raise ValueError(
                f'event_type must be one of: {", ".join(valid_types)}'
            )
        return v

    @validator('impact_filter')
    def validate_impact(cls, v):
        valid_impacts = [
            'high',
            'medium',
            'low'
        ]
        if v not in valid_impacts:
            raise ValueError(
                f'impact_filter must be one of: {", ".join(valid_impacts)}'
            )
        return v

    @validator('timing')
    def validate_timing(cls, v):
        valid_timings = ['1d', '12h', '1h']
        if v not in valid_timings:
            raise ValueError(
                f'timing must be one of: {", ".join(valid_timings)}'
            )
        return v


class MacroSubscriptionUpdate(BaseModel):
    """Schema for updating a macro event subscription."""
    subscribed: Optional[bool] = None
    impact_filter: Optional[str] = None

    @validator('impact_filter')
    def validate_impact(cls, v):
        if v is not None:
            valid_impacts = [
                'high',
                'medium',
                'low'
            ]
            if v not in valid_impacts:
                raise ValueError(
                    f'impact_filter must be one of: {", ".join(valid_impacts)}'
                )
        return v


class MacroAlertCreate(BaseModel):
    """Schema for creating a macro event alert."""
    user_id: UUID
    event_id: UUID
    event_type: str
    timing: str = Field(
        ...,
        description="1d, 12h, 1h"
    )
    impact_filter: str = Field(
        default="high",
        description="high, medium, low"
    )
    name: Optional[str] = None
    description: Optional[str] = None
    notify_in_app: bool = True
    notify_email: bool = True

    @validator('event_type')
    def validate_event_type(cls, v):
        valid_types = [
            'fed',
            'cpi',
            'gdp',
            'employment',
            'other'
        ]
        if v not in valid_types:
            raise ValueError(
                f'event_type must be one of: {", ".join(valid_types)}'
            )
        return v

    @validator('timing')
    def validate_timing(cls, v):
        valid_timings = [
            '1d',
            '12h',
            '1h'
        ]
        if v not in valid_timings:
            raise ValueError(
                f'timing must be one of: {", ".join(valid_timings)}'
            )
        return v


class MacroAlertUpdate(BaseModel):
    """Schema for updating a macro event alert."""
    event_type: Optional[str] = None
    timing: Optional[str] = None
    impact_filter: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    notify_in_app: Optional[bool] = None
    notify_email: Optional[bool] = None
    status: Optional[str] = None


class MacroAlertResponse(BaseModel):
    """Schema for macro event alert response."""
    id: str
    user_id: str
    event_id: str
    event_type: str
    timing: str
    impact_filter: str
    status: str
    created_at: str
    updated_at: str
    triggered_at: Optional[str]
    notify_in_app: bool
    notify_email: bool
    name: Optional[str]
    description: Optional[str]


class MacroEventResponse(BaseModel):
    """Schema for macro event response."""
    id: str
    event_id: str
    event_type: str
    event_name: str
    description: Optional[str]
    scheduled_at: str
    timezone: str
    impact: str
    source: Optional[str]
    url: Optional[str]