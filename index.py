# -*- coding:utf-8 -*- ＃必须在第一行或者第二行
import logging
import sys
import cgi

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'
from google.appengine.dist import use_library
use_library('django', '0.96')

from google.appengine.api import users
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.api import urlfetch
from google.appengine.api.urlfetch import DownloadError
import urllib
import base64
import datetime

from google.appengine.ext.webapp import template

from zd_db import *
from zd_func import *
from zd_define import *

from google.appengine.ext import db
from google.appengine.api import apiproxy_stub_map #hook

import re
from google.appengine.api import memcache
from google.appengine.datastore import entity_pb

import math
from google.appengine.runtime.apiproxy_errors import CapabilityDisabledError
import Cookie

from google.appengine.api import capabilities

logging.getLogger().setLevel(logging.DEBUG)

#images_enabled = capabilities.CapabilitySet('images').is_enabled()
#datastore_write_enabled = capabilities.CapabilitySet('datastore_v3', capabilities=['write']).is_enabled()
#memcache_get_enabled = capabilities.CapabilitySet('memcache', methods=['get']).is_enabled()

def capability_middleware(application):
  def wsgi_app(environ, start_response):
    if not capabilities.CapabilitySet('datastore_v3').is_enabled():
      print_error_message(environ, start_response)
    else:
      environ['capabilities.read_only'] = capabilities.CapabilitySet('datastore_v3', capabilities=['write']).is_enabled()
      return application(environ, start_response)

  return wsgi_app

##############
MYVERSION=20120518
Max_list_num=1000 #1000 limit
RUN_TIME_S=float(0)
RUN_TIME_E=float(0)
blogname='myblog'
is_local=0
myhost=os.environ['HTTP_HOST']
is_local_chk = re.search("^localhost", str(myhost), re.I)
if is_local_chk:
  is_local=1

HTTP_DATE_FMT = "%a, %d %b %Y %H:%M:%S GMT"

DB_TIME = 0

def hook_db(service, call, request, response):
  global DB_TIME
  DB_TIME += 1
  #print str(DB_TIME)+"<br>"

#GetPostCallHooks  GetPreCallHooks
apiproxy_stub_map.apiproxy.GetPostCallHooks().Append('db_hook', hook_db, 'datastore_v3')

class Refresh(webapp.RequestHandler):
  def get(self):
    if val_user():
      memcache.flush_all()
      self.redirect("/")
    else:
      self.redirect(users.create_login_url(self.request.uri))

def get_microtime2():
  from time import clock
  t = clock()
  return t

def get_microtime():
  from decimal import Decimal
  import time,datetime
  #self.response.out.write('<h1>'+str(time.time())+'</h1>') #1284618234.97
  #self.response.out.write('<h1>'+str(datetime.datetime.now())+'</h1>') #2010-09-16 09:34:47.781000
  t1=str(time.time())
  t2=str(datetime.datetime.now())
  result=0
  m1 = re.search("^([0-9]+)\.", t1)
  if m1 and m1.group(1):
    result+=Decimal(m1.group(1))
  m2 = re.search("\.([0-9]+)$", t2)
  if m2 and m2.group(1):
    result+=Decimal('0.'+m2.group(1))
  return result

def bmk_start(self):
  global RUN_TIME_S
  RUN_TIME_S=get_microtime2()
  #self.response.out.write('<h4>'+str(RUN_TIME_S)+'</h4>')

def bmk_end(self):
  global RUN_TIME_E,DB_TIME
  RUN_TIME_E=get_microtime2()
  #self.response.out.write('<h4>'+str(RUN_TIME_E)+'</h4>')
  RUN_TIME = float(RUN_TIME_E) - float(RUN_TIME_S)
  self.response.out.write('<div id="state">'+str(DB_TIME)+' Queries and RunTime in %0.6f seconds.</div>' % RUN_TIME)
  DB_TIME=0

def grab_url(self,url):
  url_cache = deserialize_entities(memcache.get(url),0)
  if url_cache is not None:
      return url_cache
  else:
      try:
        url_cache = urlfetch.fetch(url=url, method=urlfetch.GET)
	#asyc fetch
	#rpc = urlfetch.create_rpc()
        #urlfetch.make_fetch_call(rpc, url)
        #result = rpc.get_result()
        #if result.status_code == 200:
        #  url_cache = result.content

      except Exception, err:
        logging.info('%s could not be reached' % url)
        url_cache = urlfetch.fetch(url=url, method=urlfetch.GET)
      if not memcache.set(url, serialize_entities(url_cache)):
          logging.error("Memcache set failed.")
      return url_cache

####################

class UploadHandler(webapp.RequestHandler):
  def get(self,id):
     pass
     #(\d+)\?qqfile=([0-9a-z_\.]+)
     #import os
     #entryIndex = str(id)
     #self.response.out.write(entryIndex+"<br>"+os.environ["QUERY_STRING"])

  def post(self,id):
    global blogname
    #from google.appengine.api import images
    #import getimageinfo
    file_data = self.request.body
    logging.info('Size: %d' % len(file_data))
    #file = self.request.POST['file']

    #content_type, width, height = getimageinfo.getImageInfo(file)

    #avatar = images.resize(self.request.get("img"), 32, 32)
    #image = images.Image(file)
    #img = image.crop(0.0, 0.0, 0.5, 0.5)
    #img = image.execute_transforms(output_encoding=images.JPEG)
    if len(file_data)>0:
      if len(file_data) > 1024*1024:
        output_json({'error':"Image is too large (over 1M)."})
      entryIndex = int(id)
      qstring=os.environ["QUERY_STRING"]
      m = re.search("^qqfile=([0-9a-z_\.]+)$", qstring, re.I )
      if m:
        filename = unicode(str(m.group(1)),'utf-8')
      else:
        output_json({'error':"No Image Name."})

      logging.info('Name: %s' % filename)
      logging.info('Index: %s' % str(entryIndex))
      m = re.search("^([0-9a-z_]+)\.(jpg|gif|png)$", filename, re.I )
      file_url =""
      if m:
        if m.group(2).lower()=='jpg':
	  filetype='image/jpeg'
	elif m.group(2).lower()=='gif':
	  filetype='image/gif'
	elif m.group(2).lower()=='png':
	  filetype='image/png'
	else:
	  output_json({'error':"Invalid Image Type."})
        if entryIndex > 0:
          def txn():
            pic_index = PicIndex.get_by_key_name(blogname)
            if pic_index is None:
              pic_index = PicIndex(key_name=blogname)
            else:
              pic_index.max_index += 1
            new_index = pic_index.max_index
	    pic_index.put()
            file_url = "http://%s/%d/%s" % (self.request.host, new_index, filename)
	    logging.info('file_url: %s' % str(file_url))
	    #imageData = images.Image(file_data)
            entity = BlogPics(
              key_name=blogname + str(new_index),
              parent=pic_index, index=new_index,
              data=file_data, mimetype=filetype, info=filename,entryIndex=entryIndex)
            entity.put()
            #array('success'=>true,'img'=>$img,'id'=>$insert_id);
	    output_json({'success':"true",'img':file_url})
          #db.run_in_transaction(txn)
	  txn()

        else:
          output_json({'error':"Id lost."})
        #
        #self.response.out.write("Your uploaded file is now available at %s" % (file_url,))
      else:
        output_json({'error':"Invalid Image Name."})
    else:
      output_json({'error':"Nothing to upload.3"})

