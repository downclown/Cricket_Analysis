import pandas as pd
import numpy as np

# This class does all the batting analysis for the ODI dataset.
# It reads the csv file once, cleans it, and after that every method below
# answers one simple question (who scored the most, how many sixes, and so on).
class ODIAnalysis:
  def __init__(self, path):
    # read the whole csv file into a pandas dataframe
    # try/except: if the path is wrong or the file is empty we print a clear message first,
    # then raise the error again so the GUI can show it in its error window too
    try:
        self.df = pd.read_csv(path)
    except FileNotFoundError:
        print("File not found, check the path :", path)
        raise
    except pd.errors.EmptyDataError:
        print("The csv file is empty :", path)
        raise

    # an empty dictionary, it gets filled when we ask for the top five scorers
    self.top_scorers = {}

    # clean the data straight away so every method below can trust it
    self._preprocessing()

  # Cleans the raw data. The csv has the batting rows first and the bowling rows
  # at the end, so here we keep only the batting part and fix the data types.
  def _preprocessing(self):
    # the last 86194 rows are bowling records, so we cut them off
    self.df = self.df.iloc[:-86194, :].reset_index(drop=True)

    # the csv writes '-' where a value is missing, we turn that into a real empty value (NaN)
    self.df = self.df.replace('-', np.nan)

    # these columns are numbers, but pandas read them as text because of the '-' signs
    numeric_cols = [
        'Innings Runs Scored Num',
        'Innings Boundary Sixes',
        'Innings Boundary Fours',
        'Innings Balls Faced',
        'Innings Batting Strike Rate',
        'Innings Not Out Flag'
    ]

    # turn every one of them into numbers, anything that still can't be converted becomes NaN
    # try/except: if the csv is the wrong file, one of these columns will be missing (KeyError),
    # so we print which one and raise a clearer error instead of a confusing one
    try:
        for col in numeric_cols:
            self.df[col] = pd.to_numeric(self.df[col], errors='coerce')
    except KeyError as e:
        print("Column missing in the csv :", e)
        raise ValueError("Column missing in the csv : " + str(e))

    # take the year out of the date (for example 1/14/2018 gives 2018)
    # we need it later to compare how batting changed from year to year
    self.df['Year'] = pd.to_datetime(self.df['Innings Date'], format='%m/%d/%Y', errors='coerce').dt.year

  # Finds the single highest score in the whole dataset and prints who scored it.
  def top_scorer(self):
    # idxmax gives the row number of the biggest value
    self.index = self.df['Innings Runs Scored Num'].idxmax()
    print("Top Scorer : ")
    print('-'*20)
    print("Player:", self.df.loc[self.index, 'Innings Player'])
    print("Runs:", self.df.loc[self.index, 'Innings Runs Scored Num'])

  # Same idea as above but the other way round, it finds the lowest score (usually a duck, 0 runs).
  def lowest_scorer(self):
    self.index = self.df['Innings Runs Scored Num'].idxmin()
    print("Lowest Scorer : ")
    print('-'*20)
    print("Player:", self.df.loc[self.index, 'Innings Player'])
    print("Runs:", self.df.loc[self.index, 'Innings Runs Scored Num'])


  # Finds the five biggest single innings scores and stores them in a dictionary
  # as {player: runs}. Note that this is about one innings, not a whole career.
  # If a player appears twice in the top five, the dictionary keeps only one of them.
  def top_five_scorers_dict(self):
    # sort all innings from highest to lowest and keep the first five
    top_df = self.df.sort_values(by='Innings Runs Scored Num', ascending=False).head(5)
    self.top_scorers = {}
    print("Top 5 Scorers : ")
    print('-'*20)
    # go through the five rows one by one and put them in the dictionary
    for index, row in top_df.iterrows():
        player = row['Innings Player']
        runs = row['Innings Runs Scored Num']
        self.top_scorers[player] = runs
    return self.top_scorers

  # The average strike rate (runs per 100 balls) over every innings in the dataset.
  def avg_strike_rate(self):
   return self.df['Innings Batting Strike Rate'].mean()

  # Adds up the sixes hit in all the innings.
  def total_six(self):
    return self.df['Innings Boundary Sixes'].sum()

  # Adds up the fours hit in all the innings.
  def total_fours(self):
    return self.df['Innings Boundary Fours'].sum()


  # Works out the batting average of every player, in one table.
  # Batting average = total runs / number of times the player got out.
  # Only players with at least 20 innings are kept, so someone who played
  # 2 matches and scored 150 doesn't end up at the top by luck.
  def batting_average_table(self, min_innings=20):
    # only innings where the player really batted (DNB rows have no runs)
    batted_df = self.df[self.df['Innings Runs Scored Num'].notna()]

    # group the rows player by player and add up runs, innings and not outs
    # (each pair like ('Innings Runs Scored Num', 'sum') is a tuple: column name, what to do with it)
    table = batted_df.groupby('Innings Player').agg(
        runs=('Innings Runs Scored Num', 'sum'),
        innings=('Innings Runs Scored Num', 'count'),
        not_outs=('Innings Not Out Flag', 'sum')
    )

    # a player is out in every innings except the not out ones
    table['outs'] = table['innings'] - table['not_outs']

    # players who were never out have no average (we can't divide by 0), so keep outs > 0
    table = table[(table['innings'] >= min_innings) & (table['outs'] > 0)]
    table['average'] = table['runs'] / table['outs']
    return table

  # Takes the table above and returns the five best averages as a dictionary {player: average}.
  def top_five_batting_average_dict(self):
    table = self.batting_average_table()
    top = table['average'].sort_values(ascending=False).head(5)
    return top.round(2).to_dict()


  # Counts how many innings fall into each score range: 0-9, 10-49, 50-99 and 100+.
  # This is where tuples are used. Every range is one tuple of three fixed values:
  # (lowest score, highest score, name of the range). A tuple fits here because
  # the three values belong together and should never change while the code runs.
  def innings_by_score_range(self):
    score_ranges = [
        (0, 9, '0-9'),
        (10, 49, '10-49'),
        (50, 99, '50-99'),
        (100, 1000, '100+')
    ]

    # only innings where the player really batted
    runs = self.df['Innings Runs Scored Num'].dropna()

    counts = {}
    # unpack each tuple into three variables, then count the innings inside that range
    for low, high, name in score_ranges:
        counts[name] = ((runs >= low) & (runs <= high)).sum()
    return pd.Series(counts)

  # Finds which score range happens most often. It returns a tuple (range name, number of innings),
  # so the caller can unpack it like:  name, count = odi.most_common_score_range()
  def most_common_score_range(self):
    counts = self.innings_by_score_range()
    return (counts.idxmax(), int(counts.max()))


  # ---- the methods below only prepare data for the charts in the GUI ----

  # Top 10 players by total career runs (all their innings added together).
  def top_career_runs(self):
    career = self.df.groupby('Innings Player')['Innings Runs Scored Num'].sum()
    return career.sort_values(ascending=False).head(10)

  # Top 10 batting averages, again with at least 20 innings.
  def top_batting_averages(self):
    table = self.batting_average_table()
    return table['average'].sort_values(ascending=False).head(10).round(2)

  # The average number of runs scored per innings in every year, to see how batting changed over time.
  def runs_per_year(self):
    return self.df.groupby('Year')['Innings Runs Scored Num'].mean().round(2)

  # Total runs scored by each country, biggest first.
  def runs_by_country(self):
    return self.df.groupby('Country')['Innings Runs Scored Num'].sum().sort_values(ascending=False)


  # Gives a small summary for one player: innings, runs, sixes, fours, strike rate and batting average.
  # If the name isn't in the data it just returns the text "Player not found".
  def player_summary(self, name):
    # keep only the rows of this player
    player_df = self.df[self.df['Innings Player'] == name]

    if player_df.empty:
        return "Player not found"

    total_runs = player_df['Innings Runs Scored Num'].sum()
    total_sixes = player_df['Innings Boundary Sixes'].sum()
    total_fours = player_df['Innings Boundary Fours'].sum()
    total_balls = player_df['Innings Balls Faced'].sum()

    # innings = rows where he batted, outs = innings minus the not outs
    innings = player_df['Innings Runs Scored Num'].count()
    outs = innings - player_df['Innings Not Out Flag'].sum()

    # strike rate = runs per 100 balls, average = runs per dismissal
    # (the "if" part stops us from dividing by zero)
    strike_rate = (total_runs / total_balls) * 100 if total_balls > 0 else 0
    average = total_runs / outs if outs > 0 else 0

    summary = {
        'Player': name,
        'Innings': int(innings),
        'Total Runs': int(total_runs),
        'Total Sixes': int(total_sixes),
        'Total Fours': int(total_fours),
        'Strike Rate': round(strike_rate, 2),
        'Batting Average': round(average, 2)
    }

    return summary
