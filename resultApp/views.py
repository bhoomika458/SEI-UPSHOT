from django.shortcuts import render
from datetime import datetime
from resultApp.models import *
from django.db import IntegrityError
from django.db.models import Q
from io import BytesIO
from django.http import HttpResponse
from django.template.loader import get_template
from xhtml2pdf import pisa
from django.views import View
import re 
import smtplib
from selenium import webdriver 
import time 
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from collections import defaultdict as dfd
from selenium.webdriver.chrome.options import Options

options = Options()
options = webdriver.ChromeOptions()
options.add_argument('--ignore-certificate-errors')
options.add_argument('--ignore-ssl-errors')
options.headless = True


# brower = webdriver.Chrome(executable_path ="C:\\chromedriver.exe", chrome_options=options)
# brower.get("https://govexams.com/knit/searchresult.aspx") 

#############################
branch_list={"MCA":"Master of Computer Applications",
				"MBA":"Master of Business Administration",
				"MSc":"Master of Science",
				"NA":"Result not available...!"
				}
				

branch_code={"MCA":1,"MBA":2,"MSc":3}
code_branch={1:"MCA",2:"MBA",3:"MSc"}

# Create your views here.
def getDataForPdf(batch,branch,year):
	rankData =[]
	sortedRankData =[]
	msg=''
	marksWithDetail =[]
	stdName = dfd(str)
	totalBacklog=0
	updateDate = 'NA'
	

	
	msg = 'Result not available yet.....!'
	
	allBranchRoll = rollNoGenerator(int(batch[2::]))
	if branch=='MCA':branchRoll = allBranchRoll[int(74*branch_code['MCA']-74): int(74*branch_code['MCA']): ]
	if branch=='MBA':branchRoll = allBranchRoll[int(74*branch_code['MBA']-74): int(74*branch_code['MBA']): ]
	if branch=='MSc':branchRoll = allBranchRoll[int(74*branch_code['MSc']-74): int(74*branch_code['MSc']): ]
	
	

	std = Student.objects.filter(roll__in=branchRoll)
	for i in std:
		stdName[i.roll]=i.name

	try:
			allMarks1 = Marks.objects.filter(roll__in=branchRoll, semester=year)
			allMarks2 = Marks.objects.filter(roll__in=branchRoll, semester=year[0])
			if len(allMarks1)>len(allMarks2):
				allMarks = allMarks1
			else:
				year = year[0]
				allMarks = allMarks2
			
			for i in allMarks:
				updateDate= i.dinank
				rankData.append({ 'y': i.obtain_marks, 'label': i.roll },)
				if i.carry_over_status>0:
					totalBacklog+=1

			sortedAllData = sorted(allMarks, key= lambda x: x.obtain_marks, reverse=True)
			sortedRankData =[]

			for idx,i in enumerate(sortedAllData):
				sortedRankData.append({ 'y': i.obtain_marks, 'label': i.roll+"("+str(idx+1)+")" })
				marksWithDetail.append({'roll':i.roll  ,'name':stdName[i.roll],  'mark': i.obtain_marks, 'rank':str(idx+1), 'status':i.carry_over_status})


			
			marksWithDetailRnk = sorted(marksWithDetail, key= lambda x : int(x['rank']))
			print('/////////',marksWithDetailRnk,updateDate)
			# for idx,v in  enumerate(marksWithDetailRnk):
			# 	v['sno']=(idx+1)

			if len(allMarks)!=0:
				msg= ''


				#print(i.obtain_marks,i.total_marks)
				

	except:
		print("Exception from class rank")
	allDetailForPdf = dict()
	allDetailForPdf['marksWithDetailRnk']=marksWithDetailRnk
	allDetailForPdf['batch']=batch
	allDetailForPdf['branch']=branch
	allDetailForPdf['year']=year
	allDetailForPdf['printDate']=datetime.now()
	allDetailForPdf['updateDate']=updateDate
	#batch,branch,year

	#print('pppppppp',allDetailForPdf)

	return allDetailForPdf

		
def pdfDekho(request):
	return render(request,'classRankPdf.html')

def renderToPdf(template_src, context_dict={}):
	template =get_template(template_src)
	html = template.render(context_dict)
	result = BytesIO()
	pdf = pisa.pisaDocument(BytesIO(html.encode("ISO-8859-1")), result)

	if not pdf.err:
		return HttpResponse(result.getvalue(), content_type='application/pdf' )
	else:
		None
