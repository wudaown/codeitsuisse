from django.shortcuts import render
from django.http import HttpResponse
import json
import logging
import time
import datetime
import math
from itertools import groupby
import queue
import re
import random
from django.shortcuts import redirect
import requests
from django.views.decorators.cache import cache_page

from .models import Greeting

runId = 0

logger = logging.getLogger(__name__)

# Create your views here.
def index(request):
	# return HttpResponse('Hello from Python!')
	return render(request, 'index.html')

def calculateemptyarea(request):
	body = request.body.decode('utf-8')
	data=json.loads(body)

	container = data["container"]
	cx = container["coordinate"]["X"]
	cy = container["coordinate"]["Y"]
	cw = container["width"]
	ch = container["height"]
	carea = cw * ch

	if "rectangle" in data:
		rectangle = data["rectangle"]
		rx = rectangle["coordinate"]["X"]
		ry = rectangle["coordinate"]["Y"]
		rw = rectangle["width"]
		rh = rectangle["height"]
		return HttpResponse(str(carea - recArea(cx,cy,cw,ch,rx,ry,rw,rh)), content_type='text/plain')
	elif "square" in data:
		square = data["square"]
		rx = square["coordinate"]["X"]
		ry = square["coordinate"]["Y"]
		rw = square["width"]
		return HttpResponse(str(carea - recArea(cx,cy,cw,ch,rx,ry,rw,rw)), content_type='text/plain')
	elif "circle" in data:
		logger.error(body)
		circle = data["circle"]
		cirx = circle["center"]["X"]
		ciry = circle["center"]["Y"]
		cirr = circle["radius"]
		return HttpResponse(str(carea - recCircleArea(cx,cy,cw,ch,cirx, ciry, cirr, carea)), content_type='text/plain')
	else:
		pass

def recArea(xa, ya, wa,ha, xb, yb, wb, hb):
	dx = min(xb + wb, xa + wa) - max(xa, xb)
	dy = min(ya + ha, yb + hb) - max(ya, yb)

	if dx >=0 and dy >= 0:
		return dx * dy
	return 0

def recCircleArea(xa,ya,wa,ha, xc, yc, rc, carea):
	if xc + rc <= xa or xc - rc >= xa + wa or yc + rc <= ya or yc - rc >= ya + ha: #外切
		return 0
	#内含
	if xc + rc <= xa + wa and xc - rc >= xa and yc + rc <= ya + ha and yc - rc >= ya:
		return math.pi * rc * rc

	inCircle = 0
	rsquare = rc * rc
	for i in range(10000):
		r1 = random.random()
		r2 = random.random()

		x1 = xa + wa * r1
		y1 = ya + ha * r2

		diffX = x1 - xc
		diffY = y1 - yc

		dis = diffX * diffX + diffY * diffY
		if dis < rsquare:
			inCircle+= 1

	return inCircle / 10000 * carea

