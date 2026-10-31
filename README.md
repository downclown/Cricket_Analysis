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
