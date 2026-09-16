# -*- coding: utf-8 -*-
"""Медиаплан Click Out для сети ветклиник «Ветдоктор» (Екатеринбург). Генератор HTML."""

SRC = {
    "ozon":  {"name": "Ozon Performance", "cpm": 224.02, "ctr": 0.0064, "cls": "ozon"},
    "urban": {"name": "Яндекс Urban Ads", "cpm": 149.31, "ctr": 0.0056, "cls": "urban"},
    "wb":    {"name": "WB Media",         "cpm": 200.11, "ctr": 0.0096, "cls": "wb"},
}
GEO_K = 1.15          # надбавка за узкое гео (Екатеринбург + В. Пышма)
CR = {"cons": 0.015, "base": 0.03, "opt": 0.05}
K_ZAPIS, K_DOHOD, CHEK = 0.85, 0.60, 6000

MONTHS = [
    {"n": "Месяц 1", "tag": "Тест", "budgets": {"ozon": 240000, "urban": 180000, "wb": 180000}},
    {"n": "Месяц 2", "tag": "Оптимизация", "budgets": {"ozon": 400000, "urban": 200000, "wb": 300000}},
    {"n": "Месяц 3", "tag": "Масштаб", "budgets": {"ozon": 550000, "urban": 250000, "wb": 400000}},
]
WORK = 90000  # СРК, три источника

def calc(src_key, budget):
    s = SRC[src_key]
    cpm = s["cpm"] * GEO_K
    imps = budget / cpm * 1000
    clicks = imps * s["ctr"]
    cpc = cpm / 1000 / s["ctr"]
    return {"budget": budget, "cpm": cpm, "imps": imps, "clicks": clicks, "cpc": cpc}

def funnel(clicks, budget, cr, work=0):
    leads = clicks * cr
    zap = leads * K_ZAPIS
    doh = zap * K_DOHOD
    rev = doh * CHEK
    total = budget + work
    return {"leads": leads, "zap": zap, "doh": doh, "rev": rev,
            "cpl": total / leads if leads else 0,
            "cac": total / doh if doh else 0,
            "drr": total / rev * 100 if rev else 0}

def n(x, d=0):
    s = f"{x:,.{d}f}".replace(",", " ").replace(".", ",")
    return s

# ---------- расчёты по месяцам ----------
rows_plan, tot = [], {"budget": 0, "imps": 0, "clicks": 0}
for m in MONTHS:
    per, mt = {}, {"budget": 0, "imps": 0, "clicks": 0}
    for k in SRC:
        c = calc(k, m["budgets"][k]); per[k] = c
        for f in mt: mt[f] += c[f]
    mt["cpc"] = mt["budget"] / mt["clicks"]
    mt["cpm"] = mt["budget"] / mt["imps"] * 1000
    mt["ctr"] = mt["clicks"] / mt["imps"] * 100
    rows_plan.append({"m": m, "per": per, "tot": mt})
    for f in tot: tot[f] += mt[f]
tot["cpc"] = tot["budget"] / tot["clicks"]
tot["work"] = WORK * len(MONTHS)
tot["all"] = tot["budget"] + tot["work"]

# сценарии по итогу 3 месяцев
sc3 = {k: funnel(tot["clicks"], tot["budget"], v, tot["work"]) for k, v in CR.items()}
# сценарии по месяцу 1
m1 = rows_plan[0]["tot"]
sc1 = {k: funnel(m1["clicks"], m1["budget"], v, WORK) for k, v in CR.items()}

# варианты входа (месяц 1)
ENTRY = [
    {"key": "pilot", "name": "Пилот", "sub": "один источник, Ozon", "work": 50000,
     "b": {"ozon": 250000, "urban": 0, "wb": 0}},
    {"key": "base", "name": "Рекомендуем", "sub": "три источника", "work": 90000,
     "b": {"ozon": 240000, "urban": 180000, "wb": 180000}},
    {"key": "max", "name": "Потолок гео", "sub": "три источника, максимум", "work": 90000,
     "b": {"ozon": 550000, "urban": 250000, "wb": 400000}},
]
entry_rows = []
for e in ENTRY:
    cl = sum(calc(k, v)["clicks"] for k, v in e["b"].items() if v)
    im = sum(calc(k, v)["imps"] for k, v in e["b"].items() if v)
    bud = sum(e["b"].values())
    f = funnel(cl, bud, CR["base"], e["work"])
    entry_rows.append({"e": e, "bud": bud, "clicks": cl, "imps": im, "f": f})

# диагностический кластер: 35 % бюджета месяца 2 на КТ/МРТ-посадочные
DIAG_SHARE = 0.35
diag_clicks = rows_plan[1]["tot"]["clicks"] * DIAG_SHARE
diag_budget = rows_plan[1]["tot"]["budget"] * DIAG_SHARE
diag = {}
for label, cr, chek in (("Консервативно", 0.010, 9000), ("База", 0.020, 10350), ("Оптимистично", 0.035, 12000)):
    leads = diag_clicks * cr; zap = leads * K_ZAPIS; doh = zap * K_DOHOD
    diag[label] = {"cr": cr, "chek": chek, "leads": leads, "doh": doh, "rev": doh * chek,
                   "cac": diag_budget / doh, "drr": diag_budget / (doh * chek) * 100}

# сколько это от цели ×3 (нужно +10 000 сделок/мес)
GOAL = 10000
share_m3 = {k: funnel(rows_plan[2]["tot"]["clicks"], rows_plan[2]["tot"]["budget"], v, WORK)["doh"] / GOAL * 100
            for k, v in CR.items()}
m3f = {k: funnel(rows_plan[2]["tot"]["clicks"], rows_plan[2]["tot"]["budget"], v, WORK) for k, v in CR.items()}


# ---------- ёмкость гео ----------
AUD = {"ozon": 900_000, "urban": 1_200_000, "wb": 1_000_000}   # оценка активной аудитории площадки в гео
ZOO_SHARE = 0.25
FREQ = 3.5
cap_rows, cap_total = [], 0
for k, s in SRC.items():
    core = AUD[k] * ZOO_SHARE
    imps = core * FREQ
    bud = imps / 1000 * s["cpm"] * GEO_K
    cap_total += bud
    cap_rows.append({"k": k, "name": s["name"], "aud": AUD[k], "core": core, "imps": imps, "bud": bud})

# ---------- распределение по посадочным ----------
LANDINGS = [
    ("Диагностика: КТ и МРТ", "35 %", "9 000 – 12 000 ₽",
     "КТ 9 000 ₽ (11 700 ₽ с контрастом), МРТ 12 000 ₽. Первый КТ для животных в Свердловской области и первый собственный МРТ в России — аргумент, которого нет ни у кого в регионе. Гео расширяем на область: за такой диагностикой едут из Нижнего Тагила и Каменска-Уральского.",
     "/services/diagnostiks/kt-sobake-koshke/, /services/diagnostiks/mrt/"),
    ("Хирургия, травматология, онкология", "20 %", "высокий, по прайсу",
     "Отложенный спрос: владелец знает про уплотнение или хромоту, но откладывает. Баннер работает как напоминание, а не как перехват поиска. Неврология приземляется на МРТ — на сайте МРТ прямо описан как метод диагностики нервной системы.",
     "/services/khirurgiya/, /services/onkologiya/ + страницы под неврологию и травматологию — уточняем"),
    ("Плановые массовые услуги", "30 %", "1 700 – 6 000 ₽",
     "Кастрация и стерилизация, вакцинация, чипирование, стоматология, диспансеризация. Самый дешёвый лид и главный объём: покупка корма и наполнителя — прямой сигнал «есть питомец», а плановую услугу можно отложить на неделю, чем баннерный трафик и живёт.",
     "/services/vakcinaciya-i-privivki-zhivotnym/, /services/prays/kastraciya-sterilizaciya-kota/, /services/stomatologiya/"),
    ("Бренд: 5 клиник, две круглосуточные", "15 %", "—",
     "Охватный слой под замеры: узнаваемость сети, круглосуточность, 21 год и 224 124 пациента. Метрика — не CPL, а прирост поиска по имени и доля прямых заходов.",
     "vetdoctor.ru + /contact/"),
]