def horseRacing(request):
	body = request.body.decode('utf-8')
	races = sorted(json.loads(body)["data"], key=lambda d: (d['racedate'], d['raceno'], int(d['Placing'])))
	if len(races) == 2229:
		logger.error(races)
	ans = {"q1": {}, "q2": {}, "q3": []}
	
	horse_wins = {}
	horse_score = {}
	jockey_wins = {}
	jockey_score = {}
	trainer_wins = {}
	trainer_score = {}

	for race in races:
		place = int(race["Placing"])
		horse = race["Horse"]
		trainer = race["Trainer"]
		jockey = race["jockeycode"]
		if place == 1:
			new_score = 7
			if horse in horse_score:
				new_score += horse_score[horse]
			new_val = 1
			if horse in horse_wins:
				new_val = horse_wins[horse] + 1
			
			horse_wins[horse] = new_val
			horse_score[horse] = new_score

			new_val = 1
			new_score = 7
			if trainer in trainer_score:
				new_score += trainer_score[trainer]
			if trainer in trainer_wins:
				new_val = trainer_wins[trainer] + 1

			trainer_wins[trainer] = new_val
			trainer_score[trainer] = new_score

			new_val = 1
			new_score = 7
			if jockey in jockey_score:
				new_score += jockey_score[jockey]
			if jockey in jockey_wins:
				jockey_wins[jockey] += 1

			jockey_wins[trainer] = new_val
			jockey_score[trainer] = new_score

		elif place == 2:
			new_score = 3
			if horse in horse_score:
				new_score += horse_score[horse]
			horse_score[horse] = new_score

			new_score = 3
			if trainer in trainer_score:
				new_score += trainer_score[trainer]
			trainer_score[trainer] = new_score

			new_score = 3
			if jockey in jockey_score:
				new_score += jockey_score[jockey]
			jockey_score[jockey] = new_score

		elif place == 3:
			new_score = 1
			if horse in horse_score:
				new_score += horse_score[horse]
			horse_score[horse] = new_score

			new_score = 1
			if trainer in trainer_score:
				new_score += trainer_score[trainer]
			trainer_score[trainer] = new_score

			new_score = 1
			if jockey in jockey_score:
				new_score += jockey_score[jockey]
			jockey_score[jockey] = new_score

	winHorse_c = 0
	winTrainer_c = 0
	winJockey_c = 0
	winHorse = ""
	winTrainer = ""
	winJackey = ""

	for horse, wins in horse_wins.items():
		if wins > winHorse_c:
			winHorse_c = wins
			winHorse = horse
	for trainer, wins in trainer_wins.items():
		if wins > winTrainer_c:
			winTrainer_c = wins
			winTrainer = trainer
	for jackey, wins in jockey_wins.items():
		if wins > winJockey_c:
			winJockey_c = wins
			winJackey = jackey
	ans["q1"] = {"horse": winHorse, "jockey": winJackey, "trainer": winTrainer}

	scoreHorse = 0
	maxHorse = ""
	scoreTrainer = 0
	maxTrainer = ""
	scoreJackey = 0
	maxJackey = ""

	for horse, score in horse_score.items():
		if score > scoreHorse:
			scoreHorse = score
			maxHorse = horse
	for trainer, score in trainer_score.items():
		if score > scoreTrainer:
			scoreTrainer = score
			maxTrainer = trainer
	for jackey, score in jockey_score.items():
		if score > scoreJackey:
			scoreJackey = score
			maxJackey = jackey
	ans["q2"] = {"horse": maxHorse, "jockey": maxJackey, "trainer": maxTrainer}

	if len(races) < 3:
		ans["q3"] = []
	else:
		jackyResults = []
		jackeyMap = {}
		jackeys = []
		for i in range(3):
			jackeys.append(races[i]["jockeycode"])

		middleRaceId = getRaceId(races[1])
		if getRaceId(races[0]) == middleRaceId and middleRaceId == getRaceId(races[2]):
			jackeyMap[",".join(jackeys)] = [middleRaceId]

		for i in range(3, len(races)):
			jackeys = jackeys[1:]
			jackeys.append(races[i]["jockeycode"].strip())
			raceid = getRaceId(races[i])

			jackySequence = ",".join(jackeys)
			if jackySequence in jackeyMap:
				raceSequence = jackeyMap[jackySequence]
				if raceSequence[-1] != raceid:
					raceSequence.append(raceid)
					if len(raceSequence) > 3:
						raceSequence = raceSequence[1:]
					if len(raceSequence) == 3:
						jackyResults.append({"jockeys": jackeys, "races": raceSequence})
					jackeyMap[jackySequence] = raceSequence
			else:
				jackeyMap[jackySequence] = [raceid]

		ans["q3"] = jackyResults

	return HttpResponse(json.dumps(ans), content_type='application/json')

def isSequentialRace(raceSequence):
	length = len(raceSequence)
	race1 = raceSequence[length-3].split(":")
	race2 = raceSequence[length-2].split(":")
	race3 = raceSequence[length-1].split(":")
	date1 = race1[0]
	date2 = race2[0]
	date3 = race3[0]
	id1 = int(race1[1])
	id2 = int(race2[1])
	id3 = int(race3[1])

	if date1 == date2 and date2 == date3:
		if id1 + 1 == id2 and id2 + 1 == id3:
			return True
	elif date2 == date3:
		if id2 + 1 == id3:
			return True
	elif date1 == date2:
		if id1 + 1 == id2:
			return True
	return False


def getRaceId(race):
	return race["racedate"] + ":" + race["raceno"]

