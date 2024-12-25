from flask import Flask,request,render_template,redirect,url_for,flash,session,send_file
import mysql.connector
from otp import genotp
from cmail import sendmail
from stoken import encode,decode
from flask_session import Session
# from io import bytes
from io import BytesIO
import flask_excel as excel
import re
app=Flask(__name__)
excel.init_excel(app)
app.config['SESSION_TYPE']='filesystem'
app.secret_key ='123'
Session(app)
mydb=mysql.connector.connect(host='localhost',user='root',password='admin',db='snm')
@app.route('/')
def home():
    return render_template('welcome.html')
@app.route('/create',methods=['GET','POST'])
def create():
    if request.method=='POST':
        print(request.form)
        username=request.form['user_name']
        uemail=request.form['email']
        password=request.form['password']
        conformpassword=request.form['confirm_password']
        cursor=mydb.cursor()
        cursor.execute('select count(user_email) from users_info where user_email=%s',[uemail])
        result=cursor.fetchone()
        print(result)
        if result[0]==0:
            gotp=genotp()
            udata={'username':username,'useremail':uemail,'password':password,'otp':gotp}
            print(gotp)
            subject='OTP For Smiple Notes Manager'
            body=f'otp for registration of Simple notes manager{gotp}'
            sendmail(to=uemail,subject=subject,body=body)
            flash('otp has sent to given mail.')
            return redirect(url_for('otp',enudata=encode(data=udata)))
        elif result[0]>0:
            flash('Email already existed')
            return redirect(url_for('login'))
        else:
            return 'something went wrong'
    return render_template('create.html')
@app.route('/otp/<enudata>',methods=['GET','POST'])
def otp(enudata):
    if request.method=='POST':
        uotp=request.form['otp']
        try:
            dudata=decode(data=enudata)
        except Exception as e:
            print(e)
            return 'something went wrong'
        else:
            if dudata['otp']==uotp:
                cursor=mydb.cursor()
                cursor.execute('insert into users_info(username,user_email,password) values(%s,%s,%s)',[dudata['username'],dudata['usermail'],dudata['password']])
                mydb.commit()
                cursor.close()
                flash('Registration successfully completed')
                return redirect(url_for('login'))
            else:
                return 'invalid otp'
    return render_template('otp.html')
@app.route('/login',methods=['GET','POST'])
def login():
    if not session.get('user'):
        if request.method=='POST':
            uemail=request.form['useremail']
            password=request.form['password']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select count(user_email) from users_info where user_email=%s',[uemail])
            bdata=cursor.fetchone()#1, or 0,
            if bdata[0]==1:
                cursor.execute('select password from users_info where user_email=%s',[uemail])
                bpassword=cursor.fetchone() #( 0x31323300000000000000 )
                if password==bpassword[0].decode('utf-8'):
                    session['user']=uemail
                    
                    return redirect(url_for('dashboard'))
                else:
                    flash('password was wrong')
                    return redirect(url_for('login'))
            elif bdata[0]==0:
                flash('Email was not existed')
                return redirect(url_for('create'))
            else:
                return 'something went wrong'

        return render_template('login.html')
    else:
        return redirect(url_for('dashboard'))
@app.route('/dashboard')
def dashboard():
    if session.get('user'):
        return render_template('dashboard.html')
    else:
        return redirect(url_for('login'))
@app.route('/addnotes',methods=['GET','POST'])
# def addnotes():
#     if request.method=='POST':
#         title=request.form['title']
#         description=request.form['description']
#         cursor=mydb.cursor(buffered=True)
#         cursor.execute('select users where useremail=%s',[session.get('user')])
#         uid=cursor.fetchone()
#         if uid:
#             cursor.execute('insert into notes(title,description,user_id) values(%s,%s,%s)',[title,description,uid[0]])
#             mydb.commit()
#             cursor.close()
#             flash('Notes added successfully')
#             return redirect(url_for('dashboard'))
#         else:
#             return 'something went wrong'

