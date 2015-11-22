from google.appengine.ext import db
import hashlib
import aetycoon
#######################

class BlogIndex(db.Model):
  max_index = db.IntegerProperty(required=True, default=1)

class BlogCategory(db.Model):
    index = db.IntegerProperty(required=True)
    name = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

class BlogTag(db.Model):
    index = db.IntegerProperty(required=True)
    subindex = db.IntegerProperty(required=True)
    name = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)

class BlogTags(db.Model):
    index = db.IntegerProperty(required=True)
    name1 = db.ReferenceProperty(BlogTag,collection_name="tag1")
    name2 = db.ReferenceProperty(BlogTag,collection_name="tag2")
    name3 = db.ReferenceProperty(BlogTag,collection_name="tag3")
    name4 = db.ReferenceProperty(BlogTag,collection_name="tag4")
    name5 = db.ReferenceProperty(BlogTag,collection_name="tag5")

class BlogEntry(db.Model):
  index = db.IntegerProperty(required=True)
  title = db.StringProperty(required=True)
  body = db.TextProperty(required=True)
  created = db.DateTimeProperty(auto_now_add=True)
  cat = db.ReferenceProperty(BlogCategory)
  tag = db.ReferenceProperty(BlogTags)
  user = db.StringProperty(required=True)

class PicIndex(db.Model):
  max_index = db.IntegerProperty(required=True, default=1)

class BlogPics(db.Model):
  index = db.IntegerProperty(required=True)
  data = db.BlobProperty(required=True)
  mimetype = db.StringProperty(required=True)
  info = db.StringProperty(required=True)
  entryIndex = db.IntegerProperty(required=True)
  etag = aetycoon.DerivedProperty(lambda x: hashlib.sha1(x.data).hexdigest())
  created = db.DateTimeProperty(auto_now_add=True)

class SingleIndex(db.Model):
  max_index = db.IntegerProperty(required=True, default=1)

class SingleEntry(db.Model):
  index = db.IntegerProperty(required=True)
  title = db.StringProperty(required=True)
  body = db.TextProperty(required=True)
  created = db.DateTimeProperty(auto_now_add=True)
  pagenum = db.IntegerProperty(required=True, default=1)
  is_first = db.IntegerProperty(required=True, default=0)
  user = db.StringProperty(required=True)

class LinkIndex(db.Model):
  max_index = db.IntegerProperty(required=True, default=1)

class LinkEntry(db.Model):
  index = db.IntegerProperty(required=True)
  title = db.StringProperty(required=True)
  url = db.StringProperty(required=True)
  created = db.DateTimeProperty(auto_now_add=True)
  #parentpage = db.ReferenceProperty(SingleEntry)
  user = db.StringProperty(required=True)
