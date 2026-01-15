from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database import db
from keyboards import get_back_keyboard
from utils import format_stats

router = Router()


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    servers = await db.get_all_servers(message.from_user.id)
    text = format_stats(servers)
    await message.answer(text, reply_markup=get_back_keyboard(), parse_mode="HTML")


@router.callback_query(F.data == "stats")
async def cb_stats(callback: CallbackQuery):
    servers = await db.get_all_servers(callback.from_user.id)
    text = format_stats(servers)
    await callback.message.edit_text(text, reply_markup=get_back_keyboard(), parse_mode="HTML")
    await callback.answer()