class DelImageHandler(webapp.RequestHandler):
  def get(self, index, filename):
    global blogname
    #entity = BlogPics.get_by_key(int(id))
    entity = BlogPics.get_by_key_name(blogname + str(index), parent=db.Key.from_path('PicIndex', blogname))
    if entity is not None:
      def txn():
        entity.delete()
      db.run_in_transaction(txn)
      output_json({'ok':"delete successfully"})
    else:
      output_json({'err':"Image Not found."+filename})

class DownloadHandler(webapp.RequestHandler):
  def output_content(self, content, serve=True):
    self.response.headers['Content-Type'] = content.mimetype
    last_modified = content.created.strftime(HTTP_DATE_FMT)
    self.response.headers['Last-Modified'] = last_modified
    self.response.headers['ETag'] = content.etag
    if serve:
      self.response.headers['Content-Type'] = content.mimetype
      self.response.out.write(content.data)
    else:
      self.response.set_status(304)

  def get(self, index, filename):
    global blogname

    #entity = BlogPics.get_by_key(int(id))
    entity = BlogPics.get_by_key_name(blogname + str(index), parent=db.Key.from_path('PicIndex', blogname))
    if entity is not None:

      serve = True
      if 'If-Modified-Since' in self.request.headers:

	my_Modified_Since=self.request.headers['If-Modified-Since']
	#IE8: Thu, 17 May 2012 17:13:07 GMT; length=52664
        import re
        m = re.search(";", str(my_Modified_Since))
        if m:
	  my_Modified_Since=my_Modified_Since.split(';')[0]

        last_seen = datetime.datetime.strptime(my_Modified_Since,HTTP_DATE_FMT)
	#self.response.out.write(last_seen)
	#ValueError: unconverted data remains: ; length=37269
        if last_seen >= entity.created.replace(microsecond=0):
          serve = False
      if 'If-None-Match' in self.request.headers:
        etags = [x.strip('" ')
                 for x in self.request.headers['If-None-Match'].split(',')]
        if entity.etag in etags:
          serve = False
      #self.response.out.write(serve)
      self.output_content(entity, serve)

    else:
      self.error(404)
      self.response.out.write('404 Error image')

class SearchHandler(webapp.RequestHandler):
  def get(self,*args):
    global blogname
    from urllib import unquote

    service_ok = service_chk()
    service_ok.chk_site()
    service_ok.chk_memcache()

    bmk_start(self)
    mycounter=get_count("mytest")
    increment("mytest")
    header(self,"搜索结果")
    results = m_qc("SELECT * FROM CAIP ORDER BY date DESC",10,0)
    msgs=data_caip(results)
    arr={
	  'mycounter' : mycounter,
	  'msgs': msgs,
	  'logout':url_logout(self.request.uri)
    }
    tmpl=zd_tmpl(self)
    tmpl.render(arr,'search.html')
    bmk_end(self)
    footer(self)

class Prefresh(webapp.RequestHandler):
  def get(self):
    pass
    #eachpage=10
    #sum=m_nc("SELECT __key__ FROM CAIP")
    #page_n,page_l,page_s,page_e,cp,pages,offset=get_page_arr(1,sum,eachpage)
    #for cp in range(1,pages):
    #  offset=(cp - 1) * eachpage
    #  results = m_qc("SELECT * FROM CAIP ORDER BY date DESC",eachpage,offset)

class FreshCache(webapp.RequestHandler):
  def get(self):
    chk_user(self)
    service_ok = service_chk()
    if service_ok.memcache_ok:
      memcache.flush_all()

class GrabNew(webapp.RequestHandler):
  def get(self):
    pass

class Login(webapp.RequestHandler):
  def get(self):
    if val_user():
      self.redirect("/")
    else:
      self.redirect(users.create_login_url(self.request.uri))
  def post(self):
    import cgi,os
    import urllib
    from google.appengine.api import urlfetch
    global is_local
    is_err=0
    form = cgi.FieldStorage()
    if is_local<>1:

      myform_data = {"privatekey": '这个不可能给你的～',
                   "remoteip": os.environ['REMOTE_ADDR'],
                   "challenge": form["recaptcha_challenge_field"].value,
	           "response": form["recaptcha_response_field"].value
		   }
      myform_data = urllib.urlencode(myform_data)
      postdata = urlfetch.fetch(url='http://www.google.com/recaptcha/api/verify',
                              payload=myform_data, method=urlfetch.POST,
			      headers={'Content-Type': 'application/x-www-form-urlencoded'})
      if postdata.status_code == 200:
        m2 = re.search("^true\n", postdata.content, re.I)
        if m2 is None:
          is_err=1
      else:
        is_err=1

    if (str(form["keycode"].value)=='只是为了方便管理') & (is_err==0):
      self.redirect(users.create_login_url(self.request.uri))
    else:
      header(self,"Failed to login.")
      self.response.out.write('<h1>Failed to login.</h1>')
      self.response.out.write('<p><a href="/dl">Back</a></p>')
      footer(self)

class EmptyBlog(webapp.RequestHandler):
  def get(self):
    if val_user():
      q_del("BlogTag")
      q_del("BlogTags")
      q_del("BlogCategory")
      q_del("BlogEntry")
      q_del("BlogIndex")

