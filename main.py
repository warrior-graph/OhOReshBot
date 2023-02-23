#!/usr/bin/env python
# pylint: disable=unused-argument, wrong-import-position
# This program is dedicated to the public domain under the CC0 license.

import logging
import os
from telegram import __version__ as TG_VER
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)
import prettytable as pt
from pytz import timezone
from solartime import SolarTime
from datetime import date, timedelta, datetime
from timezonefinder import TimezoneFinder
import locale
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')


try:
    from telegram import __version_info__
except ImportError:
    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]

if __version_info__ < (20, 0, 0, "alpha", 5):
    raise RuntimeError(
        f"This example is not compatible with your current PTB version {TG_VER}. To view the "
        f"{TG_VER} version of this example, "
        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"
    )

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

logger = logging.getLogger(__name__)

REGULAR_CHOICE, HOW_MANY, LOCATION = range(3)


reply_keyboard = [
    ["Hoje", "Amanhã"],
    ["Semana"]
]

days_choice = {
    "hoje": 0,
    "amanhã": 1,
    "semana": 7
}

markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)

TOKEN = os.getenv('BOT_TOKEN')


def calculate_solartimes(latitude: float, longitude: float, day: date) -> str:
    sun = SolarTime()
    schedule = sun.sun_utc(day, latitude, longitude)
    tmz_finder = TimezoneFinder()
    user_tmz = tmz_finder.timezone_at(lat=latitude, lng=longitude)
    sunrise = schedule['sunrise'].astimezone(timezone(str(user_tmz)))
    solar_noon = schedule['noon'].astimezone(timezone(str(user_tmz)))
    sunset = schedule['sunset'].astimezone(timezone(str(user_tmz)))
    solar_midnight = sun.solar_noon_utc(
        day - timedelta(days=1), longitude).astimezone(timezone(str(user_tmz))) + timedelta(hours=12)

    table = pt.PrettyTable(['Momento', 'Horário'])
    table.align['Momento'] = 'l'
    table.align['Horário'] = 'c'
    data = [
        ('Meia noite', solar_midnight.strftime('%H:%M:%S')),
        ('Nascer do sol', sunrise.strftime('%H:%M:%S')),
        ('Meio dia', solar_noon.strftime('%H:%M:%S')),
        ('Pôr do sol', sunset.strftime('%H:%M:%S')),
    ]
    for moment, sched in data:
        table.add_row([moment, sched])
    main_table = pt.PrettyTable(['{} e.v.'.format(day.strftime('%d/%m/%Y'))])
    main_table.align['{} e.v.'.format(day.strftime('%d/%m/%Y'))] = 'c'
    main_table.add_row(['{}'.format(table)])
    return '<pre>{}</pre>'.format(main_table)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "<b><i>Faze o que tu queres há de ser tudo da Lei.</i></b>\n\n"
        "Olá, bem-vindo ao <b>Oh o RESH!</b> "
        "Vou te ajudar a calcular os horários "
        "das adorações solares contidas no "
        "<a href=\"https://www.hadnu.org/publicacoes/liber-resh-vel-helios/\">Liber Resh vel Helios</a>\n\n"
        "<b><i>Amor é a lei, amor sob vontade.</i></b>",
        parse_mode='HTML',
    )
    await regular_choice(update, context)
    return HOW_MANY


async def regular_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text(
        "Para quais dias você deseja?",
        reply_markup=markup
    )
    return HOW_MANY


async def how_many(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text
    context.user_data["choice"] = text
    await update.message.reply_text(f"Ok! Irei calcular para {text.lower()}.",
                                    reply_markup=ReplyKeyboardRemove(),
                                    )
    await update.message.reply_text(
        "Agora compartilhe sua localização atual. Precisa ser um celular. "
        "Basta selecionar o clipe(opção de compartilhar fotos) "
        "e compartilhar a localização atual.",
        reply_markup=ReplyKeyboardRemove(),
    )

    return LOCATION


async def location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    user_location = update.message.location
    user_data = context.user_data
    choice = user_data["choice"]
    days = days_choice[choice.lower()]
    del user_data["choice"]
    logger.info(
        "Location of %s: %f / %f", user.first_name, user_location.latitude, user_location.longitude
    )
    current_day = date.today()
    output = ''
    if days == 1 or days == 0:
        current_day += timedelta(days=days)
        output = calculate_solartimes(user_location.latitude,
                                      user_location.longitude, current_day)

    else:
        for i in range(days):
            output += calculate_solartimes(user_location.latitude,
                                           user_location.longitude, current_day + timedelta(days=i+1))
    await update.message.reply_text(output, parse_mode='HTML')

    return HOW_MANY


async def skip_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    logger.info("Bio of %s: %s", user.first_name, update.message.text)
    await update.message.reply_text("Vamos tentar novamente. Por favor, compartilhe sua localização.")

    return LOCATION


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    user_data = context.user_data
    if user_data.get("choice"):
        del user_data["choice"]
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "93 93/93.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def main() -> None:
    """Run the bot."""
    # Create the Application and pass it your bot's token.
    application = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            LOCATION: [
                MessageHandler(filters.LOCATION, location),
                CommandHandler("skip", skip_location),
            ],
            HOW_MANY: [
                MessageHandler(
                    filters.Regex("^(Hoje|Amanhã|Semana)$"), how_many
                )
            ],
            REGULAR_CHOICE: [
                MessageHandler(filters.TEXT, how_many),
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel),
                   CommandHandler("retry", regular_choice)],
    )

    application.add_handler(conv_handler)

    application.run_polling()


if __name__ == "__main__":
    main()
