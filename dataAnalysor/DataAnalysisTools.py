# _*_ encoding:utf-8 _*_

import codecs, MySQLdb
import sys
import re
from utils.findLineByWords import matchMedicineName
from utils.findLineByVec import *
from numpy import *
from utils.fetchMedicine import *
import copy
import time

# Aprior算法
def createC1(dataSet):
    C1 = []
    for transaction in dataSet:
        for item in transaction:
            if [item] not in C1:
                C1.append([item])
    C1.sort()
    return map(frozenset, C1)

def scanD(D, Ck, minSupport):
    ssCnt = {}
    for tid in D:
        for can in Ck:
            if can.issubset(tid):
                if not ssCnt.has_key(can):
                    ssCnt[can] = 1
                else:
                    ssCnt[can] += 1
    retList = []
    supportData = {}
    for key in ssCnt:
        support = ssCnt[key]
        if support >= minSupport:
            retList.insert(0, key)
        supportData[key] = support
    return retList, supportData

def aprioriGen(Lk, k):
    retList = []
    lenLk = len(Lk)
    for i in range(lenLk):
        for j in range(i + 1, lenLk):
            L1 = list(Lk[i])[: k - 2]
            L2 = list(Lk[j])[: k - 2]
            L1.sort()
            L2.sort()
            if L1 == L2:
                retList.append(Lk[i] | Lk[j])
    return retList

def apriori(dataSet,nCounts,minSupport):
    C1 = createC1(dataSet)
    D = map(set, dataSet)
    L1, suppData = scanD(D, C1, minSupport)
    L = [L1]
    k = 2

    while (len(L[k-2]) > 0) and (nCounts+1) >= k:
        Ck = aprioriGen(L[k-2], k)
        Lk, supK = scanD(D, Ck, minSupport)
        suppData.update(supK)
        L.append(Lk)
        k += 1
    return L, suppData

def readNearMedicine():
    """
    :return: 返回相近的药方列表
    """
    nearMedicine = codecs.open(r'F:\wushijia\workspace\medicineDialecticFilec\nearMedicine.txt','r','utf-8')
    try:
        nearMedicineText = nearMedicine.readlines()
    finally:
        nearMedicine.close()
    listNearMedicine = []
    for eachText in nearMedicineText:
        eachText = eachText.strip('\r\n')
        eText = re.split(u"\u0020", eachText)
        listNearMedicine.append(eText)
    return listNearMedicine

def readGroupDictionary():
    """
    :return: listGroupDictionary 药方名列表,listGroup 组合列表,listGroupDict 每个元素为[药方，组合]
    """
    groupDictionary = codecs.open(r'F:\wushijia\workspace\medicineDialecticFilec\groupDict.txt','r','utf-8')
    try:
        groupDictionaryText = groupDictionary.readlines()
    finally:
        groupDictionary.close()
        listMedicineName = []
    listGroup = []
    listGroupDict = []
    for eachText in groupDictionaryText:
        eachText = eachText.strip('\r\n')
        eText = re.split(u"\uff1a|\u0020", eachText)
        listGroup.append(eText[1])
        listGroupDict.append(eText)
        if eText[0] not in listMedicineName:
            listMedicineName.append(eText[0])
    return listMedicineName,listGroup,listGroupDict

def readSpecialMedicine():
    """
    :return: dict(type:dict):以所有出现过的药方名为键，均对其赋值0
    """
    specialMedicine = codecs.open(r'F:\wushijia\workspace\medicineDialecticFilec\specialMedicine.txt','r','utf-8')
    try:
        specialMedicineText = specialMedicine.readlines()
    finally:
        specialMedicine.close()
    dict = {}
    for eachText in specialMedicineText:
        eachText = eachText.strip('\r\n')
        dict.setdefault(eachText,0)
    return dict

