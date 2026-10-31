"""Tkinter interface layered on top of the ODIAnalysis (batting) and ODIBowlingAnalysis (bowling) classes."""
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
from matplotlib.figure import Figure
from matplotlib.ticker import MaxNLocator
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from odi_analysis import ODIAnalysis
from odi_bowling import ODIBowlingAnalysis

BG='#101827'; PANEL='#192538'; FG='#eef4ff'; MUTED='#aabbd1'; ACCENT='#41c6a5'; BTN='#237b79'; BTN_OFF='#2b4059'


def label(parent, text, size=11, color=FG, bold=False):
    return tk.Label(parent,text=text,bg=parent.cget('bg'),fg=color,font=('Segoe UI',size,'bold' if bold else 'normal'))

def button(parent, text, command, color=BTN):
    return tk.Button(parent,text=text,command=command,bg=color,fg='white',activebackground=ACCENT,activeforeground='#0c1827',relief='flat',font=('Segoe UI',10,'bold'),padx=15,pady=9,cursor='hand2')

def make_tree(parent, cols, height, side=None):
    frame=tk.Frame(parent,bg=BG)
    if side: frame.pack(side=side,fill='both',expand=True,padx=(0,8))
    else: frame.pack(fill='both',expand=True)
    tree=ttk.Treeview(frame,columns=cols,show='headings',height=height)
    for c in cols:tree.heading(c,text=c);tree.column(c,width=115 if c!='Player' else 175,anchor='w')
    sy=ttk.Scrollbar(frame,orient='vertical',command=tree.yview)
    sx=ttk.Scrollbar(frame,orient='horizontal',command=tree.xview)
    tree.configure(yscrollcommand=sy.set,xscrollcommand=sx.set)
    tree.grid(row=0,column=0,sticky='nsew');sy.grid(row=0,column=1,sticky='ns');sx.grid(row=1,column=0,sticky='ew')
    frame.rowconfigure(0,weight=1);frame.columnconfigure(0,weight=1)
    return tree

def fmt(value):
    # show 8.0 as 8, and missing values as a dash
    if pd.isna(value):return '—'
    if isinstance(value,float) and value.is_integer():return str(int(value))
    return str(value)


