from enum import unique
from selenium import webdriver
from selenium.webdriver.common import keys
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import re
import config
import requests
import json

class NoData_js(Exception):
    """Raised when cannot find data.js"""
    pass

class cambridge():
    def __init__(self) -> None:
        self.answers, self.data_dict, self.xml_queue, self.data_url = None, None, None, None
        self.driver = webdriver.Chrome(service = Service(ChromeDriverManager().install()))
        self.d = self.driver

    def log_in(self, login, password):
        self.d.get("https://www.cambridgeone.org/login?rurl=%2Fdashboard%2Flearner%2Fdashboard")
        self.waitLoad()
        login_field = self.d.find_element(By.XPATH, "/html/body/div[3]/div[2]/div/div[1]/div/div[2]/main/div[2]/div/div[1]/div[1]/div/div/div/div/div[2]/div/form/div[1]/div[2]/input")
        pass_field = self.d.find_element(By.XPATH, "/html/body/div[3]/div[2]/div/div[1]/div/div[2]/main/div[2]/div/div[1]/div[1]/div/div/div/div/div[2]/div/form/div[1]/div[3]/input")
        login_field.send_keys(login)
        pass_field.send_keys(password)
        self.d.find_element(By.XPATH, "/html/body/div[3]/div[2]/div/div[1]/div/div[2]/main/div[2]/div/div[1]/div[1]/div/div/div/div/div[2]/div/form/div[2]/div[1]/input").click()
        self.waitLoad()

    def find_data_js(self) -> str:
        input("waiting you...")
        self.waitLoad()
        main = self.d.page_source
        try:
            frame_obj = self.d.find_element(By.XPATH, "/html/body/app/div[2]/learner/product-view/div/div/main/div/lo-renderer/div[2]/div/activity-launch/div[1]/div/iframe")
            self.d.switch_to.frame(frame_obj)
            frame = self.d.page_source
            self.d.switch_to.default_content()
            urls = re.findall(r'(https?://\S+)', frame) # here are player.js, player.css and etc
            self.data_url = [u for u in urls if "data.js" in u][0].rstrip('></script><script')[:-1]
        except:
            raise NoData_js()
        return self.data_url
    

    def read_data_js(self, link = None) -> dict:
        try:
            if link is None:
                link = self.data_url
            js_str = requests.get(link).text
            json_str = js_str[js_str.find("{") : js_str.rfind("}") + 1]
            self.data_dict = json.loads(json_str)
            return self.data_dict
        except:
            return ""

    def get_xml_queue(self, json_dict = None) -> list:
        if json_dict is None:
            json_dict = self.data_dict
        self.xml_queue = []
        for i in ET.fromstring(json_dict['LearningObjectInfo.xml']).findall("screens/screen/name"):
            self.xml_queue.append(i.text)
        return self.xml_queue
    
    def get_answers(self, json_dict = None, xml_queue = None) -> list:
        if json_dict is None:
            json_dict = self.data_dict
        if xml_queue is None:
            xml_queue = self.xml_queue
        self.answers = []
        for test_num in range(len(xml_queue) - 1):
            xml = self.data_dict[xml_queue[test_num]]
            #ans = self.extract_answer_from_cdata(xml)
            #ans = self.extract_answer_from_xml(xml, xml_queue[test_num])
            ans = self.extract_answer_from_xml(xml)
            self.answers.append(ans)
        return self.answers

    def split_answers(self, answer) -> str:
        a = answer
        if a[0 : 2] == "1 ":
            a = a[2::]
            a = re.sub(r"\s\d\s", "\n", a)
        return a

    def extract_answer_from_xml(self, xml, f = None) -> list:
        if not f is None:
            with open(f, 'w') as f:
                f.write(xml)
        correct_response = []
        for i in re.findall(r"<correctResponse>(.+?)</correctResponse>", xml):
            correct_response.append(re.findall(r"<value>(.+?)</value>", i))
        inline_choice =  re.findall(r'<inlineChoice identifier="(.+?)">(.+?)</inlineChoice>', xml)
        simple_choice =  re.findall(r'<simpleChoice identifier="(.+?)">(.+?)</simpleChoice>', xml)
        gap_text = re.findall(r'<gapText matchMax=".+?" identifier="(.+?)" id="(.+?)" label=".+?">(.+?)</gapText>', xml)
        simple_ass_choice = re.findall(r'<simpleAssociableChoice matchMax=".+?" identifier="(.+?)" id="(.+?)">(.+?)</simpleAssociableChoice>', xml)
        
        if len(simple_ass_choice):
            for i in range(len(simple_ass_choice)):
                id = "T" + simple_ass_choice[i][1] + " " + simple_ass_choice[i][0]
                text = simple_ass_choice[i][2]
                simple_ass_choice[i] = (id, text)
        
        if len(gap_text):
            for i in range(len(gap_text)):
                id = gap_text[i][0] + " " + gap_text[i][1]
                text = gap_text[i][2]
                gap_text[i] = (id, text)
        variants = inline_choice + simple_choice + gap_text + simple_ass_choice
        answers = []
        if len(simple_choice):
            for j in range(len(correct_response[0])):
                for k in variants:
                    if k[0] == correct_response[0][j]:
                        answers.append([k[1]])
        elif len(simple_ass_choice):
            for j in range(len(correct_response[0])):
                for k in variants:
                    if k[0] == correct_response[0][j]:
                        answers.append([k[1]])
        elif len(gap_text):
            for j in range(len(correct_response[0])):
                for k in variants:
                    if k[0] == correct_response[0][j]:
                        answers.append([k[1]])
        elif len(variants):
            for i in range(len(correct_response)):
                t = []
                for j in range(len(correct_response[i])):
                    for k in variants:
                        if k[0] == correct_response[i][j]:
                            t.append(k[1])
                answers.append(t)
        else:
            answers = correct_response
        #print("variants", variants)
        #print("correct_responce", correct_response)
        #print("answers", answers)
        
        #print("simple_ass_choice", simple_ass_choice)
        #print("inline_choice", inline_choice)
        #print("simple_choice", simple_choice)
        #print("gap_text", gap_text)
        #print("variants", variants)
        #json.dump(xml, f)
        return answers

    def extract_answer_from_cdata(self, xml) -> str:
        a_str = xml
        try:
            a_str = a_str[a_str.find("<![CDATA[") + len("<![CDATA[")::]
            a_str = a_str[:a_str.find("</div>")]
            a_str = a_str.replace("&lt;", "<").replace("&bt;", ">")
            a_str = re.findall(r"<strong>(.+?)</strong>", a_str)[0]
            if str.find(a_str, "/>") != -1:
                a_str = a_str = a_str[a_str.find("/> ") + len("/> ")::]
                a_str = re.sub(r"<(.*)/>", '', a_str)
        except:
            return None
        else:
            return a_str.lstrip()
        
    def terminate(self) -> None:
        self.d.close()

    def waitLoad(self, timeout = 60) -> None:
        try:
            self.d.implicitly_wait(timeout)
        except TimeoutException:
            print("Loading took too much time!")

if __name__ == "__main__":
    c = cambridge()
    c.log_in(config.login, config.password)
    '''
    c.data_dict = json.load(open("data.json"))
    xml_queue = c.get_xml_queue()
    print(xml_queue)
    c.get_answers()
    exit()
    for i in c.answers:
        print("=============")
        print(i)
    exit()
    '''
    while True:
        try:
            c.find_data_js()
            c.read_data_js()
            with open('data.json', 'w') as f:
                json.dump(c.data_dict, f)
            xml_queue = c.get_xml_queue()
            print("Queue:", xml_queue)
            c.get_answers()
            
            for i in c.answers:
                print("=============")
                print(i)
            
        except NoData_js:
            print("Failed to find data.js on this page")
        except KeyboardInterrupt:
            c.terminate()
            break
        except:
            print("Strange exception!? Shut up fucking python!!!")