def getListinList(flag):
    """
    :param flag: True or False
    :return:flag==True,输出脉象词、太阳、少阳 、阳明、少阴、厥阴、太阴和权重大于3的词向量；
            flag == False，只输出权重大于3的词向量
    """
    listin = []
    dict = {}
    dictfile = codecs.open(r'F:\wushijia\workspace\medicineDialecticFilec\weight2q.txt', 'r', 'utf-8')

    try:
        dictText = dictfile.readlines()
    finally:
        dictfile.close()
    for eachText in dictText:
        eachText = eachText.strip('\r\n')
        eText = eachText.split(' ')
        dict.setdefault(eText[0], int(eText[1]))
    for key,value in dict.items():
        if value > 3:
            listin.append(key)
    if flag == True:
        listPulseDict = []
        ftext = codecs.open(r"F:\wushijia\workspace\medicineDialecticFilec\pulseDict.txt", "r", "utf8")
        try:
            fConfigText = ftext.readlines()
        finally:
            ftext.close()
        for eachText in fConfigText:
            eachText = eachText.strip('\r\n')
            listPulseDict.append(eachText)
        listin = list(set(listin)|set(listPulseDict))
        return listin,dict
    else:
        return listin,dict

def firstClassVocFromSpecial(lis,nCounts,num,flag):
    """
    :param lis: 输入词向量
    :param nCounts: 与输入词向量同时出现的组合数的个数
    :param num: 与输入词向量同时出现的组合数的个数为nCounts的频率最靠前的num个
    :param flag: flag = True,排除脉象词和权重大于3的词向量，flag = False，只排除权重大于3的词向量
    :return: 三种返回结果
            return 1 : 1等价于"输入的词向量未在字典中出现过！"
            return 2：2等价于"与输入词向量同时出现的最大组合数小于输入组合数个数！"
            return maxGroupTops：输出与输入词向量同时出现的组合数个数为nCounts的频率最靠前的num个

    """
    listin,dict = getListinList(flag)
    if lis not in dict.keys():
        # return "输入的词向量未在字典中出现过！"
        return 1
    else:
        pm = codecs.open(r'F:\wushijia\workspace\medicineDialecticFilec\pm.txt', 'r', 'utf-8')
        try:
            pmText = pm.readlines()
        finally:
            pm.close()
        relationPmTextList = []
        for eachText in pmText:
            eachText = eachText.strip('\r\n').split(u',')
            if set(lis.split(u',')).issubset(set(eachText)):
                relationPmTextList.append(list(set(eachText) - set(listin)))
        L, supportData = apriori(relationPmTextList, nCounts, minSupport=3)
        if nCounts <= len(L)-1:
            relationGroup = {}
            tempCounts = 0
            for items in L[nCounts]:
                if (set(lis.split(u','))).issubset(items):
                    relationGroup[items] = supportData[items]
                    tempCounts += 1
            if tempCounts < 1:
                # return "与输入词向量同时出现的最大组合数小于输入组合数个数！"
                return 2
            else:
                relationGroupSorted = sorted(relationGroup.items(), key=lambda item: item[1], reverse=True)
                k = 0
                maxGroupTops = []
                while k < len(relationGroupSorted) and k < num:
                    maxGroupTops.append(list(set(relationGroupSorted[k][0]) - set(lis.split(u','))))
                    k += 1
                return maxGroupTops
        else:
            # return "与输入词向量同时出现的最大组合数小于输入组合数个数！"
            return 2

def checkSingleDataSetQuality(listin,prescriptionName):
    # listMedicineName, listGroup, listGroupDict = readGroupDictionary()
    listGroupDict, listMedicineName = readGroupDict()
    listPulseDict = readPulseDict()
    dataSetDict = {}
    dataSetDict[prescriptionName] = 0
    if prescriptionName in listMedicineName:
        for i in range(len(listGroupDict)):
            if prescriptionName == listGroupDict[i][0] and (set(listGroupDict[i][1])-set(listPulseDict)).issubset(set(listin)):
                dataSetDict[prescriptionName] += listGroupDict[i][2]
        if dataSetDict[prescriptionName] >= 0.23:
            return "优秀"
        elif dataSetDict[prescriptionName] > 0.08 and dataSetDict[prescriptionName] < 0.23:
            return "合格"
        else:
            return "不合格"
    else:
        return "不在检查范围内"