class AnalysisPage(tk.Frame):
    """Common page (Dashboard / Player Explorer / Dataset Browser). Batting and Bowling pages fill in the details."""
    name=''
    metric_names=[]
    cards_per_row=3
    tables=[]          # (title, columns)
    record_cols=[]     # (heading, dataframe column)
    charts={}          # chart title: (analysis method, 'bar' or 'line', axis label)
    required=set()

    def __init__(self, parent, status):
        super().__init__(parent,bg=BG)
        self.status=status
        self.analysis=None
        self.filtered=None
        self.tabs=ttk.Notebook(self);self.tabs.pack(fill='both',expand=True)
        self.dashboard=tk.Frame(self.tabs,bg=BG);self.players=tk.Frame(self.tabs,bg=BG);self.charts_tab=tk.Frame(self.tabs,bg=BG);self.records=tk.Frame(self.tabs,bg=BG)
        self.tabs.add(self.dashboard,text='  Dashboard  ')
        self.tabs.add(self.players,text='  Player Explorer  ')
        self.tabs.add(self.charts_tab,text='  Charts  ')
        self.tabs.add(self.records,text='  Dataset Browser  ')
        self.build_dashboard();self.build_players();self.build_charts();self.build_records()

    # ---- building the screens ----
    def build_dashboard(self):
        label(self.dashboard,f'ODI {self.name.lower()} overview',16,bold=True).pack(anchor='w',pady=(6,15))
        cards=tk.Frame(self.dashboard,bg=BG);cards.pack(fill='x')
        self.metric_vars={}
        for i,name in enumerate(self.metric_names):
            card=tk.Frame(cards,bg=PANEL,padx=15,pady=13)
            card.grid(row=i//self.cards_per_row,column=i%self.cards_per_row,padx=5,pady=5,sticky='nsew')
            label(card,name,10,MUTED).pack(anchor='w')
            v=tk.StringVar(value='—');self.metric_vars[name]=v
            tk.Label(card,textvariable=v,bg=PANEL,fg=ACCENT,font=('Segoe UI',18,'bold')).pack(anchor='w',pady=5)
        for i in range(self.cards_per_row):cards.columnconfigure(i,weight=1)
        area=tk.Frame(self.dashboard,bg=BG);area.pack(fill='both',expand=True,pady=(14,0))
        self.table_trees=[]
        for title,cols in self.tables:
            block=tk.Frame(area,bg=BG);block.pack(side='left',fill='both',expand=True,padx=4)
            label(block,title,14,bold=True).pack(anchor='w',pady=(0,8))
            self.table_trees.append(make_tree(block,cols,height=6))
        button(self.dashboard,'Refresh Statistics',self.refresh).pack(anchor='e',pady=10)

    def build_players(self):
        label(self.players,f'Individual {self.name.lower()} summary',16,bold=True).pack(anchor='w',pady=(6,15))
        bar=tk.Frame(self.players,bg=BG);bar.pack(fill='x')
        self.player_name=tk.StringVar()
        self.player_combo=ttk.Combobox(bar,textvariable=self.player_name,width=48)
        self.player_combo.pack(side='left',padx=(0,10),ipady=5)
        self.player_combo.bind('<Return>',lambda e:self.search_player())
        button(bar,'Search Player',self.search_player).pack(side='left')
        self.player_output=tk.Text(self.players,height=14,bg=PANEL,fg=FG,insertbackground=FG,relief='flat',font=('Consolas',13),padx=22,pady=20,state='disabled')
        self.player_output.pack(fill='both',expand=True,pady=20)

    def build_charts(self):
        label(self.charts_tab,f'{self.name} charts',16,bold=True).pack(anchor='w',pady=(6,15))
        bar=tk.Frame(self.charts_tab,bg=BG);bar.pack(fill='x')
        self.chart_name=tk.StringVar(value=list(self.charts)[0])
        combo=ttk.Combobox(bar,textvariable=self.chart_name,values=list(self.charts),width=48,state='readonly')
        combo.pack(side='left',padx=(0,10),ipady=5)
        combo.bind('<<ComboboxSelected>>',lambda e:self.draw_chart())
        # button(bar,'Draw Chart',self.draw_chart).pack(side='left')
        button(bar,'Save Image',self.save_chart).pack(side='right')
        self.figure=Figure(figsize=(9,5),dpi=100,facecolor=PANEL)
        self.canvas=FigureCanvasTkAgg(self.figure,master=self.charts_tab)
        self.canvas.get_tk_widget().pack(fill='both',expand=True,pady=14)

    def build_records(self):
        label(self.records,f'Explore and export {self.name.lower()} records',16,bold=True).pack(anchor='w',pady=(6,12))
        bar=tk.Frame(self.records,bg=BG);bar.pack(fill='x',pady=(0,10))
        self.filter_text=tk.StringVar()
        entry=tk.Entry(bar,textvariable=self.filter_text,width=34,font=('Segoe UI',11))
        entry.pack(side='left',ipady=7,padx=(0,10))
        entry.bind('<Return>',lambda e:self.filter_records())
        button(bar,'Filter by Player',self.filter_records).pack(side='left',padx=(0,8))
        button(bar,'Clear Filter',self.clear_filter).pack(side='left',padx=(0,8))
        button(bar,'Export CSV',self.export_csv).pack(side='right')
        self.record_tree=make_tree(self.records,[h for h,_ in self.record_cols],height=15)
        self.record_count=label(self.records,'No data loaded',10,MUTED)
        self.record_count.pack(anchor='w',pady=8)

    # ---- loading ----
    def load(self, path):
        """Create the analysis object and check it. Raises ValueError if the file does not fit."""
        obj=self.analysis_class(path)
        missing=self.required-set(obj.df.columns)
        if missing:raise ValueError(f'{self.name}: missing required columns: '+', '.join(sorted(missing)))
        if obj.df.empty:raise ValueError(f'{self.name}: no rows remain after preprocessing. The original classes split the dataset at 86,194 rows; use the full ODI.csv.')
        return obj

    def set_analysis(self, obj):
        self.analysis=obj;self.filtered=obj.df.copy()
        self.player_combo['values']=sorted(obj.df['Innings Player'].dropna().astype(str).unique().tolist())
        self.refresh();self.show_records();self.draw_chart()

    def require_data(self):
        if self.analysis is None:
            messagebox.showwarning('Dataset needed','Please open your ODI CSV file first.')
            return False
        return True

    # ---- actions ----
    def refresh(self):
        if not self.require_data():return
        try:
            for key,value in self.compute_metrics().items():self.metric_vars[key].set(value)
            for tree,rows in zip(self.table_trees,self.table_rows()):
                tree.delete(*tree.get_children())
                for row in rows:tree.insert('','end',values=[fmt(x) for x in row])
        except (ValueError,KeyError,TypeError) as exc:messagebox.showerror('Analysis error',str(exc))

    def draw_chart(self):
        if not self.require_data():return
        title=self.chart_name.get()
        method,kind,axis_label=self.charts[title]
        try:
            data=getattr(self.analysis,method)()
            self.figure.clear()
            ax=self.figure.add_subplot(111,facecolor=PANEL)
            if kind=='line':
                ax.plot(data.index,data.values,color=ACCENT,marker='o',linewidth=2)
                ax.xaxis.set_major_locator(MaxNLocator(integer=True))
                ax.set_xlabel('Year',color=MUTED)
                ax.set_ylabel(axis_label,color=MUTED)
                ax.grid(color='#2b4059',linestyle='--',linewidth=0.7)
            else:
                # horizontal bars, biggest value at the top
                names=[str(n) for n in data.index][::-1]
                values=list(data.values)[::-1]
                bars=ax.barh(names,values,color=ACCENT)
                ax.bar_label(bars,labels=[fmt(v) for v in values],padding=4,color=FG,fontsize=9)
                ax.margins(x=0.12)
                ax.set_xlabel(axis_label,color=MUTED)
            ax.set_title(title,color=FG,fontsize=13,fontweight='bold',pad=12)
            ax.tick_params(colors=FG)
            for spine in ax.spines.values():spine.set_color('#2b4059')
            self.figure.tight_layout()
            self.canvas.draw()
        except Exception as exc:
            messagebox.showerror('Chart error',f'{type(exc).__name__}: {exc}')

    def save_chart(self):
        if not self.require_data():return
        path=filedialog.asksaveasfilename(defaultextension='.png',filetypes=[('PNG image','*.png')],initialfile=f'odi_{self.name.lower()}_chart.png')
        if not path:return
        try:self.figure.savefig(path,facecolor=self.figure.get_facecolor());self.status.set('Saved: '+path)
        except OSError as exc:messagebox.showerror('Save error',str(exc))

    def search_player(self):
        if not self.require_data():return
        name=self.player_name.get().strip()
        if not name:messagebox.showwarning('Missing name','Enter or select a player name.');return
        result=self.analysis.player_summary(name)
        text=result if isinstance(result,str) else '\n\n'.join(f'{k}:  {v}' for k,v in result.items())
        self.player_output.configure(state='normal');self.player_output.delete('1.0','end');self.player_output.insert('1.0',text);self.player_output.configure(state='disabled')
        self.status.set(f'{self.name} lookup: {name}')

    def filter_records(self):
        if not self.require_data():return
        term=self.filter_text.get().strip()
        if not term:messagebox.showwarning('Missing filter','Enter a player name or part of a name.');return
        self.filtered=self.analysis.df[self.analysis.df['Innings Player'].astype(str).str.contains(term,case=False,regex=False,na=False)].copy()
        self.show_records()

    def clear_filter(self):
        if not self.require_data():return
        self.filter_text.set('');self.filtered=self.analysis.df.copy();self.show_records()

    def show_records(self):
        self.record_tree.delete(*self.record_tree.get_children())
        df=self.filtered
        for _,r in df.head(500).iterrows():
            self.record_tree.insert('','end',values=[fmt(r.get(c)) for _,c in self.record_cols])
        self.record_count.config(text=f'{len(df):,} matching rows (first 500 displayed for responsiveness).')

    def export_csv(self):
        if not self.require_data():return
        if self.filtered is None or self.filtered.empty:messagebox.showwarning('No records','No records to export.');return
        path=filedialog.asksaveasfilename(defaultextension='.csv',filetypes=[('CSV files','*.csv')],initialfile=f'odi_{self.name.lower()}_records.csv')
        if not path:return
        try:self.filtered.to_csv(path,index=False);self.status.set('Saved: '+path);messagebox.showinfo('Export complete',f'Saved {len(self.filtered):,} records.')
        except OSError as exc:messagebox.showerror('Save error',str(exc))


class BattingPage(AnalysisPage):
    name='Batting'
    analysis_class=ODIAnalysis
    metric_names=['Innings Records','Average Strike Rate','Total Sixes','Total Fours','Highest Innings','Lowest Innings']
    cards_per_row=3
    tables=[('Top five scoring innings',['Player','Runs']),('Best batting averages (min 20 inns)',['Player','Average'])]
    charts={'Top 10 career run scorers':('top_career_runs','bar','Runs'),
            'Top 10 batting averages (min 20 innings)':('top_batting_averages','bar','Batting average'),
            'Average runs per innings by year':('runs_per_year','line','Average runs per innings'),
            'Total runs by country':('runs_by_country','bar','Runs'),
            'Innings by score range':('innings_by_score_range','bar','Number of innings')}
    record_cols=[('Player','Innings Player'),('Runs','Innings Runs Scored Num'),('Balls','Innings Balls Faced'),('Fours','Innings Boundary Fours'),('Sixes','Innings Boundary Sixes'),('Strike Rate','Innings Batting Strike Rate'),('Opposition','Opposition'),('Date','Innings Date')]
    required={'Innings Player','Innings Runs Scored Num','Innings Boundary Sixes','Innings Boundary Fours','Innings Balls Faced','Innings Batting Strike Rate'}

    def compute_metrics(self):
        a=self.analysis;df=a.df
        top=df.loc[df['Innings Runs Scored Num'].idxmax()]
        low=df.loc[df['Innings Runs Scored Num'].idxmin()]
        return {'Innings Records':f'{len(df):,}',
                'Average Strike Rate':f'{a.avg_strike_rate():.2f}',
                'Total Sixes':f'{a.total_six():,.0f}',
                'Total Fours':f'{a.total_fours():,.0f}',
                'Highest Innings':f"{top['Innings Runs Scored Num']:,.0f} — {top['Innings Player']}",
                'Lowest Innings':f"{low['Innings Runs Scored Num']:,.0f} — {low['Innings Player']}"}

    def table_rows(self):
        return [list(self.analysis.top_five_scorers_dict().items()),list(self.analysis.top_five_batting_average_dict().items())]


class BowlingPage(AnalysisPage):
    name='Bowling'
    analysis_class=ODIBowlingAnalysis
    metric_names=['Bowling Innings','Total Wickets','Average Economy Rate','Total Maidens','4 Wicket Hauls','5 Wicket Hauls','Best Bowling','Most Expensive Spell']
    cards_per_row=4
    tables=[('Top five bowling innings',['Player','Wickets']),('Top five career wickets',['Player','Wickets']),('Best economy (min 100 overs)',['Player','Economy'])]
    charts={'Top 10 career wicket takers':('top_career_wickets','bar','Wickets'),
            'Top 10 best economy rates (min 100 overs)':('best_economy_rates','bar','Economy rate (runs per over)'),
            'Average economy rate by year':('economy_per_year','line','Average economy rate'),
            'Total wickets by country':('wickets_by_country','bar','Wickets'),
            'Innings by wickets taken':('innings_by_wicket_range','bar','Number of innings')}
    record_cols=[('Player','Innings Player'),('Overs','Innings Overs Bowled'),('Maidens','Innings Maidens Bowled'),('Runs','Innings Runs Conceded'),('Wickets','Innings Wickets Taken'),('Economy','Innings Economy Rate'),('Opposition','Opposition'),('Date','Innings Date')]
    required={'Innings Player','Innings Overs Bowled','Innings Maidens Bowled','Innings Runs Conceded','Innings Wickets Taken','Innings Economy Rate','Balls Bowled'}

    def compute_metrics(self):
        a=self.analysis;df=a.df
        best=df.sort_values(by=['Innings Wickets Taken','Innings Runs Conceded'],ascending=[False,True]).iloc[0]
        costly=df.loc[df['Innings Runs Conceded'].idxmax()]
        return {'Bowling Innings':f'{len(df):,}',
                'Total Wickets':f'{a.total_wickets():,.0f}',
                'Average Economy Rate':f'{a.avg_economy_rate():.2f}',
                'Total Maidens':f'{a.total_maidens():,.0f}',
                '4 Wicket Hauls':f'{a.total_four_wickets():,}',
                '5 Wicket Hauls':f'{a.total_five_wickets():,}',
                'Best Bowling':f"{best['Innings Wickets Taken']:.0f}/{best['Innings Runs Conceded']:.0f} — {best['Innings Player']}",
                'Most Expensive Spell':f"{costly['Innings Runs Conceded']:.0f} runs — {costly['Innings Player']}"}

    def table_rows(self):
        return [list(self.analysis.top_five_wicket_takers_dict().items()),list(self.analysis.top_five_career_wickets_dict().items()),list(self.analysis.top_five_best_economy_dict().items())]


class ODIApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('ODI Cricket | Analytics')
        self.geometry('1180x800')
        self.minsize(950, 650)
        self.configure(bg=BG)
        self.style=ttk.Style(self)
        self.style.theme_use('clam')
        self.style.configure('Treeview', background=PANEL, foreground=FG, fieldbackground=PANEL, rowheight=27, borderwidth=0)
        self.style.configure('Treeview.Heading', background='#2b4059', foreground=FG, font=('Segoe UI',10,'bold'))
        self.style.map('Treeview',background=[('selected','#236c7c')])
        self.style.configure('TCombobox', padding=6)
        self.build()

    def build(self):
        header=tk.Frame(self,bg=BG,padx=24,pady=18);header.pack(fill='x')
        label(header,'ODI  /  CRICKET ANALYTICS',22,bold=True).pack(side='left')
        button(header,'Open CSV',self.open_csv).pack(side='right')
        self.bowling_btn=button(header,'Bowling',lambda:self.show_page('Bowling'));self.bowling_btn.pack(side='right',padx=(0,10))
        self.batting_btn=button(header,'Batting',lambda:self.show_page('Batting'));self.batting_btn.pack(side='right',padx=(0,6))
        self.file_label=label(self,'Choose your ODI.csv file to begin',10,MUTED)
        self.file_label.pack(anchor='w',padx=24)
        self.status=tk.StringVar(value='Ready. Open an ODI CSV file.')
        tk.Label(self,textvariable=self.status,bg='#1c2b40',fg=MUTED,anchor='w',padx=20,pady=9).pack(side='bottom',fill='x')
        container=tk.Frame(self,bg=BG);container.pack(fill='both',expand=True,padx=24,pady=16)
        self.pages={'Batting':BattingPage(container,self.status),'Bowling':BowlingPage(container,self.status)}
        self.show_page('Batting')

    def show_page(self,name):
        for page_name,page in self.pages.items():page.pack_forget()
        self.pages[name].pack(fill='both',expand=True)
        self.batting_btn.config(bg=BTN if name=='Batting' else BTN_OFF)
        self.bowling_btn.config(bg=BTN if name=='Bowling' else BTN_OFF)

    def open_csv(self):
        path=filedialog.askopenfilename(title='Select ODI CSV dataset',filetypes=[('CSV files','*.csv'),('All files','*.*')])
        if not path:return
        self.status.set('Loading dataset, please wait...');self.update_idletasks()
        try:
            # build both analyses first, so a bad file never leaves the app half loaded
            loaded={name:page.load(path) for name,page in self.pages.items()}
            for name,page in self.pages.items():page.set_analysis(loaded[name])
            self.file_label.config(text=path)
            self.status.set(f"Loaded {len(loaded['Batting'].df):,} batting innings and {len(loaded['Bowling'].df):,} bowling innings.")
        except (OSError,ValueError,KeyError,UnicodeError,pd.errors.ParserError) as exc:
            self.status.set('Could not load the dataset.')
            messagebox.showerror('Cannot load dataset',str(exc))
        except Exception as exc:
            self.status.set('Could not load the dataset.')
            messagebox.showerror('Unexpected dataset error',f'{type(exc).__name__}: {exc}')

if __name__=='__main__':
    ODIApp().mainloop()
