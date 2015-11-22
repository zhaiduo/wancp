# -*- coding:utf-8 -*- ＃必须在第一行或者第二行
#zd_func module
import sys
from google.appengine.ext import db
from zd_define import *

def header(self,title=""):
    self.response.headers['Content-Type'] = 'text/html; charset=utf-8'
    self.response.out.write("""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html xmlns="http://www.w3.org/1999/xhtml"><head><link type="text/css" rel="stylesheet" href="/css/index.css?v=20120111001" /><script type="text/javascript" src="/css/jquery.min.js?v=20120111001" ></script>""")
    if val_user():
      self.response.out.write("""<script src="/css/fileuploader.js?v=20110311" type="text/javascript"></script>
<link href="/css/fileuploader.css?v=20110310" rel="stylesheet" type="text/css" />
<script type="text/javascript">        
        function createUploader(){            
	    var id=parseInt($('#editId').attr('value'));
            var uploader = new qq.FileUploader({
                element: document.getElementById('file-uploader'),
                action: '/upload/'+id,
                debug: false
            });           
        }
	//window.onload = createUploader();
</script><script type="text/javascript" src="/css/atcion.js?v=20120111001" ></script>""")
    self.response.out.write("""<script type="text/javascript" src="/css/page.js?v=20120111001" ></script>
<meta http-equiv="Content-Type" content="text/html; charset=utf-8" /><meta name="google-site-verification" content="ANDtfByBLPf-0oUGuxDqmpgrGp3TvLs7s4u_2M8V9O4" /><link rel="shortcut icon" href="/css/favicon.ico" />""")
      
    if title!="":
      self.response.out.write('<title>'+title+' - 彩票博客 - 不止玩彩票</title>')
    self.response.out.write('<body>')

def footer(self):
    self.response.out.write("<script type=\"text/javascript\">\n")
    self.response.out.write("var _gaq = _gaq || [];\n")
    self.response.out.write("_gaq.push(['_setAccount', 'UA-281730-21']);\n")
    self.response.out.write("_gaq.push(['_trackPageview']);\n")
    self.response.out.write("(function() {\n")
    self.response.out.write("var ga = document.createElement('script'); ga.type = 'text/javascript'; ga.async = true;\n")
    self.response.out.write("ga.src = ('https:' == document.location.protocol ? 'https://ssl' : 'http://www') + '.google-analytics.com/ga.js';\n")
    self.response.out.write("var s = document.getElementsByTagName('script')[0]; s.parentNode.insertBefore(ga, s);\n")
    self.response.out.write("})();\n")
    self.response.out.write("</script></body></html>")

def err(info):
  import sys
  print "content-type:text/html\n"
  print '<link rel="stylesheet" href="/css/index.css" type=text/css><div id="error"><h1>Error: '
  print '%s' % info
  print '</h1><a href="javascript:history.go(-1);">&raquo; Back</a></div>'
  sys.exit()

def get_pages(pages,cp,intv=10):
  if(cp%intv==0):
    nnb=int(cp/intv);
  else:
    nnb=int(cp/intv)+1;
  nn_start=(nnb-1)*intv+1;
  if pages<intv:
    nn_end=pages+1;
  else:
    nn_end=nnb*intv;
  return [ nn_start, nn_end ]

def get_page_arr(cp,sum,content=10,max_pages=100):
  arr={}
  sum=int(sum)
  if sum==0:
    return [ 1, 1, 0, 0, 1, 1, 0 ]
  if(sum % content != 0):
    arr['pages']=int(int(sum/content)+1)
  else:
    arr['pages']=int(sum/content)
  #max pages
  if arr['pages'] > max_pages:
    arr['pages']=max_pages
  arr['offset']=0
  arr['cp']=cp
  if(cp<1 or cp>arr['pages']):
    arr['cp']=1
  if(arr['cp']>1000):
    arr['cp']=1
  arr['offset']=int(content*(arr['cp']-1))
  if(arr['pages']<=1):
    arr['cp']=1
  
  arr['page_s'],arr['page_e']=get_pages(arr['pages'],arr['cp'])

  if(arr['page_e']+1 > arr['pages']):
    arr['page_n']=arr['pages'] 
  else:
    arr['page_n']=arr['page_e']+1
  if(arr['page_s']-1 < 1):
    arr['page_l']=1 
  else:
    arr['page_l']=arr['page_s']-1

  return [ arr['page_n'], arr['page_l'], arr['page_s'], arr['page_e'], arr['cp'], arr['pages'], arr['offset'] ]
  

def zd_login(self,is_local):
  from google.appengine.ext.webapp import template
  import os
  
  header(self,"登录")
  template_values = {
    'is_local':is_local,
    'login_url' : self.request.uri
  }
  path = os.path.join(os.path.dirname(__file__), 'tmpl/login.html')
  self.response.out.write(template.render(path, template_values))
  footer(self)

def chk_user(self):
  from google.appengine.api import users
  user = users.get_current_user()
  if not user:
    err("Please login first.")

def val_user():
  from google.appengine.api import users
  return users.get_current_user()

