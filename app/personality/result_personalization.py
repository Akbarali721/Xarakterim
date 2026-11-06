"""Free-result copy built from stored dimension scores and an optional intent.

The four-letter type is not the source of these sentences. A close or tied
dimension is not described as a firm preference. No percentages, no invented
answers, and no claims about ability, career success, or other people's opinions.
"""

from __future__ import annotations

from app.personality.analytics_constants import INTENT_VALUES
from app.personality.constants import DIMENSION_LOW_CONFIDENCE_MAX_GAP
from app.personality.result_explanation import explain_dimensions

_PAIRS: tuple[tuple[str, str, str], ...] = (
    ("ei", "e", "i"),
    ("sn", "s", "n"),
    ("tf", "t", "f"),
    ("jp", "j", "p"),
)

# Clear preference sentences. Keys are the winning letter.
_SUMMARY = {
    "uz": {
        "e": "Javoblaringizga qaraganda, fikrni boshqalar bilan gaplashib ko‘rishni afzal ko‘rishingiz mumkin.",
        "i": "Javoblaringizga qaraganda, muhim masalani avval o‘zingiz o‘ylab ko‘rishni afzal ko‘rishingiz mumkin.",
        "s": "Ma’lumotni hozirgi aniq holat va tafsilotlar orqali qabul qilishga moyilsiz.",
        "n": "Ma’lumotni imkoniyat va keyingi qadam orqali ko‘rishga moyilsiz.",
        "t": "Qaror chiqarishda sabab va kutiladigan natijaga e’tibor berishga moyilsiz.",
        "f": "Qaror chiqarishda odamning holati va munosabatga e’tibor berishga moyilsiz.",
        "j": "Ishni oldindan tartiblab, keyin boshlashga moyilsiz.",
        "p": "Ishni vaziyatga qarab, yo‘l-yo‘lakay tartiblashga moyilsiz.",
        "mixed": "Bir nechta yo‘nalishda ikkala tomon yaqin yoki teng chiqdi. Bitta qat’iy xarakter xulosasi berilmaydi.",
        "soft": "Qolgan yo‘nalishda farq kichik yoki ikki tomon teng. Bu qat’iy xulosa emas.",
        "no_strength": "Aniq ustunlik chiqmagani uchun hozir bitta odatni foydali tomon deb ko‘rsatib bo‘lmaydi.",
        "no_challenge": "Aniq ustunlik chiqmagani uchun qiyinchilikni hozir bitta odatga bog‘lab bo‘lmaydi.",
    },
    "ru": {
        "e": "По вашим ответам вам может быть удобнее сначала проговорить мысль с другими людьми.",
        "i": "По вашим ответам вам может быть удобнее сначала обдумать важный вопрос самостоятельно.",
        "s": "Информацию вы скорее замечаете через конкретную ситуацию и детали.",
        "n": "Информацию вы скорее смотрите через возможности и следующий шаг.",
        "t": "В решении вам ближе причина и ожидаемый результат.",
        "f": "В решении вам ближе состояние человека и отношения.",
        "j": "Вам ближе сначала навести порядок в деле, а потом начать.",
        "p": "Вам ближе выстраивать дело по ходу, смотря на ситуацию.",
        "mixed": "В нескольких направлениях обе стороны вышли близко или одинаково. Одного твёрдого вывода о характере нет.",
        "soft": "В остальных направлениях разница небольшая или стороны равны. Это не твёрдый вывод.",
        "no_strength": "Явного перевеса нет, поэтому одну привычку сейчас нельзя назвать полезной стороной.",
        "no_challenge": "Явного перевеса нет, поэтому трудность сейчас нельзя привязать к одной привычке.",
    },
}