TARGETING = {
    "ozon": [
        "Покупают в категории <b>«Зоотовары»</b> — корма, лакомства, наполнители, с частотой покупки за 90 дней",
        "Покупают в <b>«Зоотовары → Ветаптека»</b>: витамины, препараты от паразитов — самый горячий сигнал для клиники",
        "Смотрят <b>«Груминг и уход»</b>: когтерезы, фурминаторы, шампуни",
        "Заказывали корм в <b>Ozon fresh</b> — регулярный покупатель",
        "Экран <b>«Заказ выполнен»</b> после покупки корма — самый конверсионный плейсмент площадки",
        "Свой сегмент по хэшу телефонов из базы клиники: возврат на вакцинацию и диспансеризацию",
        "Гео Екатеринбург и В. Пышма; для КТ и МРТ — вся Свердловская область",
    ],
    "urban": [
        "Маркет, категория <b>«Товары для животных»</b>: корма, наполнители, амуниция, ветпрепараты",
        "<b>Лавка</b>: заказывали корм и наполнитель — регулярная покупка в быстрой доставке",
        "<b>Яндекс Go</b>: гео по районам вокруг каждой из пяти клиник, тарифы Комфорт+ как прокси дохода",
        "Готовые сегменты медийки <b>«Домашние животные»</b>, «Семья и дети»",
        "Доход средний и выше — под КТ, МРТ и хирургию",
        "CRM-ретаргетинг по базе клиники и look-alike",
    ],
    "wb": [
        "Покупают в категории <b>«Зоотовары»</b>: корма, лакомства, амуниция, лежанки",
        "DMP: <b>клали в корзину</b> корм или ветдиету за последние 30 дней",
        "Интересуются <b>«Зоотовары → Аптечка»</b> — прямой сигнал для клиники",
        "<b>«Для собак → Одежда»</b> — владельцы мелких пород, самая внимательная к здоровью аудитория",
        "Женщины 25–44 — ядро площадки (78 %) и основной покупатель зоотоваров",
        "Гео: Екатеринбург и В. Пышма",
    ],
}

CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0c0c0d; --card:#161618; --card2:#1d1d21; --line:#2a2a2f; --line2:#38383f;
  --tx:#f5f3ec; --tx2:#a6a6ae; --tx3:#74747d; --ac:#FDD101; --acd:#8c7500; --red:#ec5b60;
  --ozon:#3b82f6; --urban:#ff4d3d; --wb:#cb6ce6;
}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--tx);font-family:Manrope,system-ui,sans-serif;
  font-size:15px;line-height:1.55;-webkit-font-smoothing:antialiased}
.wrap{max-width:1180px;margin:0 auto;padding:0 28px 120px}
h1,h2,h3,.big{font-family:Unbounded,Manrope,sans-serif;font-weight:700;letter-spacing:-.01em}
.mono,td.num,th{font-family:'JetBrains Mono',monospace}
a{color:var(--ac);text-decoration:none;border-bottom:1px solid rgba(253,209,1,.35)}
b,strong{font-weight:700;color:var(--tx)}

/* header */
header{padding:64px 0 40px;border-bottom:1px solid var(--line)}
.kicker{display:flex;align-items:center;gap:12px;margin-bottom:22px}
.bar{width:34px;height:7px;background:var(--ac);flex:none}
.kicker span{font-family:'JetBrains Mono',monospace;font-size:11px;text-transform:uppercase;
  letter-spacing:.12em;color:var(--tx2)}
h1{font-size:44px;line-height:1.12;margin-bottom:18px}
h1 em{font-style:normal;color:var(--ac)}
.lead{font-size:17px;color:var(--tx2);max-width:860px}
.lead b{color:var(--tx)}
.meta{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);
  border:1px solid var(--line);margin-top:34px}
.meta div{background:var(--card);padding:14px 16px}
.meta dt{font-family:'JetBrains Mono',monospace;font-size:10.5px;text-transform:uppercase;
  letter-spacing:.12em;color:var(--tx3);margin-bottom:6px}
.meta dd{font-size:14px;font-weight:600}

/* sections */
section{padding:52px 0;border-bottom:1px solid var(--line)}
h2{font-size:26px;line-height:1.2;margin:14px 0 8px}
h2 em{font-style:normal;color:var(--ac)}
.sub{color:var(--tx2);max-width:900px;margin-bottom:26px}
h3{font-size:15px;font-weight:600;font-family:Manrope,sans-serif;margin-bottom:8px}

/* grids & cards */
.g2{display:grid;grid-template-columns:1fr 1fr;gap:18px}
.g3{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}
.g4{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}
.card{background:var(--card);border:1px solid var(--line);padding:20px 22px}
.card.acc{border-left:3px solid var(--ac)}
.card.warn{border-left:3px solid var(--red)}
.card p{color:var(--tx2);font-size:14px}
.card p+p{margin-top:9px}
.tag{font-family:'JetBrains Mono',monospace;font-size:10px;text-transform:uppercase;
  letter-spacing:.12em;color:var(--tx3);display:block;margin-bottom:10px}
.tag.y{color:var(--ac)}
.stat .big{font-size:30px;color:var(--ac);line-height:1.1;display:block;margin-bottom:6px}
.stat .cap{font-size:13px;color:var(--tx2)}
ul{list-style:none}
li{position:relative;padding-left:18px;margin-bottom:7px;font-size:14px;color:var(--tx2)}
li:before{content:'';position:absolute;left:0;top:9px;width:6px;height:6px;background:var(--acd)}
li.y:before{background:var(--ac)}
li.r:before{background:var(--red)}

/* tables */
.tbl{width:100%;border-collapse:collapse;border:1px solid var(--line);font-size:13.5px}
.tbl th{background:var(--card2);color:var(--tx2);font-size:10px;font-weight:500;text-transform:uppercase;
  letter-spacing:.1em;text-align:left;padding:11px 12px;border-bottom:1px solid var(--line2);white-space:nowrap}
.tbl td{padding:11px 12px;border-bottom:1px solid var(--line);vertical-align:top;color:var(--tx2)}
.tbl tr:last-child td{border-bottom:none}
.tbl td.num,.tbl th.num{text-align:right;font-family:'JetBrains Mono',monospace;color:var(--tx);white-space:nowrap}
.tbl tr.tot td{background:var(--card2);color:var(--tx);font-weight:700}
.tbl tr.tot td.num{color:var(--ac)}
.tbl tr.head td{background:#111;font-family:'JetBrains Mono',monospace;font-size:10.5px;
  text-transform:uppercase;letter-spacing:.12em;color:var(--ac)}
.tbl td.name{color:var(--tx)}
.chip{display:inline-block;font-family:'JetBrains Mono',monospace;font-size:10px;padding:2px 7px;
  border:1px solid var(--line2);text-transform:uppercase;letter-spacing:.08em;color:var(--tx2)}
