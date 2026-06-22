# Chapter 1.2 — National Electricity Market (NEM) Grid Analysis
# 第 1.2 章 — 澳洲國家電力市場（NEM）電網分析

**Prepared for:** HDRE Taiwan research report
**Data source:** OpenElectricity API (openelectricity.org.au)
**Generated:** 2026-06-22

> **Data-coverage caveat / 資料涵蓋範圍說明:** This analysis uses the OpenElectricity
> **COMMUNITY** plan, which exposes only the **last ~730 days** of history. Figures 2 and 4
> were specified as 2020–2025 but in practice cover **2024-06 → 2026-06**. All numbers below are
> computed directly from the fetched data — none are estimated or back-filled.
> 本分析使用 OpenElectricity **社群版**，僅能取得**近約 730 天**的歷史資料。圖 2 與圖 4 原訂涵蓋
> 2020–2025 年，實際僅涵蓋 **2024-06 至 2026-06**。以下所有數字均直接由實際下載資料計算，並無估算或回填。

---

## Section 1 — Real-time Generation Mix (Fig 1)
## 第一節 — 即時發電組合（圖 1）

**EN.** Figure 1 shows the NEM generation mix over the past 7 days at 30-minute resolution
(resampled from the API's 5-minute power data; battery charging and pumped-hydro load are
excluded so the stack represents generation only). Over this window, **coal supplied ~53.3%**
of generation, confirming it remains the backbone of the grid. Variable renewables were already
material: **wind ~18.5%** and **solar ~12.1%**, together rivalling coal during midday peaks,
while **hydro (8.2%)** and **gas (6.3%)** provided dispatchable balancing. Battery output
(~1.3%) is small in energy terms but increasingly visible in evening-peak shifting.
**Implication for HDRE:** the intraday pattern — solar collapsing the midday net load and
firming technologies (gas, hydro, battery) ramping at sunset — is exactly the "duck curve"
dynamic that makes storage and flexible capacity commercially attractive in the NEM.

**繁中.** 圖 1 呈現過去 7 天、以 30 分鐘為間隔的 NEM 發電組合（由 API 的 5 分鐘功率資料重新取樣；
已排除電池充電與抽蓄負載，故堆疊圖僅代表發電量）。此期間**燃煤約佔 53.3%**，仍是電網主力。
變動性再生能源已具規模：**風電約 18.5%**、**太陽能約 12.1%**，在中午尖峰時段合計可與燃煤抗衡；
**水力（8.2%）** 與 **天然氣（6.3%）** 提供可調度的平衡電力。電池出力（約 1.3%）在電量上仍小，
但在傍晚尖峰移轉上日益明顯。**對 HDRE 的意涵：** 中午太陽能壓低淨負載、日落時可調度技術
（天然氣、水力、電池）爬升，正是使儲能與彈性容量在 NEM 具商業吸引力的「鴨子曲線」動態。

---

## Section 2 — Monthly Generation by Fuel Type (Fig 2)
## 第二節 — 各燃料類型每月發電量（圖 2）

**EN.** Figure 2 stacks monthly energy (MWh) by fuel group across the available window
(**2024-06 to 2026-06**). Across this period coal averaged **~52.3%** of generation, but the
renewable block is large and growing: **solar ~21.5%** (utility + rooftop combined in the API's
`solar` group) and **wind ~15.6%**, with **hydro 6.1%** and **gas 4.4%** rounding out the mix.
The seasonal signal is clear — solar peaks each summer (Dec–Feb) and recedes in winter, while
coal's share rises in the cooler months. **Implication for HDRE:** even on a 2-year window the
structural transition is visible; coal's share is being eroded from above by zero-marginal-cost
solar and wind. A full 2020–2025 series (requires a higher API tier) would strengthen the
trend-line, and we recommend sourcing it before final publication.

**繁中.** 圖 2 以堆疊面積呈現可取得期間（**2024-06 至 2026-06**）各燃料群組的每月電量（MWh）。
此期間燃煤平均約佔 **52.3%**，但再生能源區塊龐大且持續成長：**太陽能約 21.5%**
（API 的 `solar` 群組已合併大型與屋頂太陽能）、**風電約 15.6%**，再加上 **水力 6.1%** 與
**天然氣 4.4%**。季節訊號明顯——太陽能於每年夏季（12–2 月）達高峰、冬季回落，而燃煤佔比
則在較冷月份上升。**對 HDRE 的意涵：** 即使僅 2 年資料，結構性轉型已清晰可見；零邊際成本的
太陽能與風電正由上方侵蝕燃煤佔比。完整 2020–2025 序列（需更高階 API 方案）將強化趨勢線，
建議於正式發表前補齊。

---

## Section 3 — Generation Mix by State (Fig 3)
## 第三節 — 各州發電組合比較（圖 3）