def checkDataSetQualityAndIn(listin,prescriptionName,flag):
    """
    :param listin: 主诉
    :param prescriptionName: 主诉对应的药方
    :param flag: flag==True 按优秀、合格、不合格、不在检查范围内的优先级输出结果
                 flag == False 按不合格、合格、优秀、不在检查范围内的优先级输出结果
    :return:
    """
    str1 = "优秀"
    str2 = "合格"
    str3 = "不合格"
    str4 = "不在检查范围内"
    listin = findNear(','.join(listin))
    prescriptionNameList = matchMedicineName(prescriptionName)
    qualityLevel = []
    for item in prescriptionNameList:
        qualityLevel.append(checkSingleDataSetQuality(listin,item))
    if flag == True:
        if str1 in qualityLevel:
            return str1
        elif str2 in qualityLevel:
            return str2
        elif str3 in qualityLevel:
            return str3
        else:
            return str4
    else:
        if str3 in qualityLevel:
            return str3
        elif str2 in qualityLevel:
            return str2
        elif str1 in qualityLevel:
            return str1
        else:
            return str4

def loadDataSet():
    """
    :return: output(type:dict) 键：数据库中的id值；值：id对应的prescriptionName
    """
    #连接
    conn=MySQLdb.connect(host="127.0.0.1",user="root",passwd="w1020392881",db="candyonline",charset="utf8")
    cursor = conn.cursor()
    sql_one = "SELECT id,prescriptionName FROM medicine_operation "
    output = {}
    try:
        cursor.execute(sql_one)
        results = cursor.fetchall()
    except:
        print "Error: unable to fetch data!"
    for eachText in results:
        output.setdefault(eachText[0], eachText[1])
    conn.close()
    return output

def fetchTopMedicineCounts(num):
    """
    :return: topMedicineCounts 返回药名出现总数排在前num个的列表，列表中每个元素的构成为[药名 出现总次数 出现总次数在整个数据集中的比例]
    """
    dict = readSpecialMedicine()
    listDict = dict.keys()
    medicineCounts = copy.deepcopy(dict)
    listNearMedicine = readNearMedicine()
    dataSet = loadDataSet()                     #dataSet （type:dict）:键：数据库的id号 ；值：id号对应的prescriptionName
    listPrescriptionName = dataSet.values()
    nCounts = len(listPrescriptionName)
    for item in listPrescriptionName:
        tempName = matchMedicineName(item)
        for key_values in tempName:
            medicineCounts[key_values] += 1
    for i in range(len(listNearMedicine)):
        for j in range(len(listNearMedicine[i])-1):
            medicineCounts[listNearMedicine[i][0]] += medicineCounts[listNearMedicine[i][j+1]]
    allMedicineList = []
    for value in listDict:
        allMedicineList.append([value,medicineCounts[value], round(float(medicineCounts[value]) / nCounts, 4)])
    allMedicineListSorted = sorted(allMedicineList,key=lambda x:x[-1],reverse=True)
    topMedicineCounts = []
    for i in range(num):
        topMedicineCounts.append(allMedicineListSorted[i])
    return topMedicineCounts

# if __name__ == "__main__":
    # start = time.time()
    # print firstClassVocFromSpecial(u'448',3,5,True)
    # print time.time()-start
    # topMedicineCounts = fetchTopMedicineCounts(15)
    # for item in topMedicineCounts:
    #     for items in item:
    # #         print items
    # listin = [u'33', u'3', u'9', u'12', u'152', u'80', u'1',u'136']
    # print checkDataSetQualityAndIn(listin, u'桂枝汤合葛根汤', False)

