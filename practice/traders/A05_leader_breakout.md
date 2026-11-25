# A05 leader_breakout

Status: builder settings, 2026-11-25. Untested. Market: US stocks. Holding time: 3 days to 8 weeks.

## What it tries to do

It copies, in a cash-only form, what several contest-winning stock traders say they do: buy strong stocks breaking to new highs out of a quiet stretch, with a close stop, and trade less when the market is weak. The model judges the chart setup and the company story, which these traders call partly subjective.

## Why this might work

- MEASURED: some traders posted strong checked contest returns in several years, for example Kell, Luk and Minervini (`docs/research/17_verified_traders_and_their_methods.md`, [organizer rules](https://financial-competitions.com/rules)).
- STATED: their methods. Kell describes 2 to 12 week holds, 10 and 20 day averages, and cutting exposure when the market is below its 20-day average ([Kell interview](https://stockbsessed.substack.com/p/oliver-kell-interview-the-mind-and)). Minervini's published method describes a first stop no more than 7% to 8% below entry ([ChartMill on SEPA](https://www.chartmill.com/documentation/trading-and-investing/methodologies/523-SEPA-Explained-Mark-Minervinis-Specific-Entry-Point-Analysis-System)). Kullamägi says position value is usually 10% to 15% ([trader FAQ](https://qullamaggie.com/faq/)).
- STATED: buying all-time highs with a trailing stop beat the index in a test that kept dead stocks, with margin and undisclosed sizing ([Wilcox and Crittenden](https://enjoytheride.world/wp-content/uploads/2023/06/WilcoxCrittenden2005.pdf)).
- MEASURED, against: the fund built on the IBD 50 list returned 3.72% a year against 13.71% for the S&P 500, April 2015 to December 2025 ([SEC prospectus](https://www.sec.gov/Archives/edgar/data/0002104659/000121390026047001/ea0286847-05_497k.htm)).
- MEASURED, against: the winners used margin and some shorting. The contest does not check which rules made the returns (document 17). This card has neither.
- Honest summary: the returns are real, the link from method to return is not shown, and this is not their full method.

## What it looks at each time it wakes

- Its holdings and cash.
- Daily bars for the last year for the stocks that the plain feed shows within 5% of their 52-week high and with average daily dollar volume above $20 million.
- The total market fund's daily bars.
- Alpaca news and a web search for each candidate: "[company] earnings growth", latest report and guidance.

## How it decides to buy

1. Market check: the total market fund is above its 20-day and 50-day averages. If below the 20-day, at most 2 positions. If below the 50-day, no new buys.
2. The stock's price is above its 50-day and 200-day averages, and the 50-day is above the 200-day.
3. The last few weeks show a narrowing price range on lower volume, and today it breaks above that range on higher volume.
4. Latest report shows sales and earnings growth, checked in the company's release.
5. No report due in the next 5 trading days.
6. Share price above $10.

## How big

- 12% of its budget per position, at most 6 positions. In a weak market (box 1), at most 2 positions.

## How it gets out

- Stop price: the low of the breakout day, and never more than 7% below entry.
- Target price: none at entry. Once the price is 10% above entry, the model raises the stop to entry at its next wake; after that it may raise the stop to below the 20-day average, written as a price.
- Exit-by time: 8 weeks after entry, at 15:45 Eastern.

## What it never does

- Uses margin, shorts, or adds to a losing position.
- Buys a stock that is already more than 5% above the top of its range.
- Holds through an earnings report in the first trial.

## When it wakes

- 10:30 and 15:30 Eastern on market days. Most buys happen at 15:30, when the day's volume is mostly known.

## What would make us drop it

- The rules in `practice/traders/ROSTER.md`, "How we judge".
- The traders it copies say win rates near a quarter are normal (Luk, STATED, document 17). A low win rate alone is not a reason to drop it. Its gap to its comparator is.
