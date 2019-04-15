from selenium import webdriver
import numpy as np
import pandas as pd
from bs4 import BeautifulSoup
import time
import random
import datetime
import warnings
print("Start of the script ...")
# translations: for cz
level_translation = " Úroveň "
done_translation = " hod. Hotovo v "
village_center = "Centrum"
fields_types = ["Dřevorubec", "Hliněný důl", "Železný důl", "Obilné pole"]
driverPathLocale = "d:\chromeDriver\chromedriver.exe"

# EN
#
# level_translation = " Level "
# village_center = "Buildings"
# fields_types = ["Woodcutter", "Clay Pit", "Iron Mine", "Cropland"]
# done_translation = " hrs. done at "
# construct_new_building_translation = "Construct new building"

class TravianPlayer(object):
    def __init__(self, username, password, server):
        self.username = username
        self.password = password
        self.server = server
        self.driver = webdriver.Chrome(driverPathLocale)
        self.time_to_wait = 0

    def login(self):
        self.driver.get(self.server + "dorf1.php")
        self.driver.find_element_by_name('name').send_keys(self.username)
        self.driver.find_element_by_name('password').send_keys(self.password)
        self.driver.find_element_by_name("s1").click()


    def switch_to_dorf1(func):
        def switch(self, *args, **kwargs):
            if ("dorf1.php" not in self.driver.current_url) or (self.driver.current_url[-1]=="#"):
                self.driver.get(self.server + "dorf1.php")
            return func(self, *args, **kwargs)
        return switch

    def switch_to_dorf2(func):
        def switch(self, *args, **kwargs):
            if "dorf2" not in self.driver.current_url:
                self.driver.get(self.server + "dorf2.php")
            return func(self, *args, **kwargs)
        return switch

    def switch_to_hero_adventures(func):
        def switch(self, *args, **kwargs):
            if "hero.php?t=3" not in self.driver.current_url:
                self.driver.get(self.server + "hero.php?t=3")
            return func(self, *args, **kwargs)
        return switch

    def switch_to_hero(func):
        def switch(self, *args, **kwargs):
            if "hero.php?t=3" not in self.driver.current_url:
                self.driver.get(self.server + "hero.php")
            return func(self, *args, **kwargs)
        return switch

    def get_villages_information(self):
        # self.driver
        anchor = self.driver.find_element_by_css_selector("#sidebarBoxVillagelist")
        anchor = anchor.find_elements_by_css_selector("a")
        #print(list(map(lambda x: x.text,a)))
        #a = a.find_elements_by_class_name("name")
        _data_villages = pd.DataFrame({"village_id":[i for i in range(1,len(anchor)+1)],
                                       "village_name": list(map(lambda x: x.find_element_by_class_name("name").text,anchor)),
                                        "village_link":list(map(lambda x: x.get_attribute("href"), anchor))})
        #_data_villages.to_csv("villages_information.csv", index = False, encoding="UTF-8")
        return(_data_villages)

    @switch_to_hero
    def get_hero_health(self):
        power = self.driver.find_element_by_class_name("powervalue").text
        power = power.strip("\u202c%\u202c")
        power = power.strip("\u202d\u202d")
        power = int(power)
        print("Hero's health is: " + str(power) + "%")
        time.sleep(2)
        return(power)

    def go_to_hero_adventure(self, village_id: int, _at_least_health: int = 20):
        _hero_health = self.get_hero_health()
        self.switch_to_village(village_id)
        self.switch_to_hero_adventures()
        _flag_hero_has_enough_health = _at_least_health < _hero_health
        #_flag_hero_has_enough_health=True
        _flag_are_there_adventures = len(self.driver.find_elements_by_class_name("gotoAdventure"))>0
        if (_flag_are_there_adventures and _flag_hero_has_enough_health):
            adventure_link = self.driver.find_element_by_class_name("gotoAdventure").get_attribute("href")
            self.driver.get(adventure_link)
            button_adventure = self.driver.find_element_by_class_name("startAdventure")
            button_adventure.click()
        else:
            print("There are no adventures for hero to go on or hero is not present in the village. Or not enough health.")
        time.sleep(2)

    @switch_to_dorf1
    def create_data_frame_available_upgrades(self):
        """
        For current village, scrape the available tile upgrades and save it to ..\tile_upgrades.csv

        """
        field_map = self.driver.find_element_by_css_selector('map#rx')
        fields = field_map.find_elements_by_css_selector("area")

        link = list(map(lambda x: x.get_attribute("href"), fields))
        link = list(filter(lambda x: "build.php" in x,link ))
        type_levels = list(map(lambda x: x.get_attribute("alt"), fields))
        type_levels = list(filter(lambda x: not(village_center in x), type_levels))
        _type = list(map(lambda x: x.split(level_translation)[0], type_levels))
        _level = list(map(lambda x: x.split(level_translation, 2)[1], type_levels))
        _data = {"link": link,
                 "type":_type,
                 "level":_level
                 }
        _data_pd = pd.DataFrame(_data).sort_values('level')
        _data_pd.to_csv("tile_upgrades.csv", index = False, encoding = "UTF-8")


    def do_trade_on_auctions(self):
        pass

    def do_send_autoattacks(self):
        pass



    @switch_to_dorf2
    def create_data_frame_available_buildings(self, village_id: int):
        """
        We are checking for already built buildings and their levels.


        :return:
        """
        try:
            data_buildings_done = pd.read_csv("data_buildings_in_centrum.csv", encoding = "utf-8")
            data_buildings_done = data_buildings_done[data_buildings_done['village_id'] != village_id]
        except:
            data_buildings_done = None

        print("Creating list of available buildings..")
        path = "build.php?id="

        building_names = []
        building_urls = []
        building_levels = []
        list_iter_temp = [i for i in range(18,40)]

        for i in range(18,40):
            idx = list_iter_temp[random.randint(0,len(list_iter_temp)-1)]
            list_iter_temp.remove(idx)
            time.sleep(random.randint(0, 3))
            _url_building = self.server + path + str(idx)
            print(_url_building)
            building_urls.append(_url_building)
            self.driver.get(_url_building)
            titleInHeader_element = self.driver.find_element_by_class_name("titleInHeader")
            titleInHeader_element_text = titleInHeader_element.text
            strings_in_the_header = titleInHeader_element_text.split(level_translation)
            building_name = strings_in_the_header[0]
            building_names.append(building_name)
            level_of_the_building = 0 if len(strings_in_the_header)==1 else (int(strings_in_the_header[1]))
            building_levels.append(level_of_the_building)

        data_buildings_in_centrum = pd.DataFrame({
                                             "building_name":building_names,
                                             "building_url": building_urls,
                                             "building_level":building_levels})
        data_buildings_in_centrum["village_id"] = village_id
        if data_buildings_done is not None:
            data_buildings_in_centrum = data_buildings_in_centrum.append(data_buildings_done)


        data_buildings_in_centrum.to_csv("data_buildings_in_centrum.csv", index=False, encoding = "utf-8")

    @switch_to_dorf2
    def do_build_new_building(self, building_to_build: str):
        """
        City Wall has to be id 40
        Case for cranny not done (can be level 10 only)
        :return:
        """
        print("Attempting to build a new building " + building_to_build)
        # find
        path = "build.php?id="

        building_names = []
        building_urls = []
        building_levels = []
        list_iter_temp = [i for i in range(18, 40)]

        for i in range(18, 40):
            idx = list_iter_temp[random.randint(0, len(list_iter_temp) - 1)]
            list_iter_temp.remove(idx)
            time.sleep(random.randint(0, 3))
            _url_building = self.server + path + str(idx)
            print(_url_building)
            building_urls.append(_url_building)
            self.driver.get(_url_building)
            titleInHeader_element = self.driver.find_element_by_class_name("titleInHeader")
            titleInHeader_element_text = titleInHeader_element.text
            print("titleInHeader_element_text")
            if titleInHeader_element_text == construct_new_building_translation:
                for category_buildings in range(1,4):
                    url_new_build = _url_building + "&category=" + str(category_buildings)
                    self.driver.get(url_new_build)
                    anchor = self.driver.find_element_by_id("build")
                    anchor = anchor.find_elements_by_link_text(building_to_build)
                    # print(len(anchor))
                    if len(anchor) ==0:
                        continue
                    else:
                        anchor = anchor[0]
                        upgrade_button = anchor.find_element_by_css_selector('div.contractLink button')
                        print("Building " + building_to_build + " succesfuly beeing built.")
                        upgrade_button.click()
                        break

    @switch_to_dorf2
    def switch_to_village(self, village_id):
        df_villages = self.get_villages_information()
        df_village_row = df_villages[df_villages['village_id'] == village_id]

        if (df_village_row.shape[0] == 0):
            raise Exception("Village with the given id " + str(village_id) + " not available.")

        village_link = df_village_row.village_link.iloc[0]
        self.driver.get(village_link)

    @switch_to_dorf2
    def do_upgrade_building(self,village_id: int, building_to_upgrade: str, to_level: int):
        """
        Prerequisities: Only one building in village
        TODO:
        """
        time.sleep(random.randint(1,4))
        self.switch_to_village(village_id)
        currently_beeing_upgraded = self.get_currently_beeing_upgraded_buildings()
        if currently_beeing_upgraded.shape[0] == 0:
            #_flag_can_upgrade_building = True
            print("No tile, no building is beeing upgraded.")
        elif currently_beeing_upgraded[currently_beeing_upgraded['upgrade_type'] == 'building'].shape[0] == 0:
            #_flag_can_upgrade_building = True
            print("No builiding is beeing upgraded.")
        else:
            return
            #raise Exception("Already upgrading some building. Not upgrading " + building_to_upgrade + ".")

        try:
            df_buildings_built_raw = pd.read_csv("data_buildings_in_centrum.csv", encoding = "UTF-8")
        except:
            _flag_scan_run_already = True
            self.create_data_frame_available_buildings(village_id)
            df_buildings_built_raw = pd.read_csv("data_buildings_in_centrum.csv", encoding="UTF-8")

        df_buildings_built = df_buildings_built_raw[df_buildings_built_raw['village_id']==village_id]

        if df_buildings_built.shape[0] == 0:
            _flag_scan_run_already = True
            self.create_data_frame_available_buildings(village_id)
            df_buildings_built_raw = pd.read_csv("data_buildings_in_centrum.csv", encoding="UTF-8")
            df_buildings_built = df_buildings_built_raw[df_buildings_built_raw['village_id'] == village_id]
            df_buildings_built = df_buildings_built.sort_values('building_level')

        building_row = df_buildings_built[(df_buildings_built['building_name'] == building_to_upgrade) & (df_buildings_built['building_level'] <20)]

        if building_row.shape[0] == 0:
            if not(_flag_scan_run_already):
                self.create_data_frame_available_buildings(village_id)
                df_buildings_built_raw = pd.read_csv("data_buildings_in_centrum.csv", encoding="UTF-8")
                df_buildings_built = df_buildings_built_raw[df_buildings_built_raw['village_id'] == village_id]
                df_buildings_built = df_buildings_built.sort_values('building_level')
                building_row = df_buildings_built[(df_buildings_built['building_name'] == building_to_upgrade) & (df_buildings_built['building_level'] < 20)]
                if building_row.shape[0] == 0:
                    raise Exception("No such building in the village to upgrade.")
            else:
                raise Exception("No such building in the village to upgrade.")



        print("Attempting upgrading building " + building_to_upgrade)
        url_building = building_row['building_url'].iloc[0]

        self.driver.get(url_building)
        titleInHeader_element = self.driver.find_element_by_class_name("titleInHeader")
        titleInHeader_element_text = titleInHeader_element.text
        strings_in_the_header = titleInHeader_element_text.split(level_translation)
        building_name_in_header = strings_in_the_header[0]
        if building_name_in_header != building_to_upgrade:
            warnings.warn ("We are not upgrading correct building. Rerun creation of dataframe for available buildings.")

        current_level_building = 0 if len(strings_in_the_header) == 1 else (int(strings_in_the_header[1]))
        if current_level_building < to_level:
            upgrade_button = self.driver.find_element_by_css_selector('div.upgradeButtonsContainer div.section1 button')
            if "green" in upgrade_button.get_attribute("class"):
                upgrade_button.click()

                print("Upgrading building" )

                # df_buildings_built_raw[df_buildings_built_raw["building_url"] == url_building]['building_level'] = df_buildings_built[df_buildings_built["building_url"] == url_building]['building_level'] +1
                # df_buildings_built.to_csv("data_buildings_in_centrum.csv", index=False, encoding = "UTF-8")
            else:
                print("Can not upgrade , not enough resources")
        else:
            print("Level already reached.")

    def storages_almost_full_check(self):
        """
        check if storages are almost full
        :return:
        """
        pass


    def do_upgrade_warehouse(self):
        """
        tell script to upgrade warehouse
        :return:
        """
        pass

    @switch_to_dorf1
    def upgrade_tile(self, village_id: int, do_not_upgrade=None):
        """

        :type do_not_upgrade: list of field types not to upgrade
        """
        if do_not_upgrade is None:
            do_not_upgrade = []
        self.switch_to_village(village_id)
        self.create_data_frame_available_upgrades()
        currently_beeing_upgraded = self.get_currently_beeing_upgraded_buildings()
        # print(currently_beeing_upgraded)
        if currently_beeing_upgraded.shape[0] == 0:
            _flag_can_upgrade_tile = True
        elif currently_beeing_upgraded[currently_beeing_upgraded['upgrade_type']=='field'].shape[0] == 0:
            _flag_can_upgrade_tile = True
        else:
            _flag_can_upgrade_tile = False

        if _flag_can_upgrade_tile:
            _data_upgrades = pd.read_csv("tile_upgrades.csv", encoding = "UTF-8")
            _data_upgrades.sort_values("level",inplace=True)
            _data_upgrades = _data_upgrades[_data_upgrades.apply(lambda x: not(x['type'] in do_not_upgrade),1)]
            upgrade_level = _data_upgrades['level'].tolist()[0]
            upgrade_link = _data_upgrades['link'].tolist()[0]
            upgrade_type = _data_upgrades['type'].tolist()[0]
            self.driver.get(upgrade_link)
            upgrade_button = self.driver.find_element_by_css_selector('div.upgradeButtonsContainer div.section1 button')
            print()
            if "green" in upgrade_button.get_attribute("class"):
                upgrade_button.click()
                #upgrade_time = self.driver.find_element_by_css_selector('div.upgradeButtonsContainer div.section1 inlineIcon').text[0:5]
                #print(upgrade_time)
                print("Upgrading " + upgrade_type + " Level " + str(upgrade_level))
                #upgrade_time = upgrade_time.second+upgrade_time.minute*60+upgrade_time.hour*3600
                #self.time_to_wait = max(self.time_to_wait, 300)
            else:
                print("Can not upgrade " + upgrade_type + " Level " + str(upgrade_level) + "")
                self.time_to_wait = max(self.time_to_wait, 300)
        else:
            print("Already upgrading a field ...")
    time.sleep(2)

    @switch_to_dorf1
    def get_currently_beeing_upgraded_buildings(self) -> pd.DataFrame:
        bookmark = self.driver.find_elements_by_css_selector('h5')
        if len(bookmark)>0:
            bookmark = bookmark[0].find_element_by_xpath('../ul/li')
            build_duration_divs = bookmark.find_elements_by_css_selector("div.buildDuration")
            built_names_divs = bookmark.find_elements_by_css_selector("div.name")
            upgrade_times = list(map(lambda x: x.text.split(done_translation)[0],build_duration_divs))
            upgrade_times = list(map(lambda x: datetime.datetime.strptime(x,'%H:%M:%S'),upgrade_times))
            upgrade_times_seconds = list(map(lambda x: 3600*x.hour + 60*x.minute + x.second, upgrade_times))

            upgraded_name = list(map(lambda x: x.text.split(level_translation)[0], built_names_divs))

            upgrade_type = list(map(lambda x: "field" if (x in fields_types) else "building",upgraded_name))
            data_temp = {"building": upgraded_name,
                         "time_to_finish": upgrade_times,
                         "time_to_finish_seconds": upgrade_times_seconds,
                         "upgrade_type":upgrade_type}
            data_return = pd.DataFrame(data_temp)
            data_return.to_csv("dataUpgrading.csv")
            print("Currently beeing upgraded buildings: ")
            print(data_return)
            return data_return
        else:
            data_temp = {"building":[], "time_to_finish":[], "time_to_finish_seconds":[],"upgrade_type":[]}
            return pd.DataFrame(data_temp)