#     return render_template('addnotes.html')
def addnotes():
    if session.get('user'):
        if request.method=='POST':
            tittle=request.form['title']
            description=request.form['description']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select user_id from users_info where user_email=%s',[session.get('user')])
            uid=cursor.fetchone()
            if uid:
                try:
                    cursor.execute('insert into notes(title,ndescription,user_id) values(%s,%s,%s)',[tittle,description,uid[0]])
                    mydb.commit()
                    cursor.close()
                    
                except mysql.connector.errors.IntegrityError:
                    flash('Duplicate Title Entry')
                    return redirect(url_for('dashboard'))
                except mysql.connector.errors.ProgrammingError:
                    flash('cloud not add notes')
                    print(mysql.connector.errors.ProgrammingError)
                    return redirect(url_for('dashboard'))
                else:
                    flash('Notes added successfully')
                    return redirect(url_for('dashboard'))
            else:
                return 'something went wrong'
        return render_template('addnotes.html')
    else:
        return redirect(url_for('login'))
@app.route('/viewallnotes')
def viewallnotes():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("select user_id from users_info where user_email=%s",[session.get('user')])
            uid=cursor.fetchone()#(1,)
            cursor.execute('select nid,title,create_at from notes where user_id=%s',[uid[0]])
            ndata=cursor.fetchall() #[( 1 | python | ctfygvubhnjkm | 2024-12-18 13:05:33 |       2 ),(inko data ela tuple lo vastundi)]
            print(ndata)
        except Exception as e:
            print(e)
            return redirect(url_for("dashboard"))
        else:
            return render_template("viewallnotes.html",ndata=ndata)
    else:
        return redirect(url_for('login'))

