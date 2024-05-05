from __future__ import unicode_literals

import calendar
import datetime
import operator
import re

from itertools import chain
from json import dumps
from json import loads

from .compat import compat_chr
from .compat import compat_str
from .compat import compat_map
from .compat import compat_zip_longest


def js_to_json(code):
	COMMENT_RE = r'/\*(?:(?!\*/).)*?\*/|//[^\n]*\n'
	SKIP_RE = r'\s*(?:{comment})?\s*'.format(comment=COMMENT_RE)

	def fix_kv(m):
		v = m.group(0)
		if v in ('true', 'false', 'null'):
			return v
		elif v in ('undefined', 'void 0'):
			return 'null'
		elif v.startswith('/*') or v.startswith('//') or v.startswith('!') or v == ',':
			return ''

		if v[0] in ("'", '"'):
			v = re.sub(r'(?s)\\.|"', lambda m: {
				'"': '\\"',
				"\\'": "'",
				'\\\n': '',
				'\\x': '\\u00',
			}.get(m.group(0), m.group(0)), v[1:-1])

			return '"%s"' % v

		raise ValueError('Unknown value:', v)

	return re.sub(r'''(?sx)
		"(?:[^"\\]*(?:\\\\|\\['"nurtbfx/\n]))*[^"\\]*"|
		'(?:[^'\\]*(?:\\\\|\\['"nurtbfx/\n]))*[^'\\]*'|
		{comment}|,(?={skip}[\]}}])|
		(?:(?<![0-9])[eE]|[a-df-zA-DF-Z_])[.a-zA-Z_0-9]*|
		\b(?:0[xX][0-9a-fA-F]+|0+[0-7]+)(?:{skip}:)?|
		[0-9]+(?={skip}:)|
		!+
		'''.format(comment=COMMENT_RE, skip=SKIP_RE), fix_kv, code)


DATE_FORMATS_MONTH_FIRST = (
	'%d %B %Y',
	'%d %b %Y',
	'%B %d %Y',
	'%B %dst %Y',
	'%B %dnd %Y',
	'%B %drd %Y',
	'%B %dth %Y',
	'%b %d %Y',
	'%b %dst %Y',
	'%b %dnd %Y',
	'%b %drd %Y',
	'%b %dth %Y',
	'%b %dst %Y %I:%M',
	'%b %dnd %Y %I:%M',
	'%b %drd %Y %I:%M',
	'%b %dth %Y %I:%M',
	'%Y %m %d',
	'%Y-%m-%d',
	'%Y.%m.%d.',
	'%Y/%m/%d',
	'%Y/%m/%d %H:%M',
	'%Y/%m/%d %H:%M:%S',
	'%Y%m%d%H%M',
	'%Y%m%d%H%M%S',
	'%Y%m%d',
	'%Y-%m-%d %H:%M',
	'%Y-%m-%d %H:%M:%S',
	'%Y-%m-%d %H:%M:%S.%f',
	'%Y-%m-%d %H:%M:%S:%f',
	'%d.%m.%Y %H:%M',
	'%d.%m.%Y %H.%M',
	'%Y-%m-%dT%H:%M:%SZ',
	'%Y-%m-%dT%H:%M:%S.%fZ',
	'%Y-%m-%dT%H:%M:%S.%f0Z',
	'%Y-%m-%dT%H:%M:%S',
	'%Y-%m-%dT%H:%M:%S.%f',
	'%Y-%m-%dT%H:%M',
	'%b %d %Y at %H:%M',
	'%b %d %Y at %H:%M:%S',
	'%B %d %Y at %H:%M',
	'%B %d %Y at %H:%M:%S',
	'%H:%M %d-%b-%Y',
	'%m-%d-%Y',
	'%m.%d.%Y',
	'%m/%d/%Y',
	'%m/%d/%y',
	'%m/%d/%Y %H:%M:%S',
)


