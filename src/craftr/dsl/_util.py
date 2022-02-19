
import functools

depth = 0

def debug_trace(func):
  return func
  @functools.wraps(func)
  def wrapper(*a, **kw):
    global depth
    print(depth * '| ' + 'enter', func.__name__)
    try:
      depth += 1
      try:
        result = func(*a, **kw)
      finally:
        depth -= 1
    except Exception as exc:
      print(depth * '| ' + 'error in', func.__name__, exc)
      raise
    else:
      print(depth * '| ' + 'return', func.__name__, repr(result))
      return result
  return wrapper