@app.route('/viewnotes/<nid>')
def viewnotes(nid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("select * from notes where nid=%s",[nid])
            ndata=cursor.fetchone() #[( 1 | python | ctfygvubhnjkm | 2024-12-18 13:05:33 | 2|
        except Exception as e:
            print(e)
            return redirect(url_for("viewallnotes"))
        else:
            return render_template("viewnotes.html",ndata=ndata)
    else:
        return redirect(url_for('login'))
@app.route('/updatenotes/<nid>',methods=['GET','POST'])
def updatenotes(nid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute("select * from notes where nid=%s",[nid])
        ndata=cursor.fetchone()
        if request.method=="POST":
            try:
                title=request.form['title']
                desc=request.form['description']
                cursor=mydb.cursor(buffered=True)
                cursor.execute('update notes set title=%s,ndescription=%s where nid=%s',[title,desc,nid])
                mydb.commit()
                cursor.close()
            except Exception as e:
                print(e)
            else:
                flash("Notes updates successfully")
                return redirect(url_for('dashboard'))
        return render_template("updatenotes.html",ndata=ndata)
    else:
        return redirect(url_for('login'))
@app.route("/deletenotes/<nid>")
def deletenotes(nid):
    if session.get('user'):
        try:# error vasthe adi user ki chupinchakunda manage chestundi
            cursor=mydb.cursor(buffered=True)
            cursor.execute("delete from notes where nid=%s",[nid])
            mydb.commit()
            cursor.close()
        except Exception as e:
            print(e)
            flash('could not delete notes')
            return redirect(url_for('viewallnotes'))
        else:
            flash("Deleted successfully")
            return redirect(url_for("viewallnotes"))
    else:
        return redirect(url_for('login'))
@app.route('/uploadfile',methods=['GET','POST'])
def uploadfile():
    if session.get('user'):
        if request.method=='POST':
            filedata=request.files['file']
            fname=filedata.filename
            fdata=filedata.read()
            try:
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select user_id from users_info where user_email=%s',[session.get('user')])
                uid=cursor.fetchone()
                cursor.execute('insert into filedata(filename,fdata,added_by) values(%s,%s,%s)',[fname,fdata,uid[0]])
                mydb.commit()
            except Exception as e:
                print(e)
                flash('file couldnot upload')
                return redirect(url_for('dashboard'))
            else:
                flash('file uploaded sucessfully')
                return redirect(url_for('dashboard'))
                # print(filedata)
                # print(filedata.read())
        return render_template('upload.html')
    else:
        return redirect(url_for('login'))
@app.route('/allfiles')
def allfiles():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("select user_id from users_info where user_email=%s",[session.get('user')])
            uid=cursor.fetchone()#(1,)
            cursor.execute('select fid,filename,created_at from filedata where added_by=%s',[uid[0]])
            filesdata=cursor.fetchall() #[( 1 | python | ctfygvubhnjkm | 2024-12-18 13:05:33 |       2 ),(inko data ela tuple lo vastundi)]
            print(filesdata)
        except Exception as e:
            print(e)
            return redirect(url_for("dashboard"))
        else:
            return render_template("allfiles.html",filesdata=filesdata)
    else:
        return redirect(url_for('login'))


@app.route('/viewfile/<fid>')
def viewfile(fid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select filename,fdata from filedata where fid=%s',[fid])
            fdata=cursor.fetchone()
            bytes_data=BytesIO(fdata[1])
            return send_file(bytes_data,download_name=fdata[0],as_attachment=False)
        except Exception as e:
            print(e)
            flash("couldn't not open file")
            return redirect(url_for("dashboard"))
    else:
        return redirect(url_for('login'))
@app.route('/downloadfile/<fid>')
def downloadfile(fid):
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('select filename,fdata from filedata where fid=%s',[fid])
            fdata=cursor.fetchone()
            bytes_data=BytesIO(fdata[1])
            return send_file(bytes_data,download_name=fdata[0],as_attachment=True)
        except Exception as e:
            print(e)
            flash("couldn't not open file")
            return redirect(url_for("dashboard"))
    else:
        return redirect(url_for('login'))
@app.route('/getexceldata')
def getexceldata():
    if session.get('user'):
        try:
            cursor=mydb.cursor(buffered=True)
            cursor.execute("select user_id from users_info where user_email=%s",[session.get('user')])
            uid=cursor.fetchone()#(1,)
            cursor.execute('select nid,title,ndescription,create_at from notes where user_id=%s',[uid[0]])
            ndata=cursor.fetchall() #[( 1 | python | ctfygvubhnjkm | 2024-12-18 13:05:33 |       2 ),(inko data ela tuple lo vastundi)]
            print(ndata)
        except Exception as e:
            print(e)
            flash('No data found')
            return redirect(url_for("dashboard"))
        else:
            array_data=[list(i) for i in ndata]
            columns=['Notes_id','title','content','created_time']
            array_data.insert(0,columns)
            return excel.make_response_from_array(array_data,'xlsx',filename='notesdata')#[( 1 | python | ctfygvubhnjkm | 2024-12-18 13:05:33 |       2 ),(inko data ela tuple lo vastundi)]

        # return render_template("viewallnotes.html",ndata=ndata) 
    else:
        return redirect(url_for('login'))
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('welcome'))
    else:
        return redirect(url_for('login'))
@app.route('/search',methods=['GET','POST'])
def search():
    if session.get('user'):
        try:
            if request.method=='POST':
                sdata=request.form['sname']
                strg=['A-Za-z0-9']
                pattern=re.compile(f'^{strg}',re.IGNORECASE)
                if (pattern.match(sdata)):
                    cursor=mydb.cursor(buffered=True)
                    cursor.execute('select * from notes where nid like %s or title like %s or ndescription like %s or create_at like %s',[sdata+'%',sdata+'%',sdata+'%',sdata+'%'])
                    sdata=cursor.fetchall()
                    cursor.close()
                    return render_template('dashboard.html',sdata=sdata)
                else:
                    flash('No Data found')
                    return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('dashboard'))
        except Exception as e:
            print(e)
            flash("can't find anything")
            return redirect(url_for("dashboard"))
    else:
        return redirect(url_for('login'))


app.run(use_reloader=True,debug=True)