################################
#dereference multiple ReferenceProperty fields on the same set of entities
#http://blog.notdot.net/2010/01/ReferenceProperty-prefetching-in-App-Engine
def prefetch_refprops(entities, *props):
    fields = [(entity, prop) for entity in entities for prop in props]
    ref_keys = [prop.get_value_for_datastore(x) for x, prop in fields]
    ref_entities = dict((x.key(), x) for x in db.get(set(ref_keys)))
    for (entity, prop), ref_key in zip(fields, ref_keys):
        prop.__set__(entity, ref_entities[ref_key])
    return entities

###############################
def data_blogs(results):
  blogs=[]
  #ReferenceProperty prefetching
  prefetch_refprops(results, BlogEntry.cat, BlogEntry.tag)
  for result in results:
    if result is not None:
      mytags=[]
      #BlogTags.name1.get_value_for_datastore(result.tag)
      if(result.tag and result.tag.name1 is not None):
        mytags.append(result.tag.name1.name.encode('utf-8'))
      if(result.tag and result.tag.name2 is not None):
        mytags.append(result.tag.name2.name.encode('utf-8'))
      if(result.tag and result.tag.name3 is not None):
        mytags.append(result.tag.name3.name.encode('utf-8'))
      if(result.tag and result.tag.name4 is not None):
        mytags.append(result.tag.name4.name.encode('utf-8'))
      if(result.tag and result.tag.name5 is not None):
        mytags.append(result.tag.name5.name.encode('utf-8'))
      blogs.append({
	  'index': str(result.index),
	  'title': result.title.encode('utf-8'),
	  'body': result.body.encode('utf-8'),
	  'cat': result.cat.name.encode('utf-8'),
          'tags': mytags,
          'user': result.user.encode('utf-8'),
	  'created': str(result.created),
      })
  return blogs

def data_pics(results):
  pics=[]
  for result in results:
    if result is not None:
      pics.append({
	  'index': str(result.index),
	  'entryIndex': str(result.entryIndex),
	  'info': result.info.encode('utf-8'),
	  'created': str(result.created),
      })
  return pics

def data_cats(results):
  cats=[]
  for result in results:
    if result is not None:
      cats.append({
	  'index': str(result.index),
	  'name': result.name.encode('utf-8'),
	  'created': str(result.created),
      })
  return cats

def data_tags(results):
  tags=[]
  for result in results:
    if result is not None:
      tags.append({
	  'index': str(result.index),
	  'subindex': str(result.subindex),
	  'name': result.name.encode('utf-8'),
	  'created': str(result.created),
      })
  return tags

def data_caip(results):
  caip=[]
  for result in results:
    if result is not None:
      caip.append({
	  'numbs': str(result.numbs),
	  'numb1': "%02d" % result.numb1,
	  'numb2': "%02d" % result.numb2,
	  'numb3': "%02d" % result.numb3,
	  'numb4': "%02d" % result.numb4,
	  'numb5': "%02d" % result.numb5,
	  'numb6': "%02d" % result.numb6,
	  'numb7': "%02d" % result.numb7,
	  'date': str(result.date),
      })
  return caip

def uname():
  from google.appengine.api import users
  user=users.get_current_user()
  if user:
    nickname=user.nickname()
  else:
    nickname=''
  return nickname

def url_login(url):
  from google.appengine.api import users
  user=users.get_current_user()
  if user:
    return users.create_login_url(url)
  else:
    return "/"

def url_logout(url):
  from google.appengine.api import users
  user=users.get_current_user()
  if user:
    return users.create_logout_url(url)
  else:
    return "/"

def output_json(mydic):
  import sys
  from google.appengine.dist import use_library
  use_library('django', '0.96')
  from django.utils import simplejson
  print 'Content-type: text/x-json\n\n'
  print simplejson.dumps(mydic,ensure_ascii = False)
  sys.exit(1)

def is_numb(n):
 import re
 m = re.search("^([0-9]+)$", str(n), re.I)
 if m:
   return True
 else:
   return False

def chk_empty(self,key,form):
  if form[key] is None or str(form[key].value) == "":
    err("Please enter the "+str(key)+".")

def chk_index(self,rst):
  if rst.index and int(rst.index)<=0:
    err("Can't find this entry.")

###############################
class zd_tmpl():
  def __init__(self,trg):
    self.trg=trg

  def render(self,arr,fn):
    from google.appengine.ext.webapp import template
    from google.appengine.api import users
    import os
    template_values = {
       'nickname': uname(),
       'logout_url' : url_logout(self.trg.request.uri),
    }
    if type(arr)==type({}):
      template_values.update(arr)
    path = os.path.join(os.path.dirname(__file__), "tmpl/"+fn)
    self.trg.response.out.write(template.render(path, template_values))
	
class service_chk():
  def __init__(self):
    from google.appengine.api.capabilities import CapabilitySet
    import sys
    memcache_service = CapabilitySet('memcache', methods=['add''set','get'])
    datastore_service = CapabilitySet('datastore_v3', methods=['write'])
    self.memcache_ok = memcache_service.is_enabled()
    self.datastore_ok = datastore_service.is_enabled()
  
  def chk_site(self):
    if not self.memcache_ok or not self.datastore_ok:
      print 'Sorry: Scheduled Maintenance.'
      sys.exit(1)

  def chk_memcache(self):
    if not self.memcache_ok:
      print 'Sorry: Scheduled Maintenance.'
      sys.exit(1)

  

class MyError(Exception):
    def __init__(self, value):
      self.value = value
    def __str__(self):
      return repr(self.value)