_EXAMPLE = {
    "uz": {
        "e": "Masalan, yangi fikr kelganda uni bir odamga aytib ko‘rish sizga qulay bo‘lishi mumkin.",
        "i": "Masalan, javob berishdan oldin bir necha daqiqa o‘ylab olish sizga qulay bo‘lishi mumkin.",
        "s": "Masalan, tanlovda hozirgi narx, muddat va aniq shartlarga qaraysiz.",
        "n": "Masalan, tanlovda bu narsa keyin yana qayerda ishlatilishini so‘raysiz.",
        "t": "Masalan, ikki variantning qanday natija berishini yonma-yon yozib solishtirasiz.",
        "f": "Masalan, yechimdan oldin odamning hozirgi holatini so‘rab olasiz.",
        "j": "Masalan, ertangi ishlarni oldindan qisqa ro‘yxatga yozasiz.",
        "p": "Masalan, reja bekor bo‘lsa, o‘sha paytdagi qulay ishni tanlaysiz.",
        "close": "Masalan, bugungi kichik ishda ikkala usul ham qo‘l kelishi mumkin.",
    },
    "ru": {
        "e": "Например, новую мысль может быть удобнее сразу сказать одному человеку.",
        "i": "Например, перед ответом может быть удобнее пару минут подумать одному.",
        "s": "Например, при выборе вы смотрите на цену, срок и конкретные условия.",
        "n": "Например, при выборе вы спрашиваете, где это ещё может пригодиться.",
        "t": "Например, два варианта вы сравниваете по тому, к какому результату они ведут.",
        "f": "Например, перед решением вы спрашиваете, как человек себя сейчас чувствует.",
        "j": "Например, дела на завтра вы заранее записываете коротким списком.",
        "p": "Например, если план отменился, вы выбираете то, что удобно в этот момент.",
        "close": "Например, в небольшом сегодняшнем деле могут пригодиться оба способа.",
    },
}

_STRENGTH = {
    "uz": {
        "e": (
            "Fikrni gapirish orqali aniqlash",
            "Fikrni ovoz chiqarib aytish masalani tezroq ko‘rishga yordam berishi mumkin.",
            "Guruhda birinchi variantni aytish kerak bo‘lgan paytda foydali bo‘lishi mumkin.",
        ),
        "i": (
            "Avval o‘ylab, keyin aytish",
            "Javobdan oldin o‘zingiz ko‘rib chiqish shoshqaloq gapdan saqlashi mumkin.",
            "Muhim xabar yoki qaror oldidan foydali bo‘lishi mumkin.",
        ),
        "s": (
            "Hozirgi holatni ko‘rish",
            "Aniq tafsilotni payqash nima borligini tez tushunishga yordam berishi mumkin.",
            "Narx, muddat yoki mavjud shartni solishtirishda foydali bo‘lishi mumkin.",
        ),
        "n": (
            "Keyingi imkoniyatni ko‘rish",
            "Bitta ishning boshqa joyda ham ishlashini ko‘rish yangi yo‘l topishga yordam berishi mumkin.",
            "Reja hali ochiq bo‘lgan paytda foydali bo‘lishi mumkin.",
        ),
        "t": (
            "Sabab va natijani solishtirish",
            "Nima o‘zgarishini yozib qo‘yish ikki variantni tinchroq solishtirishga yordam berishi mumkin.",
            "Kichik qarorni tanlashda foydali bo‘lishi mumkin.",
        ),
        "f": (
            "Odamning holatini hisobga olish",
            "Avval holatni so‘rash suhbatni yechimdan oldin tushunarli qilishi mumkin.",
            "Yaqin odam bilan gaplashishda foydali bo‘lishi mumkin.",
        ),
        "j": (
            "Oldindan tartib",
            "Qisqa ro‘yxat ertangi ishni esdan chiqarmaslikka yordam berishi mumkin.",
            "Bir kunda bir nechta ish bo‘lganda foydali bo‘lishi mumkin.",
        ),
        "p": (
            "Vaziyatga moslash",
            "Reja o‘zgarganda boshqa qulay ishni tanlash vaqtni yo‘qotmaslikka yordam berishi mumkin.",
            "Kutilmagan bekor bo‘lishda foydali bo‘lishi mumkin.",
        ),
    },
    "ru": {
        "e": (
            "Прояснять мысль в разговоре",
            "Проговорить мысль вслух может помочь быстрее увидеть суть вопроса.",
            "Это может пригодиться, когда в группе нужно назвать первый вариант.",
        ),
        "i": (
            "Сначала обдумать, потом сказать",
            "Короткая пауза перед ответом может уберечь от слишком быстрого слова.",
            "Это может пригодиться перед важным сообщением или решением.",
        ),
        "s": (
            "Видеть текущую ситуацию",
            "Заметить конкретную деталь может помочь быстрее понять, что уже есть.",
            "Это может пригодиться, когда сравниваете цену, срок или условие.",
        ),
        "n": (
            "Видеть следующую возможность",
            "Заметить, где ещё пригодится одно дело, может помочь найти другой путь.",
            "Это может пригодиться, пока план ещё открыт.",
        ),
        "t": (
            "Сравнивать причину и результат",
            "Записать, что изменится, может помочь спокойнее сравнить два варианта.",
            "Это может пригодиться при небольшом выборе.",
        ),
        "f": (
            "Учитывать состояние человека",
            "Сначала спросить, как человек себя чувствует, может сделать разговор понятнее.",
            "Это может пригодиться в разговоре с близким человеком.",
        ),
        "j": (
            "Порядок заранее",
            "Короткий список может помочь не забыть завтрашние дела.",
            "Это может пригодиться, когда за день несколько дел.",
        ),
        "p": (
            "Подстраиваться под ситуацию",
            "Если план изменился, выбрать другое удобное дело может сберечь время.",
            "Это может пригодиться, когда что-то неожиданно отменилось.",
        ),
    },
}

