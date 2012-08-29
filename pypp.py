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
from ast import literal_eval
from datetime import datetime
from os import path
from re import compile as regex

directives = (
  regex(r'''(?P<indent>\s*)[#](?P<directive>include|inside)\s*(?P<name>".*")?'''),
  regex(r'''(?P<indent>\s*)[#](?P<directive>define|local)\s*(?P<name>\S+)\s?(?P<value>".*")?'''),
  regex(r'''(?P<indent>\s*)[#](?P<directive>(?:el)?ifn?(?:def)?)\s*(?P<name>\S*)'''),
  regex(r'''(?P<indent>\s*)[#](?P<directive>[#])(?P<value>.*)'''),
  regex(r'''(?P<indent>\s*)[#](?P<directive>for)\s*(?:(?P<name>\S+)\s+)?(?P<value>\S+)'''),
  regex(r'''(?P<indent>\s*)[#](?P<directive>end|else)'''),
)

today = datetime.today()

defaults = {
  '' : '',
  '__INDENT__' : '',
  '__DATE__' : today.strftime('%b %d %Y'),
  '__TIME__' : today.strftime('%H:%M:%S'),
}

class copy_file(object):
  def __init__(self, file):
    self.file = file
    self.name = file.name
    self.closed = file.closed
    self.offset = file.tell()
  def readline(self):
    if self.offset is not None:
      self.seek(self.offset)
      self.offset = None
    return self.file.readline()
  def close(self):
    pass
  def tell(self):
    return self.file.tell() if self.offset is None else self.offset
  def seek(self, offset):
    self.file.seek(offset)

def preprocess(name, values={}, output=print):
  global directives, defaults
  if not output:
    output = lambda a : a
  current = open(name, 'r')
  inner, outer = [], []
  
  stack  = [dict(defaults)]
  stack[-1].update(values)
  stack[-1]['__file__'] = path.abspath(name)
  stack[-1]['__line__'] = 0
  match  = None
  
  ignoring = 0
  
  def push(file_stack=outer, next_file=None):
    nonlocal stack, match, current
    stack.append(dict(stack[-1]))
    stack[-1]['__INDENT__'] += match.group('indent')
    if next_file:
      stack[-1]['__file__'] = path.abspath(next_file.name)
      stack[-1]['__line__'] = 0
    file_stack.append(current)
    current = next_file if next_file else copy_file(current)
  def pop():
    nonlocal stack, current
    stack.pop()
    current.close()
    try:
      current = outer.pop()
    except IndexError:
      current = None
  while current:
    line = current.readline()
    stack[-1]['__line__'] = int(stack[-1]['__line__']) + 1
    if not line:
      pop()
    else:
      line = line.rstrip()
      while line:
        try:
          match = next(match for match in (directive.match(line) for directive in directives) if match)
        except StopIteration:
          match = None
        if not line:
          pass
        elif ignoring and not match:
          pass
        elif not match:
          output(stack[-1]['__INDENT__'] + line % stack[-1])
        elif match.group('directive') == 'end':
          if ignoring:
            ignoring -= 1
          if not ignoring:
            pop()
        elif ignoring and match.group('directive') in ['if','ifn','ifdef','ifndef','for']:
          ignoring += 1
        elif ignoring <= 1 and match.group('directive') == 'else':
          ignoring = not ignoring
        elif ignoring <= 1 and match.group('directive') in ['elif','elifn','elifdef','elifndef']:
          ignoring = not ignoring or \
                      (('n' in match.group('directive')) ==
                        bool((match.group('name') in values)
                          if match.group('directive').endswith('def')
                          else values[match.group('name')]))
        elif ignoring:
          pass
        elif match.group('directive') == '#':
          line = match.group('value') % values
          continue
        elif match.group('directive') in ['include','inside']:
          side = outer if match.group('directive') == 'include' else inner
          if match.group('name'):
            loc = path.dirname(current.name)
            rel = match.group('name')[1:-1]
            new_file = open(path.join(loc, rel), 'r')
          else:
            new_file = inner.pop()
          push(side, new_file)
        elif match.group('directive') in ['define','local']:
          for values in reversed(stack):
            if match.group('name'):
              values[match.group('name')] = match.group('value')[1:-1] % values
            else:
              del values[match.group('name')]
            if match.group('directive') == 'local':
              break
        elif match.group('directive') == 'for':
          value = stack[-1][match.group('value')]
          if isinstance(value,str):
            value = literal_eval(value)
          if not len(value):
            ignoring = 1
            push()
          else:
            for v in value:
              push()
              if match.group('name'):
                stack[-1][match.group('name')] = v
              else:
                stack[-1].update(v)
        elif match.group('directive') in ['if','ifn','ifdef','ifndef']:
          ignoring = (('n' in match.group('directive')) ==
                      bool((match.group('name') in values)
                        if match.group('directive').endswith('def')
                        else values[match.group('name')]))
          push()
        break
