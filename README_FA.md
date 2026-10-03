# شبیه‌ساز اتوماتا و آزمایشگاه زبان‌ها و ماشین‌ها

پروژه دسکتاپ درس نظریه زبان‌ها و ماشین‌ها در مقطع کارشناسی مهندسی کامپیوتر، ساخته‌شده با Python و PySide6.

سازنده: Mohammadreza Kazemi — ساخته شده توسط محمدرضا کاظمی

## امکانات نهایی

### اتوماتا و Designer
- طراحی گرافیکی DFA، NFA و ε-NFA
- حالت‌های DFA و NFA در Designer
- ساخت State با دوبارکلیک یا دکمه
- جابه‌جایی Stateها با ماوس
- تعیین Start و Final
- رسم Transition با نمادهای دلخواه مانند 0، 1، a، b و ε
- چند مقصد برای یک Symbol در NFA
- جلوگیری از Transition غیرقطعی در DFA
- حذف State و حذف Transition مشخص
- ورود ماشین از متن
- تشخیص خودکار DFA/NFA
- جدول Transition

### Simulator
- Run، Step، Previous و Reset
- تنظیم مدت هر مرحله از 1 تا 60 ثانیه
- نمایش State فعلی و مسیر واقعی
- نمایش هم‌زمان Stateهای ممکن در NFA
- محاسبه صحیح ε-Closure در شروع و بین مراحل
- ردیابی دقیق Transition با source، symbol و target
- انیمیشن یال‌های رفت و برگشت و یال‌های موازی

### NFA → DFA
- Subset Construction واقعی
- پشتیبانی از ε-Closure
- نگهداری State تهی ∅ در صورت نیاز
- نمایش ماشین ورودی و DFA خروجی در دو گراف
- جابه‌جایی Stateهای هر دو گراف
- Auto-layout
- گزارش Stateها و Transitionهای DFA

### Grammar Lab
- CFG و Validation
- Classification
- FIRST و FOLLOW
- String Parsing و Parse Tree
- Leftmost Derivation
- حذف Left Recursion
- Left Factoring
- LL(1) Table و Conflict Detection

### رابط کاربری
- فارسی / انگلیسی
- Dark UI دانشگاهی
- Designer، Simulator، Transition Table، NFA → DFA و Grammar Lab

## قالب ورود ماشین

~~~text
states=q0,q1,q2; alphabet=a,b; start=q0; finals=q2; transitions=q0,a,q0|q0,a,q1|q0,b,q0|q1,b,q2|q2,a,q2|q2,b,q2
~~~

## اجرای پروژه در Windows

Python 3.11 را انتخاب کنید:

~~~powershell
py -3.11 -m pip install -r requirements.txt
py -3.11 main.py
~~~

تست‌ها:

~~~powershell
py -3.11 -m unittest discover -s tests -v
~~~

## ساختار پروژه
- main.py — رابط گرافیکی و کنترل تعاملات
- automata.py — مدل و الگوریتم‌های DFA/NFA/ε-NFA
- grammar.py — الگوریتم‌های CFG و LL(1)
- tests/test_automata.py — تست‌های اتوماتا
- tests/test_grammar.py — تست‌های گرامر
- .github/workflows/tests.yml — Syntax Check و Unit Tests
- REPORT_FA.md — گزارش کامل پروژه

## اصلاحات مهم نسخه جدید
1. Transitionهای دارای Symbol متفاوت دیگر روی یک یال ادغام نمی‌شوند.
2. یال‌های رفت و برگشت و یال‌های موازی به صورت جداگانه رسم می‌شوند.
3. NFA به عنوان یک مسیر قطعی نمایش داده نمی‌شود و مجموعه Stateهای ممکن حفظ می‌شود.
4. ε-Closure در شروع و در هر مرحله Simulation اعمال می‌شود.
5. Transitionهای دقیق استفاده‌شده در هر مرحله ذخیره می‌شوند.
6. پذیرش رشته تهی در ε-NFA بر اساس ε-Closure محاسبه می‌شود.
7. حذف Transition مستقل به Designer اضافه شده است.
8. تست‌های branching NFA و ε-NFA → DFA به مجموعه تست‌ها اضافه شده‌اند.

ساخته شده توسط محمدرضا کاظمی