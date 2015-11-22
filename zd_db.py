# -*- coding:utf-8 -*- ＃必须在第一行或者第二行
#zd_db module

from google.appengine.ext import db
from google.appengine.api import memcache
from google.appengine.datastore import entity_pb
from zd_define import *
from zd_func import err
####################

#DATA
class BMK(db.Model):
      mytime = db.StringProperty()
      date = db.StringProperty()

class CAIP(db.Model):
      numbs = db.StringProperty()
      date = db.StringProperty()
      numb1 = db.IntegerProperty()
      numb2 = db.IntegerProperty()
      numb3 = db.IntegerProperty()
      numb4 = db.IntegerProperty()
      numb5 = db.IntegerProperty()
      numb6 = db.IntegerProperty()
      numb7 = db.IntegerProperty()

#####################################

def post_single(user, blogname, myindex, title, body, pagenum):
  import sys,re
  def txn():
    
    if int(myindex)>0:
      my_key_name=blogname + str(myindex) + "_1"
      single_cz = SingleEntry.get_by_key_name(my_key_name,parent=db.Key.from_path('SingleIndex', blogname))
      if single_cz is None:
        err("Can't find This Single Page.")
      else:
        my_key_name=blogname + str(myindex) + "_" + str(pagenum)
        single_cz = SingleEntry.get_by_key_name(my_key_name,parent=db.Key.from_path('SingleIndex', blogname))
	if single_cz is not None:
          err("The page "+str(pagenum)+" of Single Pageis existed.")
	else:
	  single_index = SingleIndex(key_name=blogname)
	  single_index.max_index += 1
          single_index.put()
	  new_entry = SingleEntry(
            key_name=my_key_name,
            parent=single_index, index=int(myindex),
            user=unicode(str(user),'utf-8'), title=unicode(title,'utf-8'), body=unicode(body,'utf-8'),
	    pagenum=int(pagenum), is_first=0)
          new_entry.put()
    else:
      single_index = SingleIndex.get_by_key_name(blogname)
      if single_index is None:
        single_index = SingleIndex(key_name=blogname)
      new_index = single_index.max_index
      obj = db.get(db.Key.from_path("SingleIndex", blogname, "SingleEntry", blogname + str(new_index) + "_" + str(pagenum)))
      if (not obj):
        is_first=0
        if int(pagenum)==1:
	  is_first=1
          single_index.max_index += 1
          single_index.put()
        new_entry = SingleEntry(
          key_name=blogname + str(new_index) + "_" + str(pagenum),
          parent=single_index, index=new_index,
          user=unicode(str(user),'utf-8'), title=unicode(title,'utf-8'), body=unicode(body,'utf-8'),
	  pagenum=int(pagenum), is_first=int(is_first))
        new_entry.put()
      else:
        err("This Single Page is existed.")
  db.run_in_transaction(txn)

def post_entry(user, blogname, title, body, category, taglist):
  import sys,re
  def txn():
    blog_index = BlogIndex.get_by_key_name(blogname)
    if blog_index is None:
      blog_index = BlogIndex(key_name=blogname)
    new_index = blog_index.max_index
    obj = db.get(db.Key.from_path("BlogIndex", blogname, "BlogEntry", blogname + str(new_index)))
    if not obj:
      blog_index.max_index += 1
      blog_index.put()

      ##############################
      obj = db.get(db.Key.from_path("BlogIndex", blogname, "BlogCategory", unicode(category,'utf-8')))
      #print str(obj)+"<br>"
      #print unicode(category,'utf-8')
      #sys.exit(1)
      if not obj:
        new_cat = BlogCategory(
          key_name=unicode(category,'utf-8'),
          parent=blog_index, index=new_index,
          name=unicode(category,'utf-8'))
        new_cat.put()
      else:
        new_cat=obj
      
      obj = db.get(db.Key.from_path("BlogIndex", blogname, "BlogTags", unicode(taglist,'utf-8')))
      if not obj:
        new_tags = BlogTags(
          key_name=unicode(taglist,'utf-8'),
          parent=blog_index, index=new_index)


        tag_arr=taglist.split(",")
        tgi=1
	for tag_item in tag_arr:
	  #print tag_item
          #sys.exit(1)
	  m = re.search("^[\s]*$", str(tag_item), re.I | re.M | re.U)
          if m:
	    continue
          if tgi>5:
            break
	  myindex=float(new_index) + float(tgi/10)
          obj = db.get(db.Key.from_path("BlogIndex", blogname, "BlogTag", unicode(tag_item,'utf-8')))
          if not obj:
            new_tag = BlogTag(
              key_name=unicode(tag_item,'utf-8'),
              parent=blog_index, index=new_index, subindex=tgi,
              name=unicode(tag_item,'utf-8'))
            new_tag.put()
          else:
            new_tag=obj
          if tgi==1:
            new_tags.name1=new_tag.key()
          elif tgi==2:
            new_tags.name2=new_tag.key()
          elif tgi==3:
            new_tags.name3=new_tag.key()
          elif tgi==4:
            new_tags.name4=new_tag.key()
          elif tgi==5:
            new_tags.name5=new_tag.key()
          else:
            break
          tgi+=1
        new_tags.put()
      else:
        new_tags=obj
      
      ##############################

      new_entry = BlogEntry(
        key_name=blogname + str(new_index),
        parent=blog_index, index=new_index,
        user=unicode(str(user),'utf-8'), title=unicode(title,'utf-8'), body=unicode(body,'utf-8'),
	cat=new_cat.key(), tag=new_tags.key())
      new_entry.put()
  db.run_in_transaction(txn)

