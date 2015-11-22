import sys

try:
  from google.appengine.runtime import apiproxy
  from google.appengine.runtime import apiproxy_errors
except ImportError:
  print 'Failed to import google.appengine.runtime';
  sys.exit(1)

class APIErrorHook(object):
  def __init__(self):
    self.error_map = {}  # Maps (api, method) tuples to error statuses

  def set_error_code(self, service, method, code):
    self.error_map[(service, method)] = code

  def get_error_code(self, service, method):
    """Returns the error code to return for a service and method, or None."""
    return self.error_map.get((service, method), None)

  def _error_hook(self, service, method, request, response):
    error_code = self.get_error_code(service, method)
    if error_code:
      raise apiproxy_errors.ApplicationError(error_code)

  def install(self, apiproxy, unique_name):
    apiproxy.GetPreCallHooks().Append(unique_name, self._error_hook)

  

class CapabilityHook(APIErrorHook):
  # Maps (service, method) tuples to the capability it depends on
  _CAPABILITY_MAP = {
    ('datastore_v3', 'Put'): 'write',
    ('datastore_v3', 'Delete'): 'write',
  }

  def __init__(self):
    self.disabled_capabilities = set()  # Set of (service, capability) tuples that are disabled
    super(CapabilityHook, self).__init__()

  def set_capability_disabled(self, service, capability, disabled):
    if disabled:
      self.disabled_capabilities.add((service, capability))
    else:
      self.disabled_capabilities.discard((service, capability))

  def get_error_code(self, service, method):
    if (service, '*') in self.disabled_capabilities:
      return apiproxy.CAPABILITY_DISABLED
    required_capability = CapabilityHook._CAPABILITY_MAP.get((service, method), None)
    if required_capability and (service, required_capability) in self.disabled_capabilities:
      return apiproxy.CAPABILITY_DISABLED
    return super(CapabilityHook, self).get_error_code(service, method)

  def _capability_hook(self, service, method, request, response):
    # Accumulate a mapping of capabilities to enabled-ness
    capabilities = {}
    for capability in request.capability_list():
      if (method, capability) in self.disabled_capabilities:
        capabilities[(method, capability)] = False
      else:
        capabilities[(method, capability)] = True
    for method in request.call_list():
      required_capability = CapabilityHook._CAPABILITY_MAP.get(method, '*')
      if required_capability in self.disabled_capabilities or (service, '*') in self.disabled_capabilities:
        capabilities[(method, capability)] = False
      else:
        capabilities.setdefault((method, capability), True)

    # Add them to the response
    response.clear_config()
    for (service, capability), enabled in capabilities.items():
      config = response.add_config()
      config.set_package(service)
      config.set_capability(capability)
      config.set_status(capabilities.IsEnabledResponse.ENABLED if enabled else capabilities.IsEnabledResponse.DISABLED)

    # Calculate the summary response
    config.set_summary_status(capabilities.IsEnabledResponse.ENABLED if False not in capabilities.values() else capabilities.IsEnabledResponse.DISABLED)

  def install(self, apiproxy, unique_name):
    apiproxy.GetPostCallHooks().Append(unique_name, self._capability_hook, 'capability_service')
    super(CapabilityHook, self).install(apiproxy, unique_name)


  

