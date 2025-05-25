import os
import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    Message,
    CallbackQuery,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from typing import List, Optional
import httpx
import logging
import re

router = Router()

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

class GenerationStates(StatesGroup):
    choosing_mode = State()
    choosing_style = State()
    entering_keywords = State()
    entering_example = State()

# Keyboard functions
def get_main_menu_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🎲 Random Generation", callback_data="mode_random")],
        [InlineKeyboardButton(text="🔑 Generation by Keywords", callback_data="mode_keywords")],
        [InlineKeyboardButton(text="📝 Generation Similar to Example", callback_data="mode_example")],
    ])

def get_style_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🧠 Serious Name", callback_data="style_serious")],
        [InlineKeyboardButton(text="🤣 Non-serious Name", callback_data="style_nonserious")],
        [InlineKeyboardButton(text="⬅️ Back to Main Menu", callback_data="back_to_main")],
    ])

def get_back_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Back to Main Menu", callback_data="back_to_main")],
    ])

def get_results_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Generate more", callback_data="generate_more")],
        [InlineKeyboardButton(text="⬅️ Back to Main Menu", callback_data="back_to_main")],
    ])

@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(
        "Welcome to the Techno Track Name Generator! 🎧\n\n"
        "I can help you generate creative names for your techno tracks.\n"
        "Choose a generation mode:",
        reply_markup=get_main_menu_keyboard()
    )

@router.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer("Help message here", parse_mode="Markdown")

