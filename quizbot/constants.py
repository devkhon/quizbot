from aiogram import types

ADMIN_ROLES = (types.ChatMemberOwner, types.ChatMemberAdministrator)
NON_ADMIN_ROLES = (types.ChatMemberMember, types.ChatMemberLeft, types.ChatMemberBanned)