def extract_timezone(date_str):
	m = re.search(
		r'''(?x)
			^.{8,}?											  # >=8 char non-TZ prefix, if present
			(?P<tz>Z|											# just the UTC Z, or
				(?:(?<=.\b\d{4}|\b\d{2}:\d\d)|				   # preceded by 4 digits or hh:mm or
					(?<!.\b[a-zA-Z]{3}|[a-zA-Z]{4}|..\b\d\d))	 # not preceded by 3 alpha word or >= 4 alpha or 2 digits
					[ ]?										  # optional space
				(?P<sign>\+|-)								   # +/-
				(?P<hours>[0-9]{2}):?(?P<minutes>[0-9]{2})	   # hh[:]mm
			$)
		''', date_str)
	date_str = date_str[:-len(m.group('tz'))]
	if not m.group('sign'):
		timezone = datetime.timedelta()
	else:
		sign = 1 if m.group('sign') == '+' else -1
		timezone = datetime.timedelta(
			hours=sign * int(m.group('hours')),
			minutes=sign * int(m.group('minutes')))
	return timezone, date_str


def unified_timestamp(date_str):
	date_str = re.sub(r'\s+', ' ', re.sub(
		r'(?i)[,|]|(mon|tues?|wed(nes)?|thu(rs)?|fri|sat(ur)?)(day)?', '', date_str))

	pm_delta = 12 if re.search(r'(?i)PM', date_str) else 0
	timezone, date_str = extract_timezone(date_str)

	# Remove AM/PM + timezone
	date_str = re.sub(r'(?i)\s*(?:AM|PM)(?:\s+[A-Z]+)?', '', date_str)

	for expression in DATE_FORMATS_MONTH_FIRST:
		try:
			dt = datetime.datetime.strptime(date_str, expression) - timezone + datetime.timedelta(hours=pm_delta)
			return calendar.timegm(dt.timetuple())
		except ValueError:
			pass


def remove_quotes(s):
	if s is None or len(s) < 2:
		return s
	for quote in ('"', "'", ):
		if s[0] == quote and s[-1] == quote:
			return s[1:-1]
	return s


# NB In principle NaN cannot be checked by membership.
# Here all NaN values are actually this one, so _NaN is _NaN,
# although _NaN != _NaN.

_NaN = float('nan')


def _js_bit_op(op):

	def zeroise(x):
		return 0 if x in (None, JSUndefined, _NaN) else x

	def wrapped(a, b):
		return op(zeroise(a), zeroise(b)) & 0xffffffff

	return wrapped


def _js_arith_op(op):

	def wrapped(a, b):
		if JSUndefined in (a, b):
			return _NaN
		return op(a or 0, b or 0)

	return wrapped


def _js_div(a, b):
	if JSUndefined in (a, b) or not (a or b):
		return _NaN
	return operator.truediv(a or 0, b) if b else float('inf')


def _js_mod(a, b):
	if JSUndefined in (a, b) or not b:
		return _NaN
	return (a or 0) % b


def _js_exp(a, b):
	if not b:
		return 1  # even 0 ** 0 !!
	elif JSUndefined in (a, b):
		return _NaN
	return (a or 0) ** b


def _js_eq_op(op):

	def wrapped(a, b):
		if set((a, b)) <= set((None, JSUndefined)):
			return op(a, a)
		return op(a, b)

	return wrapped


def _js_comp_op(op):

	def wrapped(a, b):
		if JSUndefined in (a, b):
			return False
		if isinstance(a, compat_str):
			b = compat_str(b or 0)
		elif isinstance(b, compat_str):
			a = compat_str(a or 0)
		return op(a or 0, b or 0)

	return wrapped


def _js_ternary(cndn, if_true=True, if_false=False):
	"""Simulate JS's ternary operator (cndn?if_true:if_false)"""
	if cndn in (False, None, 0, '', JSUndefined, _NaN):
		return if_false
	return if_true


# (op, definition) in order of binding priority, tightest first
# avoid dict to maintain order
# definition None => Defined in JSInterpreter._operator
_OPERATORS = (
	('>>', _js_bit_op(operator.rshift)),
	('<<', _js_bit_op(operator.lshift)),
	('+', _js_arith_op(operator.add)),
	('-', _js_arith_op(operator.sub)),
	('*', _js_arith_op(operator.mul)),
	('%', _js_mod),
	('/', _js_div),
	('**', _js_exp),
)

_COMP_OPERATORS = (
	('===', operator.is_),
	('!==', operator.is_not),
	('==', _js_eq_op(operator.eq)),
	('!=', _js_eq_op(operator.ne)),
	('<=', _js_comp_op(operator.le)),
	('>=', _js_comp_op(operator.ge)),
	('<', _js_comp_op(operator.lt)),
	('>', _js_comp_op(operator.gt)),
)

