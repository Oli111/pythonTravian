from map_parser_functions import *
import math
_dir_raw_data = 'rawMapData'
_dir_preprocessed = "preprocessedMapData"
fakes_per_attacker = 4
_village_pop_at_least = 500
_targeted_village_between_hrs = [5,24]
const_catapult_speed = 3
_target_top_players = 22
_aliances_attacked_list = ["TSR"]
_enemies_excluded_list = ["'Clarence Beeks'"]
#preprocess_data(_dir_raw_data, _dir_preprocessed)

### Reading the data
import os
_data_file = os.listdir(_dir_preprocessed).pop()
pdf_map = pd.read_csv(f"{_dir_preprocessed}/{_data_file}")
pdf_map_enemies = pdf_map[pdf_map['aliance_name'].apply(lambda x: x.strip("'") in _aliances_attacked_list)]
pdf_enemies_pop = pdf_map_enemies\
    .groupby('player_name')\
    .agg({'village_pop':'sum'})\
    .rename(columns = {'village_pop':'player_pop'})\
    .reset_index()


pdf_map_enemies_capitals = pdf_map_enemies\
    .groupby('player_name')\
    .agg({'village_pop': 'max'})\
    .reset_index()
pdf_map_enemies_capitals['capital'] = True
pdf_map_enemies = pdf_map_enemies\
    .merge(pdf_map_enemies_capitals,
           on = ['player_name', 'village_pop'],
           how ='outer')\
    .fillna(False)

pdf_enemies_pop.sort_values('player_pop', ascending = False, inplace =True)
pdf_enemies_pop = pdf_enemies_pop.head(_target_top_players)

pdf_map_enemies = pdf_map_enemies.merge(pdf_enemies_pop, on = 'player_name')
pdf_map_enemies = pdf_map_enemies[pdf_map_enemies['village_pop']>_village_pop_at_least]
pdf_map_enemies.to_csv("targeted_villages.csv", encoding = 'UTF-8')



pdf_attackers = pd.read_csv("attackers.csv")
### priority
pdf_map['player_name'] = pdf_map['player_name'].apply(lambda x: x.strip("'"))
pdf_attackers = pdf_map.merge(pdf_attackers, on = 'player_name')
pdf_attackers_capitals = pdf_attackers.groupby('player_name').agg({'village_pop':'max'}).reset_index()
pdf_attackers = pdf_attackers.merge(pdf_attackers_capitals, on = ['player_name', 'village_pop'])



# for each attacker pick at least one capital if possible

pdf_targets = pd.DataFrame({'coord_x':[], 'coord_y':[], 'attacker':[]})
pdf_map_enemies = pdf_map_enemies.sample(frac=1).reset_index(drop=True)

for index, row in pdf_attackers.iterrows():

    coord_x, coord_y, player_name = row['coord_x'], row['coord_y'], row['player_name']
    # print(player_name)
    pdf_map_enemies['distance'] = pdf_map_enemies.apply(
        lambda x: math.sqrt((x['coord_x'] - coord_x) ** 2 + (x['coord_y'] - coord_y) ** 2), 1)

    pdf_map_enemies['distance_hrs'] = pdf_map_enemies['distance']/const_catapult_speed


    pdf_map_enemies_for_player = pdf_map_enemies[(pdf_map_enemies['distance_hrs']>_targeted_village_between_hrs[0]) &
                                                        (pdf_map_enemies['distance_hrs']<_targeted_village_between_hrs[1])]
    print(pdf_map_enemies_for_player.shape[0])
    pdf_map_enemies_capitals = pdf_map_enemies_for_player[pdf_map_enemies_for_player['capital']]

    if pdf_map_enemies_capitals.shape[0] > 0:
        index_data = pdf_map_enemies_capitals.index[0]
        subtract_from_num_of_attacks = 1
        row_target = pdf_map_enemies.loc[index_data,:]
        pdf_targets = pdf_targets.append(pd.DataFrame({'coord_x':[row_target['coord_x']],
                                                       'coord_y':[row_target['coord_y']],
                                                       'attacker':[player_name],
                                                       'target_player': [row_target['player_name']],
                                                       'village_pop': [row_target['village_pop']],
                                                       'distance_hrs': [row_target['distance_hrs']]
                                                       }))
        pdf_map_enemies.drop(index_data, inplace = True, axis = 0)
        pdf_map_enemies_for_player.drop(index_data, inplace = True, axis = 0)
    else:
        subtract_from_num_of_attacks = 0
    for _attack_num in range(fakes_per_attacker-subtract_from_num_of_attacks):
        index_data = pdf_map_enemies_for_player.index[0]
        print(index_data)
        row_target = pdf_map_enemies.loc[index_data, :]
        pdf_targets = pdf_targets.append(pd.DataFrame({'coord_x': [row_target['coord_x']],
                                                       'coord_y': [row_target['coord_y']],
                                                       'attacker': [player_name],
                                                       'target_player': [row_target['player_name']],
                                                       'village_pop': [row_target['village_pop']],
                                                       'distance_hrs': [row_target['distance_hrs']]
                                                       }))
        pdf_map_enemies.drop(index_data, inplace=True, axis = 0)
        pdf_map_enemies_for_player.drop(index_data, inplace=True, axis=0)



pdf_targets['village_url'] = pdf_targets.apply(lambda x: f"https://ts5.travian.com/position_details.php?x={str(int(x['coord_x']))}&y={str(int(x['coord_y']))}",1)
pdf_targets.to_csv("targets.csv")
#_attacker = attackers_list[0]

