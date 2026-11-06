"""Xarakterim: kelishilgan 24 ta o‘zbekcha savol (TZ-3B).

Har yo‘nalishga 6 savol: EI, SN, TF, JP.
Javoblar tartibi: A/B — birinchi qutb, C/D — ikkinchi qutb.
Mavjud import, o‘zgaruvchi nomi va tuple tuzilishi saqlangan.
Bu savollar ilmiy validatsiyadan o‘tgan psixologik diagnostika emas.
"""

from app.models.enums import PersonalityDimension

PERSONALITY_QUESTIONS_UZ: list[tuple[str, PersonalityDimension, list[str]]] = [
    # E / I — muloqot va ichki mulohaza
    (
        "Bir haftalik ish yoki o‘qishdan keyin bo‘sh vaqtingiz paydo bo‘ldi. Qanday dam olishni afzal ko‘rasiz?",
        PersonalityDimension.EI,
        [
            "Do‘stlar bilan uchrashib, vaqtni birga o‘tkazishni.",
            "Bir-ikki yaqinim bilan suhbatlashishni.",
            "Avval yolg‘iz dam olib, keyin yaqinlarim bilan gaplashishni.",
            "Tinch joyda o‘zim yoqtirgan mashg‘ulot bilan shug‘ullanishni.",
        ],
    ),
    (
        "Xayolingizga qiziqarli bir fikr keldi. Uni qanday rivojlantirish sizga qulayroq?",
        PersonalityDimension.EI,
        [
            "Bir nechta odam bilan muhokama qilib, yangi fikrlar olaman.",
            "Bir yaqinim bilan maslahatlashaman.",
            "Avval o‘zim o‘ylab, keyin kimdandir fikr so‘rayman.",
            "Avval fikrni mustaqil ravishda batafsil ishlab chiqaman.",
        ],
    ),
    (
        "Bir nechta odam biror mavzuda suhbatlashyapti. Odatda o‘zingizni qanday tutasiz?",
        PersonalityDimension.EI,
        [
            "Faol gaplashaman, suhbatga yangi mavzular qo‘shaman.",
            "Suhbatga tez-tez qo‘shilib, fikrimni bildiraman.",
            "Ko‘proq tinglayman, fikrim bo‘lsa aytaman.",
            "Asosan tinglashni va boshqalarning fikrini kuzatishni afzal ko‘raman.",
        ],
    ),
    (
        "O‘zingiz qiziqqan yangi ko‘nikmani o‘rganmoqchisiz. Qanday o‘rganish sizga qulay?",
        PersonalityDimension.EI,
        [
            "Guruhda, boshqalar bilan fikr almashib o‘rganish.",
            "Bir tanishim bilan birga o‘rganish.",
            "Mustaqil o‘rganib, kerak bo‘lsa maslahat so‘rash.",
            "O‘zim izlanib, mustaqil mashq qilish.",
        ],
    ),
    (
        "Siz uzoq kutgan yaxshi xabarni eshitdingiz. Birinchi nima qilishni xohlaysiz?",
        PersonalityDimension.EI,
        [
            "Quvonchimni bir nechta yaqinim bilan bo‘lishishni.",
            "Eng yaqin odamimga darhol aytishni.",
            "Biroz vaqt o‘tib, yaqinimga aytishni.",
            "Avval bu xursandchilikni o‘zimcha his qilishni.",
        ],
    ),
    (
        "Sizga biror vazifa berildi. Uni yolg‘iz yoki boshqalar bilan bajarish imkoningiz bor. Qaysi usul sizga qulayroq?",
        PersonalityDimension.EI,
        [
            "Bir nechta odam bilan birga ishlash.",
            "Bitta hamkor bilan vazifani bajarish.",
            "Asosan mustaqil ishlab, kerak bo‘lsa maslahatlashish.",
            "Vazifani boshidan oxirigacha mustaqil bajarish.",
        ],
    ),
    # S / N — ma'lumotga e'tibor
    (
        "Sizga ilgari bilmagan bir mavzuni tushuntirishyapti. Qanday tushuntirish sizga qulayroq?",
        PersonalityDimension.SN,
        [
            "Avval amalda qanday bajarilishini ko‘rsatishsa.",
            "Hayotiy misollar orqali tushuntirishsa.",
            "Avval umumiy mazmunini tushuntirib, keyin misollar keltirishsa.",
            "Asosiy g‘oya va boshqa mavzular bilan bog‘liqligini tushuntirishsa.",
        ],
    ),
    (
        "Kimdir sizga ilgari eshitmagan yangi bir g‘oya haqida gapirdi. Sizni birinchi nima qiziqtiradi?",
        PersonalityDimension.SN,
        [
            "Bu g‘oya amalda qanday ishlashi.",
            "Uni qo‘llab ko‘rganlar qanday natija olgani.",
            "Bu g‘oyani yana qayerlarda ishlatish mumkinligi.",
            "Undan kelajakda qanday yangi imkoniyatlar paydo bo‘lishi.",
        ],
    ),
    (
        "O‘zingizga esda qolgan bir voqeani boshqalarga aytib bermoqchisiz. Odatda nimadan boshlaysiz?",
        PersonalityDimension.SN,
        [
            "Voqea qayerda va qachon bo‘lganidan.",
            "Voqeada sodir bo‘lgan asosiy hodisalardan.",
            "Voqeaning umumiy mazmunidan.",
            "Bu voqea nimani anglatishi yoki undan qanday xulosa chiqarganimdan.",
        ],
    ),
    (
        "Ish, o‘qish yoki boshqa mashg‘ulotingizda yangi tartib joriy qilindi. Sizni birinchi nima qiziqtiradi?",
        PersonalityDimension.SN,
        [
            "Endi aniq nimalar qilish kerakligi.",
            "Oldingi tartibdan qanday amaliy farqi borligi.",
            "Nima uchun bunday o‘zgarish kiritilgani.",
            "Bu o‘zgarish kelajakda yana qanday imkoniyatlar ochishi mumkinligi.",
        ],
    ),
    (
        "Sizga ilgari ko‘rmagan bir suratni ko‘rsatishdi. Birinchi nimaga e'tibor berasiz?",
        PersonalityDimension.SN,
        [
            "Suratda kimlar va nimalar borligiga.",
            "Suratdagi mayda tafsilotlarga.",
            "Suratning umumiy mazmuniga.",
            "Suratdagi narsalar bir-biri bilan qanday bog‘langaniga.",
        ],
    ),
    (
        "Bir xil muammo bir necha marta takrorlandi. Vaziyatni tushunish uchun nimaga ko‘proq e'tibor berasiz?",
        PersonalityDimension.SN,
        [
            "Har safar aynan nima sodir bo‘lganiga.",
            "Muammo takrorlangan paytdagi o‘xshash holatlarga.",
            "Bu holatlarni bir-biri bilan nima bog‘lab turganiga.",
            "Muammoning ortida qanday umumiy sabab yoki qonuniyat bo‘lishi mumkinligiga.",
        ],
    ),
    # T / F — qarordagi mezonlar
    (
        "Sizga ikkita yaxshi ish taklif qilishdi. Qaysi jihat qaroringizga ko‘proq ta'sir qiladi?",
        PersonalityDimension.TF,
        [
            "Maosh, ish sharoiti va aniq imkoniyatlar.",
            "Qaysi ishda kasbiy o‘sish imkoniyati ko‘proqligi.",
            "Qaysi jamoada o‘zimni qulay his qilishim.",
            "Qaysi ish shaxsiy qadriyatlarim va qiziqishlarimga yaqinligi.",
        ],
    ),
    (
        "Do‘stingiz biror muammo haqida maslahat so‘radi. Odatda suhbatni qanday boshlaysiz?",
        PersonalityDimension.TF,
        [
            "Muammoning sababini aniqlashga kirishaman.",
            "Uni hal qilish uchun mavjud variantlarni aytaman.",
            "Avval uning vaziyatini yaxshiroq tushunishga harakat qilaman.",
            "Avval uni tinglab, ruhiy qo‘llab-quvvatlashga harakat qilaman.",
        ],
    ),
    (
        "Do‘stlaringiz bilan dam olish uchun ikkita joydan birini tanlashingiz kerak. Siz uchun nima muhimroq?",
        PersonalityDimension.TF,
        [
            "Qaysi joyga borish qulayroq ekanligi.",
            "Qaysi joy narxi va sharoiti bo‘yicha yaxshiroqligi.",
            "Qaysi joy ko‘pchilikka ko‘proq yoqishi.",
            "Qaysi joy barcha do‘stlarimning xohishlariga mos kelishi.",
        ],
    ),
    (
        "Bir nechta odam bilan muhim masalani hal qilishingiz kerak. Fikrlar turlicha. Qaysi yo‘lni afzal ko‘rasiz?",
        PersonalityDimension.TF,
        [
            "Eng samarali variantni dalillar bilan tanlashni.",
            "Har bir variantning foyda va kamchiliklarini taqqoslashni.",
            "Har bir odamning fikrini hisobga olib, umumiy qarorga kelishni.",
            "Barcha tomonlar o‘zini hisobga olingan deb his qiladigan yechim topishni.",
        ],
    ),
    (
        "Birgalikda bajariladigan ishga mas'ul odamni tanlash kerak. Siz kimni tanlaysiz?",
        PersonalityDimension.TF,
        [
            "Bu ishda tajribasi eng ko‘p odamni.",
            "Oldin yaxshi natija ko‘rsatgan odamni.",
            "Bu vazifani bajarishga eng qiziqqan odamni.",
            "Bu mas'uliyat orqali rivojlanishni istayotgan odamni.",
        ],
    ),
    (
        "Siz uchun muhim bo‘lgan masalada yaqin insoningiz bilan fikringiz to‘g‘ri kelmadi. Qarorga kelishda nimani afzal ko‘rasiz?",
        PersonalityDimension.TF,
        [
            "Har ikkala fikrni dalillar bilan solishtirishni.",
            "Qaysi qaror amalda yaxshiroq natija berishini aniqlashni.",
            "Ikkalamizning fikrimizni hisobga oladigan yechim topishni.",
            "Har ikkalamiz uchun muhim bo‘lgan qadriyatlarni tushunib olishni.",
        ],
    ),
    # J / P — rejalilik va moslashuvchanlik
    (
        "Ertaga bir nechta muhim ishingiz bor. Odatda qanday tayyorgarlik ko‘rasiz?",
        PersonalityDimension.JP,
        [
            "Ishlarning vaqtini va tartibini oldindan belgilayman.",
            "Eng muhim ishlarni ro‘yxatga yozaman.",
            "Asosiy vazifalarni belgilab, qolganini vaziyatga qarab qilaman.",
            "Ertangi vaziyatga qarab ishlarni tanlayman.",
        ],
    ),
    (
        "Dam olish kuniga oldindan reja tuzgansiz, lekin u kutilmaganda bekor bo‘ldi. Odatda nima qilasiz?",
        PersonalityDimension.JP,
        [
            "Darhol yangi reja tuzaman.",
            "Bo‘shagan vaqtni boshqa rejalashtirilgan ishga ajrataman.",
            "Vaziyatga qarab boshqa mashg‘ulot tanlayman.",
            "Bo‘sh vaqt paydo bo‘lganidan foydalanib, o‘sha payt nimani xohlasam, shuni qilaman.",
        ],
    ),
    (
        "O‘zingiz uchun qimmatbaho buyum sotib olmoqchisiz. Odatda qanday tanlaysiz?",
        PersonalityDimension.JP,
        [
            "Oldindan talablarimni aniqlab, ularga mosini tanlayman.",
            "Bir nechta variantni solishtirib, qaror qilaman.",
            "Yaxshi yangi variant chiqsa, tanlovimni o‘zgartiraman.",
            "Yangi imkoniyatlarni ko‘rib chiqishni davom ettiraman, tanlovni shoshirmayman.",
        ],
    ),
    (
        "Bir haftadan keyin muhim topshiriqni tugatishingiz kerak. Qanday ishlash sizga qulay?",
        PersonalityDimension.JP,
        [
            "Birinchi kundanoq aniq jadval tuzib ishlash.",
            "Vazifani qismlarga bo‘lib, bosqichma-bosqich bajarish.",
            "Asosiy yo‘nalishni belgilab, ish tartibini vaziyatga moslashtirish.",
            "Qaysi qismidan boshlash va qachon shug‘ullanishni jarayonda hal qilish.",
        ],
    ),
    (
        "Do‘stlaringiz bilan boshqa shaharga sayohat qilmoqchisiz. Qanday sayohat sizga ko‘proq yoqadi?",
        PersonalityDimension.JP,
        [
            "Qayerlarga borishimizni oldindan rejalashtirilgan sayohat.",
            "Asosiy joylar belgilangan, qolgan vaqt erkin bo‘lgan sayohat.",
            "Borganimizdan keyin qiziqarli joylarni tanlab boradigan sayohat.",
            "Oldindan aniq yo‘nalish belgilamasdan, yangi imkoniyatlarga qarab harakatlanadigan sayohat.",
        ],
    ),
    (
        "Bo‘sh vaqtingizda o‘zingiz yoqtirgan bir nechta mashg‘ulot bilan shug‘ullanmoqchisiz. Qanday harakat qilasiz?",
        PersonalityDimension.JP,
        [
            "Bittasini tanlab, tugatgach keyingisiga o‘taman.",
            "Avval muhimrog‘ini bajarib, keyin boshqasiga o‘taman.",
            "Qiziqishimga qarab mashg‘ulotlarni almashtirib turaman.",
            "Bir nechta mashg‘ulotni boshlab, qaysi biri ko‘proq qiziqtirsa, o‘shani davom ettiraman.",
        ],
    ),
]
