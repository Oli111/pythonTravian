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
# level_translation = " Úroveň "
# done_translation = " hod. Hotovo v "
# village_center = "Centrum"
# fields_types = ["Dřevorubec", "Hliněný důl", "Železný důl", "Obilné pole"]
driverPathLocale = "d:\chromeDriver\chromedriver.exe"

# EN
#
level_translation = " Level "
village_center = "Buildings"
fields_types = ["Woodcutter", "Clay Pit", "Iron Mine", "Cropland"]
done_translation = " hrs. done at "
construct_new_building_translation = "Construct new building"

class TravianPlayer(object):
    def __init__(self, username, password, server):
        options = webdriver.ChromeOptions()
        options.add_argument('headless')
        self.username = username
        self.password = password
        self.server = server
        self.driver = webdriver.Chrome(driverPathLocale, chrome_options=options)
        self.time_to_wait = 0
        self.wait_to_send_fl = time.localtime()

    def login(self):
        """
        Will login to the server with the given username and password.
        :return: None
        """
        self.driver.get(self.server + "dorf1.php")
        self.driver.find_element_by_name('name').send_keys(self.username)
        self.driver.find_element_by_name('password').send_keys(self.password)
        self.driver.find_element_by_name("s1").click()


    def switch_to_dorf1(func):
        """
        If not url on the tiles page then we swtich to the tiles.
        :return:
        """
        def switch(self, *args, **kwargs):
            if ("dorf1.php" not in self.driver.current_url) or (self.driver.current_url[-1]=="#"):
                self.driver.get(self.server + "dorf1.php")
            return func(self, *args, **kwargs)
        return switch

    def switch_to_dorf2(func):
        """
        switches to the city centre.
        :return:
        """
        def switch(self, *args, **kwargs):
            if "dorf2" not in self.driver.current_url:
                self.driver.get(self.server + "dorf2.php")
            return func(self, *args, **kwargs)
        return switch

    def switch_to_hero_adventures(self):
        if "hero.php?t=3" not in self.driver.current_url:
            self.driver.get(self.server + "hero.php?t=3")


    def switch_to_hero(func):
        def switch(self, *args, **kwargs):
            if "hero.php?t=3" not in self.driver.current_url:
                self.driver.get(self.server + "hero.php")
            return func(self, *args, **kwargs)
        return switch

    def get_villages_information(self):
        """
        :return: pd.DataFrame with columns village_id, village_name, village_link
        """
        anchor = self.driver.find_element_by_css_selector("#sidebarBoxVillagelist")
        anchor = anchor.find_elements_by_css_selector("a")
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
        time.sleep(random.randint(1,10))
        return(power)

    def go_to_hero_adventure(self, village_id: int, _at_least_health: int = 20):
        _hero_health = self.get_hero_health()
        self.switch_to_village(village_id)
        self.switch_to_hero_adventures()
        _flag_hero_has_enough_health = _at_least_health < _hero_health
        if not(_flag_hero_has_enough_health):
            print("Not going to adventure: Hero has less than " + str(_hero_health) + "% health.")
            return
        _flag_are_there_adventures = len(self.driver.find_elements_by_class_name("gotoAdventure"))>0
        if not(_flag_are_there_adventures):
            print("No available adventures.")
            return
        adventure_link = self.driver.find_element_by_class_name("gotoAdventure").get_attribute("href")
        if adventure_link is None:
            print("Not going for adventure: Hero not in the village.")
            return
        self.driver.get(adventure_link)
        button_adventure = self.driver.find_element_by_class_name("startAdventure")
        button_adventure.click()
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


    def switch_to_auctions(func):
        """
        Decorator. Refreshes auctions.
        """
        def switch(self, *args, **kwargs):
            self.driver.get("https://ts20.czsk.travian.com/hero.php?t=4")
            return func(self, *args, **kwargs)
        return switch


    def do_trade_on_auctions(self):
        pass

    def do_send_autoattacks(self):
        pass



    @switch_to_dorf2
    def create_data_frame_available_buildings(self, village_id: int):
        """
        We are checking for already built buildings and their levels.
        TODO: what if we build a new building manualy

        :return:
        """
        self.switch_to_village(village_id)
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
        list_iter_temp = [i for i in range(18,41)]

        for i in range(18,41):
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
    def do_build_new_building(self, village_id, building_to_build: str):
        """
        City Wall has to be id 40
        Case for cranny not done (can be level 10 only)
        :return:
        """
        self.switch_to_village(village_id)
        print("Attempting to build a new building " + building_to_build)
        # find
        path = "build.php?id="


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
        time.sleep(random.randint(1,10))
        _flag_scan_run_already = False
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
                    print("No such building in the village to upgrade.")
                    return
            else:
                print("No such building in the village to upgrade.")
                return



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
                print("Upgrading building " + building_to_upgrade)
                upgrade_button.click()

                print("Updating data ... ")
                df_buildings_built_raw = pd.read_csv("data_buildings_in_centrum.csv", encoding="UTF-8")
                df_buildings_built_raw.loc[(df_buildings_built_raw.building_url == url_building) &
                                       (df_buildings_built_raw.village_id == village_id),'building_level'] = current_level_building + 1
                df_buildings_built_raw.to_csv("data_buildings_in_centrum.csv", index = False, encoding="UTF-8")
            else:
                print(building_to_upgrade + ": Can not upgrade , not enough resources")
        else:
            print(building_to_upgrade + ": Level already reached.")

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
            upgrade_button = self.driver.find_elements_by_css_selector('div.upgradeButtonsContainer div.section1 button')
            if len(upgrade_button)==0:
                print("Already upgrading to level 10")
                return
            upgrade_button = upgrade_button[0]
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
    time.sleep(10)

    @switch_to_dorf1
    def get_currently_beeing_upgraded_buildings(self) -> pd.DataFrame:
        bookmark = self.driver.find_elements_by_css_selector('h5')
        if len(bookmark)>0:
            bookmark = bookmark[0].find_element_by_xpath('../ul')
            build_duration_divs = bookmark.find_elements_by_css_selector("div.buildDuration")
            built_names_divs = bookmark.find_elements_by_css_selector("div.name")

            upgraded_name = list(map(lambda x: x.text.split(level_translation)[0], built_names_divs))

            upgrade_type = list(map(lambda x: "field" if (x in fields_types) else "building",upgraded_name))
            data_temp = {"building": upgraded_name,
                         "upgrade_type":upgrade_type}
            data_return = pd.DataFrame(data_temp)

            return data_return
        else:
            data_temp = {"building":[], "time_to_finish":[], "time_to_finish_seconds":[],"upgrade_type":[]}
            return pd.DataFrame(data_temp)


    def switch_to_gather_point(self):
        self.driver.get(self.server + "build.php?tt=99&id=39")

    def do_open_farmlist(self, farmlist_id):
        switchs_to_click = self.driver.find_elements_by_xpath("*//div[@class='openedClosedSwitch switchClosed']")
        switch_to_click = switchs_to_click[farmlist_id-2]
        switch_to_click.click()

    def do_send_farm_list(self, village_id, farmlist_id=1):

        print("Tryinh to send fl for village id " + str(village_id) + " farmlist. " +  str(farmlist_id))
        self.switch_to_village(village_id)
        time.sleep(random.randint(1, 4))
        self.switch_to_gather_point()
        time.sleep(random.randint(3,6))
        if farmlist_id>1:
            try:
                self.do_open_farmlist(farmlist_id)
            except:
                print("Probably not enough farmlists in the village.")
                return
        time.sleep(random.randint(3, 6))
        anchors = self.driver.find_elements_by_xpath("*//div[@class='markAll']/input[@type='checkbox']")
        print("number of checkboxes " + str(len(anchors)))
        anchor  = anchors[min(farmlist_id-1, len(anchors)-1)]
        # anchor = anchor.find_element_by_class_name('markAll')
        time.sleep(3)
        anchor.click()
        time.sleep(random.randint(3, 6))
        anchors = self.driver.find_elements_by_xpath("*//button[@type='submit']")
        print("number of checkboxes " + str(len(anchors)))
        anchor  = anchors[min(farmlist_id-1, len(anchors)-1)]

        anchor.click()
        time.sleep(5)

    def do_check_if_attacks_incomming(self, village_id):
        self.switch_to_village(village_id)
        attacks = self.driver.find_elements_by_xpath("*//img[@class='att2']/@src")

    def do_send_troops(self,
                       from_village_id:int,
                       unit_type_id:int,
                       number_of_units:int,
                       attack_type_id:int,
                       coordinates:list
                       ):

        self.switch_to_village(from_village_id)

        self.driver.get(self.server + "build.php?gid=16#td")
        time.sleep(random.randint(1,3))
        self.driver.get(self.server + "build.php?tt=2&id=39")
        _to_input = self.driver.find_element_by_xpath(f"*//input[@name='t{unit_type_id}']")
        _to_input.send_keys(number_of_units)
        _attack_type_button = self.driver.find_elements_by_xpath("*//input[@class='radio']")[attack_type_id-1]
        _attack_type_button.click()
        try:
            self.driver.find_element_by_xpath("*//input[@id='xCoordInput']").send_keys(coordinates[0])
            self.driver.find_element_by_xpath("*//input[@id='yCoordInput']").send_keys(coordinates[1])
            time.sleep(1)
            button = self.driver.find_element_by_xpath("*//button[@id='btn_ok']")
            button.click()
            time.sleep(1)
            self.driver.find_element_by_xpath("*//button[@id='btn_ok']").click()
        except:
            print("sending unssuccesful")

    @switch_to_auctions
    def do_try_to_buy_on_auctions(self, comodity: str, max_silver_per_one: float):
        """

        :param comodity: name of the comodity to buy.
        :param max_silver_per_one: Maximum amount of silver for one comodity.
        :return: Places a bid for the comodity based on maximum amount.
        """
        def invest (_url:str, invest_amount:int):
            """
            :param _url: href Url for the button for investing.
            :param invest_amount: amount of silver to invest
            """

            self.driver.get(_url)
            anchor2 = player1.driver.find_element_by_class_name("auctionDetails")
            anchor2.find_element_by_name("maxBid").send_keys(str(invest_amount))
            time.sleep(random.int(1,2))
            actualy_invested = int(anchor2.find_element_by_name("maxBid").get_attribute("text"))
            if actualy_invested <= invest_amount:
                print("Actualy investing")
                self.driver.find_element_by_css_selector("div.submitBid").click()
            else:
                print("Not investing due to bugs")

        df_settings = pd.DataFrame({"name": [comodity],
                                    "max_cost": [max_silver_per_one]})
        anchor = player1.driver.find_element_by_css_selector("table")
        bid_buttons = anchor.find_elements_by_class_name("bidButton")
        bid_buttons_urls = list(map(lambda x: x.get_attribute("href"), bid_buttons))
        _time_to_end_auction = anchor.find_elements_by_class_name("timer")
        _time_to_end_auction_list = list(map(lambda x: int(x.get_attribute("value")), _time_to_end_auction))
        _silver_cost = anchor.find_elements_by_class_name("silver")
        _silver_cost.pop(0)
        _silver_cost.pop(0)
        _silver_cost_list = list(
            map(lambda x: int(x.get_attribute("innerHTML").strip("\n\t\t\t").strip("\t\t\t")), _silver_cost))

        _name_of_product = anchor.find_elements_by_class_name("name")
        _name_of_product_list = list(
            map(lambda x: x.get_attribute("innerHTML").strip("\n\t\t\t\t\u202d\u202d").replace("\u202c", ""),
                _name_of_product))
        _name_of_product_list.pop(0)
        if (len(bid_buttons_urls) == len(_time_to_end_auction_list)):
            _df_auctions = pd.DataFrame({"name": list(map(lambda x: x.split("×")[1].strip(),_name_of_product_list)),
                             "amount":list(map(lambda x: int(x.split("×")[0]),_name_of_product_list)),
                             "url": bid_buttons_urls,
                             "time_to_end": _time_to_end_auction_list,
                             "cost":_silver_cost_list
                            })
            _df_auctions['cost_per_one'] = _df_auctions.apply(lambda x: x['cost']/x['amount'],1)
            _df_auctions = _df_auctions.merge(df_settings, on = "name")
            _df_auctions.sort_values('cost_per_one', inplace = True)
            _df_to_buy = _df_auctions[_df_auctions.cost_per_one < max_silver_per_one]

            if _df_to_buy.shape[0] > 0:
                _df_to_buy = _df_to_buy.iloc[0, :]
                _url = _df_to_buy['url']
                _amount = int(_df_to_buy['amount'])
                _invest_amount_of_silver = _amount * max_silver_per_one
                try:
                    print("Investing into " + str(_amount) + " " + comodity + " " + str(_invest_amount_of_silver) + " of silver.")
                    invest(_url, _invest_amount_of_silver)
                except:
                    print("An error occured, while investing into " + comodity + ".")
            else:
                print("Nothing suitable for investing for " + comodity)
        else:
            print("For one of the bids, we don't have enough silver. Fix in the code needed for this case.")
    time.sleep(random.randint(3,10))

    def do_scan_territory(self,
        village_id = 2,
        farms_distance_from = 98,
        farms_distance_to = 120,
        base_village_x = -73,
        base_village_y = -98,
        scouts_number = 180):
        _df_villages_of_farms = pd.read_csv("_df_villages_of_farms.csv", encoding='UTF-8')
        _df_villages_of_farms['distance'] = _df_villages_of_farms.apply(lambda x: sqrt((x['coord_x'] - base_village_x)**2 + (x['coord_y'] - base_village_y)**2),1)
        _df_villages_of_farms.sort_values('distance',inplace=True)
        _df_villages_of_farms = _df_villages_of_farms[ (farms_distance_from < _df_villages_of_farms['distance']) &
                                                       (_df_villages_of_farms['distance']< farms_distance_to)]
        _df_villages_of_farms=_df_villages_of_farms.head(scouts_number)
        for index, row in _df_villages_of_farms.iterrows():
            print("Sending spies to " + row['player_name'])
            player1.do_send_troops(village_id, 4, 1, 3, [row['coord_x'], row['coord_y']])
            time.sleep(random.randint(2,10))


    def do_count_crop(self, village_id):
        self.switch_to_village(village_id)
        anchors = self.driver.find_element_by_xpath("*//li[@id='stockBarResource4']/div[@class='middle']/div[@class='barBox']/div[@id='lbar4']")
        style = anchors.get_attribute('style')
        _granary_fullness_perc = int(style.strip('width: |%;'))
        return _granary_fullness_perc

    def do_exchange_crop_for_resources(self, village_id):


        def do_redistribute_res(_times = 3):
            for i in range(_times):
                time.sleep(random.randint(1, 3))
                anchors = self.driver.find_element_by_xpath("*//input[@name='desired[3]']")
                anchors.clear()
                anchors.send_keys("0")
                time.sleep(random.randint(1, 3))
                anchors = self.driver.find_elements_by_xpath("*//button[@class ='gold ']")
                anchors_values = list(map(lambda x: x.get_attribute('value'), anchors))
                anchors = anchors[anchors_values.index('Distribute remaining resources.')]
                # print(anchors_values)
                # time.sleep(random.randint(5, 6))
                anchors.click()

        self.switch_to_village(village_id)
        data_buildings_done = pd.read_csv("data_buildings_in_centrum.csv", encoding="utf-8")
        _url_marketplace = data_buildings_done[(data_buildings_done['village_id']==village_id) & (data_buildings_done['building_name']=='Marketplace')]['building_url'].iloc[0]
        self.driver.get(_url_marketplace)

        anchors = self.driver.find_elements_by_xpath("*//div[@class='npcMerchant']/button[@class='gold ']")[0]
        anchors.click()

        do_redistribute_res()
        time.sleep(random.randint(5, 8))
        anchors = self.driver.find_elements_by_xpath("*//button[@class ='gold ']")
        anchors_values = list(map(lambda x: x.get_attribute('value'), anchors))
        anchors = anchors[anchors_values.index('Redeem')]
        anchors.click()