_LOG_OPERATORS = (
	('|', _js_bit_op(operator.or_)),
	('^', _js_bit_op(operator.xor)),
	('&', _js_bit_op(operator.and_)),
)

_SC_OPERATORS = (
	('?', None),
	('??', None),
	('||', None),
	('&&', None),
)

_OPERATOR_RE = '|'.join(map(lambda x: re.escape(x[0]), _OPERATORS + _LOG_OPERATORS))

_NAME_RE = r'[a-zA-Z_$][\w$]*'
_MATCHING_PARENS = dict(zip(*zip('()', '{}', '[]')))
_QUOTES = '\'"/'


class JSUndefined():
	pass


class JSBreak(Exception):
	pass


class JSContinue(Exception):
	pass


class JSThrow(Exception):
	pass


class LocalNameSpace(compat_map):
	def __getitem__(self, key):
		try:
			return super(LocalNameSpace, self).__getitem__(key)
		except KeyError:
			return JSUndefined

	def __setitem__(self, key, value):
		for scope in self.maps:
			if key in scope:
				scope[key] = value
				return
		self.maps[0][key] = value


class JSInterpreter(object):
	__named_object_counter = 0

	def __init__(self, code, objects=None):
		self.code, self._functions = code, {}
		self._objects = {} if objects is None else objects

	def _named_object(self, namespace, obj):
		self.__named_object_counter += 1
		name = '%s%d' % ('__youtube_jsinterp_obj', self.__named_object_counter)
		namespace[name] = obj
		return name

	@classmethod
	def _separate(cls, expr, delim=',', max_split=None, skip_delims=None):
		OP_CHARS = '+-*/%&|^=<>!,;{}:['
		if not expr:
			return
		# collections.Counter() is ~10% slower in both 2.7 and 3.9
		counters = {k: 0 for k in _MATCHING_PARENS.values()}
		start, splits, pos, delim_len = 0, 0, 0, len(delim) - 1
		in_quote, escaping = None, False
		after_op, in_regex_char_group = True, False

		for idx, char in enumerate(expr):
			paren_delta = 0
			if not in_quote:
				if char in _MATCHING_PARENS:
					counters[_MATCHING_PARENS[char]] += 1
					paren_delta = 1
				elif char in counters:
					counters[char] -= 1
					paren_delta = -1
			if not escaping:
				if char in _QUOTES and in_quote in (char, None):
					if in_quote or after_op or char != '/':
						in_quote = None if in_quote and not in_regex_char_group else char
				elif in_quote == '/' and char in '[]':
					in_regex_char_group = char == '['
			escaping = not escaping and in_quote and char == '\\'
			in_unary_op = (not in_quote and not in_regex_char_group and after_op not in (True, False) and char in '-+')
			after_op = not in_quote and (char in OP_CHARS or paren_delta > 0 or (after_op and char.isspace()))

			if char != delim[pos] or any(counters.values()) or in_quote or in_unary_op:
				pos = 0
				continue
			elif pos != delim_len:
				pos += 1
				continue
			yield expr[start: idx - delim_len]
			start, pos = idx + 1, 0
			splits += 1
			if max_split and splits >= max_split:
				break
		yield expr[start:]

	@classmethod
	def _separate_at_paren(cls, expr, delim=None):
		if delim is None:
			delim = expr and _MATCHING_PARENS[expr[0]]
		separated = list(cls._separate(expr, delim, 1))

		if len(separated) < 2:
			raise RuntimeError('No terminating paren %s in %s' % (delim, expr))
		return separated[0][1:].strip(), separated[1].strip()

	@staticmethod
	def _all_operators():
		return chain(
			# Ref: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Operator_Precedence
			_SC_OPERATORS, _LOG_OPERATORS, _COMP_OPERATORS, _OPERATORS)

	def _operator(self, op, left_val, right_expr, local_vars, allow_recursion):
		if op in ('||', '&&'):
			if (op == '&&') ^ _js_ternary(left_val):
				return left_val  # short circuiting
		elif op == '??':
			if left_val not in (None, JSUndefined):
				return left_val
		elif op == '?':
			right_expr = _js_ternary(left_val, *self._separate(right_expr, ':', 1))

		right_val = self.interpret_expression(right_expr, local_vars, allow_recursion)
		opfunc = op and next((v for k, v in self._all_operators() if k == op), None)
		if not opfunc:
			return right_val

		try:
			return opfunc(left_val, right_val)
		except Exception as e:
			raise RuntimeError('Failed to evaluate', left_val, op, right_val, e)

	def _index(self, obj, idx):
		if idx == 'length':
			return len(obj)
		try:
			return obj[int(idx)] if isinstance(obj, list) else obj[idx]
		except Exception as e:
			raise RuntimeError('Cannot get index', idx, e)

	def _dump(self, obj, namespace):
		try:
			return dumps(obj)
		except TypeError:
			return self._named_object(namespace, obj)

	# used below
	_VAR_RET_THROW_RE = re.compile(r'''(?x)
		(?P<var>(?:var|const|let)\s)|return(?:\s+|(?=["'])|$)|(?P<throw>throw\s+)
		''')
	_COMPOUND_RE = re.compile(r'''(?x)
		(?P<try>try)\s*\{|
		(?P<if>if)\s*\(|
		(?P<switch>switch)\s*\(|
		(?P<for>for)\s*\(|
		(?P<while>while)\s*\(
		''')
	_FINALLY_RE = re.compile(r'finally\s*\{')
	_SWITCH_RE = re.compile(r'switch\s*\(')

	def interpret_statement(self, stmt, local_vars, allow_recursion=100):
		if allow_recursion < 0:
			raise RuntimeError('Recursion limit reached')
		allow_recursion -= 1

		should_return = False
		# fails on (eg) if (...) stmt1; else stmt2;
		sub_statements = list(self._separate(stmt, ';')) or ['']
		expr = stmt = sub_statements.pop().strip()
		for sub_stmt in sub_statements:
			ret, should_return = self.interpret_statement(sub_stmt, local_vars, allow_recursion)
			if should_return:
				return ret, should_return

		m = self._VAR_RET_THROW_RE.match(stmt)
		if m:
			expr = stmt[len(m.group(0)):].strip()
			if m.group('throw'):
				raise JSThrow()
			should_return = not m.group('var')
		if not expr:
			return None, should_return

		if expr[0] in _QUOTES:
			inner, outer = self._separate(expr, expr[0], 1)
			if expr[0] == '/':
				inner = re.compile(inner[1:].replace('[[', r'[\['))
			else:
				inner = loads(js_to_json(inner + expr[0]))
			if not outer:
				return inner, should_return
			expr = self._named_object(local_vars, inner) + outer

		if expr.startswith('new '):
			obj = expr[4:]
			if obj.startswith('Date('):
				left, right = self._separate_at_paren(obj[4:])
				date = unified_timestamp(
					self.interpret_expression(left, local_vars, allow_recursion))
				if date is None:
					raise RuntimeError('Failed to parse date', left)
				expr = self._dump(int(date * 1000), local_vars) + right
			else:
				raise RuntimeError('Unsupported object', obj)

		if expr.startswith('void '):
			left = self.interpret_expression(expr[5:], local_vars, allow_recursion)
			return None, should_return

		if expr.startswith('{'):
			inner, outer = self._separate_at_paren(expr)
			# try for object expression (Map)
			sub_expressions = [list(self._separate(sub_expr.strip(), ':', 1)) for sub_expr in self._separate(inner)]
			if all(len(sub_expr) == 2 for sub_expr in sub_expressions):
				def dict_item(key, val):
					val = self.interpret_expression(val, local_vars, allow_recursion)
					if re.match(_NAME_RE, key):
						return key, val
					return self.interpret_expression(key, local_vars, allow_recursion), val

				return dict(dict_item(k, v) for k, v in sub_expressions), should_return

			inner, should_abort = self.interpret_statement(inner, local_vars, allow_recursion)
			if not outer or should_abort:
				return inner, should_abort or should_return
			else:
				expr = self._dump(inner, local_vars) + outer

		if expr.startswith('('):

			m = re.match(r'\((?P<d>[a-z])%(?P<e>[a-z])\.length\+(?P=e)\.length\)%(?P=e)\.length', expr)
			if m:
				# short-cut eval of frequently used `(d%e.length+e.length)%e.length`, worth ~6% on `pytest -k test_nsig`
				outer = None
				inner, should_abort = self._offset_e_by_d(m.group('d'), m.group('e'), local_vars)
			else:
				inner, outer = self._separate_at_paren(expr)
				inner, should_abort = self.interpret_statement(inner, local_vars, allow_recursion)
			if not outer or should_abort:
				return inner, should_abort or should_return
			else:
				expr = self._dump(inner, local_vars) + outer

		if expr.startswith('['):
			inner, outer = self._separate_at_paren(expr)
			name = self._named_object(local_vars, [
				self.interpret_expression(item, local_vars, allow_recursion)
				for item in self._separate(inner)])
			expr = name + outer

		m = self._COMPOUND_RE.match(expr)
		md = m.groupdict() if m else {}
		if md.get('if'):
			cndn, expr = self._separate_at_paren(expr[m.end() - 1:])
			if_expr, expr = self._separate_at_paren(expr.lstrip())
			else_expr = None
			m = re.match(r'else\s*{', expr)
			if m:
				else_expr, expr = self._separate_at_paren(expr[m.end() - 1:])
			cndn = _js_ternary(self.interpret_expression(cndn, local_vars, allow_recursion))
			ret, should_abort = self.interpret_statement(
				if_expr if cndn else else_expr, local_vars, allow_recursion)
			if should_abort:
				return ret, True

		elif md.get('try'):
			try_expr, expr = self._separate_at_paren(expr[m.end() - 1:])
			err = None
			try:
				ret, should_abort = self.interpret_statement(try_expr, local_vars, allow_recursion)
				if should_abort:
					return ret, True
			except Exception as e:
				# This works for now, but makes debugging future issues very hard
				err = e

			pending = (None, False)
			m = re.match(r'catch\s*(?P<err>\(\s*{_NAME_RE}\s*\))?\{{'.format(**globals()), expr)
			if m:
				sub_expr, expr = self._separate_at_paren(expr[m.end() - 1:])
				if err:
					catch_vars = {}
					if m.group('err'):
						catch_vars[m.group('err')] = err
					catch_vars = local_vars.new_child(m=catch_vars)
					err = None
					pending = self.interpret_statement(sub_expr, catch_vars, allow_recursion)

			m = self._FINALLY_RE.match(expr)
			if m:
				sub_expr, expr = self._separate_at_paren(expr[m.end() - 1:])
				ret, should_abort = self.interpret_statement(sub_expr, local_vars, allow_recursion)
				if should_abort:
					return ret, True

			ret, should_abort = pending
			if should_abort:
				return ret, True

			if err:
				raise err

		elif md.get('for') or md.get('while'):
			init_or_cond, remaining = self._separate_at_paren(expr[m.end() - 1:])
			if remaining.startswith('{'):
				body, expr = self._separate_at_paren(remaining)
			else:
				switch_m = self._SWITCH_RE.match(remaining)
				if switch_m:
					switch_val, remaining = self._separate_at_paren(remaining[switch_m.end() - 1:])
					body, expr = self._separate_at_paren(remaining, '}')
					body = 'switch(%s){%s}' % (switch_val, body)
				else:
					body, expr = remaining, ''
			if md.get('for'):
				start, cndn, increment = self._separate(init_or_cond, ';')
				self.interpret_expression(start, local_vars, allow_recursion)
			else:
				cndn, increment = init_or_cond, None
			while _js_ternary(self.interpret_expression(cndn, local_vars, allow_recursion)):
				try:
					ret, should_abort = self.interpret_statement(body, local_vars, allow_recursion)
					if should_abort:
						return ret, True
				except JSBreak:
					break
				except JSContinue:
					pass
				if increment:
					self.interpret_expression(increment, local_vars, allow_recursion)

		elif md.get('switch'):
			switch_val, remaining = self._separate_at_paren(expr[m.end() - 1:])
			switch_val = self.interpret_expression(switch_val, local_vars, allow_recursion)
			body, expr = self._separate_at_paren(remaining, '}')
			items = body.replace('default:', 'case default:').split('case ')[1:]
			for default in (False, True):
				matched = False
				for item in items:
					case, stmt = (i.strip() for i in self._separate(item, ':', 1))
					if default:
						matched = matched or case == 'default'
					elif not matched:
						matched = (case != 'default' and switch_val == self.interpret_expression(case, local_vars, allow_recursion))
					if not matched:
						continue
					try:
						ret, should_abort = self.interpret_statement(stmt, local_vars, allow_recursion)
						if should_abort:
							return ret
					except JSBreak:
						break
				if matched:
					break

		if md:
			ret, should_abort = self.interpret_statement(expr, local_vars, allow_recursion)
			return ret, should_abort or should_return

		# Comma separated statements
		sub_expressions = list(self._separate(expr))
		if len(sub_expressions) > 1:
			for sub_expr in sub_expressions:
				ret, should_abort = self.interpret_statement(sub_expr, local_vars, allow_recursion)
				if should_abort:
					return ret, True
			return ret, False

		for m in re.finditer(r'''(?x)
				(?P<pre_sign>\+\+|--)(?P<var1>{_NAME_RE})|
				(?P<var2>{_NAME_RE})(?P<post_sign>\+\+|--)'''.format(**globals()), expr):
			var = m.group('var1') or m.group('var2')
			start, end = m.span()
			sign = m.group('pre_sign') or m.group('post_sign')
			ret = local_vars[var]
			local_vars[var] += 1 if sign[0] == '+' else -1
			if m.group('pre_sign'):
				ret = local_vars[var]
			expr = expr[:start] + self._dump(ret, local_vars) + expr[end:]

		if not expr:
			return None, should_return

		m = re.match(r'''(?x)
			(?P<assign>
				(?P<out>{_NAME_RE})(?:\[(?P<index>[^\]]+?)\])?\s*
				(?P<op>{_OPERATOR_RE})?
				=(?!=)(?P<expr>.*)$
			)|(?P<return>
				(?!if|return|true|false|null|undefined)(?P<name>{_NAME_RE})$
			)|(?P<indexing>
				(?P<in>{_NAME_RE})\[(?P<idx>.+)\]$
			)|(?P<attribute>
				(?P<var>{_NAME_RE})(?:(?P<nullish>\?)?\.(?P<member>[^(]+)|\[(?P<member2>[^\]]+)\])\s*
			)|(?P<function>
				(?P<fname>{_NAME_RE})\((?P<args>.*)\)$
			)'''.format(**globals()), expr)
		md = m.groupdict() if m else {}
		if md.get('assign'):
			left_val = local_vars.get(m.group('out'))

			if not m.group('index'):
				local_vars[m.group('out')] = self._operator(
					m.group('op'), left_val, m.group('expr'), local_vars, allow_recursion)
				return local_vars[m.group('out')], should_return
			elif left_val in (None, JSUndefined):
				raise RuntimeError('Cannot index undefined variable', m.group('out'))

			idx = self.interpret_expression(m.group('index'), local_vars, allow_recursion)
			if not isinstance(idx, (int, float)):
				raise RuntimeError('List index %s must be integer' % idx)
			idx = int(idx)
			left_val[idx] = self._operator(
				m.group('op'), self._index(left_val, idx), m.group('expr'), local_vars, allow_recursion)
			return left_val[idx], should_return

		elif expr.isdigit():
			return int(expr), should_return

		elif expr == 'break':
			raise JSBreak()
		elif expr == 'continue':
			raise JSContinue()

		elif expr == 'undefined':
			return JSUndefined, should_return
		elif expr == 'NaN':
			return _NaN, should_return

		elif md.get('return'):
			return local_vars[m.group('name')], should_return

		try:
			ret = loads(js_to_json(expr))  # strict=True)
			if not md.get('attribute'):
				return ret, should_return
		except ValueError:
			pass

		if md.get('indexing'):
			val = local_vars[m.group('in')]
			idx = self.interpret_expression(m.group('idx'), local_vars, allow_recursion)
			return self._index(val, idx), should_return

		for op, _ in self._all_operators():
			# hackety: </> have higher priority than <</>>, but don't confuse them
			skip_delim = (op + op) if op in '<>*?' else None
			if op == '?':
				skip_delim = (skip_delim, '?.')
			separated = list(self._separate(expr, op, skip_delims=skip_delim))
			if len(separated) < 2:
				continue

			right_expr = separated.pop()
			# handle operators that are both unary and binary, minimal BODMAS
			if op in ('+', '-'):
				undone = 0
				while len(separated) > 1 and not separated[-1].strip():
					undone += 1
					separated.pop()
				if op == '-' and undone % 2 != 0:
					right_expr = op + right_expr
				left_val = separated[-1]
				for dm_op in ('*', '%', '/', '**'):
					bodmas = tuple(self._separate(left_val, dm_op, skip_delims=skip_delim))
					if len(bodmas) > 1 and not bodmas[-1].strip():
						expr = op.join(separated) + op + right_expr
						right_expr = None
						break
				if right_expr is None:
					continue

			left_val = self.interpret_expression(op.join(separated), local_vars, allow_recursion)
			return self._operator(op, left_val, right_expr, local_vars, allow_recursion), should_return

		if md.get('attribute'):
			variable, member, nullish = m.group('var', 'member', 'nullish')
			if not member:
				member = self.interpret_expression(m.group('member2'), local_vars, allow_recursion)
			arg_str = expr[m.end():]
			if arg_str.startswith('('):
				arg_str, remaining = self._separate_at_paren(arg_str)
			else:
				arg_str, remaining = None, arg_str

			def eval_method():
				if (variable, member) == ('console', 'debug'):
					return
				types = {
					'String': compat_str,
					'Math': float,
				}
				obj = local_vars.get(variable)
				if obj in (JSUndefined, None):
					obj = types.get(variable, JSUndefined)
				if obj is JSUndefined:
					try:
						if variable not in self._objects:
							self._objects[variable] = self.extract_object(variable)
						obj = self._objects[variable]
					except Exception:
						if not nullish:
							raise

				if nullish and obj is JSUndefined:
					return JSUndefined

				# Member access
				if arg_str is None:
					return self._index(obj, member)

				# Function call
				argvals = [
					self.interpret_expression(v, local_vars, allow_recursion)
					for v in self._separate(arg_str)]

				if obj == compat_str:
					if member == 'fromCharCode':
						return ''.join(map(compat_chr, argvals))
					raise RuntimeError('Unsupported string method', member)
				elif obj == float:
					if member == 'pow':
						return argvals[0] ** argvals[1]
					raise RuntimeError('Unsupported Math method', member)

				if member == 'split':
					return obj.split(argvals[0]) if argvals[0] else list(obj)
				elif member == 'join':
					return argvals[0].join(obj)
				elif member == 'reverse':
					obj.reverse()
					return obj
				elif member == 'slice':
					return obj[argvals[0]:]
				elif member == 'splice':
					index, how_many = map(int, (argvals + [len(obj)])[:2])
					if index < 0:
						index += len(obj)
					add_items = argvals[2:]
					res = []
					for i in range(index, min(index + how_many, len(obj))):
						res.append(obj.pop(index))
					for i, item in enumerate(add_items):
						obj.insert(index + i, item)
					return res
				elif member == 'unshift':
					for item in reversed(argvals):
						obj.insert(0, item)
					return obj
				elif member == 'pop':
					if not obj:
						return
					return obj.pop()
				elif member == 'push':
					obj.extend(argvals)
					return obj
				elif member == 'forEach':
					f, this = (argvals + [''])[:2]
					return [f((item, idx, obj), {'this': this}, allow_recursion) for idx, item in enumerate(obj)]
				elif member == 'indexOf':
					idx, start = (argvals + [0])[:2]
					try:
						return obj.index(idx, start)
					except ValueError:
						return -1
				elif member == 'charCodeAt':
					idx = argvals[0] if isinstance(argvals[0], int) else 0
					if idx >= len(obj):
						return None
					return ord(obj[idx])

				idx = int(member) if isinstance(obj, list) else member
				return obj[idx](argvals, allow_recursion=allow_recursion)

			if remaining:
				ret, should_abort = self.interpret_statement(
					self._named_object(local_vars, eval_method()) + remaining,
					local_vars, allow_recursion)
				return ret, should_return or should_abort
			else:
				return eval_method(), should_return

		elif md.get('function'):
			fname = m.group('fname')
			argvals = [self.interpret_expression(v, local_vars, allow_recursion) for v in self._separate(m.group('args'))]
			if fname in local_vars:
				return local_vars[fname](argvals, allow_recursion=allow_recursion), should_return
			elif fname not in self._functions:
				self._functions[fname] = self.extract_function_from_code(*self.extract_function_code(fname))
			return self._functions[fname](argvals, allow_recursion=allow_recursion), should_return

		raise RuntimeError('Unsupported JS expression', expr[:40])

	def interpret_expression(self, expr, local_vars, allow_recursion):
		ret, should_return = self.interpret_statement(expr, local_vars, allow_recursion)
		if should_return:
			raise RuntimeError('Cannot return from an expression')
		return ret

	def extract_object(self, objname):
		_FUNC_NAME_RE = r'''(?:[a-zA-Z$0-9]+|"[a-zA-Z$0-9]+"|'[a-zA-Z$0-9]+')'''
		obj = {}
		fields = None
		for obj_m in re.finditer(
			r'''(?xs)
				{0}\s*\.\s*{1}|{1}\s*=\s*\{{\s*
				(?P<fields>({2}\s*:\s*function\s*\(.*?\)\s*\{{.*?}}(?:,\s*)?)*)
				}}\s*;
			'''.format(_NAME_RE, re.escape(objname), _FUNC_NAME_RE),
			self.code):
			fields = obj_m.group('fields')
			if fields:
				break
		else:
			raise RuntimeError('Could not find object ' + objname)
		# Currently, it only supports function definitions
		fields_m = re.finditer(
			r'''(?x)
				(?P<key>%s)\s*:\s*function\s*\((?P<args>(?:%s|,)*)\){(?P<code>[^}]+)}
			''' % (_FUNC_NAME_RE, _NAME_RE),
			fields)
		for f in fields_m:
			argnames = self.build_arglist(f.group('args'))
			obj[remove_quotes(f.group('key'))] = self.build_function(argnames, f.group('code'))

		return obj

	@staticmethod
	def _offset_e_by_d(d, e, local_vars):
		""" Short-cut eval: (d%e.length+e.length)%e.length """
		try:
			d = local_vars[d]
			e = local_vars[e]
			e = len(e)
			return _js_mod(_js_mod(d, e) + e, e), False
		except Exception:
			return None, True

	def extract_function_code(self, funcname):
		""" @returns argnames, code """
		func_m = re.search(
			r'''(?xs)
				(?:
					function\s+%(name)s|
					[{;,]\s*%(name)s\s*=\s*function|
					(?:var|const|let)\s+%(name)s\s*=\s*function
				)\s*
				\((?P<args>[^)]*)\)\s*
				(?P<code>{.+})''' % {'name': re.escape(funcname)},
			self.code)
		if func_m is None:
			raise RuntimeError('Could not find JS function', funcname)
		code, _ = self._separate_at_paren(func_m.group('code'))  # refine the match
		return self.build_arglist(func_m.group('args')), code

	def extract_function_from_code(self, argnames, code, *global_stack):
		local_vars = {}
		while True:
			mobj = re.search(r'function\((?P<args>[^)]*)\)\s*{', code)
			if mobj is None:
				break
			start, body_start = mobj.span()
			body, remaining = self._separate_at_paren(code[body_start - 1:], '}')
			name = self._named_object(local_vars, self.extract_function_from_code(
				[x.strip() for x in mobj.group('args').split(',')],
				body, local_vars, *global_stack))
			code = code[:start] + name + remaining
		return self.build_function(argnames, code, local_vars, *global_stack)

	@classmethod
	def build_arglist(cls, arg_text):
		if not arg_text:
			return []

		def valid_arg(y):
			y = y.strip()
			if not y:
				raise RuntimeError('Missing arg in "%s"' % arg_text)
			return y

		return [valid_arg(x) for x in cls._separate(arg_text)]

	def build_function(self, argnames, code, *global_stack):
		global_stack = list(global_stack) or [{}]
		argnames = tuple(argnames)

		def resf(args, kwargs={}, allow_recursion=100):
			global_stack[0].update(
				compat_zip_longest(argnames, args, fillvalue=None))
			global_stack[0].update(kwargs)
			var_stack = LocalNameSpace(*global_stack)
			ret, should_abort = self.interpret_statement(code.replace('\n', ' '), var_stack, allow_recursion - 1)
			if should_abort:
				return ret
		return resf
