# ODI Cricket Analytics GUI (Batting + Bowling)

## Project layout
```
ODI_Cricket_GUI/
  gui.py                 # Tkinter application (run this)
  odi_analysis.py        # ODIAnalysis  - batting class (your original code + new methods)
  odi_bowling.py         # ODIBowlingAnalysis - bowling class (same style as the batting one)
  requirements.txt
  notebooks/
    Python_Course_Project_original.ipynb   # your original batting notebook (untouched)
    ODI_Batting_Analysis.ipynb             # batting class with the new methods
    ODI_Bowling_Analysis.ipynb             # bowling class with the new methods
```

## Run locally (Windows / VS Code)
1. Install Python 3.10+ (Tkinter comes with the standard Windows installer).
2. Open this folder in VS Code.
3. In terminal: `pip install -r requirements.txt`
4. Run: `python gui.py`
5. Click **Open CSV** and choose your original `ODI.csv` file (the full file, 171,968 rows). Batting and bowling are both loaded from this one file.

Use the **Batting** / **Bowling** buttons in the top bar to switch between the two sections.

## Features (each section has four tabs)
| Tab | Batting | Bowling |
|---|---|---|
| Dashboard | innings count, average strike rate, total sixes/fours, highest and lowest innings, top five scoring innings, top five batting averages | innings count, total wickets, average economy rate, total maidens, 4- and 5-wicket hauls, best bowling, most expensive spell, top five bowling innings, top five career wicket takers, top five best economy rates |
| Player Explorer | innings, runs, sixes, fours, strike rate, batting average | innings, wickets, runs conceded, maidens, economy rate, bowling average |
| Charts | top 10 career run scorers, top 10 batting averages, average runs per innings by year, total runs by country, innings by score range | top 10 career wicket takers, top 10 best economy rates, average economy rate by year, total wickets by country, innings by wickets taken |
| Dataset Browser | filter by player name, browse records, export to CSV | same |

Charts can be saved as PNG images with the **Save Image** button.

## Where tuples, lists and dictionaries are used
- **Tuples:** `innings_by_score_range()` (batting) and `innings_by_wicket_range()` (bowling) store every range as a tuple, for example `(50, 99, '50-99')`, and unpack it in a loop with `for low, high, name in ranges`. `most_common_score_range()` and `most_common_wicket_range()` return a tuple `(range name, number of innings)`.
- **Dictionaries:** the top-five results, the player summaries and the counts per range.
- **Lists:** column names to convert, sort orders and the list of ranges.

## Where try/except is used
Both `odi_analysis.py` and `odi_bowling.py` have two try/except blocks:
- `__init__` : reading the csv. A wrong path (`FileNotFoundError`) or an empty file (`EmptyDataError`) prints a clear message and raises the error again, so the GUI shows it in its error window.
- `_preprocessing` : converting the number columns. If the csv is the wrong file, a missing column (`KeyError`) prints the column name and raises a clearer `ValueError`.

## How the data is split
The CSV holds batting rows first and bowling rows after them (the last 86,194 rows).
- `ODIAnalysis` keeps everything except the last 86,194 rows (batting).
- `ODIBowlingAnalysis` keeps the last 86,194 rows, drops the rows where the player did not bowl, and converts overs such as `8.5` (8 overs 5 balls) into balls so economy rate is exact.
- Batting average = total runs divided by the number of times out (innings minus not outs). Only players with at least 20 innings are ranked.
- Best economy = total runs conceded per over across a career. Only bowlers with at least 100 overs are ranked, so a bowler with a couple of overs cannot top the list.
- The `4 Wickets` column in the CSV is not reliable, so 4- and 5-wicket hauls are counted from the wickets taken column.

## Notes for project report
Covers: GUI, 5+ operations, CSV load/export, input validation (empty name, player not found, wrong or missing columns), analysis, classes/functions, and graceful error messages. The source dataset is never modified. The top-five-innings functions use a dictionary, so if one player appears twice in the top five, the entries collapse into one (the original batting behaviour, kept for bowling too).

Tkinter needs a desktop environment, so run it locally; it will not display in hosted Colab.
