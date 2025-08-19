"""
Интерпретатор анкет который использует json-подобный синтаксис для набора вопросов и возможных ответов.
Отправь anketa для запуска беседы по анкете.
"""

from telethon import events

import json


@tlgbot.on(events.NewMessage(chats=tlgbot.settings.get_all_user_id(), pattern='anketa'))
async def handler(event):
    types_answer_message = {"int": "число", "string": "строка",
                            "float": "число с плавающей точкой", "list": "список ответов"}
    result_data = {}

    with open("plugins_bot/runner_questionnaire/example.json") as f:
        all_question_json = f.read()

    all_question = json.loads(all_question_json)

    await event.reply("Начнём беседу...")

    chat_id = event.chat_id
    async with tlgbot.conversation(chat_id) as conv:
        # response = conv.wait_event(events.NewMessage(incoming=True))
        for num in range(len(all_question)):
            question = all_question[num]
            var_question = question["var"]
            await conv.send_message(f"Ответьте на {num + 1} вопрос:")
            await conv.send_message(question["question"])
            type_answer = question["answer"]["type"]
            await conv.send_message(f"Ответ должен быть {types_answer_message[type_answer]}")

            if type_answer == "list":
                list_answer = question["answer"]["list_answer"]
                await conv.send_message("Нужно выбрать цифрой ответ из списка:")
                string_message = ""
                for i in range(len(list_answer)):
                    string_message += f"{i + 1} - {list_answer[i]}" + "\n"
                await conv.send_message(string_message)
            answer_full = await conv.get_response()
            answer = answer_full.message

            if type_answer == "int":
                while not all(x.isdigit() for x in answer):
                    await conv.send_message("Нужно ввести число. Попробуйте ещё раз.")
                    answer_full = await conv.get_response()
                    answer = answer_full.message
                result_data[var_question] = int(answer)

            if type_answer == "float":
                flag_exit = True
                while flag_exit:
                    try:
                        num_answer = float(answer)
                        flag_exit = False
                    except ValueError:
                        await conv.send_message("Нужно ввести число. Попробуйте ещё раз.")
                        answer_full = await conv.get_response()
                        answer = answer_full.message
                result_data[var_question] = num_answer

            if type_answer == "list":
                flag_exit = True
                while flag_exit:
                    try:
                        num_answer = int(answer)
                        await conv.send_message(answer)
                        if (num_answer <= 0) or (num_answer > len(list_answer)):
                            await conv.send_message("Нужно выбрать номер варианта ответа.")
                            answer_full = await conv.get_response()
                            answer = answer_full.message
                        else:
                            flag_exit = False
                    except ValueError:
                        await conv.send_message("Нужно выбрать номер варианта ответа.")
                        answer_full = await conv.get_response()
                        answer = answer_full.message
                        # flag_exit = True
                result_data[var_question] = list_answer[num_answer - 1]

            if type_answer == "string":
                flag_exit = True
                while flag_exit:
                    if answer.strip() == "":
                        await conv.send_message("Нужно чтобы строка была не пустой. Попробуйте еще раз.")
                        answer_full = await conv.get_response()
                        answer = answer_full.message
                    else:
                        flag_exit = False
                result_data[var_question] = answer

    await event.respond(str(result_data))
    await event.respond("Беседа закончена.")