def releaseSchedule(request):
	cv = ['A', '+0100', 'B', '+0200', 'C', '+0300', 'D', '+0400', 'E', '+0500', 'F', '+0600', 'G', '+0700', 'H',
		  '+0800',
		  'I', '+0900', 'K', '+1000', 'L', '+1100', 'M', '+1200', 'N', '-0100', 'O', '-0200', 'P', '-0300',
		  'Q', '-0400', 'R', '-0500', 'S', '-0600', 'T', '-0700', 'U', '-0800', 'V', '-0900', 'W', '-1000', 'X',
		  '-1100',
		  'Y', '-1200', 'Z', '+0000']
	idx = 0
	body = request.body.decode('utf-8')
	data = json.loads(body)


	n = data[0].split(';')
	krange = int(n[0])
	ans = []
	for i in range(0, 2 * krange+1):
		ans.append([0, 0])

	for i in range(0, len(cv), 2):
		if (cv[i] in n[1]):
			n[1] = n[1].replace(cv[i], cv[i + 1])
		if (cv[i] in n[2]):
			n[2] = n[2].replace(cv[i], cv[i + 1])

	start = datetime.datetime.strptime(n[1], "%d-%m-%Y %H:%M:%S.%f%z")
	end = datetime.datetime.strptime(n[2], "%d-%m-%Y %H:%M:%S.%f%z")

	# print(start.timestamp(),end.timestamp())
	start = start.timestamp()
	end = end.timestamp()

	if (krange == 0):
		return HttpResponse(str(end-start), content_type='text/plain')

	for i in range(1, krange + 1):
		tmp = data[i].split(';')
		for j in range(0, len(cv), 2):
			if (cv[j] in tmp[1]):
				tmp[1] = tmp[1].replace(cv[j], cv[j + 1])
			if (cv[j] in tmp[2]):
				tmp[2] = tmp[2].replace(cv[j], cv[j + 1])

		task_start = datetime.datetime.strptime(tmp[1], "%d-%m-%Y %H:%M:%S.%f%z")
		task_end = datetime.datetime.strptime(tmp[2], "%d-%m-%Y %H:%M:%S.%f%z")


		task_start=task_start.timestamp()
		task_end=task_end.timestamp()

		if (task_end <= start):
			task_end = start
		if (task_start<=start):
			task_start = start
		if (task_end >= end):
			task_end = end
		if (task_start >= end):
			task_start = end
		ans[idx][0] = task_start
		ans[idx][1] = 0  # start
		idx += 1
		ans[idx][0] = task_end
		ans[idx][1] = 1  # end
		idx += 1

	ans[idx][0]=end
	ans[idx][1]=0

	idx+=1
	ans.sort()
	cur = start
	out_put = 0.0
	count = 0
	for i in range(0, len(ans)):
		# if(ans[i][1]>end):
		#     break
		if (ans[i][1] == 0):  # start
			count += 1
			if count == 1:
				out_put = max(out_put, ans[i][0] - cur)
		else:
			count -= 1
			if (count == 0):
				cur = ans[i][0]
	# print(out_put)
	return HttpResponse(str(out_put), content_type='text/plain')


def db(request):

	greeting = Greeting()
	greeting.save()

	greetings = Greeting.objects.all()

	return render(request, 'db.html', {'greetings': greetings})

def heist(request):
	if request.method == 'POST':
		body = request.body.decode('utf-8')
		if body.find('{') == -1:
			return HttpResponse(json.dumps({"heist":0}), content_type='application/json')
		content = json.loads(body)
		r = 0
		maxWeight = content['maxWeight']
		vault = content['vault']
		unitValue = []
		for i in range(len(vault)):
			if(vault[i]['weight']==0):
					r+=vault[i]['value']
					continue
			unitValue.append([ float(vault[i]['value'])/float( vault[i]['weight'] ),vault[i]['weight']])

		unitValue =  sorted(unitValue,reverse=True)

		
		index = 0
		while (maxWeight > 0 and index < len(unitValue)):
			if maxWeight >= unitValue[index][1]:
				maxWeight -= unitValue[index][1]
				r += unitValue[index][0] * unitValue[index][1]
			else:
				r += unitValue[index][0] * maxWeight
				maxWeight = 0
			index = index + 1

		return HttpResponse(json.dumps({"heist":r}), content_type='application/json')
	return HttpResponse(json.dumps({"heist":0}), content_type='application/json')

@cache_page(60 * 15)
def sort(request):
    # return redirect("https://blooming-plains-39022.herokuapp.com/sort", permanent=True)
    #{[1,42,3,8]}
    data=[]
    flag=1
    idx=0
    while(idx<20):
        idx+=0
        try:
    	    flag=int(request.read(4))
            data.append(flag)
        except:
    	    pass
    # counter = [0] * 20010
    # for i in data:
    # 	counter[i+10000] += 1
    
    # ndx = 0
    # for i in range(len(counter)):
    # 	while 0 < counter[i]:
    # 		data[ndx] = i-10000
    # 		ndx += 1
    # 		counter[i] -= 1
    return HttpResponse(json.dumps(data), content_type='application/json')

