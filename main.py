from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re
import config
import requests
import json

class cambridge():
    def __init__(self) -> None:
        self.driver = webdriver.Chrome(service = Service(ChromeDriverManager().install()))
        self.d = self.driver
        self.d.get("https://www.cambridgeone.org/login?rurl=%2Fdashboard%2Flearner%2Fdashboard")
        self.waitLoad()
        login_field = self.d.find_element(By.XPATH, "/html/body/div[3]/div[2]/div/div[1]/div/div[2]/main/div[2]/div/div[1]/div[1]/div/div/div/div/div[2]/div/form/div[1]/div[2]/input")
        pass_field = self.d.find_element(By.XPATH, "/html/body/div[3]/div[2]/div/div[1]/div/div[2]/main/div[2]/div/div[1]/div[1]/div/div/div/div/div[2]/div/form/div[1]/div[3]/input")
        login_field.send_keys(config.login)
        pass_field.send_keys(config.password)
        self.d.find_element(By.XPATH, "/html/body/div[3]/div[2]/div/div[1]/div/div[2]/main/div[2]/div/div[1]/div[1]/div/div/div/div/div[2]/div/form/div[2]/div[1]/input").click()
        self.waitLoad()
        
        
    def find_data_js(self) -> str:
        input("waiting you...")
        self.waitLoad()
        main = self.d.page_source
        '''
        with open('main.html', 'w') as f:
            f.write(self.d.page_source)
        '''
        self.d.switch_to.frame(self.d.find_element(By.XPATH, "/html/body/app/div[2]/learner/product-view/div/div/main/div/lo-renderer/div[2]/div/activity-launch/div[1]/div/iframe"))
        frame = self.d.page_source
        '''
        with open('frame.html', 'w') as f:
            f.write(self.d.page_source)
        '''
        self.d.switch_to.default_content()
        urls = re.findall(r'(https?://\S+)', frame) # here are player.js, player.css and etc
        self.data_url = [u for u in urls if "data.js" in u][0].rstrip('></script><script')[:-1]
        return self.data_url
        

    def read_data_js(self, link = None) -> str:
        try:
            if link is None:
                link = self.data_url
            js_str = requests.get(link).text
            self.json_str = js_str[js_str.find("{") : js_str.rfind("}") + 1]
            return self.json_str
        except:
            return ""
    def get_xml_queue(self, json_str = None) -> list:
        if json_str is None:
            json_str = self.json_str
        a = []
        for i in ET.fromstring(json.loads(json_str)['LearningObjectInfo.xml']).findall("screens/screen/name"):
            a.append(i.text)
        return a
    def terminate(self) -> None:
        self.d.close()

    def waitLoad(self, timeout = 60) -> None:
        try:
            self.d.implicitly_wait(timeout)
        except TimeoutException:
            print("Loading took too much time!")

if __name__ == "__main__":
    c = cambridge()
    while True:
        try:
            c.find_data_js()
            with open('data.js', 'w') as f:
                f.write(c.read_data_js())
            print(c.get_xml_queue())
        except KeyboardInterrupt:
            c.terminate()
            break
        except:
            print("Strange exception!? Shut up fucking python!!!")
