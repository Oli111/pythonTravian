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

    @switch_to_hero_adventures
    def get_avaiblable_adventures(self):
        pass

    @switch_to_hero_adventures
    def go_to_hero_adventure(self):
        adventure_link = self.driver.find_element_by_class_name("gotoAdventure").get_attribute("href")
        self.driver.get(adventure_link)
        button_adventure = self.driver.find_element_by_class_name("startAdventure")
        button_adventure.click()

    @switch_to_dorf1
    def create_data_frame_available_upgrades(self):
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
        _data_pd.to_csv("upgrades.csv", index = False, encoding = "UTF-8")


    def do_trade_on_auctions(self):
        pass

    def do_send_autoattacks(self):
        pass


    @switch_to_dorf2
    def create_data_frame_available_buildings(self):
        """
        We are checking for already built buildings and their levels.


        :return:
        """
        print("Creating list of avaible buildings..")
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
            building_names.append(strings_in_the_header[0])
            level_of_the_building = 0 if len(strings_in_the_header)==1 else (int(strings_in_the_header[1]))
            building_levels.append(level_of_the_building)

        data_buildings_dorf2 = pd.DataFrame({"building_name":building_names,
                                             "building_url": building_urls,
                                             "building_level":building_levels})


        data_buildings_dorf2.to_csv("data_buildings_dorf2.csv", index=False, encoding = "utf-8")

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
    def do_upgrade_building(self, building_to_upgrade: str, to_level: int):
        """
        Prerequisities: Only one building in village
        TODO:
        """
        df_buildings_built = pd.read_csv("data_buildings_dorf2.csv", encoding = "UTF-8")
        df_buildings_built = df_buildings_built.sort_values('building_level')
        # print(df_buildings_built.columns)
        building_row = df_buildings_built[(df_buildings_built['building_name'] == building_to_upgrade) & (df_buildings_built['building_level'] <20)]

        currently_beeing_upgraded = self.get_currently_beeing_upgraded_buildings()
        if currently_beeing_upgraded.shape[0] == 0:
            _flag_can_upgrade_building = True
        elif currently_beeing_upgraded[currently_beeing_upgraded['upgrade_type']=='building'].shape[0] == 0:
            _flag_can_upgrade_building = True
        else:
            print("Already upgrading some building.")
            _flag_can_upgrade_building = False
        if building_row.shape[0] ==0:
            print("Building " + building_to_upgrade + " is not built, or has level 20. We should retry running list of built buildings.")
        elif _flag_can_upgrade_building:

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
                    # upgrade_time = self.driver.find_element_by_css_selector('div.upgradeButtonsContainer div.section1 inlineIcon').text[0:5]
                    # print(upgrade_time)
                    print("Upgrading building" )
                    df_buildings_built[df_buildings_built["building_url"] == url_building]['building_level'] = df_buildings_built[df_buildings_built["building_url"] == url_building]['building_level'] +1
                    df_buildings_built.to_csv("data_buildings_dorf2.csv", index=False, encoding = "UTF-8")
                    # upgrade_time = upgrade_time.second+upgrade_time.minute*60+upgrade_time.hour*3600
                    # self.time_to_wait = max(self.time_to_wait, 300)
                else:
                    print("Can not upgrade , not enough resources")
            else:
                print("Level already reached.")
        else:
            print("Already upgrading a building ...")

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
    def upgrade_tile(self, do_not_upgrade=None):
        """

        :type do_not_upgrade: list of field types not to upgrade
        """
        if do_not_upgrade is None:
            do_not_upgrade = []
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
            _data_upgrades = pd.read_csv("upgrades.csv", encoding = "UTF-8")
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




player1 = TravianPlayer("Olie", "mu694ek","https://ts20.czsk.travian.com/")

#player1 = TravianPlayer("Olie", "mu694ek","https://ts8.anglosphere.travian.com/")


player1.login()
# player2.login()
#player1.do_build_new_building("City Wall")
# player1.create_data_frame_available_buildings()
#player1.do_upgrade_building("Main Building", 3)
#player1.upgrade_tile("Obilné pole")
#player1.create_data_frame_available_buildings()
# player1.create_data_frame_available_buildings()
# player1.go_to_hero_adventure()

# print(player1.driver.find_element_by_css_selector("div.buildDuration").text)
# print(player1.driver.find_element_by_css_selector("div.name").text)

#
player1.create_data_frame_available_buildings()
while True:
    print("Checking available upgrades")
    try:
        # player1.do_upgrade_building("Rezidence", 10)
        print("Trying to upgrade tile")
        # player1.do_upgrade_building("Úkryt", 10)
        player1.do_upgrade_building("Tržiště", 10)
        #player1.do_upgrade_building("Rezidence", 10)
        #player1.upgrade_tile(["Obilné pole"])
        player1.do_upgrade_building("Hlavní budova", 10)
        #player1.do_upgrade_building("Main Building", 5)
        #player1.do_upgrade_building("Barracks", 3)
        #player1.do_upgrade_building("Granary", 4)
        player1.upgrade_tile()
    except:
        pass
    try:
        time_to_wait = player1.driver.find_element_by_css_selector("div.buildDuration").text[0:5]
        time_to_wait = time_to_wait + "00" if (time_to_wait[-1] == ":") else time_to_wait+ ":00"
    except:
        print("Nothing beeing upgraded")
        time_to_wait = "00:04:00"
    print("Time sleeping approximately: " + time_to_wait)
    pt = datetime.datetime.strptime(time_to_wait.strip(),'%H:%M:%S')
    time_to_wait = pt.second+pt.minute*60+pt.hour*3600
    time.sleep(max(time_to_wait,30) + random.randint(0,10))
