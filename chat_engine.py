# -*- coding: utf-8 -*-
"""ChatEngine: Rich 100% offline Russian/English conversational engine with Affinity scaling, actions & name memory."""
import re
import random


def _norm(text):
    t = text.lower().strip()
    t = t.replace("ё", "е")
    return re.sub(r"\s+", " ", t)


def _has_any(text, keys):
    return any(k in text for k in keys)


def _has_word(text, words):
    tokens = set(re.findall(r"[a-zа-я0-9\-]+", text))
    return any(w in tokens for w in words)


class ChatEngine:
    """Offline rule + fuzzy-stem conversational engine for Marin Kitagawa."""

    def __init__(self):
        self.rude_streak = 0
        self.last_reply = ""

    def _pick(self, options, name=""):
        pool = [o for o in options if o != self.last_reply] or list(options)
        msg = random.choice(pool)
        if "{name}" in msg:
            msg = msg.format(name=name if name else "солнышко")
        elif "{name_opt}" in msg:
            msg = msg.format(name_opt=(f", {name}" if name else ""))
        self.last_reply = msg
        return msg

    def respond(self, raw_text, ctx):
        """Process user chat input and return a response dict:
        {reply, emote, mood_delta, aff_delta, tease_delta, particle, action, set_name}
        ctx keys: aff_lvl, mood, outfit, collar_relaxed, music_on, rain_on, light, player_name
        """
        raw = raw_text.strip()
        if not raw:
            return None
        t = _norm(raw)
        aff = ctx.get("aff_lvl", 1)
        outfit = ctx.get("outfit", 0)
        name = ctx.get("player_name", "")
        rain = ctx.get("rain_on", False)
        music = ctx.get("music_on", False)

        out = {
            "reply": "",
            "emote": "normal",
            "mood_delta": 2.0,
            "aff_delta": 2,
            "tease_delta": 0.0,
            "particle": None,
            "action": None,
            "set_name": None,
        }

        # ------------------------------------------------ 1. Name memory ("меня зовут [Имя]" / "зови меня [Имя]")
        m_name = re.search(
            r"(?:меня зовут|зови меня|мо[её] имя|называй меня|my name is|call me)\s+([а-яa-z][а-яa-z0-9\-]{1,18})",
            raw, flags=re.IGNORECASE
        )
        if m_name:
            new_name = m_name.group(1).strip().capitalize()
            out["set_name"] = new_name
            out["emote"] = "starry"
            out["mood_delta"] = 6.0
            out["aff_delta"] = 6
            out["particle"] = "star"
            out["reply"] = self._pick([
                f"{new_name}! Какое классное имя~ Я точно запомню!",
                f"Приятно познакомиться, {new_name}~! Теперь буду звать тебя так!",
                f"Записала в сердечко: {new_name}~ Рада, что мы общаемся!",
            ], new_name)
            return out

        # ------------------------------------------------ 2. Actionable Room Commands
        if _has_any(t, ("выключи музык", "убери музык", "выруби музык", "стоп музык", "music off", "stop music")):
            out["action"] = "music_off"
            out["emote"] = "normal"
            out["reply"] = self._pick(["Ладно, ставлю лоу-фай на паузу~ Посидим в тишине!", "Выключила музыку! Теперь слышно только нас~"])
            return out

        if _has_any(t, ("включи музык", "поставь музык", "хочу музык", "вруби лоу", "лоу-фай", "лоуфай", "lofi", "music on", "play music")):
            out["action"] = "music_on"
            out["emote"] = "pet"
            out["particle"] = "star"
            out["reply"] = self._pick(["Включаю наш уютный 16-битный лоу-фай~!", "Еее, музычка пошла! Сразу такой чилл~!"])
            return out

        if _has_any(t, ("включи дождь", "хочу дождь", "пусть идет дождь", "rain on", "дождик включи")):
            out["action"] = "rain_on"
            out["emote"] = "romantic"
            out["reply"] = self._pick(["О, за окном пошёл уютный дождик~ Обожаю эту атмосферу!", "Включила дождь! Давай слушать капельки вместе~"])
            return out

        if _has_any(t, ("выключи дождь", "убери дождь", "хватит дождя", "ясно", "солнечно", "rain off")):
            out["action"] = "rain_off"
            out["emote"] = "pet"
            out["reply"] = self._pick(["Тучки разошлись, снова ясно!", "Выключила дождь — можно любоваться чистым небом~"])
            return out

        if _has_any(t, ("дождь", "дождик", "погода", "rain", "weather")) and not _has_any(t, ("как дела",)):
            if rain:
                out["emote"] = "romantic"
                out["reply"] = self._pick(["Слушать шум дождя за окном рядом с тобой — чистый кайф~", "Капельки так красиво бегут по стеклу, правда?"])
            else:
                out["action"] = "rain_on"
                out["emote"] = "pet"
                out["reply"] = self._pick(["Хочешь уютный дождик за окном? Лови, включила~!"])
            return out

        if _has_any(t, ("выключи свет", "выруби свет", "погаси свет", "потуши ламп", "выключи ламп", "light off", "темноту")):
            out["action"] = "light_off"
            out["emote"] = "sleepy"
            out["reply"] = self._pick(["Гашу свет~ Стало так загадочно и уютно!", "Выключила лампу... теперь можно и порелаксировать~"])
            return out

        if _has_any(t, ("включи свет", "включи ламп", "сделай светл", "light on", "утро", "день")):
            out["action"] = "light_on"
            out["emote"] = "pet"
            out["reply"] = self._pick(["Готово, стало светло и солнечно~!", "Включила свет! Теперь всё отлично видно~"])
            return out

        if _has_any(t, ("романтик", "гирлянд", "свечи", "вечер", "закат", "romantic")):
            out["action"] = "romantic"
            out["emote"] = "romantic"
            out["particle"] = "heart"
            out["aff_delta"] = 4
            out["reply"] = self._pick([
                "М-м, включаю Romantic Glow и гирлянду~ Атмосфера просто волшебная...",
                "Розово-золотой свет и огоньки гирлянды~ Только ты и я{name_opt}~",
            ], name)
            return out

        if _has_any(t, ("переодень", "смени одежд", "другой наряд", "другую одежд", "шкаф", "change outfit", "dress up")):
            out["action"] = "wardrobe"
            out["emote"] = "starry"
            out["reply"] = self._pick(["Секундочку, сейчас примерю кое-что новенькое~!", "О, показ мод! Бегу к шкафу~"])
            return out

        if _has_any(t, ("очки", "кошачьи ушки", "ушки", "ободок", "аксессуар", "glasses", "cat ears")):
            out["action"] = "accessory"
            out["emote"] = "smug"
            out["reply"] = self._pick(["О, сменю аксессуар! Ну как, мне идёт?~", "Примеряю образ! Обожаю мелкие детали для косплея~"])
            return out

        if _has_any(t, ("сядь на кровать", "на кровать", "посиди на кровати", "приляг", "отдохни на кровати", "sit on bed")):
            out["action"] = "sit_bed"
            out["emote"] = "pet"
            out["reply"] = self._pick(["Иду на кроватку~ Там так мягко!", "Окей, устроюсь на краю кровати и полистаю телефон~"])
            return out

        if _has_any(t, ("почитай", "читай манг", "садись читать", "read manga")):
            out["action"] = "read_manga"
            out["emote"] = "starry"
            out["reply"] = self._pick(["Ура! Сажусь на ковёр с любимой мангой~", "О, отличная идея! Сейчас дочитаю ту самую главу~"])
            return out

        if _has_any(t, ("поиграем", "сыграем", "камень ножниц", "кнб", "мини-игр", "миниигр", "play game", "rps")):
            out["action"] = "start_rps"
            out["emote"] = "smug"
            out["reply"] = self._pick(["Вызов принят! Сыграем в Камень-Ножницы-Бумага — я не поддаюсь~!", "Еее, играем! Выбирай жест внизу~"])
            return out

        if _has_any(t, ("потанцуй", "танцуй", "танец", "dance")):
            out["action"] = "dance"
            out["emote"] = "starry"
            out["particle"] = "star"
            out["reply"] = self._pick(["Включаю ритм! Смотри, как я танцую~!", "Ля-ля-ля~ Двигаемся в такт лоу-фаю~!"])
            return out

        if _has_any(t, ("потянись", "разминк", "stretch")):
            out["action"] = "stretch"
            out["emote"] = "pet"
            out["reply"] = self._pick(["М-м-м... *сладко потягивается* Ох, сразу легче стало~!"])
            return out

        if _has_any(t, ("помаши", "маши", "wave")):
            out["action"] = "wave"
            out["emote"] = "pet"
            out["reply"] = self._pick(["Привет-привет{name_opt}~! Машу тебе обеими руками... ну ладно, одной, но от души!"], name)
            return out

        if _has_any(t, ("застегни", "застегнут", "button up")):
            out["action"] = "collar_button"
            out["emote"] = "normal"
            out["reply"] = self._pick(["Окей, поправлю воротничок обратно~", "Застёгиваю пуговку — всё аккуратно!"])
            return out

        if _has_any(t, ("жарко", "душно", "расстегни", "пуговк", "по-домашнему", "unbutton", "hot in here")):
            if outfit not in (0, 1, 4):
                out["emote"] = "smug"
                out["reply"] = self._pick([
                    "Хи-хи, на этом наряде нет пуговок! Переодень меня в рубашку, если хочешь~",
                    "В худи или футболке пуговок нет~ Сначала заглянем в шкаф!",
                ])
            elif aff >= 3:
                out["action"] = "collar_relax"
                out["emote"] = "flustered"
                out["mood_delta"] = 6.0
                out["aff_delta"] = 5
                out["particle"] = "heart"
                out["reply"] = self._pick([
                    "П-правда тут тепло... Ладно, раз ты не против, расстегну верхнюю пуговку~",
                    "Ой, смущаешь меня{name_opt}... Ну хорошо, побуду чуть более по-домашнему~",
                ], name)
            else:
                out["emote"] = "flustered"
                out["mood_delta"] = 1.0
                out["reply"] = self._pick([
                    "Э-эй! Мы ещё не настолько близки, вообще-то! Погладь меня сперва или поболтаем подольше~",
                    "Хей, не спеши так~! Подними наш Affinity хотя бы до Lv.3, хи-хи!",
                ])
            return out

        # ------------------------------------------------ 3. Teasing / Rude / Playful Banter
        if _has_any(t, ("дура", "глупая", "тупая", "отстань", "бесишь", "надоела", "не люблю", "плохая",
                        "злюка", "вредная", "уйди", "замолчи", "stupid", "shut up", "hate you", "annoying")):
            self.rude_streak += 1
            out["emote"] = "pout"
            out["mood_delta"] = -6.0
            out["aff_delta"] = 0
            out["tease_delta"] = 1.8
            out["particle"] = "excl"
            if self.rude_streak >= 2:
                self.rude_streak = 0
                out["action"] = "throw_pillow"
                out["reply"] = self._pick([
                    "Ах вот как?! Получай подушкой прямо в нос!! Хмпф!",
                    "Всё, ты сам напросился! Лови подушку, вредина!!",
                ])
            else:
                out["reply"] = self._pick([
                    "Хмпф!! Вообще-то я обиделась! И не смотри на меня так!",
                    "Эй! Нельзя так говорить девушке! Извинись, или в ход пойдёт подушка!",
                    "Ну и ладно! Буду дуться, пока не погладишь меня~",
                ])
            return out

        self.rude_streak = max(0, self.rude_streak - 1)

        # ------------------------------------------------ 4. Romance, Compliments & Flirt (Affinity-scaled!)
        is_flirt = _has_any(t, (
            "люблю", "влюблен", "влюбил", "поцелу", "чмок", "обним", "обнять", "скучал", "выходи за меня",
            "женимся", "пофлирт", "флирт", "моя девуш", "красив", "милая", "милашка", "красотка", "няш",
            "очаровательн", "лучшая", "обожаю", "прекрасн", "чудесн", "солнышко", "котик", "комплимент",
            "идеальн", "любуюсь", "богиня", "love you", "cute", "pretty", "beautiful", "kiss", "hug", "marry", "miss you"
        ))
        if is_flirt:
            if aff >= 4:
                out["emote"] = "romantic"
                out["mood_delta"] = 10.0
                out["aff_delta"] = 12
                out["particle"] = "kiss_heart"
                out["reply"] = self._pick([
                    "М-м... {name}, у меня от твоих слов сердечко тает~ Я тебя тоже очень-очень люблю! Чмок~",
                    "Ты всегда знаешь, как сделать меня самой счастливой{name_opt}~ Лови воздушный поцелуй!",
                    "Ой, я вся покраснела... Обнимаю тебя крепко-крепко{name_opt}~ Не уходи далеко, ладно?",
                    "С тобой даже обычный вечер чувствуется как сцена из самого романтичного аниме{name_opt}~",
                ], name)
            elif aff == 3:
                out["emote"] = "flustered"
                out["mood_delta"] = 8.0
                out["aff_delta"] = 8
                out["particle"] = "heart"
                out["reply"] = self._pick([
                    "А-ай! Не говори такие сладкие вещи так внезапно{name_opt}~ Я же вся красная!",
                    "Хе-хе... правда так думаешь? Ты мне тоже очень нравишься~!",
                    "Ой, ну перестань меня так смущать~ Хотя... нет, говори ещё! Хи-хи~",
                ], name)
            else:
                out["emote"] = "flustered"
                out["mood_delta"] = 6.0
                out["aff_delta"] = 6
                out["particle"] = "heart"
                out["reply"] = self._pick([
                    "Ч-чего?! Вот так прямо в лоб?! Смущаешь меня, вообще-то~",
                    "Хи-хи, какой ты шустрый{name_opt}! Но мне приятно, спасибо~!",
                    "Ого, комплимент принят! Я и правда старалась с образом сегодня~",
                ], name)
            return out

        # ------------------------------------------------ 5. Heart-to-Heart & Emotional Support
        if _has_any(t, ("грустн", "печаль", "тоск", "устал", "выгор", "плохо", "тяжело", "одинок",
                        "скучно", "депресс", "стресс", "болит", "sad", "tired", "lonely", "bored", "stressed")):
            out["emote"] = "romantic" if aff >= 3 else "pet"
            out["mood_delta"] = 4.0
            out["aff_delta"] = 6
            out["particle"] = "heart"
            out["reply"] = self._pick([
                "Эй{name_opt}, не грусти... Посиди со мной в комнате, включим лоу-фай и отдохнём вместе~",
                "Ты так много стараешься! Выдохни, погладь меня или давай выпьем бабл-ти — всё обязательно наладится!",
                "Иди сюда, мысленно крепко обнимаю тебя{name_opt}~ Я всегда здесь, если захочешь просто поболтать!",
                "Если скучно или тяжело — давай сыграем в Камень-Ножницы-Бумага или устроим подушечный бой? Обещаю поднять настроение!",
            ], name)
            return out

        # ------------------------------------------------ 6. Greetings & Goodbyes
        if _has_any(t, ("доброе утро", "с добрым утром", "good morning")):
            out["emote"] = "starry"
            out["mood_delta"] = 5.0
            out["aff_delta"] = 4
            out["particle"] = "star"
            out["action"] = "wave"
            out["reply"] = self._pick([
                "Доброе утро{name_opt}~! Надеюсь, ты отлично выспался! Готов к классному дню?",
                "Утречка{name_opt}~! Солнышко уже светит, а я как раз привела себя в порядок~",
            ], name)
            return out

        if _has_any(t, ("спокойной ночи", "сладких снов", "иду спать", "доброй ночи", "good night", "goodnight")):
            out["emote"] = "sleepy"
            out["mood_delta"] = 5.0
            out["aff_delta"] = 5
            out["particle"] = "heart"
            out["reply"] = self._pick([
                "Спокойной ночи{name_opt}~ Пусть тебе приснится что-нибудь очень уютное и тёплое~ Zzz...",
                "Сладких снов{name_opt}! Завтра обязательно заглядывай ко мне снова~!",
            ], name)
            return out

        if _has_word(t, ("пока", "бай", "прощай", "bye", "увидимся", "до встречи")):
            out["emote"] = "romantic" if aff >= 3 else "pet"
            out["action"] = "wave"
            out["reply"] = self._pick([
                "Пока-пока{name_opt}~! Буду ждать тебя в комнате!",
                "Не пропадай надолго{name_opt}~ Возвращайся поскорее!",
            ], name)
            return out

        if _has_word(t, ("привет", "приветик", "хай", "ку", "здарова", "здравствуй", "йо", "hello", "hi", "hey")) or _has_any(t, ("добрый день", "добрый вечер")):
            out["emote"] = "romantic" if aff >= 4 else "starry"
            out["mood_delta"] = 4.0
            out["aff_delta"] = 4
            out["action"] = "wave"
            out["particle"] = "heart" if aff >= 3 else "star"
            out["reply"] = self._pick([
                "Привет-привет{name_opt}~! Так рада тебя видеть!",
                "Хай-хай{name_opt}~! Как раз думала о тебе — чем займёмся сегодня?",
                "О, привет{name_opt}! Заходи, располагайся поудобнее~",
            ], name)
            return out

        # ------------------------------------------------ 7. Casual Chat & Marin's Canon Interests
        if _has_any(t, ("как дела", "как ты", "как настроение", "что нового", "how are you")):
            out["emote"] = "pet"
            out["aff_delta"] = 3
            if rain:
                out["reply"] = self._pick(["Супер-уютно! Слушаю дождик за окном и болтаю с тобой{name_opt}~"], name)
            elif music:
                out["reply"] = self._pick(["На все сто! Под этот лоу-фай настроение просто космос~ А у тебя как?"])
            else:
                out["reply"] = self._pick([
                    "Отлично{name_opt}~! Особенно когда ты заглядываешь поболтать!",
                    "У меня всё супер! Придумываю новый косплей и отдыхаю в комнате~ А как твои дела?",
                ], name)
            return out

        if _has_any(t, ("что делаешь", "чем занята", "чем занимаешься", "what are you doing")):
            out["emote"] = "smug"
            out["reply"] = self._pick([
                "Отдыхаю в своей уютной комнате, листаю мангу и жду, когда ты меня погладишь~",
                "Прикидываю выкройку для нового косплея! Ну и болтаю с тобой, конечно~",
            ])
            return out

        if _has_any(t, ("коспле", "шизуку", "годжо", "шить", "костюм", "cosplay")):
            out["emote"] = "starry"
            out["mood_delta"] = 5.0
            out["aff_delta"] = 5
            out["particle"] = "star"
            out["reply"] = self._pick([
                "Ооо, косплей — моя главная страсть!! Мечтаю сшить идеальное готическое платье Шизуку-тан!",
                "Обожаю перевоплощаться в любимых персонажей! Если хочешь, можем сделать косплей-селфи камерой из тумбочки~",
            ])
            return out

        if _has_any(t, ("манг", "аниме", "тайтл", "сериал", "manga", "anime")):
            out["emote"] = "starry"
            out["mood_delta"] = 4.0
            out["aff_delta"] = 4
            out["reply"] = self._pick([
                "Аниме и манга — это жизнь!! Кстати, на полу лежит мой любимый томик — кликни или скажи «почитай мангу»!",
                "Я недавно прочитала такую крутую главу, что до сих пор под впечатлением! А какой твой любимый жанр?",
            ])
            return out

        if _has_any(t, ("бабл", "чай", "еда", "кушать", "вкусн", "конфет", "сладк", "кофе", "boba", "tea", "food")):
            out["emote"] = "starry"
            out["mood_delta"] = 4.0
            out["aff_delta"] = 3
            out["reply"] = self._pick([
                "Ммм, бабл-ти с тапиокой и сладости — моя слабость! Перетащи стаканчик с тумбочки ко мне~",
                "Обожаю вкусно перекусить! В верхнем ящике тумбочки, кстати, спрятана коробочка конфет~",
            ])
            return out

        if _has_any(t, ("кто ты", "как тебя зовут", "расскажи о себе", "who are you")):
            out["emote"] = "smug"
            out["reply"] = self._pick([
                "Я Марин Китагава~! Обожаю аниме, мангу, косплей, бабл-ти и уютные вечера с тобой!",
            ])
            return out

        if _has_any(t, ("спасибо", "благодар", "пасиб", "сяб", "thanks", "thank you")):
            out["emote"] = "pet"
            out["mood_delta"] = 4.0
            out["aff_delta"] = 3
            out["particle"] = "heart"
            out["reply"] = self._pick([
                "Всегда пожалуйста{name_opt}~! Обращайся в любое время!",
                "Хи-хи, не за что~! Мне самой в радость!",
            ], name)
            return out

        if _has_any(t, ("шутк", "рассмеши", "анекдот", "joke")):
            out["emote"] = "smug"
            out["particle"] = "star"
            out["reply"] = self._pick([
                "Знаешь, почему косплееры никогда не теряют нить разговора? Потому что у них всегда есть запасная катушка! Хи-хи~",
                "Мой идеальный план на день: 1) бабл-ти, 2) манга на ковре, 3) чтобы ты меня гладил ПКМ~ Идеально же!",
            ])
            return out

        if _has_any(t, ("селфи", "фотк", "камер", "сфотка", "selfie", "photo")):
            out["emote"] = "starry"
            out["reply"] = self._pick([
                "Хочешь классный Полароид-снимок? Открой нижний ящик тумбочки и поднеси камеру ко мне~!",
            ])
            return out

        # ------------------------------------------------ 8. Lively In-Character Fallback (never dry!)
        out["emote"] = random.choice(("pet", "smug", "normal", "starry"))
        out["aff_delta"] = 3
        fallbacks = [
            "Хи-хи, интересно звучит{name_opt}~ Расскажешь подробнее?",
            "Ого! Правда? Мне нравится, как ты рассуждаешь~",
            "М-м, слушаю тебя внимательно{name_opt}~ С тобой так легко болтать!",
            "Ага-ага! Кстати, ты можешь попросить меня включить музыку, дождик, почитать мангу или поиграть в КНБ~",
            "Хе-хе, ты такой прикольный{name_opt}! Обожаю наши посиделки в этой комнате~",
        ]
        if rain:
            fallbacks.append("Под шум дождика за окном любой наш разговор кажется таким уютным{name_opt}~")
        out["reply"] = self._pick(fallbacks, name)
        return out