# def countSort(aList):
# 	counter = [0] * 20010
# 	for i in aList:
# 		counter[i+10000] += 1
 
# 	ndx = 0
# 	for i in range(len(counter)):
# 		while 0 < counter[i]:
# 			aList[ndx] = i-10000
# 			ndx += 1
# 			counter[i] -= 1

def stringcompression(request, mode):
	body_unicode = request.body.decode('utf-8')
	data = json.loads(body_unicode)["data"]
	if mode == 'RLE':        
		return HttpResponse(str(rle(data)), content_type='text/plain')
	elif mode == 'LZW':
		return HttpResponse(str(lzw(data)), content_type='text/plain')
	elif mode == 'WDE':
		return HttpResponse(str(wde(data)), content_type='text/plain')
	else:
		pass

def rle(ch):
	xlen=len(ch)
	if(xlen == 0):
		return 0
	prev = '0'
	cnt=0
	ans=[]
	for i in range(0,xlen):
		if(ch[i] == prev):
			cnt+=1
		else:
			if(cnt == 0):
				prev = ch[i]
				cnt=1
			elif(cnt == 1):
				ans.append(prev)
				prev=ch[i]
				cnt=1
			else:
				ans.append(str(cnt))
				ans.append(prev)
				prev=ch[i]
				cnt=1
	if(cnt==1):
		ans.append(prev)
	else:
		ans.append(str(cnt))
		ans.append(prev)
	s=''.join(ans)
	#print(s,len(s))


	return len(s)*8

def lzw(ch):
	count=1
	xlen=len(ch)
	if(xlen == 0):
		return 0

	chdict={}
	for i in range(0,xlen):
		if(ch[i] not in chdict):
			chdict[ch[i]]=ord(ch[i])

	tmp_ch = ch[0]
	idx=256
	for i in range(1,xlen):
		if(tmp_ch+ch[i] not in chdict):
			chdict[tmp_ch+ch[i]] = idx
			count+=1
			#print(chdict[tmp_ch])
			idx +=1
			tmp_ch = ch[i]
		else:
			tmp_ch=tmp_ch+ch[i]
	count -= 1
	return count*12

def wde(ch):
	if(len(ch)==0):
		return 0
	non_char=0

	xlen=len(ch)
	idx=256
	tmp_ch=""
	chdict={}

	for i in range(0,xlen):
		if(ch[i].isalpha()):
			tmp_ch=tmp_ch+ch[i]
		else:
 #           print(ch[i])
			if(tmp_ch == ""):
				non_char+=1
				continue
			if(tmp_ch in chdict):
				chdict[tmp_ch][2]+=1
			else:
				chdict[tmp_ch]=[idx,8*len(tmp_ch),1]
				idx+=1
			non_char+=1
			tmp_ch=""

	if(not tmp_ch == ""):
		if (tmp_ch in chdict):
			chdict[tmp_ch][2] += 1
		else:
			chdict[tmp_ch] = [idx, 8 * len(tmp_ch), 1]
			idx += 1

	ans=non_char*12
	#print(chdict)
	for item in chdict:
		ans+=chdict[item][2]*12
		ans+=chdict[item][1]
		#print(item,chdict[item][2],chdict[item][1], chdict[item][2]*12+chdict[item][1])
	#print(non_char,ans)
	return ans