data = {}
class ViewPdf(View):
	print("==========")
	# def __init__(self,batch ,branch,year):
	# 	print(branch)
	def get(self, request, *arg, **kwargs):
		print(kwargs)
		print(kwargs['branch_code'] )
		pdf = renderToPdf('classRankPdf.html',getDataForPdf(kwargs['batch'],kwargs['branch_code'],kwargs['year']))
		return HttpResponse(pdf ,content_type='application/pdf')

def countVisitor():
	visitUpdate = Visitor(count=1)
	visitUpdate.save()

	return Visitor.objects.all().count()

def rollNoGenerator(year):
	year=str(year)

	lateral_code='8'
	course_code=['1','2','3']
	linear=62
	lateral=12
	def rollconvert(param):
		if param<10:k='0'+str(param)
		else:k=str(param)
		return str(k)

	roll=[]
	for h in course_code:
		for i in range(1,linear+1):roll.append(year+h+rollconvert(i))

		year=str(int(year)+1)
		for i in range(1,lateral+1):roll.append(year+lateral_code+h+rollconvert(i))
		year=str(int(year)-1)

	# print(roll)
	# rool=['19207','19208','19209','19210']
	return roll

def updateStudentScrape(rollList):
	#brower = webdriver.Chrome(executable_path ="C:\\chromedriver.exe", chrome_options=options)
	
	rollno=rollList
	print("====>>>",len(rollno))
	def letsdo(roll):

		brower = webdriver.Chrome(executable_path ="C:\\chromedriver.exe", chrome_options=options)
		brower.get("https://govexams.com/knit/searchresult.aspx") 

		count=0
		i=-1
		while 1:
			i+=1
			if len(roll)==i:
				break
			print("--->",roll[i])
			user=brower.find_element_by_xpath("//*[@id='txtrollno']").clear()
			user=brower.find_element_by_xpath("//*[@id='txtrollno']").send_keys(roll[i])

			brower.find_element_by_xpath("//*[@id='btnSearch']").click()
			
			
			select = Select(brower.find_element_by_id("ddlResult"))


			text=[]
			el = brower.find_element_by_id('ddlResult')
			for option in el.find_elements_by_tag_name('option'):
			    text.append(option.get_attribute("value"))

			#msg=brower.find_element_by_xpath("//*[@id='lblmsg']").text
			if len(text)==0:
					print("Invalid student id",roll[i])
					continue
			count+=1
			#st_detail=semWise(text,roll[i])
			select.select_by_value(text[1])
			brower.find_element_by_xpath("//*[@id='btnGo']").click()
			
			brower.forward()
				

	
			name = brower.find_element_by_xpath("//*[@id='lblname']").text
			fname= brower.find_element_by_xpath("//*[@id='lblfname']").text
			course = brower.find_element_by_xpath("//*[@id='lblbranch']").text
			#carryOver = brower.find_element_by_xpath("//*[@id='tblYear']/tbody/tr[3]/td[2]").text
			#if name not in detail[id]:
			print(name,fname,course)

			execute=Student(roll=roll[i],name=name,fname=fname,course=course)
			execute.save()


				
			time.sleep(1)
			brower.back()
			brower.refresh()


	letsdo(rollno)
	
	time.sleep(1)
	#brower.close()



