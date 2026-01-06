import pytest
from db_handler import parse_quantity, repair_json_string

def test_parse_quantity_logic():
    """בודק שפונקציית הפרסור יודעת להפריד בין מספר ליחידת מידה"""
    # בדיקת גרם
    assert parse_quantity("100g") == (100.0, "g")
    # בדיקת מיליגרם עם רווח
    assert parse_quantity("2.5 mg") == (2.5, "mg")
    # בדיקת מיקרוגרם
    assert parse_quantity("500mcg") == (500.0, "mcg")
    # בדיקת מקרה שבו ה-AI מחזיר רק מספר
    assert parse_quantity(50) == (50.0, "unknown")

def test_json_repair_logic():
    """בודק שפונקציית התיקון מצליחה לסדר JSON שבור שה-AI לעיתים מייצר"""
    # מקרה נפוץ: חסר גרשיים לפני הערך
    broken = '{ "iron": 2mg" }'
    fixed = repair_json_string(broken)
    assert '"iron": "2mg"' in fixed or '"iron":"2mg"' in fixed

def test_deficiency_calculation_logic():
    """
    כאן אפשר להוסיף בעתיד בדיקה ללוגיקת החוסרים.
    כרגע נוודא לפחות שהפונקציות הבסיסיות מחזירות ערכים הגיוניים.
    """
    val, unit = parse_quantity("0mg")
    assert val == 0