def get_single(blogname, index, pagenum=1):
  entry = SingleEntry.get_by_key_name(blogname + str(index) + '_'+str(pagenum), parent=db.Key.from_path('SingleIndex', blogname))
  return entry

def get_entry(blogname, index):
  entry = BlogEntry.get_by_key_name(blogname + str(index), parent=db.Key.from_path('BlogIndex', blogname))
  return entry

def get_tag(blogname,tagname):
  obj = db.get(db.Key.from_path("BlogIndex", blogname, "BlogTag", unicode(tagname,'utf-8')))
  return obj

def get_tags_key(mytagobj):
        keys=[]
	tag_q=db.GqlQuery("SELECT __key__ FROM BlogTags where name1 = :1", mytagobj.key())
	keys=keys+tag_q.fetch(1000)
	tag_q=db.GqlQuery("SELECT __key__ FROM BlogTags where name2 = :1", mytagobj.key())
	keys=keys+tag_q.fetch(1000)
	tag_q=db.GqlQuery("SELECT __key__ FROM BlogTags where name3 = :1", mytagobj.key())
	keys=keys+tag_q.fetch(1000)
	tag_q=db.GqlQuery("SELECT __key__ FROM BlogTags where name4 = :1", mytagobj.key())
	keys=keys+tag_q.fetch(1000)
	tag_q=db.GqlQuery("SELECT __key__ FROM BlogTags where name5 = :1", mytagobj.key())
	keys=keys+tag_q.fetch(1000)
	return keys

def get_category(blogname,catname):
  obj = db.get(db.Key.from_path("BlogIndex", blogname, "BlogCategory", unicode(catname,'utf-8')))
  return obj

def get_entries(start_index):
  extra = None
  if start_index is None:
    entries = BlogEntry.gql(
      'ORDER BY index DESC').fetch(
      POSTS_PER_PAGE + 1)
  else:
    start_index = int(start_index)
    entries = BlogEntry.gql(
      'WHERE index <= :1 ORDER BY index DESC',
      start_index).fetch(POSTS_PER_PAGE + 1)
  if len(entries) > POSTS_PER_PAGE:
    extra = entries[-1]
    entries = entries[:POSTS_PER_PAGE]
  return entries, extra