from config import login_config
from math import sqrt

player1 = TravianPlayer(login_config["username"], login_config["password"],login_config["server"])
player1.login()

timetosendfl = datetime.datetime.now()
timetosendfl = timetosendfl + datetime.timedelta(seconds=1)


player1.do_scan_territory(village_id = 3,
        farms_distance_from = 0,
        farms_distance_to = 130,
        base_village_x = -73,
        base_village_y = -98,
        scouts_number = 300)
#

#player1.create_data_frame_available_buildings(10)
while True:
    try:
        #player1.go_to_hero_adventure(2)
        crop_perc = player1.do_count_crop(village_id=2)
        if crop_perc > 98:
            player1.do_exchange_crop_for_resources(2)

        if timetosendfl < datetime.datetime.now():
            player1.do_send_farm_list(2, 1)
            player1.do_send_farm_list(2, 2)
            player1.do_send_farm_list(2, 3)
            player1.do_send_farm_list(2, 4)
            timetosendfl = timetosendfl + datetime.timedelta(seconds=2900)
            print("Next farmlist will be send at " + str(timetosendfl))

        player1.do_upgrade_building(2, "Warehouse", 19)
        player1.do_upgrade_building(3, "Rally Point", 15)
        player1.do_upgrade_building(3, "Warehouse", 19)
        player1.do_upgrade_building(3, "Granary", 19)

        player1.do_upgrade_building(6, "Warehouse", 19)




        player1.do_upgrade_building(8, "Marketplace", 15)
        player1.do_upgrade_building(8, "Granary", 19)
        player1.do_upgrade_building(8, "Sawmill", 5)
        player1.do_upgrade_building(8, "Bakery", 4)
        player1.do_upgrade_building(8, "Brickyard", 5)
        #player1.do_upgrade_building(8, "Academy", 20)
        #player1.do_upgrade_building(8, "Residence", 20)
        player1.do_upgrade_building(8, "Hero's Mansion", 10)
        player1.upgrade_tile(8)

        player1.do_upgrade_building(9, "Bakery", 4)

        #player1.do_upgrade_building(10, "Main Building", 15)
        #player1.do_upgrade_building(10, "Warehouse", 12)
        #player1.do_upgrade_building(10, "Granary", 12)
        player1.upgrade_tile(10)
        #player1.do_upgrade_building(10, "Residence", 10)
        player1.upgrade_tile(11)

    except:
        pass
    #try:
        # player1.do_try_to_buy_on_auctions("Klec", 15)
    #except:
        #print("An error while investing")
    try:
        player1.driver.get("https://ts5.travian.com/dorf1.php")
        time_to_wait = player1.driver.find_element_by_css_selector("div.buildDuration").text[0:5]
        time_to_wait = time_to_wait + "59" if (time_to_wait[-1] == ":") else time_to_wait+ ":59"
    except:
        print("Nothing beeing upgraded")
        time_to_wait = "00:40:00"
    print("Time sleeping approximately: " + time_to_wait)
    try:
        pt = datetime.datetime.strptime(time_to_wait.strip(),'%H:%M:%S')
    except:
        pt = datetime.datetime.strptime(time_to_wait.strip(), 'HH:%M:%S')
    time_to_wait = pt.second+pt.minute*60+pt.hour*3600
    time.sleep(min(time_to_wait,1200) + random.randint(0,300))
