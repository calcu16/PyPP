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
from os import path
from re import compile as regex

directives = (
  regex(r'''(?P<indent>\s*)[#](?P<directive>include|inside)\s*(?P<name>".*")?'''),
  regex(r'''(?P<indent>\s*)[#](?P<directive>define|local)\s*(?P<name>\S*)\s?(?P<value>.*)'''),
  regex(r'''(?P<indent>\s*)[#](?P<directive>undef|ignore)\s*(?P<name>\S*)'''),
  regex(r'''(?P<indent>\s*)[#](?P<directive>(?:el)?ifn?(?:def)?)\s*(?P<name>\S*)'''),
  regex(r'''(?P<indent>\s*)[#](?P<directive>end)'''),
)

defaults = {
  '__indent__' : ''
}

class copy_file(object):
  def __init__(self, file):
    self.file = file
  def __iter__(self):
    return self
  def __next__(self):
    return next(self.file)
  def close(self):
    pass

def preprocess(name, values, output=print):
  global directives, defaults
  if not output:
    output = lambda a : a
  current = open(name, 'r')
  inner, outer = [], []
  
  stack  = [dict(defaults)]
  stack[-1].update(values)
  match  = None
  
  ignoring = 0
  
  def push():
    nonlocal stack, match
    stack.append(dict(stack[-1]))
    stack[-1]['__indent__'] += match.group('indent')
  def pop():
    nonlocal stack, current
    stack.pop()
    current.close()
    try:
      current = outer.pop()
    except IndexError:
      current = None
  while current:
    try:
      line = next(current)
    except StopIteration:
      pop()
    else:
      line = line.rstrip()
      try:
        match = next(match for match in (directive.match(line) for directive in directives) if match)
      except StopIteration:
        match = None
      if not line:
        pass
      elif ignoring and not match:
        pass
      elif not match:
        output(stack[-1]['__indent__'] + line % stack[-1])
      elif match.group('directive') == 'end':
        if ignoring:
          ignoring -= 1
        if not ignoring:
          pop()
      elif ignoring and match.group('directive') in ['if','ifn','ifdef','ifndef']:
        ignoring += 1
      elif ignoring <= 1 and match.group('directive') == 'else':
        ignoring = not ignoring
      elif ignoring <= 1 and match.group('directive') in ['elif','elifn','elifdef','elifndef']:
        ignoring = not ignoring or \
                    (('n' in match.group('directive')) !=
                      ((match.group('name') in values)
                        if match.group('directive').endswith('def')
                        else values[match.group('name')]))
      elif ignoring:
        pass
      elif match.group('directive') in ['include','inside']:
        old = current
        push()
        current = open(path.join(path.dirname(current.name), match.group('name')[1:-1]), 'r') if match.group('name') else inner.pop()
        (outer if match.group('directive') == 'include' else inner).append(old)
      elif match.group('directive') in ['define','local']:
        for values in reversed(stack):
          values[match.group('name')] = match.group('value')
          if match.group('directive') == 'local':
            break
      elif match.group('directive') in ['if','ifn','ifdef','ifndef']:
        ignoring = (('n' in match.group('directive')) !=
                    ((match.group('name') in values)
                      if match.group('directive').endswith('def')
                      else values[match.group('name')]))
        push()
        outer.append(current)
        current = copy_file(current)
