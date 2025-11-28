from persiantools import digits
from persiantools.jdatetime import JalaliDateTime, JalaliDate
import datetime

def to_persian_number(text):
    """Convert English numbers to Persian numbers"""
    return digits.en_to_fa(str(text))

def to_english_number(text):
    """Convert Persian numbers to English numbers"""
    return digits.fa_to_en(str(text))

def gregorian_to_jalali(gregorian_date):
    """Convert Gregorian date to Jalali date"""
    if isinstance(gregorian_date, datetime.datetime):
        # Convert datetime to JalaliDateTime
        j_date = JalaliDate(gregorian_date.date())
        return JalaliDateTime(j_date.year, j_date.month, j_date.day,
                            gregorian_date.hour, gregorian_date.minute, gregorian_date.second)
    elif isinstance(gregorian_date, datetime.date):
        # Convert date to JalaliDate
        return JalaliDate(gregorian_date)
    else:
        return None

def jalali_to_gregorian(jalali_date):
    """Convert Jalali date to Gregorian date"""
    # JalaliDate and JalaliDateTime both have to_gregorian() method
    return jalali_date.to_gregorian() if jalali_date else None

def format_jalali_datetime(datetime_str):
    """Format datetime string to Jalali datetime"""
    dt = datetime.datetime.fromisoformat(datetime_str)
    return JalaliDateTime(dt)

def get_persian_month_name(month_number):
    """Get Persian month name from number"""
    months = ["فروردین", "اردیبهشت", "خرداد", "تیر", "مرداد", "شهریور",
              "مهر", "آبان", "آذر", "دی", "بهمن", "اسفند"]
    return months[month_number - 1] if 1 <= month_number <= 12 else ""

def get_persian_weekday_name(weekday_number):
    """Get Persian weekday name from number"""
    weekdays = ["شنبه", "یکشنبه", "دوشنبه", "سه‌شنبه", "چهارشنبه", "پنج‌شنبه", "جمعه"]
    return weekdays[weekday_number] if 0 <= weekday_number <= 6 else ""

def validate_jalali_date(year, month, day):
    """Validate if a Jalali date is valid"""
    try:
        JalaliDate(year, month, day)
        return True
    except:
        return False