def update_blog(blogname,rst,title,body,category,mytaglist):
  import sys,re
  def txn():
      if title == "":
        err("Please enter the title.")
      if unicode(title,'utf-8') != rst.title:
        rst.title=unicode(title,'utf-8')

      if body == "":
        err("Please enter the body.")
      if unicode(body,'utf-8') != rst.body:
        rst.body=unicode(body,'utf-8')

      if category == "":
        err("Please enter the category.")

      blog_index = BlogIndex.get_by_key_name(blogname)
      
      if unicode(category,'utf-8') != rst.cat.name:
	obj = db.get(db.Key.from_path("BlogIndex", blogname, "BlogCategory", unicode(category,'utf-8')))
        if not obj:
          new_cat = BlogCategory(
            key_name=unicode(category,'utf-8'),
            parent=blog_index, index=rst.index,
            name=unicode(category,'utf-8'))
          new_cat.put()
        else:
          new_cat=obj
        rst.cat=new_cat.key()

      if str(mytaglist) == "":
        err("Please enter the tag.")

      mytags=""
      tag_num=0
      if(rst.tag and rst.tag.name1 is not None):
        mytags+=rst.tag.name1.name
	tag_num+=1
      if(rst.tag and rst.tag.name2 is not None):
        tag_num+=1
        if mytags=="":
          mytags+=rst.tag.name2.name
	else:
          mytags+=","+rst.tag.name2.name
      if(rst.tag and rst.tag.name3 is not None):
        tag_num+=1
        if mytags=="":
          mytags+=rst.tag.name3.name
	else:
          mytags+=","+rst.tag.name3.name
      if(rst.tag and rst.tag.name4 is not None):
        tag_num+=1
        if mytags=="":
          mytags+=rst.tag.name4.name
	else:
          mytags+=","+rst.tag.name4.name
      if(rst.tag and rst.tag.name5 is not None):
        tag_num+=1
        if mytags=="":
          mytags+=rst.tag.name5.name
	else:
          mytags+=","+rst.tag.name5.name


      if mytags != unicode(mytaglist,'utf-8'):
        
        objs = db.get(db.Key.from_path("BlogIndex", blogname, "BlogTags", unicode(mytaglist,'utf-8')))
        if not objs:
          new_tags = BlogTags(
            key_name=unicode(mytaglist,'utf-8'),
            parent=blog_index, index=rst.index)

          tag_arr=mytaglist.split(",")
          tgi=1
          for tag_item in tag_arr:
	    if tgi>5:
              break
            m = re.search("^[\s]*$", str(tag_item), re.I | re.M | re.U)
            if m:
	      if tgi==1:
                new_tags.name1=None
              elif tgi==2:
                new_tags.name2=None
              elif tgi==3:
                new_tags.name3=None
              elif tgi==4:
                new_tags.name4=None
              elif tgi==5:
                new_tags.name5=None
	      continue
	  
	    #entity = BlogTag.get_by_key_name(unicode(tag_item,'utf-8'),parent=blog_index)
	    entity = db.get(db.Key.from_path("BlogIndex", blogname, "BlogTag", unicode(tag_item,'utf-8')))
            if entity is None:
                if blog_index is not None:
                  new_tag = BlogTag(
                    key_name=unicode(tag_item,'utf-8'),
                    parent=blog_index, index=rst.index, subindex=tag_num+1,
                    name=unicode(tag_item,'utf-8'))
                  new_tag.put()
	        else:
	          print "blog_index lost."
	          sys.exit(1)
	        if tgi==1:
                  new_tags.name1=new_tag.key()
                elif tgi==2:
                  new_tags.name2=new_tag.key()
                elif tgi==3:
                  new_tags.name3=new_tag.key()
                elif tgi==4:
                  new_tags.name4=new_tag.key()
                elif tgi==5:
                  new_tags.name5=new_tag.key()
	    else:
	      if tgi==1:
                new_tags.name1=entity.key()
              elif tgi==2:
                new_tags.name2=entity.key()
              elif tgi==3:
                new_tags.name3=entity.key()
              elif tgi==4:
                new_tags.name4=entity.key()
              elif tgi==5:
                new_tags.name5=entity.key()
	    tgi+=1
	  new_tags.put()
          rst.tag=new_tags.key()
        else:
	  rst.tag=objs.key()
      db.put(rst)
  db.run_in_transaction(txn)

def update_single(blogname,rst,title,body):
  import sys,re
  def txn():
      if title == "":
        err("Please enter the title.")
      if unicode(title,'utf-8') != rst.title:
        rst.title=unicode(title,'utf-8')
      if body == "":
        err("Please enter the body.")
      if unicode(body,'utf-8') != rst.body:
        rst.body=unicode(body,'utf-8')
      db.put(rst)
  db.run_in_transaction(txn)

############################