@router.callback_query(F.data.startswith("mode_"))
async def process_mode_selection(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    mode = callback.data.split("_")[1]
    await state.update_data(mode=mode)

    if mode == "example":
        await state.set_state(GenerationStates.entering_example)
        await callback.message.edit_text("Enter example track:", reply_markup=get_back_keyboard())
    else:
        await state.set_state(GenerationStates.choosing_style)
        await callback.message.edit_text("Choose a style:", reply_markup=get_style_keyboard())

@router.callback_query(F.data.startswith("style_"))
async def process_style_selection(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    style = callback.data.split("_")[1]
    data = await state.get_data()
    await state.update_data(style=style)

    if data.get("mode") == "random":
        track_names = await generate_track_names(style=style)
        await callback.message.edit_text(format_track_names(track_names, style), reply_markup=get_results_keyboard())
        # Store parameters for generate_more
        await state.update_data(last_style=style, last_mode="random")
    else:
        await state.set_state(GenerationStates.entering_keywords)
        await callback.message.edit_text("Enter keywords:", reply_markup=get_back_keyboard())

@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await callback.message.edit_text("Choose a generation mode:", reply_markup=get_main_menu_keyboard())

@router.callback_query(F.data == "generate_more")
async def generate_more(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    data = await state.get_data()
    
    # Get the last generation parameters
    last_mode = data.get("last_mode")
    
    if last_mode == "random":
        style = data.get("last_style")
        track_names = await generate_track_names(style=style)
        await callback.message.edit_text(format_track_names(track_names, style), reply_markup=get_results_keyboard())
    
    elif last_mode == "keywords":
        style = data.get("last_style")
        keywords = data.get("last_keywords")
        track_names = await generate_track_names(style=style, keywords=keywords)
        await callback.message.edit_text(format_track_names(track_names, style), reply_markup=get_results_keyboard())
    
    elif last_mode == "example":
        example = data.get("last_example")
        track_names = await generate_track_names(example=example)
        await callback.message.edit_text(format_track_names(track_names, "based on your example"), reply_markup=get_results_keyboard())
    
    # Keep the state data for further regenerations

@router.message(GenerationStates.entering_keywords)
async def process_keywords(message: Message, state: FSMContext):
    keywords = message.text.strip()
    data = await state.get_data()
    style = data.get("style")
    track_names = await generate_track_names(style=style, keywords=keywords)
    await message.answer(format_track_names(track_names, style), reply_markup=get_results_keyboard())
    # Store parameters for generate_more
    await state.update_data(last_style=style, last_keywords=keywords, last_mode="keywords")

@router.message(GenerationStates.entering_example)
async def process_example(message: Message, state: FSMContext):
    example = message.text.strip()
    track_names = await generate_track_names(example=example)
    await message.answer(format_track_names(track_names, "based on your example"), reply_markup=get_results_keyboard())
    # Store parameters for generate_more
    await state.update_data(last_example=example, last_mode="example")

def format_track_names(track_names: List[str], style: str) -> str:
    # Remove asterisks from style name to avoid Markdown formatting
    clean_style = style.replace("*", "")
    result = f"🎧 {clean_style.capitalize()} Track Names 🎧\n\n"
    # Remove any asterisks from track names to avoid Markdown formatting
    clean_names = [name.replace("*", "") for name in track_names]
    result += "\n".join([f"{i+1}. {name}" for i, name in enumerate(clean_names)])
    return result

async def generate_track_names(style: Optional[str] = None, keywords: Optional[str] = None, example: Optional[str] = None) -> List[str]:
    # Define detailed descriptions for each style
    serious_description = (
        "Names that evoke themes related to science, medicine, psychology, warfare, historical events, space, philosophy, technology, etc. "
        "These names should be intriguing, memorable, and potentially reference niche or profound concepts. "
        "Examples: Infinite Extension, Spiral Galaxy, Signal Path, Value Of Icons, Mind Field, Primal Fear, The Fall Of Babylon, Substance Abuse, "
        "Quantum Entanglement, Chronosleep, Synaptic Resonance, The Last Archive, Elysian Fields, Axiom Protocol, Dark Matter Halos, Sentient Algorithm."
    )
    
    nonserious_description = (
        "Names that are humorous, absurd, playful, or unconventional, providing a stark contrast to the 'serious' category. "
        "Examples: Drop Your Pants, Hard Being Hot, Russian Porn Magazine, Satan Was A Babyboomer, Eating Concrete, "
        "My Cat Wrote This, Disco Pickle, Existential Traffic Jam, Keyboard Cat's Revenge, Schrödinger's Lunchbox, Glitchy Banana, The Algorithm Is Drunk, Laser Toaster."
    )
    
    if example:
        prompt = f"Generate 10 techno track names similar to: {example}. Output ONLY the track names in a numbered list, without any descriptions or explanations."
    elif keywords:
        style_desc = serious_description if style == "serious" else nonserious_description if style == "nonserious" else ""
        prompt = f"Generate 10 techno track names using these keywords: {keywords}\n\nStyle description: {style_desc}\n\nOutput ONLY the track names in a numbered list, without any descriptions or explanations."
    else:
        style_desc = serious_description if style == "serious" else nonserious_description if style == "nonserious" else ""
        prompt = f"Generate 10 techno track names in this style:\n{style_desc}\n\nOutput ONLY the track names in a numbered list, without any descriptions or explanations."

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                OPENROUTER_URL,
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://techno-track-name.vercel.app",
                    "X-Title": "Techno Track Name Generator",
                },
                json={
                    "model": "google/gemma-3-4b-it:free",
                    "messages": [
                        {"role": "system", "content": "You are a creative assistant generating techno track names."},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.9,
                    "max_tokens": 300,
                },
                timeout=30.0,
            )
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            return parse_track_names(content)
    except Exception as e:
        logging.error(str(e))
        return ["Error generating names"]

def parse_track_names(content: str) -> List[str]:
    import re
    lines = re.findall(r'\d+\.\s*(.*)', content)
    if not lines:
        lines = [line.strip("-* ") for line in content.splitlines() if line.strip()]
    # Clean any remaining asterisks from the parsed names
    lines = [line.replace("*", "") for line in lines]
    return lines[:10]

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)

# Main polling function
async def main():
    logging.info("Starting bot with long polling")
    await dp.start_polling(bot)

# Function to run the bot
def run_bot():
    asyncio.run(main())

# For direct execution
if __name__ == "__main__":
    run_bot()