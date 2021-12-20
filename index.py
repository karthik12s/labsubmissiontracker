from flask import Flask,redirect,render_template,url_for,request
import requests
import json
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import datetime
import os
import ssl
os.environ['TZ'] = 'Asia/Kolkata' # set new timezone
time.tzset()
time.localtime()
from pymongo import MongoClient
client = MongoClient("mongodb+srv://admin:bzhandles@datastore.rzoau.mongodb.net/myFirstDatabase&retryWrites=true&w=majority",ssl_cert_reqs=ssl.CERT_NONE)

app = Flask(__name__)

def getLeetcode(name):
  try:
    headers = {
          "content-type": "application/json",
          "origin": "https://leetcode-cn.com",
          "referer": "https://leetcode-cn.com/problemset/all/"
      }
    query = {
      "operationName": "getUserProfile",
      "variables": {
        "username": name
      },
      "query": "query getUserProfile($username: String!) {\n  allQuestionsCount {\n    difficulty\n    count\n    __typename\n  }\n  matchedUser(username: $username) {\n    username\n    socialAccounts\n    githubUrl\n    contributions {\n      points\n      questionCount\n      testcaseCount\n      __typename\n    }\n    profile {\n      realName\n      websites\n      countryName\n      skillTags\n      company\n      school\n      starRating\n      aboutMe\n      userAvatar\n      reputation\n      ranking\n      __typename\n    }\n    submissionCalendar\n    submitStats: submitStatsGlobal {\n      acSubmissionNum {\n        difficulty\n        count\n        submissions\n        __typename\n      }\n      totalSubmissionNum {\n        difficulty\n        count\n        submissions\n        __typename\n      }\n      __typename\n    }\n    badges {\n      id\n      displayName\n      icon\n      creationDate\n      __typename\n    }\n    upcomingBadges {\n      name\n      icon\n      __typename\n    }\n    activeBadge {\n      id\n      __typename\n    }\n    __typename\n  }\n}\n"
    }
    response = requests.post("https://leetcode.com/graphql", headers=headers, data=json.dumps(query))
    data = json.loads(response.text)
    return int(data['data']['matchedUser']['submitStats']['acSubmissionNum'][0]['count'])
  except:
    return 0


def getHackerrank(name):
  try:
    agent = {"User-Agent":'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.115 Safari/537.36'}
    response = requests.get("https://www.hackerrank.com/rest/hackers/"+name+"/badges", headers = agent)
    data = response.json()
    # print(data['models'][2]['solved'])
    s = 0
    for i in range(len(data['models'])):
      s+= int(data['models'][i]['solved'])
    return s
  except:
    return 0

def getCodechef(name):
  try:
    r = requests.get('https://www.codechef.com/users/'+name)
    soup = BeautifulSoup(r.content, 'html.parser')
    s = soup.find('section', class_='rating-data-section problems-solved')
    soup1 = BeautifulSoup(str(s))
    s1 = soup1.find('h5')
    solved = s1.contents[0]
    return int(solved.split('(')[-1][:-1])
  except:
    return 0


def getCodeforces(name):
  try:
    r = requests.get('https://codeforces.com/profile/'+name)
    soup = BeautifulSoup(r.content, 'html.parser')
    s = soup.find('div', class_='_UserActivityFrame_counterValue')
    soup1 = BeautifulSoup(str(s))
    s1 = soup1.find('h5')
    return int(s.contents[0].split()[0])
  except:
    return 0


def getVjudge(name):
  try:
    r = requests.get("https://vjudge.net/user/"+name)
    soup = BeautifulSoup(r.content, 'html.parser')
    s = soup.find_all('td')
    s1 = s[3]
    soup1 = BeautifulSoup(str(s1))
    s1 = soup1.find('a')
    return(int(s1.contents[0]))
  except:
    return 0

def scrapesubmissions(l):
  l1 = []
  for i in l:
    d = {}
    d['VJudge'] = getVjudge(i['VJudge'])
    d['LeetCode'] = getLeetcode(i['LeetCode'])
    d['Codechef'] = getCodechef(i['CodeChef'])
    d['Codeforces'] = getCodeforces(i['Codeforces'])
    d['HackerRank'] = getHackerrank(i['HackerRank'])
    l1.append(d)
  return l1