class EditSingle(webapp.RequestHandler):
  def post(self):
    import cgi
    global blogname
    chk_user(self)
    form = cgi.FieldStorage()
    chk_empty(self,"index",form)
    index = str(form["index"].value)
    m = re.search("^([0-9]+)_([0-9]+)$", str(index), re.I)
    if m is None:
      output_json({'err':"index lost"})
    else:
      rst=get_single(blogname, int(m.group(1)), int(m.group(2)))
      chk_index(self,rst)
      chk_empty(self,"title",form)
      chk_empty(self,"body",form)
      title = str(form["title"].value)
      category = ""
      mytaglist = ""
      body = str(form["body"].value)

      update_single(blogname,rst,title,body)

      #output_json([{'index': str(rst.index),'title': title.encode('utf-8'),'body': body.encode('utf-8'),'category': category.encode('utf-8'),'tag': mytaglist.encode('utf-8')}])

    header(self,"OK")
    self.response.out.write('<h1>Edit page successfully</h1>')
    self.response.out.write('<p><a href="/r">Back</a></p>')
    footer(self)
    #sys.exit(1)

  def get(self):
    global blogname
    chk_user(self)
    index = self.request.get('i')
    mykey = self.request.get('key')
    m = re.search("_([0-9]+)$", str(mykey), re.I)
    if not m.group(1):
      output_json({'err':"key lost"})
    else:
      mykey=m.group(1)
    m = re.search("^([0-9]+)$", str(index), re.I)
    if not m.group(1):
      output_json({'err':"index lost"})
    else:
      rst=get_single(blogname, int(m.group(1)),int(mykey))
      if rst.index and int(rst.index)<=0:
        output_json({'err':'Can\'t find this page.'})
      arr={}
      arr['index']=str(rst.index)
      arr['title']=rst.title.encode('utf-8')
      arr['body']=rst.body.encode('utf-8')
      arr['category']=''
      arr['tag']=''
      output_json([{'key': mykey,'index': arr['index'],'title': arr['title'],'body': arr['body'],'category': arr['category'],'tag': arr['tag']}])
    sys.exit(1)

class EditBlog(webapp.RequestHandler):
  def post(self):
    import cgi
    global blogname
    chk_user(self)
    form = cgi.FieldStorage()
    chk_empty(self,"index",form)
    index = str(form["index"].value)
    if not is_numb(index):
      output_json({'err':"index lost"})
    else:
      rst=get_entry(blogname, int(index))
      chk_index(self,rst)
      chk_empty(self,"title",form)
      chk_empty(self,"body",form)
      chk_empty(self,"category",form)
      chk_empty(self,"tag",form)
      title = str(form["title"].value)
      category = str(form["category"].value)
      mytaglist = str(form["tag"].value)
      body = str(form["body"].value)

      update_blog(blogname,rst,title,body,category,mytaglist)

      #output_json([{'index': str(rst.index),'title': title.encode('utf-8'),'body': body.encode('utf-8'),'category': category.encode('utf-8'),'tag': mytaglist.encode('utf-8')}])

    header(self,"OK")
    self.response.out.write('<h1>Edit blog successfully</h1>')
    self.response.out.write('<p><a href="/r">Back</a></p>')
    footer(self)
    #sys.exit(1)

  def get(self):
    global blogname
    chk_user(self)
    index = self.request.get('i')
    m = re.search("^([0-9]+)$", str(index), re.I)
    if not m.group(1):
      output_json({'err':"index lost"})
    else:
      rst=get_entry(blogname, int(m.group(1)))
      if rst.index and int(rst.index)<=0:
        err("Can't find this entry.")
      arr={}
      arr['index']=str(rst.index)
      arr['title']=rst.title.encode('utf-8')
      arr['body']=rst.body.encode('utf-8')
      arr['category']=rst.cat.name.encode('utf-8')

      mytags=""
      if(rst.tag and rst.tag.name1 is not None):
        mytags+=rst.tag.name1.name
      if(rst.tag and rst.tag.name2 is not None):
        if mytags=="":
          mytags+=rst.tag.name2.name
	else:
          mytags+=","+rst.tag.name2.name
      if(rst.tag and rst.tag.name3 is not None):
        if mytags=="":
          mytags+=rst.tag.name3.name
	else:
          mytags+=","+rst.tag.name3.name
      if(rst.tag and rst.tag.name4 is not None):
        if mytags=="":
          mytags+=rst.tag.name4.name
	else:
          mytags+=","+rst.tag.name4.name
      if(rst.tag and rst.tag.name5 is not None):
        if mytags=="":
          mytags+=rst.tag.name5.name
	else:
          mytags+=","+rst.tag.name5.name
      arr['tag']=mytags.encode('utf-8')
      #print arr['tag']
      #sys.exit(1)
      output_json([{'index': arr['index'],'title': arr['title'],'body': arr['body'],'category': arr['category'],'tag': arr['tag']}])
    sys.exit(1)

class DelSingle(webapp.RequestHandler):
  def post(self):
    import cgi
    global blogname
    chk_user(self)
    form = cgi.FieldStorage()
    chk_empty(self,"index",form)
    index = str(form["index"].value)
    m = re.search("^([0-9]+)_([0-9]+)$", str(index), re.I)
    if m is None:
      output_json({'err':"index lost"})
    else:
      if int(m.group(2))==1:
        rst = m_q("SELECT * FROM SingleEntry where index = :1",1000,0,int(m.group(1)))
	def txn():
	  for x in rst:
	    x.delete()
	db.run_in_transaction(txn)
      else:
        rst=get_single(blogname, int(m.group(1)), int(m.group(2)))
        def txn():
          rst.delete()
        db.run_in_transaction(txn)
      output_json({'ok':"delete successfully"})

class DelBlog(webapp.RequestHandler):
  def post(self):
    import cgi
    global blogname
    chk_user(self)
    form = cgi.FieldStorage()
    chk_empty(self,"index",form)
    index = str(form["index"].value)
    if not is_numb(index):
      output_json({'err':"index lost"})
    else:
      rst=get_entry(blogname, int(index))
      chk_index(self,rst)

      def txn():
        rst.delete()

      db.run_in_transaction(txn)
      output_json({'ok':"delete successfully"})