def trainPlanner(request):
	body_unicode = request.body.decode('utf-8')
	data = json.loads(body_unicode)
	destination = data["destination"]
	stations = data["stations"]

	graph = {}

	for station in stations:
		name = station["name"]
		passengers = int(station["passengers"])

		if name not in graph:
			graph[name] = {"neighbors": {}}
		graph[name]["passengers"] = passengers

		connections = station["connections"]
		for connection in connections:
			source = connection["station"]
			line = connection["line"]

			graph[name]["neighbors"][source] = line
			if source not in graph:
				graph[source] = {"neighbors": {}}
			graph[source]["neighbors"][name] = line

	minDis = {}
	minDis[destination] = {"dis": 0}
	q = queue.Queue()
	q.put({"station": destination, "dis": 0})


	while not q.empty():
		state = q.get()
		station = state["station"]
		dis = state["dis"]

		for neighbor in graph[station]["neighbors"]:
			nStation = neighbor
			if nStation in minDis and minDis[nStation]["dis"] > dis + 1:
				minDis[nStation] = {"from": station, "dis": dis + 1}
				q.put({"station": nStation, "dis": dis + 1})
			elif nStation not in minDis:
				minDis[nStation] = {"from": station, "dis": dis + 1}
				q.put({"station": nStation, "dis": dis + 1})

	q2 = queue.Queue()
	for station in graph:
		neighbors = graph[station]["neighbors"]
		curDis = minDis[station]["dis"]

		tail = True
		for neighbor in neighbors:
			dis = minDis[neighbor]["dis"]
			if curDis < dis:
				tail = False
		if tail:
			q2.put(station)

	maxPassenger = 0
	maxLine = ""
	reachVia = ""

	visited = set()
	while not q2.empty():
		station = q2.get()
		if station in visited:
			continue
		visited.add(station)

		dis = minDis[station]["dis"]
		passengers = graph[station]["passengers"]

		if dis == 1:
			if passengers > maxPassenger:
				maxPassenger = passengers
				reachVia = station
				maxLine = graph[destination]["neighbors"][station]
			continue
		fromStation = minDis[station]["from"]
		graph[fromStation]["passengers"] += passengers
		q2.put(fromStation)

	return HttpResponse(json.dumps({"line": maxLine, "totalNumOfPassengers": maxPassenger, "reachingVia": reachVia}), content_type='application/json')




def interact(request):
    data = {
    "team": "HS",
    "challenge": "Mini Exchange"
}
    headers = {'Content-type' : 'application/json'}
    sreq = requests.post('https://cis2017-coordinator-sg.herokuapp.com/api/evaluate', data=json.dumps(data),headers=headers)

    runId = json.dumps(sreq.text)
    return HttpResponse(json.dumps(runId), content_type='application/json')




def miniexchange(whatever):
    print(whatever)
    return HttpResponse(json.dumps(whatever))
#    body = whatever.body.decode('utf-8')
#    request = json.loads(body)
#    sod = request[0]
#    eod = request[-1]
#
#    request = request[1:-1]
#
#    border = []
#    sorder = []
#    morder = []
#    corder = []
#
#    for i in request:
#        morder.append(i)
#
#    morder.sort(key=lambda x: (x['messageId']))
#
#    for i in request:
#        if i['messageType'] == 'NEW':
#            if i['side'] == 'B':
#                border.append(i)
#            elif i['side'] == 'S':
#                sorder.append(i)
#        elif i['messageType'] == 'CANCEL':
#            corder.append(i)
#
#    for i in sorder:
#        i['fills'] = []
#        i['openQuantity'] = i['quantity']
#        if 'price' not in i:
#            i['price'] = list(sod['closePrice'].values())[0]
#
#    for i in border:
#        i['fills'] = []
#        i['openQuantity'] = i['quantity']
#        if 'price' not in i:
#            i['price'] = list(sod['closePrice'].values())[0]
#
#    sorder.sort(key=lambda x: (x['price'], x['orderId']), )
#    border.sort(key=lambda x: (x['price'], x['orderId']), reverse=True)
#
#    for i in morder:
#        if (i['messageType'] == 'NEW'):
#            newOrder(i, border, sorder)
#        if (i['messageType']) == 'CANCEL':
#            cancelOrder(i, border, sorder)
#        if (i['messageType'] == 'PRICE'):
#            amendPrice(i, border, sorder, i['price'])
#            for j in morder:
#                if (i['orderId'] == j['orderId']):
#                    if (j['messageType'] == 'NEW'):
#                        newOrder(j, border, sorder)
#
#    for i in border:
#        del i['messageId']
#        del i['messageType']
#        del i['orderType']
#
#    for i in sorder:
#        del i['messageId']
#        del i['messageType']
#        del i['orderType']
#
#    finorder = border + sorder
#    result = []
#    for i in finorder:
#        result.append(i)
#
#    fin = {"runId" : runId,
#           "result" : result}
#
#
#    headers = {'Content-type' : 'application/json'}
#    print(runId)
#    # return HttpResponse(json.dumps(fin),content_type='application/json')
#    return  requests.post('https://cis2017-coordinator-sg.herokuapp.com/api/evaluate/result',data=json.dumps(fin),headers=headers)

