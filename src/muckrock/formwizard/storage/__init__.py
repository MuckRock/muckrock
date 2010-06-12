from django.core.exceptions import ImproperlyConfigured

try:
    from importlib import import_module
except ImportError:
    from django.utils.importlib import import_module

class MissingStorageModuleException(ImproperlyConfigured):
    pass

class MissingStorageClassException(ImproperlyConfigured):
    pass

def get_storage(path, *args, **kwargs):
    i = path.rfind('.')
    module, attr = path[:i], path[i+1:]
    try:
        mod = import_module(module)
    except ImportError, e:
        raise MissingStorageModuleException('Error loading storage %s: "%s"' % (module, e))
    try:
        storage_class = getattr(mod, attr)
    except AttributeError:
        raise MissingStorageClassException('Module "%s" does not define a storage named "%s"' % (module, attr))
    return storage_class(*args, **kwargs)