class DelCat(webapp.RequestHandler):
  def get(self,*args):
    global blogname
    from urllib import unquote
    mycat=unquote(args[0])
    myobj=get_category(blogname,mycat)
    if myobj is None:
      self.error(404)
      self.response.out.write("Can't find this category.")
      sys.exit(1)
    header(self,"删除目录")
    cat_q=db.GqlQuery("SELECT __key__ FROM BlogEntry where cat = :1", myobj.key())
    asum=q_num(cat_q)
    if asum > 0:
      self.response.out.write('抱歉，无法删除目录 [ '+mycat+' ]，该目录不为空。')
      self.response.out.write('<p><a href="javascript:void(0);" onclick="history.go(-1);">Back</a></p>')
      sys.exit(1)
    arr={
	  'action' : "/dc/"+mycat+"/", #unicode(mycat,'utf-8'),
	  'name' : mycat,
	  'info' : '本次操作将会删除目录 [ '+mycat+' ] ',
	  'target' : "目录"
    }
    tmpl=zd_tmpl(self)
    tmpl.render(arr,'delete.html')
    footer(self)

  def post(self,*args):
    global blogname
    from urllib import unquote
    mycat=unquote(args[0])
    myobj=get_category(blogname,mycat)
    if myobj is None:
      self.error(404)
      self.response.out.write("Can't find this category.")
      sys.exit(1)

    cat_q=db.GqlQuery("SELECT __key__ FROM BlogEntry where cat = :1", myobj.key())
    asum=q_num(cat_q)
    if asum > 0:
      self.response.out.write('抱歉，无法删除目录 [ '+mycat+' ]，该目录不为空。')
      self.response.out.write('<p><a href="javascript:void(0);" onclick="history.go(-1);">Back</a></p>')
      sys.exit(1)

    def txn():
        myobj.delete()
    db.run_in_transaction(txn)
    header(self,"删除目录")
    self.response.out.write('删除目录成功。')
    self.response.out.write('<p><a href="/r">Back</a></p>')
    footer(self)

class DelTag(webapp.RequestHandler):
  def get(self,*args):
    global blogname
    from urllib import unquote
    mytag=unquote(args[0])
    myobj=get_tag(blogname,mytag)
    if myobj is None:
      self.error(404)
      self.response.out.write("Can't find this tag.")
      sys.exit(1)
    header(self,"删除标签")
    myresults=[]
    tag_keys=get_tags_key(myobj)
    for mykey in tag_keys:
      tag_q=db.GqlQuery("SELECT * FROM BlogEntry where tag = :1", mykey)
      myresults = myresults + tag_q.fetch(1000)
      if len(myresults) > 0:
        break

    asum=len(myresults)
    if asum > 0:
      self.response.out.write('抱歉，无法删除标签 [ '+mycat+' ]，该标签不为空。')
      self.response.out.write('<p><a href="javascript:void(0);" onclick="history.go(-1);">Back</a></p>')
      sys.exit(1)
    arr={
	  'action' : "/dt/"+mytag+"/", #unicode(mytag,'utf-8'),
	  'name' : mytag,
	  'info' : '本次操作将会删除标签 [ '+mytag+' ] ',
	  'target' : "标签"
    }
    tmpl=zd_tmpl(self)
    tmpl.render(arr,'delete.html')
    footer(self)

  def post(self,*args):
    global blogname
    from urllib import unquote
    mytag=unquote(args[0])
    myobj=get_tag(blogname,mytag)
    if myobj is None:
      self.error(404)
      self.response.out.write("Can't find this tag.")
      sys.exit(1)

    myresults=[]
    tag_keys=get_tags_key(myobj)
    for mykey in tag_keys:
      tag_q=db.GqlQuery("SELECT * FROM BlogEntry where tag = :1", mykey)
      myresults = myresults + tag_q.fetch(1000)
      if len(myresults) > 0:
        break
    asum=len(myresults)
    if asum > 0:
      self.response.out.write('抱歉，无法删除标签 [ '+mycat+' ]，该标签不为空。')
      self.response.out.write('<p><a href="javascript:void(0);" onclick="history.go(-1);">Back</a></p>')
      sys.exit(1)

    def txn():
        myobj.delete()
    db.run_in_transaction(txn)
    header(self,"删除标签")
    self.response.out.write('删除标签成功。')
    self.response.out.write('<p><a href="/r">Back</a></p>')
    footer(self)

class TagPage(webapp.RequestHandler):
  def get(self,*args):
      global blogname
      from urllib import unquote
      if args:
        mytag=unquote(args[0])
	mytagobj=get_tag(blogname,mytag)
	if mytagobj is None:
	  self.error(404)
          self.response.out.write("Can't find this tag.")
	else:
	  acp=1
          aeachpage=1000
          service_ok = service_chk()
          service_ok.chk_site()
          service_ok.chk_memcache()

          bmk_start(self)
          mycounter=get_count("mytest")
          increment("mytest")

          if len(args)==2:
            acp=int(args[1])

	  myresults=[]
          tag_keys=get_tags_key(mytagobj)
	  for mykey in tag_keys:
	    tag_q=db.GqlQuery("SELECT * FROM BlogEntry where tag = :1", mykey)
	    myresults = myresults + tag_q.fetch(1000)

          asum=len(myresults)
          apage_n,apage_l,apage_s,apage_e,acp,apages,aoffset=get_page_arr(acp,asum,aeachpage)

	  header(self,mytag)
          #results = m_qc("SELECT * FROM BlogEntry ORDER BY created DESC",aeachpage,aoffset)
          blogs=data_blogs(myresults)
          #get_entry(blogname, mytagobj.index):

	  results = m_qc("SELECT * FROM CAIP ORDER BY date DESC",10,0)
          msgs=data_caip(results)
	  arr={

	    'asum' : asum,
	    'aeachpage' : aeachpage,
	    'acp' : acp,
	    'apages' : range(apage_s,apage_e),
	    'apage_n' : apage_n,
	    'apage_l' : apage_l,
	    'apage_max' : apages,
            'mytag' : mytag,
            'mycounter' : mycounter,
	    'blogs' : blogs,
	    'msgs': msgs,
	    'logout':url_logout(self.request.uri)
          }
          tmpl=zd_tmpl(self)
          tmpl.render(arr,'tag.html')
          bmk_end(self)
          footer(self)
      else:
        self.error(404)
        self.response.out.write('404 Error Page')

