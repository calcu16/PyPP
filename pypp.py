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
)

defaults = {
  '__indent__' : ''
}

def preprocess(name, seed, output=print):
  global directives, defaults
  if not output:
    output = lambda a : a
  current = open(name, 'r')
  inner, outer = [None], [None]
  
  
  
  stack  = [None]
  values = dict(defaults)
  values.update(seed)
  match  = None
  # values
  def push():
    nonlocal stack, match, values
    stack.append(dict(values))
    values['__indent__'] += match.group('indent')
  def pop():
    nonlocal stack, values
    values = stack.pop()
  while current:
    try:
      line = next(current)
    except StopIteration:
      current.close()
      current = outer.pop()
      pop()
    else:
      line = line.rstrip()
      try:
        match = next(match for match in (directive.match(line) for directive in directives) if match)
      except StopIteration:
        match = None
      if not line:
        pass
      elif not match:
        output(values['__indent__'] + line % values)
      elif match.group('directive') in ['include','inside']:
        old = current
        current = open(path.join(path.dirname(current.name), match.group('name')[1:-1]), 'r') if match.group('name') else inner.pop()
        (outer if match.group('directive') == 'include' else inner).append(old)
        push()