def semWise(textt,id):

		brower = webdriver.Chrome(executable_path ="C:\\chromedriver.exe", chrome_options=options)
		brower.get("https://govexams.com/knit/searchresult.aspx") 

		detail=dfd(list)
		j=-1
		while 1:
			j+=1
			if len(textt)-1==j:
				break

				
			user=brower.find_element_by_xpath("//*[@id='txtrollno']").clear()
			user=brower.find_element_by_xpath("//*[@id='txtrollno']").send_keys(id)
			brower.find_element_by_xpath("//*[@id='btnSearch']").click()		

			select = Select(brower.find_element_by_id("ddlResult"))
			select.select_by_value(textt[j])

			brower.find_element_by_xpath("//*[@id='btnGo']").click()

			brower.forward()			

			totalMarks = brower.find_element_by_xpath("//*[@id='lbltotlmarksDisp']").text
			name = brower.find_element_by_xpath("//*[@id='lblname']").text
			semester= brower.find_element_by_xpath("//*[@id='lblsem']").text
			status = brower.find_element_by_xpath("//*[@id='tblYear']/tbody/tr[2]/td[2]").text
			carryOver1 = brower.find_element_by_xpath("//*[@id='tblYear']/tbody/tr[3]/td[2]").text
			yearOfResult = brower.find_element_by_xpath("//*[@id='lblsession']").text
			print('year',yearOfResult)
			yearOfResult=yearOfResult[-1:-8:-1][::-1]



			carryOver=list(map(str,carryOver1.split(',')))
			print(carryOver)
			carryOver = [x for x in carryOver if len(x)>2]
			carryOver=','.join(carryOver)
			print(carryOver)


			try:
				obtain_mark,total_mark=map(float,totalMarks.split(' / '))
			except:
				obtain_mark,total_mark=float(totalMarks),10.0

			semester=semester[11::]
			print()

			print("semester",semester)
			print("marks",totalMarks)
			print("obtain_mark",obtain_mark)
			print("total_mark",total_mark)
			print("status",status)
			print("yearOfResult",yearOfResult)
			
			noOfCarry=0

			if len(carryOver)>0:
				carry_over_status=1
				print("carryOver",carryOver,len(carryOver.split(','))  )
				noOfCarry=len(carryOver.split(','))
				try:
					execute=Carryover(roll=id, subject_code=carryOver,semester=semester,obtain_marks=obtain_mark,year_of_result=yearOfResult)
					execute.save()
				except IntegrityError as e:
					print("duplicate exception carryTable")



			try:
				execute1=Marks(roll=id,semester=semester,year_of_result=yearOfResult,obtain_marks=obtain_mark,total_marks=total_mark,status=status,carry_over_status=noOfCarry)
				execute1.save()
				pass
			except IntegrityError as e:
				
				markss=Marks.objects.get( roll=id,semester=semester )
				if markss.status!='PASS':

					markss.obtain_marks=obtain_mark
					markss.total_marks=total_mark
					markss.status=status
					markss.carry_over_status=1
					markss.year_of_result=yearOfResult
					markss.save()		
					print("duplicate Exception marksTable")
			

			brower.back()
			brower.refresh()
			time.sleep(1)
			#brower.close()
		#return detail


	




def rollNumberWise(roll):

	brower = webdriver.Chrome(executable_path ="C:\\chromedriver.exe", chrome_options=options)
	brower.get("https://govexams.com/knit/searchresult.aspx") 

	st_detail=dfd(list)
	i=-1
	while 1:
		i+=1
		if len(roll)==i:
			break
		print("--->",roll[i])
		user=brower.find_element_by_xpath("//*[@id='txtrollno']").clear()
		user=brower.find_element_by_xpath("//*[@id='txtrollno']").send_keys(roll[i])

		brower.find_element_by_xpath("//*[@id='btnSearch']").click()
		
		
		select = Select(brower.find_element_by_id("ddlResult"))


		text=[]
		el = brower.find_element_by_id('ddlResult')
		for option in el.find_elements_by_tag_name('option'):
		    text.append(option.get_attribute("value"))
		print(text)
		if len(text)==0:
				print("Invalid student id",roll[i])
				continue
		text=text[::-1]
		print(text)
		#st_detail=semWise(text,roll[i])
		semWise(text,roll[i])
		#print(st_detail)






def getAllMarks(roll):
	print(roll)
	allSemMarks = Marks.objects.filter(roll=roll)
	pieData = []
	for i in allSemMarks:
		pieData.append({ 'y': i.obtain_marks, 'name': 'Semester('+i.semester+')' })
		print('sjs',i.obtain_marks)
	return pieData

def getOverAllRank(batch,branch):
	
	
	allRoll = rollNoGenerator(batch)[(branch-1)*74 :branch*74]
	
	DataBase = Marks.objects.filter(roll__in=allRoll)
	
	allMark= dfd(list)
	
	for i in DataBase:		
		allMark[i.roll].append(round(i.obtain_marks/i.total_marks,3))

	allMrakWithRank= dfd(float)

	for i in allMark:
		allMrakWithRank[i]= round(sum(allMark[i])/len(allMark[i]),5)
	allMrakWithRankSorted = sorted(allMrakWithRank.items(), key= lambda x :x[1], reverse=True)


	return allMrakWithRankSorted



