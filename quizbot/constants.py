from enum import Enum

from aiogram import types

ADMIN_ROLES = (types.ChatMemberOwner, types.ChatMemberAdministrator)
NON_ADMIN_ROLES = (types.ChatMemberMember, types.ChatMemberLeft, types.ChatMemberBanned)


class ChangeType(str, Enum):
    BECAME_ADMIN = "became_admin"
    LEFT_ADMIN = "left_admin"
