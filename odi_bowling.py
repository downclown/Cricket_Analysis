import pandas as pd
import numpy as np

# This class does all the bowling analysis for the ODI dataset.
# It works like the batting class: read the csv once, clean it, and then
# every method answers one simple question (best bowling, economy, wickets and so on).
class ODIBowlingAnalysis:
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

    # an empty dictionary, it gets filled when we ask for the top five bowling performances
    self.top_wicket_takers = {}

    # clean the data straight away so every method below can trust it
    self._preprocessing()

  # Cleans the raw data. The bowling records are at the end of the csv,
  # so here we keep only those rows, remove the players who didn't bowl and fix the data types.
  def _preprocessing(self):
    # keep only the bowling records (last 86194 rows)
    self.df = self.df.iloc[-86194:, :].reset_index(drop=True)

    # the csv writes '-' where a value is missing, we turn that into a real empty value (NaN)
    self.df = self.df.replace('-', np.nan)

    # these columns are numbers, but pandas read them as text because of the '-' signs
    numeric_cols = [
        'Innings Overs Bowled',
        'Innings Maidens Bowled',
        'Innings Runs Conceded',
        'Innings Wickets Taken',
        'Innings Economy Rate'
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

    # drop rows where the player did not bowl (DNB) / has no bowling data
    # (a player who didn't bowl has no wickets value, so that is how we spot them)
    self.df = self.df[self.df['Innings Wickets Taken'].notna()].reset_index(drop=True)

    # overs are written like 8.5, which means 8 overs and 5 balls (not 8.5 overs!)
    # so we convert everything into balls, it makes the maths for economy rate correct
    overs = self.df['Innings Overs Bowled'].astype(int)
    extra_balls = ((self.df['Innings Overs Bowled'] - overs) * 10).round()
    self.df['Balls Bowled'] = overs * 6 + extra_balls

    # take the year out of the date (for example 1/14/2018 gives 2018)
    # we need it later to compare how bowling changed from year to year
    self.df['Year'] = pd.to_datetime(self.df['Innings Date'], format='%m/%d/%Y', errors='coerce').dt.year

  # Finds the best single bowling performance and prints it.
  # "Best" means the most wickets, and if two bowlers have the same wickets,
  # the one who gave away fewer runs wins.
  def best_bowling(self):
    top_df = self.df.sort_values(by=['Innings Wickets Taken', 'Innings Runs Conceded'], ascending=[False, True])
    self.index = top_df.index[0]
    print("Best Bowling : ")
    print('-'*20)
    print("Player:", self.df.loc[self.index, 'Innings Player'])
    print("Wickets:", self.df.loc[self.index, 'Innings Wickets Taken'])
    print("Runs Conceded:", self.df.loc[self.index, 'Innings Runs Conceded'])

  # The opposite of the best bowling, it prints the most expensive spell (the most runs given away).
  def most_expensive_bowling(self):
    self.index = self.df['Innings Runs Conceded'].idxmax()
    print("Most Expensive Bowling : ")
    print('-'*20)
    print("Player:", self.df.loc[self.index, 'Innings Player'])
    print("Runs Conceded:", self.df.loc[self.index, 'Innings Runs Conceded'])


  # Finds the five best single bowling performances (most wickets in one innings)
  # and stores them in a dictionary as {player: wickets}.
  # If a player appears twice in the top five, the dictionary keeps only one of them.
  def top_five_wicket_takers_dict(self):
    # sort by wickets (high to low), and by runs conceded (low to high) when wickets are equal
    top_df = self.df.sort_values(by=['Innings Wickets Taken', 'Innings Runs Conceded'], ascending=[False, True]).head(5)
    self.top_wicket_takers = {}
    print("Top 5 Wicket Takers : ")
    print('-'*20)
    # go through the five rows one by one and put them in the dictionary
    for index, row in top_df.iterrows():
        player = row['Innings Player']
        wickets = row['Innings Wickets Taken']
        self.top_wicket_takers[player] = wickets
    return self.top_wicket_takers

  # The five players with the most wickets over their whole career (all innings added together).
  # This is different from the method above, which looks at one innings only.
  def top_five_career_wickets_dict(self):
    career = self.df.groupby('Innings Player')['Innings Wickets Taken'].sum()
    career = career.sort_values(ascending=False).head(5)
    return career.to_dict()

  # The average economy rate (runs given per over) over every innings in the dataset.
  def avg_economy_rate(self):
    return self.df['Innings Economy Rate'].mean()

  # Adds up all the wickets taken.
  def total_wickets(self):
    return self.df['Innings Wickets Taken'].sum()

  # Adds up all the maiden overs (overs where no run was scored).
  def total_maidens(self):
    return self.df['Innings Maidens Bowled'].sum()

  # Counts the innings where a bowler took exactly 4 wickets.
  def total_four_wickets(self):
    return (self.df['Innings Wickets Taken'] == 4).sum()

  # Counts the innings where a bowler took 5 or more wickets (a "five-for").
  def total_five_wickets(self):
    return (self.df['Innings Wickets Taken'] >= 5).sum()


  # Works out the career economy rate of every bowler, in one table.
  # Economy rate = runs given / overs bowled. We use balls * 6 so the maths is exact.
  # Only bowlers with at least 100 overs are kept, otherwise someone who bowled
  # 2 overs for 3 runs would look like the best bowler ever.
  def economy_table(self, min_overs=100):
    # group the rows bowler by bowler and add up runs and balls
    # (each pair like ('Innings Runs Conceded', 'sum') is a tuple: column name, what to do with it)
    table = self.df.groupby('Innings Player').agg(
        runs=('Innings Runs Conceded', 'sum'),
        balls=('Balls Bowled', 'sum')
    )

    # only bowlers with enough overs, so a bowler with 2 overs cannot top the list
    table = table[table['balls'] >= min_overs * 6]
    table['economy'] = table['runs'] / table['balls'] * 6
    return table

  # Takes the table above and returns the five best (lowest) economy rates as a dictionary {player: economy}.
  def top_five_best_economy_dict(self):
    table = self.economy_table()
    best = table['economy'].sort_values().head(5)
    return best.round(2).to_dict()


  # Counts how many innings fall into each wicket range: 0, 1-2, 3-4 and 5+ wickets.
  # This is where tuples are used. Every range is one tuple of three fixed values:
  # (fewest wickets, most wickets, name of the range). A tuple fits here because
  # the three values belong together and should never change while the code runs.
  def innings_by_wicket_range(self):
    wicket_ranges = [
        (0, 0, '0 wickets'),
        (1, 2, '1-2 wickets'),
        (3, 4, '3-4 wickets'),
        (5, 10, '5+ wickets')
    ]

    wickets = self.df['Innings Wickets Taken']

    counts = {}
    # unpack each tuple into three variables, then count the innings inside that range
    for low, high, name in wicket_ranges:
        counts[name] = ((wickets >= low) & (wickets <= high)).sum()
    return pd.Series(counts)

  # Finds which wicket range happens most often. It returns a tuple (range name, number of innings),
  # so the caller can unpack it like:  name, count = odi.most_common_wicket_range()
  def most_common_wicket_range(self):
    counts = self.innings_by_wicket_range()
    return (counts.idxmax(), int(counts.max()))


  # ---- the methods below only prepare data for the charts in the GUI ----

  # Top 10 players by total career wickets.
  def top_career_wickets(self):
    career = self.df.groupby('Innings Player')['Innings Wickets Taken'].sum()
    return career.sort_values(ascending=False).head(10)

  # Top 10 best (lowest) career economy rates, again with at least 100 overs.
  def best_economy_rates(self):
    table = self.economy_table()
    return table['economy'].sort_values().head(10).round(2)

  # The average economy rate in every year, to see how bowling changed over time.
  def economy_per_year(self):
    return self.df.groupby('Year')['Innings Economy Rate'].mean().round(2)

  # Total wickets taken by each country, biggest first.
  def wickets_by_country(self):
    return self.df.groupby('Country')['Innings Wickets Taken'].sum().sort_values(ascending=False)


  # Gives a small summary for one bowler: innings, wickets, runs, maidens, economy and bowling average.
  # If the name isn't in the data it just returns the text "Player not found".
  def player_summary(self, name):
    # keep only the rows of this player
    player_df = self.df[self.df['Innings Player'] == name]

    if player_df.empty:
        return "Player not found"

    total_wickets = player_df['Innings Wickets Taken'].sum()
    total_runs = player_df['Innings Runs Conceded'].sum()
    total_maidens = player_df['Innings Maidens Bowled'].sum()
    total_balls = player_df['Balls Bowled'].sum()

    # economy = runs per over, bowling average = runs given per wicket
    # (the "if" part stops us from dividing by zero)
    economy = (total_runs / total_balls) * 6 if total_balls > 0 else 0
    average = total_runs / total_wickets if total_wickets > 0 else 0

    summary = {
        'Player': name,
        'Innings': len(player_df),
        'Total Wickets': int(total_wickets),
        'Total Runs Conceded': int(total_runs),
        'Total Maidens': int(total_maidens),
        'Economy Rate': round(economy, 2),
        'Bowling Average': round(average, 2)
    }

    return summary
