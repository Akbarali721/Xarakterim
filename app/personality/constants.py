"""MBTI test sizing — bank vs per-session draw."""

# V1 — bazadagi muzlatilgan savollar. Ularning variant qiymati "A"; qatorlar o'zgartirilmaydi.
QUESTION_BANK_V1 = "A"
# V2 — TZ-3B da kelishilgan savollar. Yangi sessiya shu to'plamga biriktiriladi.
QUESTION_BANK_V2 = "V2"

SESSION_QUESTION_COUNT = 24
QUESTIONS_PER_DIMENSION = 6
DIRECTION_BALANCE_PER_DIMENSION = 3
# Master bank (variant A production default): 12 per dimension, 6+6 pole directions.
BANK_QUESTIONS_PER_DIMENSION = 12
BANK_POLE_COUNT_PER_DIRECTION = 6
MAX_CONSECUTIVE_SAME_DIMENSION = 2
# Weighted scores: low confidence when dimension totals are this close.
DIMENSION_LOW_CONFIDENCE_MAX_GAP = 2
MASTER_BANK_QUESTION_COUNT = BANK_QUESTIONS_PER_DIMENSION * 4