class CatPage(webapp.RequestHandler):
  def get(self,*args):
      global blogname
      from urllib import unquote
      if args:
        mycat=unquote(args[0])
	mycatobj=get_category(blogname,mycat)
	if mycatobj is None:
	  self.error(404)
          self.response.out.write("Can't find this category.")
	else:
	  #self.response.out.write(mycat)
          acp=1
          aeachpage=10
          service_ok = service_chk()
          service_ok.chk_site()
          service_ok.chk_memcache()

          bmk_start(self)
          mycounter=get_count("mytest")
          increment("mytest")

          if len(args)==2:
            acp=int(args[1])

	  cat_q=db.GqlQuery("SELECT __key__ FROM BlogEntry where cat = :1", mycatobj.key())
          asum=q_num(cat_q)
          apage_n,apage_l,apage_s,apage_e,acp,apages,aoffset=get_page_arr(acp,asum,aeachpage)

	  header(self,mycat)
          catqq = db.GqlQuery("SELECT * FROM BlogEntry where cat = :1 ORDER BY created DESC",mycatobj.key())
	  results=catqq.fetch(aeachpage,aoffset)
          #results = m_qc("SELECT * FROM BlogEntry where cat = :cat ORDER BY created DESC",aeachpage,aoffset,cat=mycatobj.key())
          blogs=data_blogs(results)

	  results = m_qc("SELECT * FROM CAIP ORDER BY date DESC",10,0)
          msgs=data_caip(results)
	  arr={

	    'asum' : asum,
	    'aeachpage' : aeachpage,
	    'acp' : acp,
	    'apages' : range(apage_s,apage_e),
	    'apage_n' : apage_n,
	    'apage_l' : apage_l,
	    'apage_max' : apages,
            'mycat' : mycat,
            'mycounter' : mycounter,
	    'blogs' : blogs,
	    'msgs': msgs,
	    'logout':url_logout(self.request.uri)
          }
          tmpl=zd_tmpl(self)
          tmpl.render(arr,'category.html')
          bmk_end(self)
          footer(self)

      else:
        self.error(404)
        self.response.out.write('404 Error Page')

class EntryPage(webapp.RequestHandler):
  def get(self,*args):
      global blogname
      #from urllib import unquote
      if args:
        entry_index=int(args[0])
	myobj=get_entry(blogname,entry_index)

	if myobj is None:
	  self.error(404)
	  #self.response.set_status(404)
          self.response.out.write("Can't find this entry.")
	else:

          service_ok = service_chk()
          service_ok.chk_site()
          service_ok.chk_memcache()

          bmk_start(self)
          mycounter=get_count("mytest")
          increment("mytest")

	  header(self,myobj.title.encode('utf-8'))

	  results = m_qc("SELECT * FROM CAIP ORDER BY date DESC",10,0)
          msgs=data_caip(results)

	  mytags=[]
	  myobj_arr=[myobj]
	  prefetch_refprops(myobj_arr, BlogEntry.cat, BlogEntry.tag)
          myobj=myobj_arr[0]
	  if(myobj.tag and myobj.tag.name1 is not None):
            mytags.append(myobj.tag.name1.name.encode('utf-8'))
          if(myobj.tag and myobj.tag.name2 is not None):
            mytags.append(myobj.tag.name2.name.encode('utf-8'))
          if(myobj.tag and myobj.tag.name3 is not None):
            mytags.append(myobj.tag.name3.name.encode('utf-8'))
          if(myobj.tag and myobj.tag.name4 is not None):
            mytags.append(myobj.tag.name4.name.encode('utf-8'))
          if(myobj.tag and myobj.tag.name5 is not None):
            mytags.append(myobj.tag.name5.name.encode('utf-8'))
          more_entries=[]
	  arr={
            'index': str(myobj.index),
	    'title' : myobj.title.encode('utf-8'),
	    'body': myobj.body.encode('utf-8'),
	    'cat': myobj.cat.name.encode('utf-8'),
            'user': myobj.user.encode('utf-8'),
	    'created': str(myobj.created),
            'mycounter' : mycounter,
	    'tags': mytags,
	    'msgs': msgs,
	    'more_entries' : more_entries,
	    'logout':url_logout(self.request.uri)
          }
          tmpl=zd_tmpl(self)
          tmpl.render(arr,'entry.html')
          bmk_end(self)
          footer(self)

      else:
        self.error(404)
        self.response.out.write('404 Error Page')

#main page
class MainPage(webapp.RequestHandler):
  def get(self,*args):
      global blogname,is_local,myhost
      cp=1
      acp=1
      eachpage=10
      aeachpage=3
      service_ok = service_chk()
      service_ok.chk_site()
      service_ok.chk_memcache()

      #if(os.environ['PATH_INFO']):
      #  cur_request_uri=os.environ['PATH_INFO'];
      #  $etagFile = get_microtime().','.md5($cur_request_uri);
      #  $etagHeader=(isset($_SERVER['HTTP_IF_NONE_MATCH']) ? trim($_SERVER['HTTP_IF_NONE_MATCH']) : false);
      #  header("Etag: $etagFile");
      #  #make sure caching is turned on
      #  header('Cache-Control: public');
      #  $etagFile_time_arr=explode(",",$etagFile);
      #  $etagFile_time=$etagFile_time_arr[0];

      #  $etagHeader_time_arr=explode(",",$etagHeader);
      #  $etagHeader_time=$etagHeader_time_arr[0];
      #  if (preg_match("/^([0-9]+),(.+)^/i",$etagHeader) && floatval($etagHeader_time) - floatval($etagFile_time) < 3600){
      #    header("HTTP/1.1 304 Not Modified");
      #    return;

      bmk_start(self)
      mycounter=get_count("mytest")
      increment("mytest")

      page_type='a'
      if args:
        if str(args[0])=='c':
	  page_type='c'
          cp=int(args[1])
	else:
	  acp=int(args[0])

      sum=100 #m_nc("SELECT __key__ FROM CAIP")
      page_n,page_l,page_s,page_e,cp,pages,offset=get_page_arr(cp,sum,eachpage)

      asum=m_nc("SELECT __key__ FROM BlogEntry")
      apage_n,apage_l,apage_s,apage_e,acp,apages,aoffset=get_page_arr(acp,asum,aeachpage)

      header(self,"CAI PIAO")
      results = m_qc("SELECT * FROM BlogEntry ORDER BY created DESC",aeachpage,aoffset)
      #self.response.out.write(str(results))
      #return
      blogs=data_blogs(results)

      results = m_qc("SELECT * FROM BlogCategory ORDER BY created DESC",100,0)
      cats=data_cats(results)

      results = m_qc("SELECT * FROM BlogTag ORDER BY created DESC",100,0)
      tags=data_tags(results)

      #results = mq_q(CAIP,[],['-date'],[],eachpage,offset)
      results = m_qc("SELECT * FROM CAIP ORDER BY date DESC",eachpage,offset)
      msgs=data_caip(results)
      singlepages= m_qc("SELECT * FROM SingleEntry where is_first = :1 ORDER BY created DESC",10,0,1)
      arr={
        'is_local':is_local,
	'myhost':myhost,

	'page_type':page_type,
	'sum' : sum,
	'eachpage' : eachpage,
	'cp' : cp,
	'pages' : range(page_s,page_e),
	'page_n' : page_n,
	'page_l' : page_l,
	'page_max' : pages,

	'asum' : asum,
	'aeachpage' : aeachpage,
	'acp' : acp,
	'apages' : range(apage_s,apage_e),
	'apage_n' : apage_n,
	'apage_l' : apage_l,
	'apage_max' : apages,
        'singlepages' : singlepages,
        'msgs': msgs,
	'mycounter' : mycounter,
	'blogs' : blogs,
	'cats' : cats,
	'tags' : tags,
	'logout':url_logout(self.request.uri)
      }
      tmpl=zd_tmpl(self)
      tmpl.render(arr,'index.html')
      bmk_end(self)
      footer(self)

