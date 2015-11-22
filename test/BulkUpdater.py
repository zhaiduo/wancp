import logging
import time
from google.appengine.api import mail
from google.appengine.ext import db
from google.appengine.ext.deferred import defer
from google.appengine.runtime import apiproxy_errors


class BulkUpdater(object):
  """A bulk updater for datastore entities.
  
  Subclasses should implement, at a minimum, get_query and handle_entity.
  """

  # Number of entities to put() at once.
  PUT_BATCH_SIZE = 20
  
  # Number of entities to delete() at once.
  DELETE_BATCH_SIZE = 20
  
  # Maximum time to spend processing before enqueueing the next task in seconds.
  MAX_EXECUTION_TIME = 20.0
  
  # Maximum number of failures to tolerate before aborting. -1 indicates
  # no limit, in which case the list of failed keys will not be retained.
  MAX_FAILURES = 0
  
  def __init__(self):
    self.__to_put = []
    self.__to_delete = []
    self.__failed_keys = []
    self.num_processed = 0
    self.num_tasks = 0
    self.num_put = 0
    self.num_deleted = 0
  
  def get_query(self):
    """Returns the query to iterate over.

    Returns:
      A db.Query or db.GqlQuery object. The returned query must support cursors.
    """
    raise NotImplementedError()

  def handle_entity(self, entity):
    """Performs processing on a single entity.
    
    Args:
      entity: A db.Model instance to update.
    """
    raise NotImplementedError()

  def finish(self, success, failed_keys):
    """Finish processing. Called after all entities have been updated.
    
    Args:
      success: boolean: Indicates if the process completed successfully, or was
        aborted due to too many errors.
      failed_keys: list: A list of db.Key objects that could not be updated.
    """
    pass
  
  def put(self, entities):
    """Stores updated entities to the datastore.
    
    Updates are batched for efficiency.
    
    Args:
      entities: An entity, or list of entities, to store.
    """
    if isinstance(entities, db.Model):
      entities = [entities]
    self.__to_put.extend(entities)
    
    while len(self.__to_put) > self.PUT_BATCH_SIZE:
      db.put(self.__to_put[-self.PUT_BATCH_SIZE:])
      del self.__to_put[-self.PUT_BATCH_SIZE:]
      self.num_put += self.PUT_BATCH_SIZE

  def delete(self, entities):
    """Deletes entities from the datastore.
    
    Deletes are batched for efficiency.
    
    Args:
      entities: An entity, key, or list of entities or keys, to delete.
    """
    if isinstance(entities, (db.Key, db.Model, basestring)):
      entities = [entities]
    self.__to_delete.extend(entities)
    
    while len(self.__to_delete) > self.DELETE_BATCH_SIZE:
      db.delete(self.__to_delete[-self.DELETE_BATCH_SIZE:])
      del self.__to_delete[-self.DELETE_BATCH_SIZE:]
      self.num_deleted += self.DELETE_BATCH_SIZE
 
  def __process_entities(self, q):
    """Processes a batch of entities.
    
    Args:
      q: A query to iterate over doing processing.
    Returns:
      True if the update process has finished, False otherwise.
    """
    end_time = time.time() + self.MAX_EXECUTION_TIME
    for entity in q:
      try:
        self.handle_entity(entity)
      except (db.Timeout, apiproxy_errors.CapabilityDisabledError,
              apiproxy_errors.DeadlineExceededError):
        # Give up for now - reschedule for later.
        return False
      except Exception, e:
        # User exception - log and (perhaps) continue.
        logging.exception("Exception occurred while processing entity %r",
                          entity.key())
        if self.MAX_FAILURES >= 0:
          self.__failed_keys.append(entity.key())
          if len(self.__failed_keys) > self.MAX_FAILURES:
            # Update completed (failure)
            return True
      
      self.num_processed += 1
      
      if time.time() > end_time:
        return False
    
    # The loop finished - we're done!
    return True

  def run(self, _start_cursor=None):
    """Begins or continues a batch update process."""
    q = self.get_query()
    if _start_cursor:
      q.with_cursor(_start_cursor)
    
    finished = self.__process_entities(q)
    
    # Store or delete any remaining entities
    if self.__to_put:
      db.put(self.__to_put)
    if self.__to_delete:
      db.delete(self.__to_delete)
    self.num_put += len(self.__to_put)
    self.__to_put = []
    self.num_deleted += len(self.__to_delete)
    self.__to_delete = []
    
    self.num_tasks += 1
    
    if finished:
      logging.info(
          "Processed %d entities in %d tasks, putting %d and deleting %d",
          self.num_processed, self.num_tasks, self.num_put, self.num_deleted)
      self.finish(len(self.__failed_keys) <= self.MAX_FAILURES
                  and self.MAX_FAILURES >= 0,
                  self.__failed_keys)
    else:
      defer(self.run, q.cursor())

class ReportingMixin(object):
  def __init__(self, email_sender=None):
    """Constructor.
    
    Args:
      email_sender: If set, send a completion email to admins, from the provided
        email address.
    """
    super(ReportingMixin, self).__init__()
    self.email_sender = email_sender

  def finish(self, success, failed_keys):
    super(ReportingMixin, self).finish(success, failed_keys)
    if not self.email_sender:
      return

    if success:
      message = "Bulk update job %s completed successfully!\n\n" % self.__class__
      subject = "Bulk update completed"
    else:
      message = "Bulk update job %s failed.\n\n" % self.__class__
      subject = "Bulk update FAILED"
    
    message += ("Processed %d entities in %d tasks, putting %d and deleting %d\n\n"
                % (self.num_processed, self.num_tasks, self.num_put,
                   self.num_deleted))
    
    if failed_keys:
      message += "Processing failed for the following keys:\n"
      for key in failed_keys:
        message += "%r\n" % key
    
    mail.send_mail_to_admins(self.email_sender, subject, message)

class BulkPut(ReportingMixin, BulkUpdater):
  def __init__(self, query, email_sender=None):
    super(BulkPut, self).__init__(email_sender)
    self.query = query

  def get_query(self):
    return self.query

  def handle_entity(self, entity):
    self.put(entity)


class BulkDelete(ReportingMixin, BulkUpdater):
  def __init__(self, query, email_sender=None):
    super(BulkDelete, self).__init__(email_sender)
    self.query = query

  def get_query(self):
    return self.query

  def handle_entity(self, entity):
    self.delete(entity)


#We can test our updater from the remote_api console, like so:
#
#notdot-blog> updater = bulkupdate.BulkPut(models.BlogPost.all())
#notdot-blog> updater.MAX_EXECUTION_TIME=1.0
#notdot-blog> defer(updater.run)
#
#Checking the admin console shows the deferred tasks being executed, and checking our email shows a message in our inbox titled "Bulk update completed".