@app.route("/scrape/<name>")
def scrape(name):
  batch = name
  db = client['SubmissionHandles']
  col = db['Time']
  flag = False
  for i in col.find():
    s = i
  if name not in s or time.time() - s[batch]<3600:
    return {"Status":"Failed"}
  db = client['SubmissionHandles']
  col = db['BZKLU1923P2']
  l = []
  for i in col.find({"TrainingSection":batch}):
    l.append(i)
  l1 = scrapesubmissions(l)
  a = datetime.date.today()
  date = str(a.day)+"-"+str(a.month)+"-"+str(a.year)
  t = time.localtime()
  t1 = time.time()
  c_time = str(t.tm_hour)+":"+str(t.tm_min)
  for i in range(len(l)):
    if 'submissions' not in l[i]:
      l[i]['submissions'] = {}
  for i in range(len(l)):
    if date in l[i]['submissions']: 
      l[i]['submissions'][date][c_time] = l1[i]
    else:
      l[i]['submissions'] = {date:{c_time:l1[i]}}
  for i in l:
    col.update_one({"UserName":i['UserName']},{"$set":{'submissions':i['submissions']}})
  col = db['Time']
  col.update_one({},{"$set":{batch:t1}})
  return {"Status":"Success"}

@app.route("/batch/<name>",methods = ['GET','POST'])
def loaddetails(name):
  db = client['SubmissionHandles']
  col = db['BZKLU1923P2']
  l = [] 
  for i in col.find({'TrainingSection':name}):
    l.append(i)
  submissions = l[0]['submissions']
  dates = [datetime.datetime.strptime(ts, "%d-%m-%Y") for ts in submissions]
  dates.sort()
  a = dates[-1]
  recent = str(a.day)+"-"+str(a.month)+"-"+str(a.year)
  l1 = sorted((time.strptime(d, "%H:%M") for d in submissions[recent]))
  recent_time = l1[-1]
  recent_time = str(recent_time.tm_hour) + ":"+ str(recent_time.tm_min)
  l2 = []
  date_time = []
  for i in dates:
      a = i
      i = str(a.day)+"-"+str(a.month)+"-"+str(a.year)
      timings = []
      for j in submissions[i]:
          timings.append(j)
          date_time.append(i+' '+j)
  if request.method == "POST":
    start = request.form["start"].split()
    end = request.form['end'].split()
    # return {'a':start,'b':end}
    l2 = []
    for i in l:
      i['submissions'][recent][recent_time]['Username'] = i['UserName']
      d = {}
      # print(list(i['submissions'][end[0]][end[1]]))
      d['Username'] = i['UserName']
      solved_count = 0
      for j in ['VJudge', 'LeetCode', 'Codechef', 'Codeforces', 'HackerRank']:
        d[j] = int(i['submissions'][end[0]][end[1]][j])-int(i['submissions'][start[0]][start[1]][j])
        solved_count+=int(i['submissions'][end[0]][end[1]][j])-int(i['submissions'][start[0]][start[1]][j])
      d['Solved_Count'] = solved_count
      l2.append(d)
    return render_template("batch.html",l = l2,name = name,recent_time = recent_time,recent_date = recent,flag = True,start = start,end = end,date_time = date_time)
  for i in l:
    i['submissions'][recent][recent_time]['Username'] = i['UserName']
    solved_count = 0
    for j in ['VJudge', 'LeetCode', 'Codechef', 'Codeforces', 'HackerRank']:
      solved_count += i['submissions'][recent][recent_time][j]
    i['submissions'][recent][recent_time]['Solved_Count'] =solved_count
    l2.append(i['submissions'][recent][recent_time])
  print(recent,recent_time)
#   return {"timings":date_time,"submissions":l2}
  return render_template("batch.html",l = l2,name = name,recent_time = recent_time,recent_date = recent,flag = False,date_time = date_time)

@app.route("/")
def home():
    return render_template("home.html",d = ["B1","B2","B3","B4"])


if __name__ == "__main__":
    app.run(debug=True)