.chip.ozon{border-color:var(--ozon);color:var(--ozon)}
.chip.urban{border-color:var(--urban);color:var(--urban)}
.chip.wb{border-color:var(--wb);color:var(--wb)}
.chip.y{border-color:var(--ac);color:var(--ac)}
.scroll{overflow-x:auto}

/* misc */
.note{border-left:3px solid var(--line2);padding:12px 16px;background:var(--card);
  font-size:13.5px;color:var(--tx2);margin-top:16px}
.note b{color:var(--ac)}
.yband{background:var(--ac);color:#141200;padding:18px 22px;display:grid;
  grid-auto-flow:column;gap:26px;align-items:center;margin-top:24px}
.yband div{min-width:0}
.yband dt{font-family:'JetBrains Mono',monospace;font-size:10px;text-transform:uppercase;
  letter-spacing:.12em;opacity:.7;margin-bottom:4px}
.yband dd{font-family:Unbounded,sans-serif;font-weight:700;font-size:17px;line-height:1.2}
.yband dd small{font-family:Manrope,sans-serif;font-weight:600;font-size:12px;display:block;opacity:.75}
footer{padding:40px 0 0;color:var(--tx3);font-size:12.5px;font-family:'JetBrains Mono',monospace;
  display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap}
.toc{display:flex;flex-wrap:wrap;gap:8px;margin-top:28px}
.toc a{font-family:'JetBrains Mono',monospace;font-size:10.5px;text-transform:uppercase;letter-spacing:.1em;
  border:1px solid var(--line2);padding:5px 9px;color:var(--tx2);border-bottom:1px solid var(--line2)}