from config import login_config

player1 = TravianPlayer(login_config["username"], login_config["password"],login_config["server"])
# player1.do_upgrade_building(1, )
#player1 = TravianPlayer("Olie", "mu694ek","https://ts8.anglosphere.travian.com/")


player1.login()
player1.go_to_hero_adventure(2)
#player1.upgrade_tile(1,["Obilné pole"])
#player1.do_upgrade_building(1,"Hlavní budova", 15)
#player1.go_to_hero_adventure()
#
# while True:
#     print("Checking available upgrades")
#     try:
#         # player1.do_upgrade_building("Rezidence", 10)
#         player1.driver.get("https://ts20.czsk.travian.com/dorf1.php?newdid=10778&")
#         print("Trying to upgrade tile")
#         player1.upgrade_tile(1,["Obilné pole"])
#         player1.do_upgrade_building(1,"Hlavní budova", 15)
#         player1.do_upgrade_building(1, "Tržiště", 18)
#         player1.do_upgrade_building(1, "Sýpka", 14)
#         #player1.do_upgrade_building(1, "Tržiště", 15)
#         #player1.do_upgrade_building(2, "Tržiště", 8)
#
#         #player1.do_upgrade_building(2, "Mlýn", 3)
#         player1.do_upgrade_building(2, "Sýpka", 16)
#         player1.do_upgrade_building(2, "Hlavní budova", 10)
#         player1.do_upgrade_building(2,"Sklad surovin", 13)
#         player1.do_upgrade_building(2, "Tržiště",10)
#
#         player1.upgrade_tile(2)
#         #player1.do_upgrade_building("Rezidence", 10)
#         # player1.upgrade_tile(["Obilné pole"])
#         #player1.do_upgrade_building("Hlavní budova", 10)
#         #player1.do_upgrade_building("Akademie", 10)
#         #player1.do_upgrade_building("Sýpka", 13)
#         #player1.do_upgrade_building("Sklad surovin", 13)
#         #player1.do_upgrade_building("Sýpka", 4)
#         #player1.do_upgrade_building("Main Building", 5)
#         #player1.do_upgrade_building("Barracks", 3)
#         #player1.do_upgrade_building("Granary", 4)
#         #player1.upgrade_tile()
#
#     except:
#         pass
#     try:
#         time_to_wait = player1.driver.find_element_by_css_selector("div.buildDuration").text[0:5]
#         time_to_wait = time_to_wait + "59" if (time_to_wait[-1] == ":") else time_to_wait+ ":59"
#     except:
#         print("Nothing beeing upgraded")
#         time_to_wait = "00:25:00"
#     print("Time sleeping approximately: " + time_to_wait)
#     pt = datetime.datetime.strptime(time_to_wait.strip(),'%H:%M:%S')
#     time_to_wait = pt.second+pt.minute*60+pt.hour*3600
#     time.sleep(max(time_to_wait,30) + random.randint(0,10))