**EN.** Figure 3 compares the latest-12-month generation mix across the five NEM regions. The
states diverge sharply. **QLD (59.2% coal)** and **NSW (57.6% coal)** remain coal-dominated, with
VIC close behind (**53.9% coal**, brown coal). At the other extreme, **TAS is 74.4% hydro** (plus
20% wind) and effectively coal-free, while **SA runs on 52.5% wind and 28.9% solar with zero
coal**, balanced by gas (18.6%). **Implication for HDRE:** South Australia is a live case study of
a near-fully-renewable synchronous grid and the firming (gas, interconnection, batteries) it
requires — directly relevant to Taiwan's own islanded-grid planning. QLD and NSW, still heavily
coal-weighted, represent the largest decarbonisation (and investment) headroom in the NEM.

**繁中.** 圖 3 比較五個 NEM 區域最近 12 個月的發電組合，各州差異顯著。**昆士蘭（燃煤 59.2%）** 與
**新南威爾斯（燃煤 57.6%）** 仍以燃煤為主，維多利亞緊隨其後（**燃煤 53.9%**，褐煤）。另一端，
**塔斯馬尼亞 74.4% 為水力**（加上 20% 風電），幾乎無燃煤；**南澳則為 52.5% 風電與 28.9% 太陽能、
零燃煤**，並以天然氣（18.6%）平衡。**對 HDRE 的意涵：** 南澳是「近乎全再生能源同步電網」及其所需
firming（天然氣、聯網、電池）的活案例，與台灣孤島電網規劃高度相關。仍高度仰賴燃煤的昆士蘭與
新南威爾斯，則代表 NEM 中最大的減碳（與投資）空間。

---

## Section 4 — Renewable Energy Share by State (Fig 4)
## 第四節 — 各州再生能源佔比（圖 4）

**EN.** Figure 4 tracks each state's monthly renewable share (renewable energy ÷ total energy)
over the available window. The ranking is stable but every state is trending up. **TAS** sits at
the top, rising from ~81.7% to **99.2%** (hydro + wind). **SA** is the standout mainland mover at
~70–74%. The coal states are climbing from a lower base: **VIC ~37→40%**, **NSW ~22→32%**, and
**QLD ~19→32%** — QLD showing the steepest recent gains as utility solar and wind scale.
**Implication for HDRE:** the spread (TAS ~99% vs QLD ~32%) shows there is no single "Australian"
renewable trajectory; partnership and procurement strategy must be region-specific. QLD's rapid
climb signals where new renewable + storage capacity is being absorbed fastest.

**繁中.** 圖 4 追蹤各州在可取得期間的每月再生能源佔比（再生能源電量 ÷ 總電量）。排名穩定但各州皆呈
上升趨勢。**塔斯馬尼亞**居首，由約 81.7% 升至 **99.2%**（水力＋風電）。**南澳**為本島最亮眼者，達
約 70–74%。燃煤州則由較低基期攀升：**維多利亞約 37→40%**、**新南威爾斯約 22→32%**、
**昆士蘭約 19→32%**——隨大型太陽能與風電擴張，昆士蘭近期增幅最陡。**對 HDRE 的意涵：** 差距之大
（塔斯約 99% vs 昆士蘭約 32%）顯示澳洲並無單一的再生能源軌跡，合作與採購策略必須因地制宜。
昆士蘭的快速攀升，標示出新增再生能源與儲能容量被吸收最快的市場。

---

## Section 5 — Coal Unit Operating & Retirement Timeline (Fig 5)
## 第五節 — 燃煤機組運轉與除役時間軸（圖 5）

**EN.** Figure 5 is a Gantt timeline of every NEM coal unit, from commissioning to closure,
colored by status. Of 87 units in the dataset, **43 are already retired** and **44 remain
operating, totalling ~21.1 GW**. Crucially, the operating fleet's *expected* closure dates
cluster in the next two decades (2028–2050), and **~12.9 GW is scheduled to retire by 2035**.
This is the defining supply-side event of the NEM transition: more than half the current coal
capacity exits within ~10 years. **Implication for HDRE:** these retirements open a large,
date-certain capacity gap that must be filled by renewables + firming. The timeline is, in
effect, a pipeline map of where and when replacement generation and storage will be needed —
prime territory for project development and offtake positioning. (Note: end dates for operating
units are *expected* closures and are subject to AEMO/operator revision.)

**繁中.** 圖 5 為所有 NEM 燃煤機組的甘特時間軸，自商轉至除役，並以狀態著色。資料中 87 部機組裡，
**43 部已除役**，**44 部仍運轉，合計約 21.1 GW**。關鍵在於，運轉機組的*預期*除役日期集中於未來
二十年（2028–2050），且 **約 12.9 GW 預定於 2035 年前除役**。這是 NEM 轉型中供給面最具決定性的
事件：現有燃煤容量逾半將於約 10 年內退場。**對 HDRE 的意涵：** 這些除役將開出規模龐大、時程明確的
容量缺口，須由再生能源＋firming 填補。此時間軸實為「何時、何地需要替代電力與儲能」的管線地圖，
正是專案開發與購售電佈局的絕佳領域。（註：運轉機組之結束日期為*預期*除役日，可能經 AEMO／營運商
修訂。）

---

*All figures are interactive HTML in `outputs/figures/`. Source: OpenElectricity API
(openelectricity.org.au). 所有圖表為 `outputs/figures/` 中的互動式 HTML。*