class MngPicPage(webapp.RequestHandler):
  def get(self,*args):
      global blogname,is_local,myhost
      cp=1
      eachpage=3
      service_ok = service_chk()
      service_ok.chk_site()
      service_ok.chk_memcache()

      if args:
	  cp=int(args[0])

      bmk_start(self)
      mycounter=get_count("mytest")
      increment("mytest")

      sum=m_nc("SELECT __key__ FROM BlogPics")
      page_n,page_l,page_s,page_e,cp,pages,offset=get_page_arr(cp,sum,eachpage)

      header(self,"PICS MANAGEMENT")
      results = m_qc("SELECT * FROM BlogPics ORDER BY created DESC",eachpage,offset)
      #self.response.out.write(str(results))
      #return
      pics=data_pics(results)

      arr={
        'is_local':is_local,
	'myhost':myhost,

	'asum' : sum,
	'aeachpage' : eachpage,
	'acp' : cp,
	'apages' : range(page_s,page_e),
	'apage_n' : page_n,
	'apage_l' : page_l,
	'apage_max' : pages,

	'mycounter' : mycounter,
	'pics' : pics,
	'logout':url_logout(self.request.uri)
      }
      tmpl=zd_tmpl(self)
      tmpl.render(arr,'picindex.html')
      bmk_end(self)
      footer(self)


class DL(webapp.RequestHandler):
  def get(self,*args):
    global is_local
    if val_user():
      self.redirect("/")
    else:
      #referer = request.META.get('HTTP_REFERER', None)
      zd_login(self,is_local)

class Save(webapp.RequestHandler):
  def post(self):
    global blogname
    chk_user(self)
    sys_err = 0
    err_msg = ""

    form = cgi.FieldStorage()
    if not form["title"] or str(form["title"].value) == "":
      err("Please enter the title.")
    if not form["body"] or str(form["body"].value) == "":
      err("Please enter the body.")
    if not form["category"] or str(form["category"].value) == "":
      err("Please enter the category.")
    if not form["tag"] or str(form["tag"].value) == "":
      err("Please enter the tag.")


    if sys_err == 0:
      post_entry(val_user(), blogname, str(form["title"].value), str(form["body"].value), str(form["category"].value), str(form["tag"].value))

    header(self,"OK")
    self.response.out.write('<h1>Add blog successfully</h1>')
    self.response.out.write('<p><a href="/r">Back</a></p>')
    footer(self)

class Clear_All(webapp.RequestHandler):
  def post(self):
    chk_user(self)
    sys_err = 0
    err_msg = ""
    #q_del("CAIP")
    header(self,"OK")
    self.response.out.write('<h1>Clear All</h1>')
    self.response.out.write('<p><a href="/">Back</a></p>')
    footer(self)