def increment(name):
  config = CounterConfig.get_or_insert(name,name=name)
  def txn():
    import random
    index = random.randint(0, config.num_shards - 1)
    shard_name = name + str(index)
    counter = Counter.get_by_key_name(shard_name)
    if counter is None:
      counter = Counter(key_name=shard_name,name=name)
    counter.count += 1
    counter.put()
  db.run_in_transaction(txn)
  memcache.incr(name)

def get_count(name):
  total = memcache.get(name)
  if total is None:
    total = 0
    for counter in Counter.gql('WHERE name = :1', name):
      total += counter.count
    memcache.add(name, str(total), 5)
  return total

class CounterConfig(db.Model):
  name = db.StringProperty(required=True)
  num_shards = db.IntegerProperty(required=True, default=1)

class Counter(db.Model):
  name = db.StringProperty(required=True)
  count = db.IntegerProperty(required=True, default=0)

####################Query
def mq_q(kind,filters=[],orders=[],ancestors=[],limit=1000,offset=0):
  qq = kind.all()
  #qq.filter('title =', 'Imagine').order('-date').ancestor(key)
  if len(filters)>0 and len(filters)%2==0 :
    for item in filters:
      if len(item)==2:
        qq.filter(item[0], item[1])
    	
  if len(orders)>0:
    for item in orders:
      qq.order(item)

  if len(ancestors)>0:
      for item in ancestors:
        qq.ancestor(item)

  data=qq.fetch(limit,offset)
  return data

####################GqlQuery
def m_q(sql,limit=1000,offset=0,*args):
  if args:
    #args=", ".join(args)
    qq = db.GqlQuery(sql,args)
  else:
    qq = db.GqlQuery(sql)
  data=qq.fetch(limit,offset)
  return data

def q_num(q):
  holder = q.fetch(1000)
  result = len(holder)
  while len(holder) == 1000:
    holder = q.with_cursor(q.cursor()).fetch(1000)
    result += len(holder)
  return result

def m_nc(sql,limit=1000,offset=0,*args): #who care how many records? deprecated?
    sql_cache='Number: '+sql
    numb = deserialize_entities(memcache.get(sql_cache),0)
    if numb is not None:
        return numb
    else:
        if args:
	  #args=", ".join(args)
	  data = db.GqlQuery(sql,args)
	else:
	  data = db.GqlQuery(sql)
	numb=q_num(data)
	#memcache.add(sql_cache, numb, 3600)
	memcache.add(sql_cache, serialize_entities(numb), 3600)
        return numb

def m_f(q,limit=1000,offset=0):
    return q.fetch(limit,offset)

def m_qc(sql,limit=1000,offset=0,*args):
    import sys
    #memcache.flush_all()
    sql_key=str(offset)+":"+sql
    data = deserialize_entities(memcache.get(sql_key))
    #print str(data)+"------------"
    #sys.exit()
    
    if data is not None:
        return data
    else:
        if args:
	  #args=", ".join(args)
	  qq = db.GqlQuery(sql,args)
	else:
	  qq = db.GqlQuery(sql)
        data=qq.fetch(limit,offset)
	#sr_data=db.model_to_protobuf(data) 
	#memcache.add(sql_key, sr_data, 3600)
	#memcache.add(sql_key, data, 3600)
	memcache.add(sql_key, serialize_entities(data), 3600)
        return data

def q_del(tb,where="",*args):
    if where!="":
      where=" WHERE "+where
    sql="SELECT __key__ FROM "+tb+" "+where
    if args:
      args=", ".join(args)
      query = db.GqlQuery(sql,args)
    else:
      query = db.GqlQuery(sql)
    results = query.fetch(1000)
    if results:
      db.delete(results)

#serialize memcache
def serialize_entities(models):
  if models is None:
    return None
  elif isinstance(models, db.Model):
    return db.model_to_protobuf(models).Encode()
  elif isinstance(models, list):
    return [db.model_to_protobuf(x).Encode() for x in models]
  else:
    return models

def deserialize_entities(data,protobuf=1):
  if data is None:
    return None
  elif isinstance(data, str):
    if protobuf==1:
      return db.model_from_protobuf(entity_pb.EntityProto(data))
    else:
      return data
  elif isinstance(data, list):
    return [serialize_chk(x) for x in data]
  else:
    return None

def serialize_chk(data):
  if isinstance(data, str):
    return db.model_from_protobuf(entity_pb.EntityProto(data))
  else:
    return None