def amendPrice(order, border, sorder, price):
    for i in border:
        if i['orderId'] == order['orderId']:
            i['price'] = price
            border.insert(len(border), border.pop(border.index(i)))
            break

    for i in sorder:
        if i['orderId'] == order['orderId']:
            i['price'] = price
            sorder.insert(len(sorder), sorder.pop(sorder.index(i)))
            break


def cancelOrder(order, border, sorder):
    for i in border:
        if i['orderId'] == order['orderId']:
            i['state'] = "CANCELLED"
            break

    for i in sorder:
        if i['orderId'] == order['orderId']:
            i['state'] = "CANCELLED"
            break


def newOrder(order, border, sorder):
    if order['side'] == 'B':
        for i in sorder:
            if order['orderType'] == 'MKT':
                bs(order, i, i['price'])
            else:
                if i['orderType'] == 'MKT':
                    bs(order, i, order['price'])
                elif order['price'] >= i['price']:
                    bs(order, i, i['price'])
                    # if order['quantity'] >= 0:
                    #     if order['quantity'] >= i['quantity']:
                    #         order['fills'] = [{
                    #             "orderId": i['orderId'],
                    #             "price": i['price'],
                    #             "quantity": i['quantity']
                    #         }]
                    #         order['quantity'] -= i['quantity']
                    #         i['quantity'] = 0
                    #     else:
                    #         order['fills'] = [{
                    #             "orderId": i['orderId'],
                    #             "price": i['price'],
                    #             "quantity": order['quantity']
                    #         }]
                    #         i['quantity'] -= order['quantity']
                    #         order['quantity'] = 0

    if order['side'] == 'S':
        for i in border:
            if order['orderType'] == 'MKT':
                bs(order, i, i['price'])
            else:
                if i['orderType'] == 'MKT':
                    bs(order, i, order['price'])
                elif order['price'] <= i['price']:
                    bs(order, i, order['price'])
                    # if order['price'] >= i['price']:
                    #     if order['quantity'] >= 0:
                    #         if order['quantity'] >= i['quantity']:
                    #             order['fills'] = [{
                    #                 "orderId": i['orderId'],
                    #                 "price": i['price'],
                    #                 "quantity": i['quantity']
                    #             }]
                    #             order['quantity'] -= i['quantity']
                    #             i['quantity'] = 0
                    #         else:
                    #             order['fills'] = [{
                    #                 "orderId": i['orderId'],
                    #                 "price": i['price'],
                    #                 "quantity": order['quantity']
                    #             }]
                    #             i['quantity'] -= order['quantity']
                    #             order['quantity'] = 0

                    # return order


def bs(lorder, rorder, price):
    if lorder['openQuantity'] >= 0:
        if lorder['openQuantity'] >= rorder['openQuantity']:
            if (len(lorder['fills']) > 0):
                if (rorder['orderId'] not in lorder['fills'][0]['orderId']):
                    lorder['fills'].append(fillinfo(rorder['orderId'], price, lorder['openQuantity']))
            else:
                lorder['fills'].append(fillinfo(rorder['orderId'], price, lorder['openQuantity']))
                # lorder['fills'] = [
                # {
                # "orderId": rorder['orderId'],
                # # "price": rorder['price'],
                # "price" : price,
                # "quantity": rorder['quantity']
            # }
            # ]
            lorder['openQuantity'] -= rorder['openQuantity']
            rorder['openQuantity'] = 0
            statecheck(lorder)
            statecheck(rorder)
        else:
            if (len(lorder['fills']) > 0):
                if (rorder['orderId'] not in lorder['fills'][0]['orderId']):
                    lorder['fills'].append(fillinfo(rorder['orderId'], price, lorder['openQuantity']))
            else:
                lorder['fills'].append(fillinfo(rorder['orderId'], price, lorder['openQuantity']))
            # lorder['fills'] = [{
            #     "orderId": rorder['orderId'],
            #     "price" : price,
            #     # "price": rorder['price'],
            #     "quantity": lorder['quantity']
            # }]
            rorder['openQuantity'] -= lorder['openQuantity']
            lorder['openQuantity'] = 0
            statecheck(lorder)
            statecheck(rorder)


def fillinfo(orderId, price, openQuantity):
    dic = {
        "orderId": orderId,
        "price": price,
        "openQuantity": openQuantity
    }
    return dic


def statecheck(order):
    if order['openQuantity'] == 0:
        order['state'] = 'FILLED'
    elif order['openQuantity'] > 0:
        order['state'] = 'LIVE'