class Update(webapp.RequestHandler):
  global Max_list_num
  def post(self):
    chk_user(self)
    sys_err = 0
    err_msg = ""

    if sys_err == 0:
      update_url = 'http://www.gdfc.org.cn/play_list_game_5.html' #seq
      #http://www.gdfc.org.cn/play_list_game_1.html #367
      #result = urlfetch.fetch(url=update_url, method=urlfetch.GET)
      result = grab_url(self,update_url)
      stats = memcache.get_stats()

      header(self,"CAI PIAO")

      #self.response.out.write("<b>Cache Hits:%s</b><br>" % stats['hits'])
      #self.response.out.write("<b>Cache Misses:%s</b><br><br>" % stats['misses'])

      query = db.GqlQuery("SELECT * FROM CAIP ")
      results = query.fetch(Max_list_num)
      self.response.out.write("<b>Sum:%s</b><br>" % len(results))
      #for item in results:
      #  self.response.out.write("[%s] - %s<br>" % (item.numbs.encode('utf-8'),item.numb7))

      if result.status_code == 200:
        self.response.out.write('CAI PIAO成功:<pre>')

	m = re.search("name='totalPage' value='([0-9]+)'", result.content, re.I)
        if m.group(1):
          self.response.out.write("<b>Pages:%s</b> <form action=\"/update_more\" method=\"get\"><input type=\"submit\" value=\"Refresh More Data\"><input type=\"hidden\" value=\"%s\" name=\"pages\"></form><br>" % (m.group(1),m.group(1)))

	for m in re.finditer(r"([0-9]{7})</td>[^<>]+<td [^<>]+ luckyNo=\"([0-9]{14})\">", result.content, re.I | re.M | re.U | re.L | re.S):
         mydate=str(m.group(1))
         mynumb=str(m.group(2))

	 update_url2 = 'http://www.gdfc.org.cn/datas/drawinfo/twocolorball/draw_'+mydate+'.html'
	 try:
           url_cache2 = urlfetch.fetch(url=update_url2, method=urlfetch.GET)
         except DownloadError:
           logging.info('%s could not be reached' % update_url2)
	 m2 = re.search("<div class=\"play_R_tbox\">([0-9]{4})\-([0-9]{2})\-([0-9]{2})", url_cache2.content, re.I | re.U | re.L)
         if m2.group(1):
           mydate=str(m2.group(1))+'-'+str(m2.group(2))+'-'+str(m2.group(3))
	 else:
	   #try:
           #  raise MyError(mydate)
           #except MyError as e:
           print 'My exception occurred, value:', mydate
	   sys.exit(1)

	 qq = db.GqlQuery("SELECT * FROM CAIP WHERE numbs = :1 ", mynumb)
         is_cz = qq.fetch(1)
	 if len(is_cz) != 1:
	   p = re.compile(r'^([\d]{2})([\d]{2})([\d]{2})([\d]{2})([\d]{2})([\d]{2})([\d]{2})$')
           mynumb_arr=p.match(mynumb)
	   if mynumb_arr.group():
  	     self.response.out.write('date: %s <br>' % mydate)
             e = CAIP()
             e.numbs= mynumb
             e.date = mydate
	     e.numb1= int(mynumb_arr.group(1))
	     e.numb2= int(mynumb_arr.group(2))
	     e.numb3= int(mynumb_arr.group(3))
	     e.numb4= int(mynumb_arr.group(4))
	     e.numb5= int(mynumb_arr.group(5))
	     e.numb6= int(mynumb_arr.group(6))
	     e.numb7= int(mynumb_arr.group(7))
	     try:
               e.put()
             except CapabilityDisabledError:
               # fail gracefully here
               print 'Sorry: Scheduled Maintenance.'
	       sys.exit(1)

	     self.response.out.write('%s => %s [%s] <br>' % (mydate, mynumb, mynumb_arr.group(7)))
	   else:
	     self.response.out.write('Invalid: %s <br>' % (mynumb_arr))

	 else:
	   self.response.out.write('Exists: %s => %s <br>' % (mydate, mynumb))

        self.response.out.write('</pre>')
      else:
        self.response.out.write('CAI PIAO失败['+cgi.escape(result.status_code)+']:<pre>')
	self.response.out.write(result.status_code)
        self.response.out.write('</pre>')

      self.response.out.write('<p><a href="/">Back</a></p>')
      footer(self)

    else:
      header(self,"出错")
      self.response.out.write('<h1>Error</h1>')
      self.response.out.write('<font color=red>'+err_msg+'</font>')
      footer(self)

class Update_More(webapp.RequestHandler):
  global Max_list_num
  def get(self):
    chk_user(self)
    sys_err = 0
    err_msg = ""
    #print "Service Stop.";
    #sys.exit(1)
    #http://www.gdfc.org.cn/play_list_game_1.html #367
    #http://www.gdfc.org.cn/datas/history/twocolorball/history_4.html
    #contextPath+"/datas/pages/more_"+subject_id.value+"_"+pageIndex+".html";
    #"game-1":"/datas/history/367",
    #"game-5":"/datas/history/twocolorball",

    form = cgi.FieldStorage()
    pages= int(form["pages"].value)
    if pages > 0 and sys_err == 0:
      update_url = 'http://www.gdfc.org.cn/datas/history/twocolorball/history_'+str(pages)+'.html' #seq
      result = grab_url(self,update_url)
      stats = memcache.get_stats()

      header(self,"CAI PIAO")

      #self.response.out.write("<b>Cache Hits:%s</b><br>" % stats['hits'])
      #self.response.out.write("<b>Cache Misses:%s</b><br><br>" % stats['misses'])

      query = db.GqlQuery("SELECT * FROM CAIP ")
      results = query.fetch(Max_list_num)
      self.response.out.write("<b>Sum:%s</b><br>" % len(results))
      #for item in results:
      #  self.response.out.write("[%s] - %s<br>" % (item.numbs.encode('utf-8'),item.numb7))

      if result.status_code == 200:
        self.response.out.write('CAI PIAO成功:<pre>')
	next_page= pages - 1
	if next_page >= 1:
          self.response.out.write("Continue... <form action=\"/update_more\" method=\"get\"><input type=\"submit\" value=\"Refresh More Data [%s]\"><input type=\"hidden\" value=\"%s\" name=\"pages\"></form><meta http-equiv=\"refresh\" content=\"5;URL=/update_more?pages=%s\"><br>" % (next_page,next_page,next_page))
	else:
	  result.content='';
	  self.response.out.write("Finished update.")

	for m in re.finditer(r"([0-9]{7})</td>[^<>]+<td [^<>]+ luckyNo=\"([0-9]{14})\">", result.content, re.I | re.M | re.U | re.L | re.S):
         mydate=str(m.group(1))
         mynumb=str(m.group(2))

	 update_url2 = 'http://www.gdfc.org.cn/datas/drawinfo/twocolorball/draw_'+mydate+'.html'
	 url_cache2 = urlfetch.fetch(url=update_url2, method=urlfetch.GET)
	 m2 = re.search("<div class=\"play_R_tbox\">([0-9]{4})\-([0-9]{2})\-([0-9]{2})", url_cache2.content, re.I | re.U | re.L)
         if m2.group(1):
           mydate=str(m2.group(1))+'-'+str(m2.group(2))+'-'+str(m2.group(3))
	 else:
	   print 'My exception occurred, value:', mydate
	   sys.exit(1)

	 qq = db.GqlQuery("SELECT * FROM CAIP WHERE numbs = :1 ", mynumb)
         is_cz = qq.fetch(1)
	 if len(is_cz) != 1:
	   p = re.compile(r'^([\d]{2})([\d]{2})([\d]{2})([\d]{2})([\d]{2})([\d]{2})([\d]{2})$')
           mynumb_arr=p.match(mynumb)
	   if mynumb_arr.group():
  	     e = CAIP()
             e.numbs= mynumb
             e.date = mydate
	     e.numb1= int(mynumb_arr.group(1))
	     e.numb2= int(mynumb_arr.group(2))
	     e.numb3= int(mynumb_arr.group(3))
	     e.numb4= int(mynumb_arr.group(4))
	     e.numb5= int(mynumb_arr.group(5))
	     e.numb6= int(mynumb_arr.group(6))
	     e.numb7= int(mynumb_arr.group(7))
             try:
               e.put()
             except CapabilityDisabledError:
               # fail gracefully here
               print 'Sorry: Scheduled Maintenance.'
	       sys.exit(1)
	     self.response.out.write('%s => %s [%s] <br>' % (mydate, mynumb, mynumb_arr.group(7)))
	   else:
	     self.response.out.write('Invalid: %s <br>' % (mynumb_arr))

	 else:
	   self.response.out.write('Exists: %s <br>' % (mynumb))

        self.response.out.write('</pre>')
      else:
        self.response.out.write('CAI PIAO失败['+cgi.escape(result.status_code)+']:<pre>')
	self.response.out.write(result.status_code)
        self.response.out.write('</pre>')

      self.response.out.write('<p><a href="/">Back</a></p>')
      footer(self)

    else:
      header(self,"出错")
      self.response.out.write('<h1>Error</h1>')
      self.response.out.write('<font color=red>'+err_msg+'</font>')
      footer(self)