_CHALLENGE = {
    "uz": {
        "e": (
            "Agar sizda ham shunday holat kuzatilsa, gaplashayotib qarorni shoshilib aytib yuborishingiz mumkin.",
            "Aytishdan oldin bitta jumlani yozib qo‘ying.",
        ),
        "i": (
            "Agar sizda ham shunday holat kuzatilsa, o‘ylab yurgan fikringizni boshqalar eshitmasligi mumkin.",
            "Bitta odamga bitta jumla qilib ayting.",
        ),
        "s": (
            "Agar sizda ham shunday holat kuzatilsa, tafsilot ustida turib, ish nima uchun kerakligi qolib ketishi mumkin.",
            "Bir marta «bu nima uchun kerak?» deb yozing.",
        ),
        "n": (
            "Agar sizda ham shunday holat kuzatilsa, imkoniyatlar ko‘p bo‘lib, bugungi aniq qadam qolib ketishi mumkin.",
            "Bugun bajariladigan bitta qadamni yozing.",
        ),
        "t": (
            "Agar sizda ham shunday holat kuzatilsa, sababdan boshlaganingizda suhbatdosh o‘zini eshitilmagandek his qilishi mumkin.",
            "Yechimdan oldin uning holati haqida bitta savol bering.",
        ),
        "f": (
            "Agar sizda ham shunday holat kuzatilsa, kayfiyatni saqlashni o‘ylab, amaliy farq qolib ketishi mumkin.",
            "Ikki variantning bitta amaliy farqini yozing.",
        ),
        "j": (
            "Agar sizda ham shunday holat kuzatilsa, reja qotib, foydali o‘zgarishni qo‘yib yuborishingiz mumkin.",
            "Ro‘yxatda bitta ishni siljitish mumkin deb belgilang.",
        ),
        "p": (
            "Agar sizda ham shunday holat kuzatilsa, variant ochiq turib, boshlash vaqti surilib ketishi mumkin.",
            "Bitta ish uchun boshlash vaqtini yozing.",
        ),
    },
    "ru": {
        "e": (
            "Если у вас тоже так бывает, решение может прозвучать слишком быстро, пока вы говорите.",
            "Перед ответом запишите одно предложение.",
        ),
        "i": (
            "Если у вас тоже так бывает, мысль, которую вы обдумываете, другие могут не услышать.",
            "Скажите одному человеку одно предложение.",
        ),
        "s": (
            "Если у вас тоже так бывает, можно задержаться на детали и не спросить, зачем это нужно.",
            "Один раз напишите: «зачем это нужно?»",
        ),
        "n": (
            "Если у вас тоже так бывает, возможностей много, а сегодняшний конкретный шаг остаётся в стороне.",
            "Напишите один шаг, который можно сделать сегодня.",
        ),
        "t": (
            "Если у вас тоже так бывает, собеседник может почувствовать, что его не услышали, если вы сразу говорите о причине.",
            "Перед решением задайте один вопрос о его состоянии.",
        ),
        "f": (
            "Если у вас тоже так бывает, сохраняя настроение, можно упустить практическую разницу.",
            "Напишите одно практическое отличие двух вариантов.",
        ),
        "j": (
            "Если у вас тоже так бывает, план может застыть и полезное изменение пройдёт мимо.",
            "Отметьте в списке одно дело, которое можно сдвинуть.",
        ),
        "p": (
            "Если у вас тоже так бывает, варианты остаются открытыми, а время начала сдвигается.",
            "Напишите время начала для одного дела.",
        ),
    },
}