def fullResult(request, rolln=''):
	msg=''
	studentDetail = ''
	pieData = ''
	rollOrName = ''
	lineData= []
	rank='NA'


	if request.method=='POST' or rolln!='':
		if rolln!='':
			rollOrName = rolln
			if len(rollOrName)>5:
				try:
					idx=rollOrName.index('(')
					rollOrName = rollOrName[:idx:]
					print('------->',rollOrName)
				except:
					pass


		else:rollOrName=request.POST.get('rollOrName','')
		
		try:

			studentDetail=  Student.objects.get(roll=rollOrName)
			
			if len(rollOrName)==6:
				batch = int(rollOrName[0:2])-1
				branch = int(rollOrName[3])
				
			else: 
				batch = int(rollOrName[0:2])
				branch = int(rollOrName[2])
				
			allMrakWithRankSorted = getOverAllRank(batch,branch)


			for idx,vlu in enumerate(allMrakWithRankSorted):
				if vlu[0]==rollOrName:rank = idx+1

			
			
		except:
			msg="Student {} not exist".format(rollOrName)

		pieData = getAllMarks(rollOrName)

		flag=1
		try:
			allSem = Marks.objects.filter(roll=rollOrName)
			percent = 0
			year = '2019'
			#print(rollNoGenerator(int(year[2::])-4) )
			for i in allSem:
				if rollOrName not in rollNoGenerator( int(year[2::]))  :
					percent+=i.obtain_marks
				else:
					percent += i.obtain_marks/i.total_marks
					flag=0
					print("--------------------")

				if len(i.semester)==1 and rollOrName  in rollNoGenerator(int(year[2::])-4):
					lineData.append({'y':i.obtain_marks*2,'label': "* Semester "+i.semester})
				else:
					lineData.append({'y':i.obtain_marks,'label': "Semester "+i.semester})
			percent /=len(allSem)
			print('--->',percent)
			if flag:
				percent = str(round(percent*10/100,2))+'%'

			else:
				percent = str(round(percent*100,2) )+' %'

			print('percent',percent)

				

		except:
			print("Except2")

		try:
			backlogData = Carryover.objects.filter(roll=rollOrName)
		except:
			print("Except3")


		

		print('hekkko',allSem)


	context = {
		'percent':percent,
		'msg':msg,
		'studentDetail':studentDetail,

		'pieData':pieData,

		'allSem':allSem,

		'backlogData':backlogData,
		'totalBackLog':'('+str(len(backlogData))+')',
		'visit':countVisitor(),

		'lineData':lineData,
		'rank':rank
	}
	return render(request,'fullResult.html',context)

def getStudentDetail(top3,batch):
	detail = dict()
	for idx,vlu in enumerate(top3):
		data = Student.objects.get(roll=vlu[0])
		detail['roll'+str(idx+1)]= data.roll
		detail['name'+str(idx+1)]= data.name
		detail['fname'+str(idx+1)]=data.fname[:12]+'..'
		detail['branch']=data.course
		detail['percent'+str(idx+1)]=str(round(vlu[1]*100,2) )+'%'
		detail['batch']=batch

	#print(detail)
	return detail
	



def allTopers():
	allTopersDetail = []
	batch= ['2019','2020']
	branch = [1,2,3]
	for i in batch:
		topersDetail = []
		for j in branch:
			
			allMrakWithRankSorted = getOverAllRank(str(int(i))[2:],j)
			top3 = allMrakWithRankSorted[:3]
			topersDetail.append( getStudentDetail(top3,i))
		allTopersDetail.append(topersDetail)



	print(allTopersDetail)
	return allTopersDetail

		




def updateStudent(request):
	year = '2022'
	allRollNo = rollNoGenerator(int(year[2::]))
	print(allRollNo)
	updateStudentScrape(allRollNo)


	return render(request,'home.html')


def updateMarks(request):
	year = '2022'
	allRollNo = rollNoGenerator(int(year[2::]))
	print(allRollNo)
	rollNumberWise(allRollNo[150::])

	return render(request,'home.html')


