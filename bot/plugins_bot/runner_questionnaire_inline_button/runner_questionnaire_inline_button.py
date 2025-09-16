"""
Интерпретатор анкет который использует json-подобный синтаксис для набора вопросов и возможных ответов.
Отправь anketa для запуска беседы по анкете.
"""

from telethon import events, Button

import json


# Defined somewhere
def press_event(user_id):
    return events.CallbackQuery(func=lambda e: e.data.decode("utf-8"))


@tlgbot.on(tlgbot.admin_cmd('anketa_button'))
async def run_quest_inline(event):
    types_answer_message = {
        "int": tlgbot.i18n.t('type_int', lang=tlgbot.i18n.default_lang) if hasattr(tlgbot, 'i18n') else "число",
        "string": tlgbot.i18n.t('type_string', lang=tlgbot.i18n.default_lang) if hasattr(tlgbot, 'i18n') else "строка",
        "float": tlgbot.i18n.t('type_float', lang=tlgbot.i18n.default_lang) if hasattr(tlgbot, 'i18n') else "число с плавающей точкой",
        "list": tlgbot.i18n.t('type_list', lang=tlgbot.i18n.default_lang) if hasattr(tlgbot, 'i18n') else "список ответов"
    }
    result_data = {}

    with open("bot/plugins_bot/runner_questionnaire_inline_button/example.json") as f:
        all_question_json = f.read()

    all_question = json.loads(all_question_json)

    await event.reply(tlgbot.i18n.t('runner_start', lang=tlgbot.i18n.default_lang))

    chat_id = event.chat_id
    async with tlgbot.conversation(chat_id) as conv:
        # response = conv.wait_event(events.NewMessage(incoming=True))
        for num in range(len(all_question)):
            question = all_question[num]
            var_question = question["var"]
            await conv.send_message(tlgbot.i18n.t('rq_answer_n', lang=tlgbot.i18n.default_lang, n=num + 1))
            await conv.send_message(question["question"])
            type_answer = question["answer"]["type"]
            await conv.send_message(tlgbot.i18n.t('rq_type_must_be', lang=tlgbot.i18n.default_lang, type_name=types_answer_message[type_answer]))

            if type_answer == "list":
                list_answer = question["answer"]["list_answer"]
                string_message = ""
                button_answer = []
                for i in range(len(list_answer)):
                    button_answer.append(Button.inline(list_answer[i]))

                await conv.send_message(tlgbot.i18n.t('rq_choose_from_list', lang=tlgbot.i18n.default_lang), buttons=button_answer)
                answer = await conv.wait_event(press_event(event.chat_id))
                result_data[var_question] = answer.data.decode("utf-8")

            if type_answer == "int":
                answer_full = await conv.get_response()
                answer = answer_full.message
                while not all(x.isdigit() for x in answer):
                    await conv.send_message(tlgbot.i18n.t('rq_need_number', lang=tlgbot.i18n.default_lang))
                    answer_full = await conv.get_response()
                    answer = answer_full.message
                result_data[var_question] = int(answer)

            if type_answer == "float":
                answer_full = await conv.get_response()
                answer = answer_full.message
                flag_exit = True
                while flag_exit:
                    try:
                        num_answer = float(answer)
                        flag_exit = False
                    except ValueError:
                        await conv.send_message(tlgbot.i18n.t('rq_need_number', lang=tlgbot.i18n.default_lang))
                        answer_full = await conv.get_response()
                        answer = answer_full.message
                result_data[var_question] = num_answer

            if type_answer == "string":
                answer_full = await conv.get_response()
                answer = answer_full.message
                flag_exit = True
                while flag_exit:
                    if answer.strip() == "":
                        await conv.send_message(tlgbot.i18n.t('rq_string_not_empty', lang=tlgbot.i18n.default_lang))
                        answer_full = await conv.get_response()
                        answer = answer_full.message
                    else:
                        flag_exit = False
                result_data[var_question] = answer

    await event.respond(str(result_data))
    await event.respond(tlgbot.i18n.t('runner_finished', lang=tlgbot.i18n.default_lang))