_TIP = {
    "uz": {
        "e": "Bugun bitta fikringizni bitta ishonchli odamga ayting.",
        "i": "Muhim suhbatdan oldin uchta asosiy gapni yozib qo‘ying.",
        "s": "Kichik qaror uchun hozir bilgan uchta aniq faktni yozing.",
        "n": "Bitta ishning keyingi qo‘llanishini va bugungi bitta qadamini yozing.",
        "t": "Ikki variantni yonma-yon yozing: har biri nima natija beradi.",
        "f": "Javob yozishdan oldin suhbatdoshga nima kerakligini bitta gap bilan yozing.",
        "j": "Ertangi uchta muhim ishni ro‘yxatga yozing.",
        "p": "Bitta ishni 15 daqiqa ichida boshlash vaqtini belgilang, qolganini ochiq qoldiring.",
        "neutral": "Ikki kichik variantni yozing va hozir qaysi biri qulayroq ekanini belgilang.",
    },
    "ru": {
        "e": "Сегодня скажите одну свою мысль одному человеку, которому доверяете.",
        "i": "Перед важным разговором запишите три основных пункта.",
        "s": "Для небольшого решения запишите три конкретных факта, которые уже знаете.",
        "n": "Запишите, где ещё пригодится одно дело, и один шаг на сегодня.",
        "t": "Запишите два варианта рядом: к какому результату ведёт каждый.",
        "f": "Перед ответом одной фразой запишите, что может быть нужно собеседнику.",
        "j": "Запишите три важных дела на завтра.",
        "p": "Назначьте одному делу старт в ближайшие 15 минут, остальное оставьте открытым.",
        "neutral": "Запишите два небольших варианта и отметьте, какой сейчас удобнее.",
    },
}

_TODAY = {
    "uz": {
        "e": "Bitta fikringizni bitta odamga og‘zaki ayting. Tugashi: gap aytilgan bo‘ladi.",
        "i": "Muhim suhbat uchun uchta gapni qog‘ozga yozing. Tugashi: uchta gap yozilgan bo‘ladi.",
        "s": "Kichik tanlov haqida bilgan uchta faktni yozing. Tugashi: uchta fakt yozilgan bo‘ladi.",
        "n": "Bitta ishning bugungi qadamini bitta jumlada yozing. Tugashi: qadam yozilgan bo‘ladi.",
        "t": "Ikki variantni solishtirib, har birining bitta natijasini yozing. Tugashi: ikkala natija yozilgan bo‘ladi.",
        "f": "Yaqin odamga javobdan oldin uning holati haqida bitta savol yozing. Tugashi: savol yozilgan bo‘ladi.",
        "j": "Ertangi uchta muhim ishni yozing. Tugashi: uchta ish ro‘yxati tayyor bo‘ladi.",
        "p": "Bitta ishni boshlash vaqtini yozing. Tugashi: vaqt belgilanib, ish boshlangan bo‘ladi.",
        "neutral": "Ikki kichik variantni yozing va bittasini belgilang. Tugashi: ikkala variant va tanlov yozilgan bo‘ladi.",
    },
    "ru": {
        "e": "Скажите одну мысль одному человеку. Готово: фраза сказана.",
        "i": "Запишите три пункта для важного разговора. Готово: три пункта на бумаге.",
        "s": "Запишите три факта о небольшом выборе. Готово: три факта записаны.",
        "n": "Одним предложением запишите сегодняшний шаг одного дела. Готово: шаг записан.",
        "t": "У двух вариантов запишите по одному результату. Готово: оба результата записаны.",
        "f": "Перед ответом близкому человеку запишите один вопрос о его состоянии. Готово: вопрос записан.",
        "j": "Запишите три важных дела на завтра. Готово: список из трёх дел готов.",
        "p": "Запишите время начала одного дела и начните его. Готово: время стоит, дело начато.",
        "neutral": "Запишите два небольших варианта и отметьте один. Готово: оба варианта и выбор записаны.",
    },
}

