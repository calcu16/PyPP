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
import glob
import functools
import os
import sys
import unittest

import pypp

class TestPyPP(unittest.TestCase):
  def setUp(self):
    pass
  def line_tester(self, file):
    it = iter(file)
    return lambda line : self.assertEqual(next(it), line + '\n')
  def run_test(self, name, values = {}):
    if os.path.exists('test/golden/%s.gold' % name):
      with open('test/golden/%s.gold' % name, 'r') as file:
        pypp.preprocess('test/input/%s.in' % name, values, self.line_tester(file))
        self.assertRaises(StopIteration, next, file)
    else:
      it = iter(('Hello World!\n',))
      pypp.preprocess('test/input/%s.in' % name, output=self.line_tester(it))
      self.assertRaises(StopIteration, next, it)

def addTest(name):
  decorator = unittest.expectedFailure if name.startswith('_') else (lambda a : a)
  setattr(TestPyPP, 'test_' + name.replace('.','_'), decorator(lambda self : self.run_test(name)))
  

for path in glob.iglob('test/input/*.in'):
  addTest(os.path.basename(path).rsplit('.',1)[0])

if __name__ == '__main__':
  unittest.main()
