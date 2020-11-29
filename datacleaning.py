import pandas as pd 
import numpy as np 
import unidecode 

# player-ages.xlsx is 2019,2016,2014 player data copy/pasted from basketball-reference
# NBA_proj.xlsx is advanced stat data copy/pasted from bball-index from 2013-2019

def get_player_ages():
    dfs = pd.read_excel('player_ages.xlsx', sheet_name=[0,1,2],
                        usecols='B,D,E')
    df = pd.concat([dfs[0], dfs[1], dfs[2]]).reset_index().drop('index', axis=1)
    df = df.drop_duplicates(subset=['Player'])
    df['Current_Age'] = df.Age + (2020 - df.Year)

    # format consistent with bball-index names and trim columns
    df['Player'] = df['Player'].apply(lambda x: ' '.join((x.split()[:2])))
    #df['Player'] = df['Player'].apply(lambda x: ' '.join((x.replace('.', '').split()[:2])))
    
    # remove accents from names
    df['Player'] = df['Player'].apply(lambda x: unidecode.unidecode(x))
    df = df[['Player', 'Current_Age']].set_index('Player')

    # change names that aren't consistent with NBA_proj.xlsx
    # there are actually a lot more missing 
    """old_names = ['Larry Nance', 'DeAnthony Melton', 'Devonte Graham', 'DeAaron Fox',
                'DAngelo Russell', 'Kelly Oubre', 'Dennis Smith']
    new_names = ['Larry Nance Jr.', "De'Anthony Melton", "Devonte' Graham",
                "D'Angelo Russell", 'Kelly Oubre Jr.', 'Dennis Smith Jr.']
    as_list = df.index.tolist()
    for old,new in zip(old_names, new_names):
        idx = as_list.index(old)
        as_list[idx] = new
    df.index = as_list"""

    return df

def combine_playerseasons():
    """Outputs a time series DataFrame with t ,t-1, t-2, t-3,
    Age, Age-1, Age-2, Age-3 for each player-season. Since it's grouped
    into player-seasons, players can be seen multiple times"""

    # import name, year, minutes, my_stat
    dfs = pd.read_excel('NBA_proj.xlsx', sheet_name=[0,1,2,3,4,5,6],
                        usecols='A:B,E,V')

    # filter for player-seasons with > 500 minutes
    for k in dfs.keys():
        dfs[k] = dfs[k][dfs[k]['Minutes'] > 500]

    # concat everything
    df = pd.concat([dfs[0], dfs[1], dfs[2], dfs[3],
                    dfs[4], dfs[5], dfs[6]]).reset_index().drop('index', axis=1)
    df = df.rename({'my_stat': 't'}, axis=1)

    # add lags
    df['t-1'] = df.apply(lambda row: df.t[(df.Name == row.Name) & (df.Year == row.Year - 1)].values, axis=1)
    df['t-2'] = df.apply(lambda row: df.t[(df.Name == row.Name) & (df.Year == row.Year - 2)].values, axis=1)
    df['t-3'] = df.apply(lambda row: df.t[(df.Name == row.Name) & (df.Year == row.Year - 3)].values, axis=1)
    
    # convert np arrays to values and NaNs
    for i,row in df.iterrows():
        if row['t-1'].size != 0:
            df.loc[i,'t-1'] = row['t-1'].item(0)
        else:
            df.loc[i,'t-1'] = np.nan
        if row['t-2'].size != 0:
            df.loc[i,'t-2'] = row['t-2'].item(0)
        else:
            df.loc[i,'t-2'] = np.nan
        if row['t-3'].size != 0:
            df.loc[i,'t-3'] = row['t-3'].item(0)
        else:
            df.loc[i,'t-3'] = np.nan

    # add age, age-1, age-2, age-3
    age_df = get_player_ages()
    df['Age'] = np.zeros(len(df.Name))
    missing_ages = []
    j = 1
    for i,row in df.iterrows():
        try:
            # 'Age' is from 19-20 season and corresponds to 't'
            df.loc[i,'Age'] = age_df.loc[row.Name,'Current_Age'] - (2020 - row.Year)
        except KeyError:
            if row.Year == 2019:
                missing_ages.append(row.Name)
            print("{}. Error getting Age for {}".format(j, row.Name))
            j += 1
            df.loc[i,'Age'] = np.nan
    print("MISSING AGES: ")
    for i,name in enumerate(missing_ages):
        print("{}. {}".format(i,name))
    df['Age-1'] = df.Age - 1
    df['Age-2'] = df.Age - 2
    df['Age-3'] = df.Age - 3

    # transform age based on age curve formula; use delta to current year from last year
    #age_curve_df = pd.read_csv('age_curve.csv').set_index('ages')
    df['tAge'] = (-40.9 + 3.78*df.Age - 0.11*df.Age**2 + 0.001*df.Age**3) \
                 - (-40.9 + 3.78*(df.Age-1) - 0.11*(df.Age-1)**2 + 0.001*(df.Age-1)**3)

    df['tAge-1'] = (-40.9 + 3.78*(df.Age-1) - 0.11*(df.Age-1)**2 + 0.001*(df.Age-1)**3) \
                 - (-40.9 + 3.78*(df.Age-2) - 0.11*(df.Age-2)**2 + 0.001*(df.Age-2)**3)

    df['tAge-2'] = (-40.9 + 3.78*(df.Age-2) - 0.11*(df.Age-2)**2 + 0.001*(df.Age-2)**3) \
                 - (-40.9 + 3.78*(df.Age-3) - 0.11*(df.Age-3)**2 + 0.001*(df.Age-3)**3)

    df['tAge-3'] = (-40.9 + 3.78*(df.Age-3) - 0.11*(df.Age-3)**2 + 0.001*(df.Age-3)**3) \
                 - (-40.9 + 3.78*(df.Age-4) - 0.11*(df.Age-4)**2 + 0.001*(df.Age-4)**3)

    print(df.head(10)) 
    print(df.tail(10))
    print(df.shape)

    df.to_csv('player-seasons.csv')

    return df

if __name__ == "__main__":
    combine_playerseasons()