_INTENT_PREFIX = {
    "uz": {
        "strengths": "O‘zingizga yordam beradigan odatni ko‘rish uchun: ",
        "career": "Ish yoki o‘qishdagi bitta ishda: ",
        "self_understanding": "O‘zingizni kuzatish uchun: ",
        "curiosity": "",
    },
    "ru": {
        "strengths": "Чтобы заметить полезную привычку: ",
        "career": "В одном деле на работе или учёбе: ",
        "self_understanding": "Чтобы понаблюдать за собой: ",
        "curiosity": "",
    },
}


def _language(language: str) -> str:
    return language if language in _SUMMARY else "uz"


def _readings(scores: dict[str, int]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for pair, left, right in _PAIRS:
        left_score = int(scores[left])
        right_score = int(scores[right])
        gap = abs(left_score - right_score)
        if left_score == right_score:
            kind, winner = "tie", None
        elif gap <= DIMENSION_LOW_CONFIDENCE_MAX_GAP:
            kind = "close"
            winner = left if left_score > right_score else right
        else:
            kind = "clear"
            winner = left if left_score > right_score else right
        rows.append({"pair": pair, "kind": kind, "winner": winner, "gap": gap})
    return rows


def build_result_profile(
    *,
    e: int,
    i: int,
    s: int,
    n: int,
    t: int,
    f: int,
    j: int,
    p: int,
    language: str,
    intent: str | None = None,
) -> dict[str, object]:
    lang = _language(language)
    text = _SUMMARY[lang]
    scores = {"e": e, "i": i, "s": s, "n": n, "t": t, "f": f, "j": j, "p": p}
    rows = _readings(scores)
    clear = [row for row in rows if row["kind"] == "clear"]
    clear.sort(key=lambda row: int(row["gap"]), reverse=True)
    ambiguous_count = sum(1 for row in rows if row["kind"] != "clear")
    chosen_intent = intent if intent in INTENT_VALUES else None

    summary: list[str] = []
    if ambiguous_count >= 2:
        summary.append(text["mixed"])
    for row in clear[: 2 if ambiguous_count else 3]:
        summary.append(text[str(row["winner"])])
    if 0 < ambiguous_count < 4 and clear and len(summary) < 3:
        summary.append(text["soft"])
    summary = summary[:3]

    notes = explain_dimensions(
        e=e, i=i, s=s, n=n, t=t, f=f, j=j, p=p, language=lang
    )
    examples = _EXAMPLE[lang]
    for note, row in zip(notes, rows, strict=True):
        if row["kind"] == "clear" and row["winner"]:
            note["example"] = examples[str(row["winner"])]
        elif row["kind"] == "close":
            note["example"] = examples["close"]
        else:
            note["example"] = ""

    strengths = []
    for row in clear[:3]:
        title, meaning, helps = _STRENGTH[lang][str(row["winner"])]
        strengths.append({"title": title, "meaning": meaning, "helps": helps})

    challenges = []
    for row in clear[:2]:
        lead, response = _CHALLENGE[lang][str(row["winner"])]
        challenges.append({"lead": lead, "response": response})

    tip_letters = [str(row["winner"]) for row in clear[:3]]
    tips = [_TIP[lang][letter] for letter in tip_letters] or [_TIP[lang]["neutral"]]

    today_letter = str(clear[0]["winner"]) if clear else "neutral"
    today = _TODAY[lang][today_letter]
    if chosen_intent:
        prefix = _INTENT_PREFIX[lang][chosen_intent]
        if prefix:
            today = prefix + today[0].lower() + today[1:]

    return {
        "summary": summary,
        "show_type_heading": ambiguous_count < 2,
        "notes": notes,
        "strengths": strengths,
        "strength_note": "" if strengths else text["no_strength"],
        "challenges": challenges,
        "challenge_note": "" if challenges else text["no_challenge"],
        "tips": tips,
        "today": today,
    }
