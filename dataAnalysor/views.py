# _*_ encoding:utf-8 _*_

from django.views.generic.base import View
from django.shortcuts import render
from django.http import HttpResponse
import time, simplejson, MySQLdb

from utils.medicineVec import read4Vec
from DataAnalysisTools import checkDataSetQualityAndIn, fetchTopMedicineCounts, firstClassVocFromSpecial


# Create your views here.
class DataAnalysor(View):
    def get(self, request):
        cur_time = time.time()
        return render(request, "data-analysor.html",
                      {"cur_time": cur_time})


class AnalysorReceive(View):
    def post(self, request):
        print "AnalysorReceive..."
        patientContent = request.POST.get('patientContent')
        prescription = request.POST.get('prescription')
        listin = read4Vec(patientContent)[0]
        res = checkDataSetQualityAndIn(listin, prescription, False)
        return HttpResponse('{"status":"success","res":"'+res+'"}')


class DataAnalysorSave(View):
    def post(self, request):
        print "dataAnalysorSave..."
        patientContent = request.POST.get('patientContent')
        prescriptionName = request.POST.get('prescriptionName')
        qualityRecord = request.POST.get('qualityRecord')
        contentVec = ','.join(read4Vec(patientContent)[0])
        res = ''

        if patientContent is None or prescriptionName is None or qualityRecord is None:
            return HttpResponse('{"status":"success","res":"保存失败"}')
        if patientContent is '' or prescriptionName is '' or qualityRecord is '':
            return HttpResponse('{"status":"success","res":"保存失败"}')

        sql = "insert into medicinedataset_quality(patientContent,contentVec,prescriptionName,qualityRecord) VALUES ('"+\
              patientContent+"','"+contentVec+"','"+prescriptionName+"','"+qualityRecord+"')"

        conn = MySQLdb.connect("127.0.0.1", "root", "w1020392881", "candyonline", use_unicode=True, charset="utf8")
        try:
            cursor = conn.cursor()
            if cursor.execute("select id from medicinedataset_quality where patientContent='"+patientContent+"'") > 0:
                res = "输入的主诉已存在"
            else:
                cursor.execute(sql)
                res = "保存成功"
                conn.commit()
        except MySQLdb.Error as e:
            conn.rollback()
            res = "保存失败"
        finally:
            conn.close()
        # print res
        return HttpResponse('{"status":"success","res":'+simplejson.dumps(res)+'}')


class ScaleMap(View):
    def post(self, request):
        print "ScaleMap..."
        time.sleep(10)
        medicines = []
        scales = []
        res = ""
        for x in fetchTopMedicineCounts(20):
            medicines.append(x[0])
            scales.append(x[2])
        for x in range(len(medicines)):
            # print medicines[x], scales[x]
            # print scales[x], "%.2f%%" % (scales[x] * 100)
            res += medicines[x]+':'+str("%.2f%%" % (scales[x] * 100))+','
        # print res
        return HttpResponse('{"status":"success","res":'+simplejson.dumps(res)+'}')


class AssociationAndPrescription(View):
    def post(self, request):
        print "AssociationAndPrescription..."
        association = request.POST.get('association')
        nCounts = request.POST.get('nCounts')
        num = request.POST.get('num')
        flag = request.POST.get('flag')
        res = firstClassVocFromSpecial(read4Vec(association)[0][0], int(nCounts), int(num), flag == str(True))
        tmp_res = ''
        for x in res:
            tmp_res += ','.join(x)
            tmp_res += ';'
        # print tmp_res
        return HttpResponse('{"status":"success","res":"'+tmp_res+'"}')


class PrescriptionAssoicationSave(View):
    def post(self, request):
        print "PrescriptionAssoicationSave..."
        specialWord = request.POST.get('specialWord')
        prescriptionName = request.POST.get('prescriptionName')
        setNums = request.POST.get('setNums')
        sequenceChoice = request.POST.get('sequenceChoice')
        firstClassWords = request.POST.get('firstClassWords')
        contentVec = ','.join(read4Vec(specialWord)[0])
        print 'specialWord', specialWord
        print 'prescriptionName', prescriptionName
        print 'setNums', setNums
        print 'sequenceChoice', sequenceChoice
        print 'firstClassWords', firstClassWords
        print 'contentVec', contentVec

        if specialWord is None or prescriptionName is None or contentVec is None:
            return HttpResponse('{"status":"success","res":"保存失败"}')

        if specialWord is '' or prescriptionName is '' or contentVec is '':
            return HttpResponse('{"status":"success","res":"保存失败"}')
        #
        res = '返回结果为空'
        sql = "insert into classicalprescription_firstclassvoc(specialWord,prescriptionName,setNums,sequenceChoice," \
              "firstClassWords,contentVec) values ('"+specialWord+"','"+prescriptionName+"',"+setNums+","+sequenceChoice +\
              ",'"+firstClassWords+"','"+contentVec+"')"
        print sql
        conn = MySQLdb.connect("127.0.0.1", "root", "w1020392881", "candyonline", use_unicode=True, charset="utf8")
        try:
            cursor = conn.cursor()
            if cursor.execute("select id from classicalprescription_firstclassvoc where prescriptionName='"+prescriptionName+"' and contentVec='"+contentVec+"'") > 0:
                res = "当前主方与向量已存在"
            else:
                cursor.execute(sql)
                res = "保存成功"
            conn.commit()
        except MySQLdb.Error as e:
            conn.rollback()
            res = "保存失败"
        finally:
            conn.close()
        # print res
        return HttpResponse('{"status":"success","res":'+simplejson.dumps(res)+'}')