def classRank(request):
	rankData =[]
	sortedRankData =[]
	msg=''
	marksWithDetail =[]
	stdName = dfd(str)
	totalBacklog=0
	batch = ''
	branch = 'NA'
	year = ''

	if request.method=='POST':
		batch=request.POST.get('batch','')
		branch=request.POST.get('branch','')
		year=request.POST.get('year','')
		msg = 'Result not available yet.....!'

		

		allBranchRoll = rollNoGenerator(int(batch[2::]))
		if branch=='MCA':branchRoll = allBranchRoll[int(74*branch_code['MCA']-74): int(74*branch_code['MCA']): ]
		if branch=='MBA':branchRoll = allBranchRoll[int(74*branch_code['MBA']-74): int(74*branch_code['MBA']): ]
		if branch=='MSc':branchRoll = allBranchRoll[int(74*branch_code['MSc']-74): int(74*branch_code['MSc']): ]
		 
		

		std = Student.objects.filter(roll__in=branchRoll)
		for i in std:
			stdName[i.roll]=i.name

		try:
				allMarks1 = Marks.objects.filter(roll__in=branchRoll, semester=year)
				allMarks2 = Marks.objects.filter(roll__in=branchRoll, semester=year[0])
				if len(allMarks1)>len(allMarks2):
					allMarks = allMarks1
				else:
					year = year[0]
					allMarks = allMarks2
				
				for i in allMarks:
					rankData.append({ 'y': i.obtain_marks, 'label': i.roll },)
					if i.carry_over_status>0:
						totalBacklog+=1
						print(rankData)


				sortedAllData = sorted(allMarks, key= lambda x: x.obtain_marks, reverse=True)
				sortedRankData =[]

				for idx,i in enumerate(sortedAllData):
					sortedRankData.append({ 'y': i.obtain_marks, 'label': i.roll+"("+str(idx+1)+")" })
					marksWithDetail.append({'roll':i.roll  ,'name':stdName[i.roll],  'mark': i.obtain_marks, 'rank':str(idx+1), 'status':i.carry_over_status})


				marksWithDetail = sorted(marksWithDetail, key= lambda x : x['mark'], reverse=True)
				#marksWithDetailRnk = sorted(marksWithDetail, key= lambda x : x['rank'])

				for idx,v in  enumerate(marksWithDetail):
					v['sno']=(idx+1)

				if len(allMarks)!=0:
					msg= ''

				

					#print(i.obtain_marks,i.total_marks)
					

		except:
			print("Exception from class rank")



	

	context ={
			'rankData':rankData,
			'sortedRankData':sortedRankData,
			'msg':msg,
			'marksWithDetail':marksWithDetail,
			'batch':batch,
			'branch':branch_list[branch],
			'year':year,
			'totalStudent':len(marksWithDetail),
			'totalBacklog':totalBacklog,
			'visit':countVisitor(),
			
            
			'batch':batch,
			'branch_code':branch,
			'year':year,

	}

	return render(request,'classRank.html',context)


def logout(req):
	del req.session['id']
	return render(req,"loginform.html",{'error':"you have logged out"})

	


def loginPage(req):
	obj=req.POST.get('uname')
	if(obj):
			if(checkEmail(obj)):
					if(req.POST.get('psw')==req.POST.get('cpsw')):
							a = logindetails(username=req.POST.get('uname'),password=req.POST.get('psw'))
							a.save()
							return render(req,"loginform.html")
					else:
							return render(req,'loginform.html',{'error':"Passwords are not matching!!"})
			else:
					return render(req,'loginform.html',{'error':"Enter the Valid email-ID"})
	else:
			return render(req,'loginform.html')

def loggedin(req):
	uname = req.POST.get('uname')
	passw = req.POST.get('psw')
	x = logindetails.objects.all().values()
	uname_list = []
	for i in x:
		uname_list.append(i['username'])
	if(uname in uname_list):
		a = logindetails.objects.get(username = uname)
		if a.password == passw:
			req.session['id'] = uname
			return render(req,'home.html')
		else:
			return render(req,'loginform.html',{'error1':'Incorrect credentials!!'})
	else:
			return render(req,'loginform.html',{'error1':'User is Not Register '})
	
def reg(request):
	return render(request,'loginform.html')	


def checklength(username):
	if len(username) in range(5,11):
		return True
	else:
		return False

def checkEmail(email):
	regex='^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
	if(re.search(regex,email)):
		return True
	else:
		return False	



def home(request):
	

		#return render(request,'home.html')
	allTopersDetail = allTopers()
	

	context = {
	'allTopersDetail':allTopersDetail,
	'visit':countVisitor()

	}
	return render(request,'home.html',context)


def menu(req):
	return render(req,"menu.html")



def Forgot(req):
    return render(req,"Forgot.html")

def smtp_sendmail(email,password):
    server=smtplib.SMTP("smtp.gmail.com",587)
    server.ehlo()
    server.starttls()
    server.ehlo()
    server.login("suranaeducationalinstitutions@gmail.com","duhhspfuckvzewgz")
    message=f"subject:SEI\n\nUsername:- {email}\nPassword:-{password}"
    server.sendmail("suranaeducationalinstitutions@gmail.com",email,message)
    server.quit()
    print("mail sent")

def submit(req):
    email=logindetails.objects.all()
    list1=email.values()
    print(email.values())
    return render(req,'Forgot.html',{'list1':list1})

def send(req):
	email=req.POST.get('email')
	ulist=logindetails.objects.all().values()
	uname_list=[]
	for i in ulist:
		uname_list.append(i['username'])
	if email in uname_list:
		a=logindetails.objects.get(username=email)
		password1=a.password
		smtp_sendmail(email,password1)
		return render(req,"Forgot.html")

	else:
		return HttpResponse("worng mail ID")





