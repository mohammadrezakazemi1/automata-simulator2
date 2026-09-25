# شبیه‌ساز ماشین متناهی

پروژه درس نظریه زبان‌ها و ماشین‌ها در مقطع کارشناسی مهندسی کامپیوتر.

## امکانات پیاده‌سازی‌شده

- طراحی گرافیکی ماشین
- افزودن و حذف حالت‌ها
- تعیین حالت شروع و حالت‌های پذیرش
- افزودن و حذف انتقال‌ها
- اجرای DFA به صورت کامل، مرحله‌به‌مرحله و بازنشانی
- شبیه‌سازی NFA
- جدول انتقال
- تشخیص خودکار DFA یا NFA
- تبدیل واقعی NFA به DFA با روش Subset Construction
- پشتیبانی از انتقال ε
- نمایش گرافیکی حالت فعال و مسیر اجرا
- رابط فارسی / انگلیسی
- رابط دسکتاپ تیره و دانشگاهی
- تست‌های خودکار برای هسته ماشین

## اجرا در ویندوز

چون PySide6 روی Python 3.11 نصب شده، از همان مفسر استفاده کن:

```powershell
& "C:\Users\mohammadreza\AppData\Local\Programs\Python\Python311\python.exe" -m pip install -r requirements.txt
& "C:\Users\mohammadreza\AppData\Local\Programs\Python\Python311\python.exe" main.py
```

یا در VS Code، Python 3.11 را به عنوان Interpreter انتخاب کن و سپس:

```powershell
python main.py
```

اجرای تست‌ها:

```powershell
python -m unittest discover -s tests -v
```

## ساختار پروژه

- `main.py` — رابط گرافیکی PySide6
- `automata.py` — منطق DFA/NFA و تبدیل Subset Construction
- `tests/test_automata.py` — تست‌های خودکار
- `README.md` — مستندات انگلیسی

**ساخته شده توسط محمدرضا کاظمی**


## وزن یال‌ها

هر انتقال یک وزن عددی غیرمنفی دارد. هنگام رسم یال ابتدا Symbol و سپس Weight را وارد کنید. وزن روی خود یال نمایش داده می‌شود؛ برای مثال `0 [5]`.
