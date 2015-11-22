# -*- coding:utf-8 -*- ＃必须在第一行或者第二行
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import webapp

from google.appengine.api import memcache
from google.appengine.ext import db
from google.appengine.datastore import entity_pb

from zd_define import *
from APIErrorHook import *

#cursors: a new feature in version 1.3.1 

class TestPage(webapp.RequestHandler):
  def get(self,*args):
    self.response.headers['Content-Type'] = 'text/html; charset=utf-8'
    self.response.out.write("""OK<hr>""")

    #entities = deserialize_entities2(memcache.get("testblog"))
    #if not entities:
    #  entities = db.GqlQuery("SELECT * FROM BlogEntry ORDER BY created DESC").fetch(10,0)
    #  memcache.set("testblog", serialize_entities2(entities))
    #for x in entities:
    #  self.response.out.write(x.title+"<br>")

    from google.appengine.api import apiproxy_stub_map

    #error_hook = APIErrorHook()
    #error_hook.install(apiproxy_stub_map.apiproxy, 'error_hook')
    #db.get(a_key)  # Works
    #error_hook.set_error_code('datastore_v3', 'Get', apiproxy.DEADLINE_EXCEEDED)
    #db.get(a_key)  # Throws a db.Timeout error
    #error_hook.set_error_code('datastore_v3', 'Get', None)
    #db.get(a_key)  # Works again

    capability_hook = CapabilityHook()
    capability_hook.install(apiproxy_stub_map.apiproxy, 'error_hook')

    #db.put(some_entity)  # Succeeds
    #db.get(some_key)  # Succeeds
    #capabilities.CapabilitySet('datastore_v3', capabilities=['write']).is_enabled()  # Returns True

    capability_hook.set_capability_disabled('datastore_v3', 'write')
    test_index = TEST(key_name="test")
    test_index.mytime = "ok"
    test_index.put()  # Fails, raising datastore_errors.Error
    #db.get(some_key)  # Still succeeds
    #capabilities.CapabilitySet('datastore_v3', capabilities=['write']).is_enabled()  # Returns False


class TEST(db.Model):
      mytime = db.StringProperty()
      date = db.StringProperty()





  

def  serialize_entities(models):
 if models is None:
   return None
 elif isinstance(models, db.Model):
   # Just one instance
   return db.model_to_protobuf(models).Encode()
 else:
   # A list
   return [db.model_to_protobuf(x).Encode() for x in models]

def deserialize_entities(data):
 if data is None:
   return None
 elif isinstance(data, str):
   # Just one instance
   return db.model_from_protobuf(entity_pb.EntityProto(data))
 else:
   return [db.model_from_protobuf(entity_pb.EntityProto(x)) for x in data]

#####################

def serialize_entities2(models):
  if models is None:
    return None
  elif isinstance(models, db.Model):
    return db.model_to_protobuf(models).Encode()
  elif isinstance(models, list):
    return [db.model_to_protobuf(x).Encode() and isinstance(x, db.Model) for x in models]
  else:
    return models

def deserialize_entities2(data,protobuf=1):
  if data is None:
    return None
  elif isinstance(data, str):
    if protobuf==1:
      return db.model_from_protobuf(entity_pb.EntityProto(data))
    else:
      return data
  elif isinstance(data, list):
    return [db.model_from_protobuf(entity_pb.EntityProto(x)) for x in data]
  else:
    return None

#####################
class zd_db_timeout_hl(): #webapp.Handler
  def get(self):
    # Do something that could result in a datastore timeout
    try:
      while True:
        timeout_ms = 100
        try:
          #db.put(entities)
          break
        except datastore_errors.Timeout:
          thread.sleep(timeout_ms)
          timeout_ms *= 2
    except apiproxy_errors.DeadlineExceededError:
      # Ran out of retries – display an error message to the user
      pass


  def handle_exception(self, exception, debug_mode):
    if debug_mode:
      super(MyHandler, self).handle_exception(exception, debug_mode)
    else:
      if isinstance(exception, datastore_errors.Timeout):
        # Display a timeout-specific error page
	pass
      else:
        # Display a generic 500 error page.
	pass







########################


application = webapp.WSGIApplication(
                                     [('/test', TestPage)],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == '__main__':
    main()