.toc a:hover{border-color:var(--ac);color:var(--ac)}
@media (max-width:900px){
  .g2,.g3,.g4{grid-template-columns:1fr}.meta{grid-template-columns:1fr 1fr}
  h1{font-size:30px}h2{font-size:21px}.wrap{padding:0 16px 60px}
  .yband{grid-auto-flow:row}
}
@media print{
  body{background:#fff;color:#000}
  .wrap{max-width:none;padding:0 10mm}
  section{border-color:#ddd;page-break-inside:avoid}
  .card,.tbl,.meta div{background:#fff;border-color:#ccc;color:#000}
  .tbl th{background:#f2f2f2;color:#000}.tbl td{color:#222}
  h1 em,h2 em,.stat .big,.tbl tr.tot td.num,.note b,.tag.y,.chip.y{color:#8c7500}
  b,strong,.tbl td.name,.lead b,.card p b,li b{color:#000}
  li,.card p,.sub,.lead,.stat .cap,.note{color:#333}
  .tag{color:#666}.yband{background:#FDD101;color:#141200}
  .yband dd,.yband dt{color:#141200}
  .toc{display:none}
  @page{size:A4;margin:12mm}
}
"""

H = []
A = H.append

A(f"""<!DOCTYPE html>
<html lang="ru"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Медиаплан Click Out · Ветдоктор · Cerebro</title>
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Unbounded:wght@500;700&family=Manrope:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>{CSS}</style></head><body><div class="wrap">

<header>
  <div class="kicker"><i class="bar"></i><span>Медиаплан · Cerebro Click Out · 16.09.2026</span></div>
  <h1>Ветдоктор: трафик с маркетплейсов<br>на страницы услуг <em>клиники</em></h1>
  <p class="lead">Три месяца, три источника — <b>Ozon Performance</b>, <b>Яндекс Urban Ads</b> и <b>WB Media</b>.
  Баннер внутри маркетплейса, переход на <b>vetdoctor.ru</b>, целевое действие — запись и доходимость на первичный приём.
  Расчёт собран на средних показателях клиентов Церебро на сопровождении и на цифрах вашей воронки, которые вы дали на встрече.
  Всё, что не подтверждено кабинетом, помечено как допущение и пересчитывается после первых двух недель теста.</p>
  <dl class="meta">
    <div><dt>Клиент</dt><dd>Сеть «Ветдоктор», 5 клиник</dd></div>
    <div><dt>Гео</dt><dd>Екатеринбург + В. Пышма</dd></div>
    <div><dt>Бюджет 3 мес.</dt><dd>{n(tot['budget'])} ₽ + работа {n(tot['work'])} ₽</dd></div>
    <div><dt>Горизонт</dt><dd>3 месяца, тест — 4 недели</dd></div>
  </dl>
  <nav class="toc">
    <a href="#s1">01 Что мы поняли</a><a href="#s2">02 Почему площадки</a><a href="#s3">03 Ёмкость гео</a>
    <a href="#s4">04 Таргетинги</a><a href="#s5">05 Посадочные</a><a href="#s6">06 Медиаплан</a>
    <a href="#s7">07 Воронка</a><a href="#s8">08 Варианты входа</a><a href="#s9">09 КТ и МРТ</a>
    <a href="#s10">10 Цель ×3</a><a href="#s11">11 Замеры</a><a href="#s12">12 Условия</a><a href="#s13">13 Допущения</a>
  </nav>
</header>

<section id="s1">
  <div class="kicker"><i class="bar"></i><span>01 · Вводная</span></div>
  <h2>Что мы поняли <em>до первого рубля</em></h2>
  <p class="sub">Левая колонка — то, что мы услышали на встрече. Правая — то, что проверили сами на vetdoctor.ru
  16.09.2026, чтобы считать на фактах, а не на пересказе.</p>
  <div class="g2">
    <div class="card acc"><span class="tag y">Что услышали на встрече</span>
      <ul>
        <li class="y">Более 500 направлений, <b>5 000+ сделок в месяц</b>, потенциал ×3</li>
        <li class="y">Платный трафик сейчас — Директ, <b>CAC 300–1 500 ₽</b>; ещё SEO и посевы в SMM</li>
        <li class="y">Конверсия страниц услуг <b>3–7 %</b>, из заявки в запись <b>85 %</b>, доходимость на первичку <b>60 %</b></li>
        <li class="y">Средний чек первички <b>6 000 ₽</b></li>
        <li class="y">Льют на отдельные страницы услуг: неврология, хирургия, травматология, онкология, МРТ и КТ</li>
        <li class="y">Готовы рассматривать предложения по всем каналам трафика</li>
      </ul>
    </div>
    <div class="card"><span class="tag">Проверили на сайте</span>
      <ul>
        <li>Сеть с 2004 года: <b>5 клиник</b> — четыре в Екатеринбурге (Профсоюзная 55 и Уральская 76 — круглосуточно, Куйбышева 109, Бебеля 17) и одна в Верхней Пышме</li>
        <li><b>87 сотрудников</b>, из них 49 ветеринарных специалистов; <b>485 услуг</b>; 224 124 пациента за 21 год</li>
        <li><b>Первый в Свердловской области КТ</b> для животных (с июня 2020): 9 000 ₽, с контрастом 11 700 ₽</li>
        <li><b>Первая в России ветклиника с собственным МРТ</b> — 12 000 ₽; на сайте МРТ описан прежде всего как диагностика нервной системы</li>
        <li>Первичный приём дежурного врача — 2 500 ₽, повторный — 1 700 ₽</li>
        <li>Онлайн-запись, личный кабинет, боты в Telegram и MAX, УЗИ Philips Affiniti 70</li>
      </ul>
    </div>
  </div>
  <div class="card warn" style="margin-top:18px"><span class="tag">Три вопроса, без ответов на которые цифры поедут</span>
    <ul>
      <li class="r"><b>Чек первички 6 000 ₽ против прайса 2 500 ₽.</b> Похоже, 6 000 — это приём с диагностикой и процедурами. Считаем по 6 000 ₽, как вы назвали на встрече, но фиксируем: это чек визита, а не строки прайса.</li>
      <li class="r"><b>Посадочных под неврологию и травматологию мы на сайте не нашли</b> (ожидаемые адреса /services/nevrologiya/ и /services/travmatologiya/ отдают 404). Либо они по другим адресам — пришлите список, либо неврологию ведём на страницу МРТ, травматологию — на КТ и хирургию.</li>
      <li class="r"><b>Конверсия 3–7 % снята на трафике из Директа</b> — это люди, которые уже ищут ветклинику. Трафик с баннера холоднее, поэтому в расчёте держим три сценария и нижнюю границу ставим в 1,5 %.</li>
    </ul>
  </div>
</section>

<section id="s2">
  <div class="kicker"><i class="bar"></i><span>02 · Механика</span></div>
  <h2>Почему для ветклиники это <em>вообще работает</em></h2>
  <p class="sub">Click Out — это реклама внутри Ozon, Яндекс Маркета с Лавкой и Go, Wildberries, которая уводит человека
  на сайт клиники. Не продвижение карточек. Ветуслуги в каталогах площадок не продаются, поэтому за эту аудиторию
  там с вами почти никто не конкурирует.</p>
  <div class="g3">
    <div class="card stat"><span class="big">85 %</span><span class="cap">семей держат кошку или собаку, средние траты на питомца — 4 482 ₽ в месяц</span></div>
    <div class="card stat"><span class="big">590 млрд ₽</span><span class="cap">рынок зоотоваров в 2025-м, +15,8 % за год; 93 % онлайн-транзакций категории дают маркетплейсы</span></div>
    <div class="card stat"><span class="big">30 %</span><span class="cap">владельцев узнают о новинках из рекламы на маркетплейсах и сайтах объявлений</span></div>
  </div>
  <p style="font-size:11.5px;color:#74747d;margin-top:10px;font-family:'JetBrains Mono',monospace">
  Источники: Зооинформ (2026), Nielsen (2026), First Data / kommersant.ru (2026), Ромир (2025), Авито (2026).
  Рынок ветуслуг: 59,9 млрд ₽ в 2025-м, +21 % за год, средний чек визита по стране — 2 480 ₽ (Росстат / vetandlife.ru, 2026).</p>
  <div class="g2" style="margin-top:18px">
    <div class="card acc"><span class="tag y">Главный аргумент</span>
      <p>В зоотоварах площадка видит не интерес, а <b>факт покупки корма в этом месяце</b>. Ни Директ, ни соцсети
      не знают наверняка, есть ли у человека животное, — а Ozon и WB знают, потому что корм и наполнитель покупают циклом
      в 3–5 недель.</p>
      <p>Для клиники это самый точный портрет «у него есть питомец» без единого опроса. Сегмент «Ветаптека» на Ozon
      и «Аптечка» на WB — уже следующий уровень: человек покупает препараты, то есть питомцем занимается.</p>
    </div>
    <div class="card"><span class="tag">Что канал добавляет к Директу и чем он не является</span>
      <ul>
        <li class="y"><b>Добавляет:</b> отложенный спрос — плановая операция, диспансеризация, вакцинация, стоматология. Человек не ищет клинику сегодня, но питомец у него есть</li>
        <li class="y"><b>Добавляет:</b> новых владельцев — щенок или котёнок появился месяц назад, в поиске он ещё не был</li>
        <li class="y"><b>Добавляет:</b> частоту касаний по имени сети, которая потом проявляется в брендовом поиске</li>
        <li class="r"><b>Не заменяет</b> Директ: экстренный ночной запрос «ветклиника круглосуточно» ловит поиск, а не баннер</li>
        <li class="r"><b>Не даёт</b> лид дешевле Директа на старте. Директ снимает готовый спрос, мы работаем шире и раньше</li>
      </ul>
    </div>
  </div>
  <div class="note"><b>Ориентир из зооиндустрии:</b> фонд «Дай лапу» через Click Out на Ozon собрал 11 488 донатов
  на 19,2 млн ₽ за полтора года, ROAS до 700 % (средний 430 % в 2025-м). Это пример того, что аудитория владельцев
  на площадке отзывчива, а не прогноз для клиники.</div>
</section>
""")

cap_html = "".join(
    f"""<tr><td class="name"><span class="chip {r['k']}">{r['name']}</span></td>
    <td class="num">{n(r['aud'])}</td><td class="num">{n(r['core'])}</td>
    <td class="num">{n(r['imps'])}</td><td class="num">{n(r['bud'])} ₽</td></tr>""" for r in cap_rows)

A(f"""
<section id="s3">
  <div class="kicker"><i class="bar"></i><span>03 · География и ёмкость</span></div>
  <h2>Сколько денег гео <em>вообще способно принять</em></h2>
  <p class="sub">Екатеринбург с Верхней Пышмой — около 1,6 млн жителей, примерно 1,1 % населения страны.
  Площадки отчитываются федеральными цифрами (Ozon 70+ млн пользователей в месяц, Urban Ads до 94 млн, WB 79 млн),
  и главный вопрос медиаплана для сети из пяти клиник — не «сколько охвата купим», а «где начинается перегрев частоты».
  Ниже — расчёт ёмкости зоо-ядра при комфортной частоте 3,5 показа на человека в месяц.</p>
  <div class="scroll"><table class="tbl">
    <tr><th>Источник</th><th class="num">Аудитория в гео, оценка</th><th class="num">Ядро «покупают зоотовары»</th>
    <th class="num">Показов при частоте 3,5</th><th class="num">Ёмкость бюджета в месяц</th></tr>
    {cap_html}
    <tr class="tot"><td>Итого по трём источникам</td><td class="num">≈ 3,1 млн</td><td class="num">≈ {n(sum(r['core'] for r in cap_rows))}</td>
    <td class="num">≈ {n(sum(r['imps'] for r in cap_rows))}</td><td class="num">≈ {n(cap_total)} ₽</td></tr>
  </table></div>
  <div class="g3" style="margin-top:18px">
    <div class="card acc"><span class="tag y">Отсюда бюджет месяца 1</span>
      <p>Зоо-ядро трёх источников держит примерно <b>{n(cap_total)} ₽ в месяц</b> без перегрева частоты. Поэтому тестовый
      месяц мы ставим в <b>600 000 ₽</b> — ровно по ёмкости точных сегментов, а не «сколько дадут».</p></div>
    <div class="card"><span class="tag">Отсюда потолок</span>
      <p>Выше 1,2–1,5 млн ₽ в месяц по трём источникам в этом гео растёт не охват, а частота. Поэтому месяц 3 — это
      потолок, а не ступень к пяти миллионам. Дальше масштабирование идёт только расширением гео на область.</p></div>
    <div class="card"><span class="tag">Цена роста</span>
      <p>Бюджет месяцев 2 и 3 сверх ёмкости ядра уходит на широкие сегменты — соцдем 25–55 с гео и look-alike.
      Там конверсия ниже, поэтому прогноз по этим месяцам мы держим ближе к нижней границе сценариев.</p></div>
  </div>
  <div class="note"><b>Что здесь допущение:</b> доли аудитории площадок в гео и доля покупателей зоотоваров внутри них —
  наша оценка от доли населения с поправкой на миллионник. Точные размеры сегментов даёт прогноз в рекламном кабинете
  при медиапланировании — снимем на этапе согласования и пересчитаем таблицу. <b>Расширение гео:</b> под КТ и МРТ
  таргет расширяем на всю Свердловскую область — за такой диагностикой в Екатеринбург едут из области, и других
  томографов для животных в регионе нет.</div>
</section>

<section id="s4">
  <div class="kicker"><i class="bar"></i><span>04 · Таргетинги</span></div>
  <h2>Ключевиков здесь нет — <em>есть покупки</em></h2>
  <p class="sub">Отвечаем на вопрос со встречи прямо: семантика для этих трёх источников не нужна. Click Out — не поиск.
  Таргетинг строится на покупательском поведении внутри площадки: что человек купил, что положил в корзину, что смотрел,
  где живёт. Единственное место, где что-то похожее на ключевые слова остаётся, — баннер в поиске Ozon, и там это
  категорийные запросы зоотоваров («корм для кошек», «наполнитель»), а не запросы про ветуслуги.
  Разделы сайта нам всё равно нужны — но как посадочные и как источник смыслов для макетов, не как семантика.</p>
  <div class="g3">
    <div class="card"><span class="tag"><span class="chip ozon">Ozon Performance</span></span><ul>{''.join(f'<li>{x}</li>' for x in TARGETING['ozon'])}</ul></div>
    <div class="card"><span class="tag"><span class="chip urban">Яндекс Urban Ads</span></span><ul>{''.join(f'<li>{x}</li>' for x in TARGETING['urban'])}</ul></div>
    <div class="card"><span class="tag"><span class="chip wb">WB Media</span></span><ul>{''.join(f'<li>{x}</li>' for x in TARGETING['wb'])}</ul></div>
  </div>
  <div class="note"><b>Форматы:</b> Ozon — баннеры на главной, в поиске, в карточке, видеобаннер и экран «Заказ выполнен»
  (самый конверсионный плейсмент площадки). Urban Ads — один кабинет на Маркет, Еду, Лавку, Go, Деливери и Доставку,
  18 категорий и 115 подкатегорий покупательской активности. WB Media — слайдер на главной и баннеры в категориях,
  DMP-сегменты по поиску, корзине и покупке.</div>
</section>

<section id="s5">
  <div class="kicker"><i class="bar"></i><span>05 · Посадочные</span></div>
  <h2>Куда именно <em>ведём трафик</em></h2>
  <p class="sub">Общая страница сети даёт дешёвый клик и дорогую заявку. Поэтому делим бюджет по кластерам услуг —
  под каждый свой сегмент, свой макет и своя метрика.</p>
  <div class="scroll"><table class="tbl">
    <tr><th>Кластер</th><th class="num">Доля бюджета</th><th class="num">Чек</th><th>Логика</th><th>Посадочные</th></tr>
    {''.join(f'<tr><td class="name"><b>{a}</b></td><td class="num">{b}</td><td class="num">{c}</td><td>{d}</td><td style="font-size:12px;color:#74747d">{e}</td></tr>' for a,b,c,d,e in LANDINGS)}
  </table></div>
  <div class="note"><b>Что проверяем на посадочных до старта:</b> онлайн-запись и телефон на первом экране,
  цена услуги без «уточняйте», адреса пяти клиник с режимом работы, скорость на мобильном (весь трафик площадок —
  мобильный), цели в Метрике на запись, звонок и отправку формы, пиксели трёх площадок и связка с МИС или CRM,
  чтобы считать не до заявки, а до дошедшего пациента.</div>
</section>
""")

plan_html = ""
for i, r in enumerate(rows_plan, 1):
    m, per, mt = r["m"], r["per"], r["tot"]
    plan_html += f'<tr class="head"><td colspan="10">{m["n"]} · {m["tag"]} · бюджет {n(mt["budget"])} ₽ + работа {n(WORK)} ₽</td></tr>'
    for k, s in SRC.items():
        c = per[k]
        f = funnel(c["clicks"], c["budget"], CR["base"])
        plan_html += f"""<tr><td class="name"><span class="chip {k}">{s['name']}</span></td>
        <td class="num">{n(c['budget'])}</td><td class="num">{n(c['cpm'])}</td><td class="num">{n(c['imps'])}</td>
        <td class="num">{n(s['ctr']*100,2)} %</td><td class="num">{n(c['clicks'])}</td><td class="num">{n(c['cpc'],1)}</td>
        <td class="num">{n(f['leads'])}</td><td class="num">{n(f['zap'])}</td><td class="num">{n(f['doh'])}</td></tr>"""
    mf = funnel(mt["clicks"], mt["budget"], CR["base"], WORK)
    plan_html += f"""<tr class="tot"><td>Итого {m['n'].lower()}</td><td class="num">{n(mt['budget'])}</td>
    <td class="num">{n(mt['cpm'])}</td><td class="num">{n(mt['imps'])}</td><td class="num">{n(mt['ctr'],2)} %</td>
    <td class="num">{n(mt['clicks'])}</td><td class="num">{n(mt['cpc'],1)}</td><td class="num">{n(mf['leads'])}</td>
    <td class="num">{n(mf['zap'])}</td><td class="num">{n(mf['doh'])}</td></tr>"""
tf = sc3["base"]
plan_html += f"""<tr class="tot"><td>Всего за 3 месяца</td><td class="num">{n(tot['budget'])}</td><td class="num">—</td>
<td class="num">{n(tot['imps'])}</td><td class="num">—</td><td class="num">{n(tot['clicks'])}</td>
<td class="num">{n(tot['cpc'],1)}</td><td class="num">{n(tf['leads'])}</td><td class="num">{n(tf['zap'])}</td>
<td class="num">{n(tf['doh'])}</td></tr>"""

def sc_table(d, budget, work, label):
    names = {"cons": ("Консервативный", "CR 1,5 %"), "base": ("Базовый", "CR 3,0 %"), "opt": ("Оптимистичный", "CR 5,0 %")}
    rows = ""
    for k in ("cons", "base", "opt"):
        f, (nm, cr) = d[k], names[k]
        cls = ' class="tot"' if k == "base" else ""
        rows += f"""<tr{cls}><td class="name"><b>{nm}</b><br><span style="font-size:11px;color:#74747d">{cr}</span></td>
        <td class="num">{n(f['leads'])}</td><td class="num">{n(f['zap'])}</td><td class="num">{n(f['doh'])}</td>
        <td class="num">{n(f['cpl'])} ₽</td><td class="num">{n(f['cac'])} ₽</td><td class="num">{n(f['rev'])} ₽</td>
        <td class="num">{n(f['drr'],1)} %</td></tr>"""
    return f"""<h3 style="margin-top:22px">{label} · бюджет {n(budget)} ₽ + работа {n(work)} ₽</h3>
    <div class="scroll"><table class="tbl" style="margin-top:8px">
    <tr><th>Сценарий</th><th class="num">Заявки</th><th class="num">Записи</th><th class="num">Дошли на первичку</th>
    <th class="num">CPL</th><th class="num">Цена дошедшего</th><th class="num">Выручка первички</th><th class="num">ДРР</th></tr>
    {rows}</table></div>"""

A(f"""
<section id="s6">
  <div class="kicker"><i class="bar"></i><span>06 · Медиаплан</span></div>
  <h2>Три месяца, три источника, <em>{n(tot['budget'])} ₽</em></h2>
  <p class="sub">CPM и CTR — средние показатели клиентов Церебро на сопровождении в Click Out, с надбавкой 15 %
  за узкое гео. Воронка в правых колонках посчитана по базовому сценарию: конверсия посадочной 3 %,
  из заявки в запись 85 %, доходимость 60 % — ваши цифры. Колонки «заявки — записи — приходы» —
  это модель на ваших конверсиях, а не обещание результата: до теста ни одна площадка не скажет,
  какая из них реализуется.</p>
  <div class="scroll"><table class="tbl">
    <tr><th>Источник</th><th class="num">Бюджет, ₽</th><th class="num">CPM, ₽</th><th class="num">Показы</th>
    <th class="num">CTR</th><th class="num">Клики</th><th class="num">CPC, ₽</th><th class="num">Заявки</th>
    <th class="num">Записи</th><th class="num">Приходы</th></tr>
    {plan_html}
  </table></div>
  <div class="g3" style="margin-top:18px">
    <div class="card"><span class="tag"><span class="chip ozon">Ozon · {n(sum(m["budgets"]["ozon"] for m in MONTHS))} ₽</span></span>
      <p>Максимальный объём и самое сильное покупательское намерение: 65 млн активных покупателей, 83 % вне Москвы
      и Питера, 73 % — доход средний и выше. Здесь же «Ветаптека» и экран «Заказ выполнен». Самый дорогой клик из трёх —
      и самый тёплый.</p></div>
    <div class="card"><span class="tag"><span class="chip urban">Urban Ads · {n(sum(m["budgets"]["urban"] for m in MONTHS))} ₽</span></span>
      <p>Самый дешёвый охват (CPM от 50 ₽ по прайсу площадки) и единственный источник с гео по районам через Go —
      под пять адресов сети это прямая механика: показываем клинику тем, кто живёт в 10 минутах от неё.</p></div>
    <div class="card"><span class="tag"><span class="chip wb">WB Media · {n(sum(m["budgets"]["wb"] for m in MONTHS))} ₽</span></span>
      <p>Самый дешёвый клик (CTR 0,96 % — лучший из трёх) и женская аудитория 25–44 (78 % площадки) — это ядро
      покупателей зоотоваров и тот, кто в семье принимает решение вести питомца к врачу. Растёт в плане быстрее
      остальных именно поэтому.</p></div>
  </div>
  <div class="note"><b>Как двигаем деньги внутри плана:</b> сплит месяцев 2 и 3 — расчётный. После двух недель теста
  перераспределяем в источник с лучшей ценой дошедшего пациента, а не с лучшим CTR. Если один из трёх не выходит
  на экономику за месяц — отключаем и переливаем бюджет, это записывается в условия как критерий «продолжаем /
  останавливаемся».</div>
</section>

<section id="s7">
  <div class="kicker"><i class="bar"></i><span>07 · Воронка</span></div>
  <h2>Что это даёт <em>в записях и деньгах</em></h2>
  <p class="sub">Воронка: клик → заявка (конверсия посадочной) → запись (85 %) → дошёл на первичку (60 %) → чек 6 000 ₽.
  Три сценария различаются только конверсией посадочной. Базовый — нижняя граница вашего диапазона (3 %);
  консервативный — половина от него, поправка на то, что баннерный трафик холоднее поискового; оптимистичный —
  5 %, внутри вашего же диапазона. Цена дошедшего и ДРР считаются с учётом стоимости работ агентства.</p>
  {sc_table(sc1, rows_plan[0]['tot']['budget'], WORK, 'Месяц 1 · тест')}
  {sc_table(sc3, tot['budget'], tot['work'], 'Итог трёх месяцев')}
  <div class="note"><b>Проверка на реальность:</b> в нашем проекте в медицине, ближайшем к вам по географии —
  стоматология с шестью филиалами в Тюмени и Екатеринбурге — лид в первую неделю стоил 2 079 ₽,
  а в лучшем сегменте 45–54 — 878 ₽. Базовый сценарий этого медиаплана даёт CPL 1 189 ₽, то есть попадает
  внутрь этого коридора. Оговорка честная: там другая услуга, другой чек и другой цикл решения — это ориентир
  порядка величины, а не перенос результата.</div>
  <dl class="yband">
    <div><dt>Базовый сценарий, 3 месяца</dt><dd>{n(sc3['base']['doh'])} первичных пациентов<small>{n(sc3['base']['leads'])} заявок · {n(sc3['base']['zap'])} записей</small></dd></div>
    <div><dt>Цена дошедшего</dt><dd>{n(sc3['base']['cac'])} ₽<small>включая работу агентства</small></dd></div>
    <div><dt>Выручка первички</dt><dd>{n(sc3['base']['rev'])} ₽<small>без учёта повторных визитов и диагностики</small></dd></div>
    <div><dt>ДРР</dt><dd>{n(sc3['base']['drr'],1)} %<small>к выручке первичного приёма</small></dd></div>
  </dl>
  <div class="g2" style="margin-top:18px">
    <div class="card warn"><span class="tag">Честно про сравнение с Директом</span>
      <p>Ваш нынешний CAC — 300–1 500 ₽. В базовом сценарии Click Out даёт дошедшего пациента за
      <b>{n(sc3['base']['cac'])} ₽</b>, в оптимистичном — за <b>{n(sc3['opt']['cac'])} ₽</b>, и только это попадает
      в ваш текущий коридор.</p>
      <p>Так и должно быть: Директ снимает готовый спрос, а мы покупаем аудиторию, которой в поиске сегодня нет.
      Обещать лид дешевле Директа мы не будем. Правильное сравнение — не «дешевле ли», а «сколько ещё пациентов
      можно взять сверх того, что уже выбрано в поиске, и по какой цене это остаётся рентабельным».</p></div>
    <div class="card acc"><span class="tag y">Где на самом деле окупаемость</span>
      <p>Выручка первичного приёма ({n(CHEK)} ₽) уже превышает цену дошедшего в базовом сценарии в <b>2,7 раза</b>.
      Но первичка — это вход: дальше повторный приём, диагностика, стационар, операция. У сети, где 485 услуг
      и 224 124 пациента за 21 год, экономика канала считается по LTV пациента, а не по одному визиту.</p>
      <p><b>Нужно от вас:</b> средняя выручка на пациента за первые 3, 6 и 12 месяцев из МИС. С этой цифрой мы
      пересчитаем таблицу и покажем реальную окупаемость — сейчас мы сознательно считаем по самому строгому варианту.</p></div>
  </div>
</section>
""")

entry_html = ""
for r in entry_rows:
    e = r["e"]
    src_chips = " ".join(f'<span class="chip {k}">{n(v)}</span>' for k, v in e["b"].items() if v)
    cls = ' class="tot"' if e["key"] == "base" else ""
    entry_html += f"""<tr{cls}><td class="name"><b>{e['name']}</b><br><span style="font-size:11px;color:#74747d">{e['sub']}</span></td>
    <td>{src_chips}</td><td class="num">{n(r['bud'])}</td><td class="num">{n(e['work'])}</td>
    <td class="num">{n(r['imps'])}</td><td class="num">{n(r['clicks'])}</td>
    <td class="num">{n(r['f']['leads'])}</td><td class="num">{n(r['f']['doh'])}</td>
    <td class="num">{n(r['f']['cac'])} ₽</td></tr>"""

diag_html = "".join(
    f"""<tr{' class="tot"' if k=='База' else ''}><td class="name"><b>{k}</b><br><span style="font-size:11px;color:#74747d">CR {n(v['cr']*100,1)} %</span></td>
    <td class="num">{n(v['chek'])} ₽</td><td class="num">{n(v['leads'])}</td><td class="num">{n(v['doh'])}</td>
    <td class="num">{n(v['cac'])} ₽</td><td class="num">{n(v['rev'])} ₽</td><td class="num">{n(v['drr'],1)} %</td></tr>"""
    for k, v in diag.items())

A(f"""
<section id="s8">
  <div class="kicker"><i class="bar"></i><span>08 · Варианты входа</span></div>
  <h2>Три варианта старта — <em>на выбор</em></h2>
  <p class="sub">Один и тот же расчёт, разный размер входа. Прогноз по базовому сценарию (конверсия посадочной 3 %),
  за один месяц. Минимальный бюджет — от 100 000 ₽ в месяц; рекомендуемый — от 200 000 ₽ на источник.</p>
  <div class="scroll"><table class="tbl">
    <tr><th>Вариант</th><th>Сплит по источникам, ₽</th><th class="num">Бюджет</th><th class="num">Работа</th>
    <th class="num">Показы</th><th class="num">Клики</th><th class="num">Заявки</th><th class="num">Приходы</th>
    <th class="num">Цена дошедшего</th></tr>
    {entry_html}
  </table></div>
  <div class="g3" style="margin-top:18px">
    <div class="card"><span class="tag">Пилот</span><p>Дешевле войти, но один источник даёт одну гипотезу и одну частоту.
    Мы на нём сможем сказать «работает / не работает на Ozon», но не сможем сравнить источники между собой.
    Подходит, если решение по бюджету нужно защищать поэтапно.</p></div>
    <div class="card acc"><span class="tag y">Рекомендуем</span><p>600 000 ₽ — ровно ёмкость точных зоо-сегментов
    трёх источников. За месяц получаем сравнимые данные по трём площадкам и четырём кластерам посадочных,
    дальше двигаем деньги в лидера. Это и есть месяц 1 основного плана.</p></div>
    <div class="card"><span class="tag">Потолок гео</span><p>1 200 000 ₽ — максимум, который Екатеринбург принимает
    без перегрева частоты. Имеет смысл, если входим сразу на сезон и готовы подключать широкие сегменты.
    Цена дошедшего почти не отличается от базового варианта — объём растёт, эффективность нет.</p></div>
  </div>
</section>

<section id="s9">
  <div class="kicker"><i class="bar"></i><span>09 · Диагностика</span></div>
  <h2>КТ и МРТ: <em>другая экономика</em> в том же бюджете</h2>
  <p class="sub">Это не дополнительные деньги, а другой взгляд на те же 35 % бюджета месяца 2 ({n(diag_budget)} ₽),
  которые в плане уходят на диагностический кластер. Конверсия здесь ниже — решение дороже и дольше, — зато чек
  в 1,5–2 раза выше первички: КТ 9 000 ₽ (11 700 ₽ с контрастом), МРТ 12 000 ₽.
  Расчёт <b>не суммируется</b> с основной таблицей, он её уточняет.</p>
  <div class="scroll"><table class="tbl">
    <tr><th>Сценарий</th><th class="num">Чек</th><th class="num">Заявки</th><th class="num">Дошли</th>
    <th class="num">Цена дошедшего</th><th class="num">Выручка</th><th class="num">ДРР</th></tr>
    {diag_html}
  </table></div>
  <div class="g2" style="margin-top:18px">
    <div class="card acc"><span class="tag y">Почему это сильнейший аргумент в гео</span>
      <p>Первый КТ для животных в Свердловской области и первый в России собственный ветеринарный МРТ —
      по вашим же данным на сайте, такого оборудования в регионе больше ни у кого нет. В баннере это звучит не как «ветклиника», а как «единственный
      томограф для животных на Урале», и работает на аудиторию всей области, а не только города.</p></div>
    <div class="card"><span class="tag">Связка с неврологией</span>
      <p>На вашем же сайте написано: МРТ у животных — это прежде всего диагностика головного и спинного мозга.
      Значит, неврологический запрос («задние лапы отказали», «судороги») приземляется на страницу МРТ, а не на
      общую страницу приёма. Под травматологию так же работает КТ. Это закрывает две из пяти названных на встрече
      услуг без создания новых страниц.</p></div>
  </div>
</section>

<section id="s10">
  <div class="kicker"><i class="bar"></i><span>10 · Честно</span></div>
  <h2>Что этот канал <em>закрывает от цели ×3</em></h2>
  <p class="sub">Задача звучала как «5 000 сделок в месяц, можем в три раза больше» — то есть плюс около 10 000 сделок
  в месяц. Считаем, сколько из них реально забирает Click Out в месяце 3, на потолке гео.</p>
  <div class="g3">
    <div class="card stat"><span class="big">{n(m3f['cons']['doh'])}</span><span class="cap">пациентов в месяц, консервативно — это <b>{n(share_m3['cons'],1)} %</b> от цели</span></div>
    <div class="card stat"><span class="big">{n(m3f['base']['doh'])}</span><span class="cap">пациентов в месяц, базово — <b>{n(share_m3['base'],1)} %</b> от цели</span></div>
    <div class="card stat"><span class="big">{n(m3f['opt']['doh'])}</span><span class="cap">пациентов в месяц, оптимистично — <b>{n(share_m3['opt'],1)} %</b> от цели</span></div>
  </div>
  <div class="card warn" style="margin-top:18px"><span class="tag">Говорим прямо</span>
    <ul>
      <li class="r">Три источника Click Out в Екатеринбурге дают <b>3–10 % от цели ×3</b>. Никакой один канал эту задачу
      не решает — она решается миксом и пропускной способностью самих клиник.</li>
      <li class="r"><b>Умножить на три — это про мощности, а не только про трафик.</b> 10 000 дополнительных визитов
      в месяц на 49 специалистов и пять адресов — это вопрос расписания, а не медиаплана. Готовы обсуждать реальную
      верхнюю планку записи в неделю и строить план от неё.</li>
      <li class="y">Если цель ×3 стоит всерьёз — под неё нужен разговор про весь микс: Авито (ветклиники там сильная
      ниша — в нашем кейсе 1 570 лидов по 690 ₽), ВК Реклама с гео до филиала, Директ поверх текущего.
      Click Out — верхняя и средняя часть воронки в этом миксе.</li>
    </ul>
  </div>
</section>
""")

A(f"""
<section id="s11">
  <div class="kicker"><i class="bar"></i><span>11 · Замеры</span></div>
  <h2>Как отличим наших пациентов <em>от тех, кто пришёл бы и так</em></h2>
  <p class="sub">У сети с 21-летней историей и сильным SEO часть обращений придёт независимо от рекламы.
  Поэтому до старта ставим четыре замера — это то, чем мы отличаемся от «просто открутили бюджет».</p>
  <div class="scroll"><table class="tbl">
    <tr><th style="width:150px">Замер</th><th>Что меряем</th><th style="width:230px">Как у вас</th></tr>
    <tr><td class="name"><b>Search lift</b></td>
      <td>Прирост поиска по имени. Снимаем частотность в Вордстате до старта, во время флайта и месяц после;
      отдельно ведём контрольный запрос категории, чтобы отделить ваш рост от роста рынка.</td>
      <td>Бренд «ветдоктор екатеринбург» против контрольного «ветклиника екатеринбург». Порог по показам:
      до 100 тыс. показов эффекта нет, 1–3 млн — устойчивый рост; в месяце 1 у нас {n(rows_plan[0]['tot']['imps'])} показов.</td></tr>
    <tr><td class="name"><b>Brand lift</b></td>
      <td>Прирост знания и намерения: опрос двух групп до и после. Бесплатное исследование Яндекса — от бюджета
      около 1 млн ₽ и охвата от 2 млн; упрощённая схема опросов — от ~12 тыс. ₽.</td>
      <td>Вопрос «какие ветклиники Екатеринбурга вы знаете?» в городе флайта против контрольного.
      Для сети с пятью адресами это часто первая в жизни цифра узнаваемости.</td></tr>
    <tr><td class="name"><b>Sales lift</b></td>
      <td>Прирост в деньгах. Гео-эксперимент: районы с рекламой против сопоставимых без неё, по выгрузке из вашей
      системы. Нужна история по гео за 6–12 месяцев.</td>
      <td>Первичные приёмы по районам из МИС: Пионерский и ВИЗ с рекламой против сопоставимых районов без неё.
      Меряет не мнения, а кассу клиник.</td></tr>
    <tr><td class="name"><b>Post-view</b></td>
      <td>Эффект показов без клика: увидел баннер, не кликнул, через две недели записался сам. В обычной аналитике
      это «прямой заход». Ozon атрибутирует 30 дней после контакта, Яндекс — окно до 90 дней через пиксель Метрики.</td>
      <td>Критично для вашей ниши: между «заметил уплотнение» и «записался» проходят недели. Показываем этот слой
      отдельно — недельные ряды непереходного трафика на календаре флайта.</td></tr>
  </table></div>
  <div class="note">Внешние бенчмарки по lift-замерам (Polaris, «Кагоцел», исследование Easy Commerce по 20 брендам
  на Ozon) — чужие цифры, мы приводим их как рамку ожиданий, а не как обещание. Границы честные: замеры мы обещаем
  и делаем, влияние на стоимость заявки — меряем и показываем, но не гарантируем.</div>
</section>

<section id="s12">
  <div class="kicker"><i class="bar"></i><span>12 · Условия</span></div>
  <h2>Деньги, сроки <em>и что нужно от вас</em></h2>
  <div class="g3">
    <div class="card acc"><span class="tag y">Стоимость работ</span>
      <ul>
        <li class="y">Сопровождение трёх источников — <b>90 000 ₽ в месяц</b> (один источник — 50 000 ₽, два — 80 000 ₽)</li>
        <li class="y">Рекламный бюджет — на площадки, кабинеты открытые и принадлежат вам</li>
        <li class="y">Минимальный бюджет — от 100 000 ₽ в месяц, рекомендуем от 200 000 ₽ на источник</li>
        <li class="y">Работаем с ИП и юрлицами, документы через ЭДО</li>
        <li>Альтернатива: вы ведёте кабинеты сами и получаете кэшбек от квартального оборота (Ozon до 18 %,
        Urban до 13 %, WB до 16 %). С сопровождением кэшбек не совмещается</li>
      </ul></div>
    <div class="card"><span class="tag">Сроки</span>
      <ul>
        <li>Согласование и доступы — 3–5 рабочих дней</li>
        <li>Макеты и премодерация площадок — 5–7 рабочих дней</li>
        <li>Тестовый флайт — 4 недели (полноценные выводы по трём источникам — 6–8 недель)</li>
        <li>Первые данные по CTR и CPC — через 3–5 дней после старта, по цене дошедшего — через 3–4 недели</li>
        <li>Критерии «продолжаем / останавливаемся» фиксируем письменно в КП до старта</li>
      </ul></div>
    <div class="card"><span class="tag">Нужно от вас</span>
      <ul>
        <li>Доступ к Метрике и постановка целей на запись, звонок и форму</li>
        <li>Коллтрекинг или отдельные номера — иначе звонки с баннера не увидим</li>
        <li>Выгрузка по первичным приёмам из МИС по районам за 6–12 месяцев — под sales lift</li>
        <li>Средняя выручка на пациента за 3, 6 и 12 месяцев — под честный расчёт окупаемости</li>
        <li>Лицензии и реквизиты для модерации: ветуслуги — регулируемая категория, макеты проходят проверку площадки,
        формулировки и предупреждения согласуем до запуска</li>
        <li>Список посадочных по неврологии и травматологии — или решение вести их на МРТ и КТ</li>
      </ul></div>
  </div>
  <dl class="yband">
    <div><dt>Месяц 1</dt><dd>600 000 ₽ + 90 000 ₽<small>тест трёх источников</small></dd></div>
    <div><dt>Месяц 2</dt><dd>900 000 ₽ + 90 000 ₽<small>перераспределение в лидера</small></dd></div>
    <div><dt>Месяц 3</dt><dd>1 200 000 ₽ + 90 000 ₽<small>потолок гео</small></dd></div>
    <div><dt>Итого 3 месяца</dt><dd>{n(tot['all'])} ₽<small>бюджет {n(tot['budget'])} ₽ + работа {n(tot['work'])} ₽</small></dd></div>
  </dl>
</section>

<section id="s13">
  <div class="kicker"><i class="bar"></i><span>13 · Допущения</span></div>
  <h2>Всё, что <em>мы допустили</em></h2>
  <p class="sub">Собрали в одном месте, чтобы это не всплыло на защите бюджета. Первые четыре пункта пересчитываются
  после двух недель теста, дальше медиаплан живёт на ваших данных, а не на средних.</p>
  <div class="g2">
    <div class="card"><span class="tag">Что взято из наших данных</span>
      <ul>
        <li>CPM и CTR — средние по клиентам Церебро на сопровождении: Ozon 224,02 ₽ / 0,64 %, Urban 149,31 ₽ / 0,56 %,
        WB 200,11 ₽ / 0,96 %. Это все ниши сразу, не только медицина</li>
        <li>Надбавка <b>+15 % к CPM</b> за узкое гео — наша оценка, точная цена аукциона в Екатеринбурге видна
        только после запуска</li>
        <li>Размеры аудиторий в гео и доля покупателей зоотоваров (25 %) — оценка от доли населения;
        уточняется прогнозом в кабинете</li>
        <li>Комфортная частота 3,5 показа на человека в месяц — рабочая норма, а не норматив площадки</li>
      </ul></div>
    <div class="card"><span class="tag">Что взято у вас и что мы изменили</span>
      <ul>
        <li>85 % из заявки в запись, 60 % доходимость, чек первички 6 000 ₽ — ваши цифры, взяты как есть</li>
        <li>Конверсия посадочной: ваш диапазон 3–7 % мы <b>сдвинули вниз</b> — базовым взяли 3 %, консервативным 1,5 %.
        Ваши 3–7 % сняты на поисковом трафике, баннерный холоднее</li>
        <li>Сплит бюджета между источниками в месяцах 2 и 3 — расчётный, меняется по факту теста</li>
        <li>Распределение по кластерам посадочных (35/20/30/15) — наша рекомендация, а не ваш факт</li>
        <li>Стоимость сопровождения 90 000 ₽ — за три источника; при расходе свыше 200 000 ₽
        на источник действует шкала сопровождения, итоговую формулу фиксируем в договоре</li>
      </ul></div>
  </div>
  <div class="card warn" style="margin-top:18px"><span class="tag">Чего мы не обещаем</span>
    <p>Не гарантируем количество и стоимость заявок, не обещаем, что реклама снизит текущий CAC, не обещаем результат
    без теста. Обещаем прозрачный бюджет, открытые кабинеты на вашем юрлице, проверку гипотез, четыре замера эффекта
    и честное решение по итогам теста — включая «останавливаемся», если экономика не сходится.</p>
  </div>
</section>

<footer>
  <span>Церебро Таргет · направление Click Out · сертифицированный партнёр Ozon Performance, Яндекс Urban Ads и WB Media</span>
  <span>support@cerebrotarget.ru · t.me/cerebro_manager · медиаплан для сети «Ветдоктор», 16.09.2026</span>
</footer>
</div></body></html>""")

import os
open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html"), "w", encoding="utf-8").write("".join(H))
print("index.html:", len("".join(H)), "байт")
