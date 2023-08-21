from typing import Optional

from pydantic import BaseModel


class UserResponse(BaseModel):
    full_name: str
    photo_url: str
    email: str
    name_channel: str
    role: str


class SettingChannel(BaseModel):
    user_channel_name: Optional[str] = None
    webcam_for: Optional[str] = None
    screenshare_for: Optional[str] = None
    screenrecord_for: Optional[str] = None
    micro_for: Optional[str] = None
