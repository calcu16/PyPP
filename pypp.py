#!/usr/bin/env python3
# Copyright (c) 2012 Andrew Carter
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met: 
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer. 
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution. 
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies, 
# either expressed or implied, of the FreeBSD Project.
'''This module provides a text preprocessor for python.'''
def preprocess(name, values={}, output=print, root='/'):
  '''Preprocess the file given by name
  
  Arguments:
    name   : The name of the file to process
    values : The default values for insertion (default: {})
    output : An output function (default: print)
  '''
  # imports required for this module
  from ast import literal_eval
  from datetime import datetime
  from os import path
  from re import compile as regex
  # regex for matching various directives
  directives = (
    regex(r'''(?P<indent>\s*)[#](?P<directive>include|inside)(?:\s+(?P<name>".*"))?\s*$'''),
    regex(r'''(?P<indent>\s*)[#](?P<directive>define|local)\s+(?:(?P<level>\d+)\s+)?(?P<name>\w+)(?:\s+(?P<value>".*"))?\s*$'''),
    regex(r'''(?P<indent>\s*)[#](?P<directive>(?:el)?ifn?(?:def)?)(?:\s+(?P<name>\w+))?\s*$'''),
    regex(r'''(?P<indent>\s*)[#](?P<directive>[#])(?P<value>.*)$'''),
    regex(r'''(?P<indent>\s*)[#](?P<directive>for)\s+(?:(?P<name>\w+)\s+)?(?P<value>(?:".*"|\w+))\s*$'''),
    regex(r'''(?P<indent>\s*)[#](?P<directive>end|else)\s*$'''),
    regex(r'''(?P<indent>\s*)[#](?P<directive>\s)(?P<value>.*)$'''),
  # catch malformed directives
    regex(r'''(?P<directive>)(?P<valid>\s*[#](?:include|inside)(\s+".*"?)?\s*)'''),
    regex(r'''(?P<directive>)(?P<valid>\s*[#](?:define|local)(\s+(?:\d+\s+)?(?:\w+\s+(?:".*")?)?)?\s*)'''),
    regex(r'''(?P<directive>)(?P<valid>\s*[#](?:(?:el)?ifn?(?:def)?)(?:\s+\w+)?\s*)'''),
    regex(r'''(?P<directive>)(?P<valid>\s*[#](?:for)(?:\s+(?:\w+\s+)?(?:".*"|\w+))?\s*)'''),
    regex(r'''(?P<directive>)(?P<valid>\s*[#](?:end|else)\s*)'''),
  # catch directive-like objects, probably an error
    regex(r'''(?P<directive>)(?P<valid>\s*[#]).*$'''),
  )
  # provide __DATE__/__TIME__ for file generation timestamps
  today = datetime.today()
  # set of default values
  defaults = {
    None         : '',
   r'\n'         : '\n',
    '__INDENT__' : '',
    '__DATE__'   : today.strftime('%b %d %Y'),
    '__TIME__'   : today.strftime('%H:%M:%S'),
    '__LEVEL__'  : 0,
  }
  # for copying a file while still having access to it's original locations
  #  used for the #for directive
  class copy_file(object):
    def __init__(self, file):
      self.file = file
      self.name = file.name
      self.closed = file.closed
      self.offset = file.tell()
      if isinstance(file, copy_file):
        self.stack  = file.stack
      else:
        self.stack = []
    def pushline(self, line):
      self.stack.append(line)
    def pushlines(self, lines):
      self.stack.extend(reversed(lines))
    def readline(self):
      if self.closed:
        raise ValueError("I/O operation on closed file.")
      if self.stack:
        return self.stack.pop()
      if self.offset is not None:
        self.seek(self.offset)
        self.offset = None
      return self.file.readline()
    def close(self):
      self.closed = True
      if not isinstance(self.file, copy_file):
        self.file.close()
    def tell(self):
      if self.closed:
        raise ValueError("I/O operation on closed file.")
      return self.file.tell() if self.offset is None else self.offset
    def seek(self, offset):
      if self.closed:
        raise ValueError("I/O operation on closed file.")
      self.file.seek(offset)
  ## FUNCTION START
  # if output is none then use identity function
  if not output:
    output = lambda a : a
  # the current file
  current = copy_file(open(name, 'r'))
  # file stacks
  inner, outer = [], []
  
  root = path.abspath(root)
  
  # build the initial stack
  stack  = [dict(defaults)]
  stack[-1].update(values)
  stack.append(dict(stack[-1]))
  stack[-1]['__FILE__'] = path.abspath(name)
  stack[-1]['__LINE__'] = 0
  stack[-1]['__LEVEL__'] = 1
  match  = None
  
  # are we ignoring the input
  #  used for if type commands
  ignoring = 0
  
  # push values onto the stack
  def push(file_stack=outer, next_file=None, values=None):
    nonlocal stack, match, current
    if not values:
      values = stack[-1]
    stack.append(dict(values))
    stack[-1]['__INDENT__'] += match.group('indent')
    if next_file:
      stack[-1]['__FILE__'] = path.abspath(next_file.name)
      stack[-1]['__LINE__'] = 0
      stack[-1]['__LEVEL__'] = len(stack) - 1
    file_stack.append(current)
    current = next_file if next_file else copy_file(current)
  # pop values from the stack
  def pop():
    nonlocal stack, current
    stack.pop()
    current.close()
    try:
      current = outer.pop()
    except IndexError:
      current = None
  # read-eval print loop
  while current:
    line = current.readline()
    stack[-1]['__LINE__'] = int(stack[-1]['__LINE__']) + 1
    if not line:
      pop()
    else:
      line = line.rstrip('\n\r')
      try:
        # get first match
        match = next(match for match in (directive.match(line) for directive in directives) if match)
      except StopIteration:
        # no matches
        match = None
      # Giant if statement of death, yay parsing
      if ignoring and not match:
        # ignoring this line
        pass
      elif not match:
        # print non-directive line
        output(stack[-1]['__INDENT__'] + line % stack[-1])
      elif not match.group('directive'):
        # bad directive
        raise SyntaxError("Invalid directive", (stack[-1]['__FILE__'], stack[-1]['__LINE__'], len(match.group('valid')), line))
      elif match.group('directive') == 'end':
        # at the end of a block
        if ignoring:
          ignoring -= 1
        if not ignoring:
          # no longer ignoring
          pop()
      elif ignoring and match.group('directive') in ['if','ifn','ifdef','ifndef','for']:
        # beginning a new block while ignoring
        ignoring += 1
      elif ignoring <= 1 and match.group('directive') == 'else':
        # was ignoring, but no longer
        ignoring = not ignoring
      elif ignoring <= 1 and match.group('directive') in ['elif','elifn','elifdef','elifndef']:
        # maybe not ignoring anymore
        ignoring = not ignoring or \
                    (('n' in match.group('directive')) ==
                      bool((match.group('name') in stack[-1])
                        if match.group('directive').endswith('def')
                        else stack[-1][match.group('name')]))
      elif ignoring:
        # this directive is not interesting when ignored
        pass
      elif match.group('directive') == '#':
        # after match rerun line
        line = match.group('value') % stack[-1]
        current.pushlines(tuple(match.group('indent') + subline for subline in line.split('\n')))
      elif match.group('directive') in ['include','inside']:
        # add the contents of another file
        side = outer if match.group('directive') == 'include' else inner
        if match.group('name'):
          loc = path.dirname(current.name)
          rel = match.group('name')[1:-1]
          if rel[0] == '/':
            rel = rel[1:]
            loc = root
          new_file = copy_file(open(path.join(loc, rel), 'r'))
        else:
          # insert the file this is surrounding
          new_file = inner.pop()
        push(file_stack=side, next_file=new_file)
      elif match.group('directive') in ['define','local']:
        # the scoope level
        level = int(match.group('level') if match.group('level') else 0)
        # get equivalent global scope
        if match.group('directive') == 'define':
          level = len(stack) - level - 2
        # go through stack defining name = value
        for i, values in enumerate(reversed(stack)):
          if level < i:
            break
          if match.group('value'):
            values[match.group('name')] = match.group('value')[1:-1] % values
          else:
            # no value, undef instead
            del values[match.group('name')]
      elif match.group('directive') == 'for':
        # iterates through values
        value = match.group('value')
        if value[0] == '"':
          # constant
          value = value[1:-1]
        else:
          # variable
          value = stack[-1][match.group('value')]
        if isinstance(value,str):
          # convert string to literal
          value = literal_eval(value)
        if not len(value):
          # nothing to iterate over
          ignoring = 1
          push()
        else:
          values = stack[-1]
          original = current
          for v in reversed(value):
            push(next_file=copy_file(original),values=values)
            if match.group('name'):
              stack[-1][match.group('name')] = v
            else:
              # expect v to be a dictionary
              stack[-1].update(v)
      elif match.group('directive') in ['if','ifn','ifdef','ifndef']:
        # conditionally ignore
        ignoring = (('n' in match.group('directive')) ==
                    bool((match.group('name') in stack[-1])
                      if match.group('directive').endswith('def')
                      else stack[-1][match.group('name')]))
        push()
      #elif comment directive
      #  pass
  return stack[0]

# command line utility
if __name__ == '__main__':
  from sys import argv
  values = {}
  for filename in argv[1:]:
    values = preprocess(filename, values)