class SinglePage(webapp.RequestHandler):
  def get(self,qs):
    bmk_start(self)
    chk_user(self)
    header(self,"Add Single Page")

    results = m_qc("SELECT * FROM CAIP ORDER BY date DESC",10,0)
    msgs=data_caip(results)
    singlepages= m_qc("SELECT * FROM SingleEntry where is_first = :1 ORDER BY created DESC",10,0,1)

    arr={
        'msgs' : msgs,
        'singlepages' : singlepages,
        'mycounter' : get_count("mytest"),
	'logout':url_logout(self.request.uri)
    }
    tmpl=zd_tmpl(self)
    tmpl.render(arr,'add_single.html')
    bmk_end(self)
    footer(self)

  def post(self,qs):
    bmk_start(self)
    chk_user(self)
    header(self,"Add Single Page")
    form = cgi.FieldStorage()
    if (form is not None) and (qs=="add"):
      sys_err = 0
      err_msg = ""

      if (not form.has_key("title")) or (form["title"] is None):
        err("Please enter the title.")
      if (not form.has_key("index")) or (form["index"] is None):
        err("Please enter the index.")
      if (not form.has_key("body")) or (form["body"] is None):
        err("Please enter the body.")
      if (not form.has_key("pagenum")) or (form["pagenum"] is None):
        err("Please enter the page num.")

      if sys_err == 0:
        post_single(val_user(), blogname, str(form["index"].value), str(form["title"].value), str(form["body"].value), str(form["pagenum"].value))

      self.response.out.write('<h1>Add single page successfully</h1>')
      self.response.out.write('<p><a href="/r">Back</a></p>')
    else:
      self.error(404)
      self.response.out.write('404 Error page')
    bmk_end(self)
    footer(self)

class ShowPage(webapp.RequestHandler):
  def get(self,id,cp):
    global blogname
    acp=1
    aeachpage=1
    if is_numb(cp):
      acp=int(cp)
    single_cz = SingleEntry.get_by_key_name(blogname+str(id)+"_"+str(acp),parent=db.Key.from_path('SingleIndex', blogname))
    if single_cz is None:
      self.error(404)
      self.response.out.write('404 Error page')
    else:
      bmk_start(self)
      header(self,single_cz.title.encode('utf-8'))
      singlepages= m_qc("SELECT * FROM SingleEntry where is_first = :1 ORDER BY created DESC",10,0,1)

      asum=m_nc("SELECT __key__ FROM SingleEntry where index = :1",1000,0,int(id))
      apage_n,apage_l,apage_s,apage_e,acp,apages,aoffset=get_page_arr(acp,asum,aeachpage)

      results = m_qc("SELECT * FROM CAIP ORDER BY date DESC",10,0)
      msgs=data_caip(results)
      arr={
        'asum' : asum,
	'aeachpage' : aeachpage,
	'acp' : acp,
	'apages' : range(apage_s,apage_e),
	'apage_n' : apage_n,
	'apage_l' : apage_l,
	'apage_max' : apages,
	'myindexpage' : 'page/'+str(id)+'/',
        'msgs' : msgs,
        'singlepage' : single_cz,
	'singlepages' : singlepages,
        'mycounter' : get_count("mytest"),
	'logout':url_logout(self.request.uri)
      }
      tmpl=zd_tmpl(self)
      tmpl.render(arr,'single.html')
      bmk_end(self)
      footer(self)

#(r'^games/$', 'MainPage'),
#(r'^games/page(?P\d+)/$', 'MainPage'),
application = webapp.WSGIApplication(
                                     [('/', MainPage),
				      ('/mng/pics/', MngPicPage),
				      ('/mng/pics/(\d+)', MngPicPage),
				      ('/tag/(.*)/', TagPage),
				      ('/tag/(.*)/(\d+)', TagPage),
				      ('/entry/(\d+)', EntryPage),
				      ('/category/(.*)/', CatPage),
				      ('/category/(.*)/(\d+)', CatPage),
				      ('/(c)/(\d+)', MainPage),
				      ('/(\d+)', MainPage),
				      ('/tasks/prefresh', Prefresh),
				      ('/upload/(\d+)', UploadHandler),
				      ('/(\d+)/(.*)', DownloadHandler),
				      ('/rm/(\d+)/(.*)', DelImageHandler),
				      ('/search/(.*)', SearchHandler),
				      #('/tasks/freshcache', FreshCache),
				      #('/tasks/grabnew', GrabNew),
				      ('/login', Login),
				      ('/dl', DL),
				      ('/singlepage/(.*)', SinglePage),
				      ('/page/(\d+)/(.*)', ShowPage),
                                      ('/update', Update),
				      ('/update_more', Update_More),
				      ('/empty', Clear_All),
				      ('/r', Refresh),
				      #('/rb', EmptyBlog),
				      ('/dt/(.*)/', DelTag),
				      ('/dc/(.*)/', DelCat),
				      ('/db', DelBlog),
				      ('/eb', EditBlog),
				      ('/sdb', DelSingle),
				      ('/seb', EditSingle),
				      ('/save', Save)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == "__main__":
  try:
    main()
  except SystemExit, e:
    print e


















