from datetime import datetime, timedelta
import json

from riotwatcher import LolWatcher, ApiError

try:
    with open("config.json", "r") as f:
        config = json.load(f)
        apiKey = config['apiKey']
        myRegion = config['myRegion']
        region = config['region']
        summonerName = config['summonerName']
        friends = config['friends']
        lol_watcher = LolWatcher(apiKey, default_match_v5=True)
        me = lol_watcher.summoner.by_name(myRegion, summonerName)
        confOk = True
except:
    confOk = False





def updateHistory():
    start = 0
    count = 20
    result = dict()
    try:
        with open(f"json/{summonerName}_matchHistory.json", "r") as f:
            res = json.load(f)

    except:
        res = dict()
    stop = False
    for i in range(0, 5):
        if stop:
            break
        for match in lol_watcher.match_v5.matchlist_by_puuid(region, me['puuid'], start=start, count=count):
            if match in res.keys():
                stop = True
                break
            rMatch = lol_watcher.match_v5.by_id(region=region, match_id=match)
            tmp = {
                "mode": rMatch['info']['gameMode'],
                "gameStart": rMatch['info']['gameStartTimestamp']
            }
            win = rMatch['info']["teams"][0]['teamId'] if rMatch['info']["teams"][0]['win'] else \
                rMatch['info']["teams"][1]['teamId']

            tmpParticipants = []
            for participant in rMatch['info']['participants']:
                if participant['summonerName'] == summonerName:
                    tmp['me'] = {
                        "champName": participant['championName'],
                        "score": f"{participant['kills']}.{participant['deaths']}.{participant['assists']}"

                    }
                    tmp['win'] = win == participant['teamId']
                else:
                    tmpParticipants.append({
                        "name": participant['summonerName'],
                        "champName": participant['championName'],
                        "score": f"{participant['kills']}.{participant['deaths']}.{participant['assists']}",
                        "win": win == participant['teamId']
                    })
            tmp['participants'] = tmpParticipants
            result[match] = tmp

        start += count
    result |= res
    with open(f"json/{summonerName}_matchHistory.json", "w+") as f:
        json.dump(result, f, indent=4)
    print("done update request", len(result.keys()), " last match")
    return res


def foundMe(participants):
    for participant in participants:
        if participant['name'] == summonerName:
            return participant
    return None


def getRecentSummonnerView(matchHistory):
    res = dict()
    idx = 0
    for id_, match in matchHistory.items():
        # print(match)
        for participant in match['participants']:

            tmpRes = {
                "lastSeen": idx,
                "mode": match['mode'],
                "time": match['gameStart'],
                "win": match['win'],
                "vs": match['win'] != participant['win'],
                "myScore": match['me']['score'],
                "myChamp": match['me']['champName'],
                "score": participant['score'],
                "champ": participant['champName']
            }
            if participant['name'] not in res.keys():
                res[participant['name']] = {
                    "found": 1,
                    "matches": [tmpRes]
                }
            else:
                res[participant['name']]['found'] += 1
                res[participant['name']]['matches'].append(tmpRes)
        idx += 1
    res = dict(sorted(res.items(), key=lambda item: item[1]['found'], reverse=True))
    # for k, v in res.items():
    #     if v['found'] > 1:
    #         print(v['found'], k, ":")
    #         for match in v['matches']:
    #             print('   ', printMatch(match))
    with open(f"json/{summonerName}_found.json", "w+") as f:
        json.dump(res, f, indent=4)
    print("done update founds")
    return res


def findSummonnerInActiveMatch(founds):
    try:
        match = lol_watcher.spectator.by_summoner(myRegion, me['id'])
        print("GAME STARTED")
        for participant in match['participants']:

            #print(participant['summonerName'],  participant['summonerName'] in founds.keys())
            if participant['summonerName'] in founds.keys():
                found = founds[participant['summonerName']]
                print(found['found'], participant['summonerName'], ":")
                for match in found['matches']:
                    print('   ', printMatch(match))

    except:
        print("NO GAME STARTED")


def printMatch(match):
    t = match['time']/1000
    return f"{match['lastSeen']} {datetime.fromtimestamp(t).strftime('%d-%m-%Y %H:%M:%S')} {match['mode']} {'W' if match['win'] else 'L'} {'VS' if match['vs'] else 'WITH'} {match['myChamp']} {match['myScore']} vs {match['champ']} {match['score']}"


if __name__ == '__main__':
    if confOk:
        matchHistory = updateHistory()

        founds = getRecentSummonnerView(matchHistory)

        findSummonnerInActiveMatch(founds)
        input("Press Enter to continue...")

