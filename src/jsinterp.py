from __future__ import unicode_literals

import operator
import re

from itertools import chain
from json import dumps, loads

from .compat import compat_chr, compat_str, compat_map, compat_zip_longest


def js_to_json(code):
	COMMENT_RE = r'/\*(?:(?!\*/).)*?\*/|//[^\n]*'
	SKIP_RE = r'\s*(?:{comment})?\s*'.format(comment=COMMENT_RE)

	def fix_kv(m):
		v = m.group(0)
		if v in ('true', 'false', 'null'):
			return v
		elif v.startswith('/*') or v.startswith('//') or v.startswith('!') or v == ',':
			return ""

		if v[0] in ("'", '"'):
			v = re.sub(r'(?s)\\.|"', lambda m: {
				'"': '\\"',
				"\\'": "'",
				'\\\n': '',
				'\\x': '\\u00',
			}.get(m.group(0), m.group(0)), v[1:-1])

		return '"%s"' % v

	return re.sub(r'''(?sx)
		"(?:[^"\\]*(?:\\\\|\\['"nurtbfx/\n]))*[^"\\]*"|
		'(?:[^'\\]*(?:\\\\|\\['"nurtbfx/\n]))*[^'\\]*'|
		{comment}|,(?={skip}[\]}}])|
		(?:(?<![0-9])[eE]|[a-df-zA-DF-Z_])[.a-zA-Z_0-9]*|
		\b(?:0[xX][0-9a-fA-F]+|0+[0-7]+)(?:{skip}:)?|
		[0-9]+(?={skip}:)|
		!+
		'''.format(comment=COMMENT_RE, skip=SKIP_RE), fix_kv, code)


def _js_arith_op(op):

	def wrapped(a, b):
		return op(a or 0, b or 0)

	return wrapped


def _js_mod(a, b):
	return (a or 0) % b


def _js_eq_op(op):

	def wrapped(a, b):
		return op(a, b)

	return wrapped


def _js_ternary(cndn, if_true=True, if_false=False):
	"""Simulate JS's ternary operator (cndn?if_true:if_false)"""
	if cndn in (False, None, 0, '', JSUndefined):
		return if_false
	return if_true


# (op, definition) in order of binding priority, tightest first
# avoid dict to maintain order
# definition None => Defined in JSInterpreter._operator
_OPERATORS = (
	('+', _js_arith_op(operator.add)),
	('-', _js_arith_op(operator.sub)),
	('*', _js_arith_op(operator.mul)),
	('%', _js_mod),
)

_COMP_OPERATORS = (
	('===', operator.is_),
	('!==', operator.is_not),
	('==', _js_eq_op(operator.eq)),
	('!=', _js_eq_op(operator.ne)),
	('<=', _js_arith_op(operator.le)),
	('>=', _js_arith_op(operator.ge)),
	('<', _js_arith_op(operator.lt)),
	('>', _js_arith_op(operator.gt)),
)

_SC_OPERATORS = (
	('?', None),
	('??', None),
	('||', None),
	('&&', None),
)

_OPERATOR_RE = '|'.join(map(lambda x: re.escape(x[0]), _OPERATORS))

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


class JSInterpreter(object):
	__named_object_counter = 0

	_RE_FLAGS = {
		# special knowledge: Python's re flags are bitmask values, current max 128
		# invent new bitmask values well above that for literal parsing
		'd': 1024,  # Generate indices for substring matches
		'g': 2048,  # Global search
		'i': re.I,  # Case-insensitive search
		'm': re.M,  # Multi-line search
		's': re.S,  # Allows . to match newline characters
		'u': re.U,  # Treat a pattern as a sequence of unicode code points
		'y': 4096,  # Perform a "sticky" search that matches starting at the current position in the target string
	}

	def __init__(self, code, objects=None):
		self.code, self._functions = code, {}
		self._objects = {} if objects is None else objects

	def _named_object(self, namespace, obj):
		self.__named_object_counter += 1
		name = '%s%d' % ('__youtube_jsinterp_obj', self.__named_object_counter)
		namespace[name] = obj
		return name

	@staticmethod
	def _separate(expr, delim=',', max_split=None):
		OP_CHARS = '+-*/%&|^=<>!,;{}:['
		if not expr:
			return
		counters = {k: 0 for k in _MATCHING_PARENS.values()}
		start, splits, pos, delim_len = 0, 0, 0, len(delim) - 1
		in_quote, escaping, after_op, in_regex_char_group, in_unary_op = None, False, True, False, False
		for idx, char in enumerate(expr):
			if not in_quote and char in _MATCHING_PARENS:
				counters[_MATCHING_PARENS[char]] += 1
			elif not in_quote and char in counters:
				# Something's wrong if we get negative, but ignore it anyway
				if counters[char]:
					counters[char] -= 1
			elif not escaping:
				if char in _QUOTES and in_quote in (char, None):
					if in_quote or after_op or char != '/':
						in_quote = None if in_quote and not in_regex_char_group else char
				elif in_quote == '/' and char in '[]':
					in_regex_char_group = char == '['
			escaping = not escaping and in_quote and char == '\\'
			in_unary_op = (not in_quote and not in_regex_char_group and after_op not in (True, False) and char in '-+')
			after_op = char if (not in_quote and char in OP_CHARS) else (char.isspace() and after_op)

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
			raise RuntimeError('No terminating paren {delim} in {expr!r:.5500}'.format(**locals()))
		return separated[0][1:].strip(), separated[1].strip()

	@staticmethod
	def _all_operators():
		return chain(
			# Ref: https://developer.mozilla.org/en-US/docs/Web/JavaScript/Reference/Operators/Operator_Precedence
			_SC_OPERATORS, _COMP_OPERATORS, _OPERATORS)

	def _operator(self, op, left_val, right_expr, expr, local_vars, allow_recursion):
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
		except Exception:
			raise RuntimeError('Failed to evaluate {left_val!r:.50} {op} {right_val!r:.50}'.format(**locals()))

	def _index(self, obj, idx):
		if idx == 'length':
			return len(obj)
		try:
			return obj[int(idx)] if isinstance(obj, list) else obj[idx]
		except Exception:
			raise RuntimeError('Cannot get index {idx:.100}'.format(**locals()))

	def _dump(self, obj, namespace):
		try:
			return dumps(obj)
		except TypeError:
			return self._named_object(namespace, obj)

	def interpret_statement(self, stmt, local_vars, allow_recursion=100):
		if allow_recursion < 0:
			raise RuntimeError('Recursion limit reached')
		allow_recursion -= 1

		should_return = False
		sub_statements = list(self._separate(stmt, ';')) or ['']
		expr = stmt = sub_statements.pop().strip()

		for sub_stmt in sub_statements:
			ret, should_return = self.interpret_statement(sub_stmt, local_vars, allow_recursion)
			if should_return:
				return ret, should_return

		m = re.match(r'(?P<var>(?:var|const|let)\s)|return(?:\s+|(?=["\'])|$)|(?P<throw>throw\s+)', stmt)
		if m:
			expr = stmt[len(m.group(0)):].strip()
			if m.group('throw'):
				raise JSThrow(self.interpret_expression(expr, local_vars, allow_recursion))
			should_return = not m.group('var')
		if not expr:
			return None, should_return

		if expr[0] in _QUOTES:
			inner, outer = self._separate(expr, expr[0], 1)
			if expr[0] == '/':
				flags = 0
				inner = re.compile(inner[1:].replace('[[', r'[\['), flags=flags)
			else:
				inner = loads(js_to_json(inner + expr[0]))
			if not outer:
				return inner, should_return
			expr = self._named_object(local_vars, inner) + outer

		if expr.startswith('('):
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

		m = re.match(r'''(?x)
			(?P<try>try)\s*\{|
			(?P<if>if)\s*\(|
			(?P<switch>switch)\s*\(|
			(?P<for>for)\s*\(|
			(?P<while>while)\s*\(
			''', expr)
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
				# XXX: This works for now, but makes debugging future issues very hard
				err = e

			pending = (None, False)
			m = re.match(r'catch\s*(?P<err>\(\s*{_NAME_RE}\s*\))?\{{'.format(**globals()), expr)
			if m:
				sub_expr, expr = self._separate_at_paren(expr[m.end() - 1:])
				if err:
					catch_vars = {}
					if m.group('err'):
						catch_vars[m.group('err')] = err.error if isinstance(err, JSThrow) else err
					catch_vars = local_vars.new_child(m=catch_vars)
					err, pending = None, self.interpret_statement(sub_expr, catch_vars, allow_recursion)

			m = re.match(r'finally\s*\{', expr)
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
				switch_m = re.match(r'switch\s*\(', remaining)
				if switch_m:
					switch_val, remaining = self._separate_at_paren(remaining[switch_m.end() - 1:])
					body, expr = self._separate_at_paren(remaining, '}')
					body = 'switch(%s){%s}' % (switch_val, body)
				else:
					body, expr = remaining, ''
			start, cndn, increment = self._separate(init_or_cond, ';')
			self.interpret_expression(start, local_vars, allow_recursion)
			while True:
				if not _js_ternary(self.interpret_expression(cndn, local_vars, allow_recursion)):
					break
				try:
					ret, should_abort = self.interpret_statement(body, local_vars, allow_recursion)
					if should_abort:
						return ret, True
				except JSBreak:
					break
				except JSContinue:
					pass
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
					m.group('op'), left_val, m.group('expr'), expr, local_vars, allow_recursion)
				return local_vars[m.group('out')], should_return
			elif left_val in (None, JSUndefined):
				raise RuntimeError('Cannot index undefined variable ' + m.group('out'))

			idx = self.interpret_expression(m.group('index'), local_vars, allow_recursion)
			if not isinstance(idx, (int, float)):
				raise RuntimeError('List index %s must be integer' % idx)
			idx = int(idx)
			left_val[idx] = self._operator(
				m.group('op'), self._index(left_val, idx), m.group('expr'), expr, local_vars, allow_recursion)
			return left_val[idx], should_return

		elif expr.isdigit():
			return int(expr), should_return

		elif expr == 'break':
			raise JSBreak()
		elif expr == 'continue':
			raise JSContinue()

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
			separated = list(self._separate(expr, op))
			right_expr = separated.pop()
			while True:
				if op in '?<>*-' and len(separated) > 1 and not separated[-1].strip():
					separated.pop()
				elif not (separated and op == '?' and right_expr.startswith('.')):
					break
				right_expr = op + right_expr
				if op != '-':
					right_expr = separated.pop() + op + right_expr
			if not separated:
				continue
			left_val = self.interpret_expression(op.join(separated), local_vars, allow_recursion)
			return self._operator(op, left_val, right_expr, expr, local_vars, allow_recursion), should_return

		if md.get('attribute'):
			variable, member, nullish = m.group('var', 'member', 'nullish')
			if not member:
				member = self.interpret_expression(m.group('member2'), local_vars, allow_recursion)
			arg_str = expr[m.end():]
			if arg_str.startswith('('):
				arg_str, remaining = self._separate_at_paren(arg_str)
			else:
				arg_str, remaining = None, arg_str

			def assertion(cndn, msg):
				""" assert, but without risk of getting optimized out """
				if not cndn:
					memb = member
					raise RuntimeError('{memb} {msg}'.format(**locals()))

			def eval_method():
				types = {
					'String': compat_str,
					'Math': float,
				}
				obj = local_vars.get(variable)
				if obj in (JSUndefined, None):
					obj = types.get(variable, JSUndefined)

				if nullish and obj is JSUndefined:
					return JSUndefined

				# Member access
				if arg_str is None:
					return self._index(obj, member)

				# Function call
				argvals = [
					self.interpret_expression(v, local_vars, allow_recursion)
					for v in self._separate(arg_str)]

				ARG_ERROR = 'takes one or more arguments'
				LIST_ERROR = 'must be applied on a list'

				if obj == compat_str:
					if member == 'fromCharCode':
						assertion(argvals, ARG_ERROR)
						return ''.join(map(compat_chr, argvals))
					raise RuntimeError('Unsupported string method ' + member)
				elif obj == float:
					if member == 'pow':
						assertion(len(argvals) == 2, 'takes two arguments')
						return argvals[0] ** argvals[1]
					raise RuntimeError('Unsupported Math method ' + member)

				if member == 'split':
					assertion(argvals, ARG_ERROR)
					assertion(len(argvals) == 1, 'with limit argument is not implemented')
					return obj.split(argvals[0]) if argvals[0] else list(obj)
				elif member == 'join':
					assertion(isinstance(obj, list), LIST_ERROR)
					assertion(len(argvals) == 1, 'takes exactly one argument')
					return argvals[0].join(obj)
				elif member == 'reverse':
					assertion(not argvals, 'does not take any arguments')
					obj.reverse()
					return obj
				elif member == 'splice':
					assertion(isinstance(obj, list), LIST_ERROR)
					assertion(argvals, ARG_ERROR)
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
					assertion(isinstance(obj, list), LIST_ERROR)
					assertion(argvals, ARG_ERROR)
					for item in reversed(argvals):
						obj.insert(0, item)
					return obj
				elif member == 'pop':
					assertion(isinstance(obj, list), LIST_ERROR)
					assertion(not argvals, 'does not take any arguments')
					if not obj:
						return
					return obj.pop()
				elif member == 'push':
					assertion(argvals, ARG_ERROR)
					obj.extend(argvals)
					return obj
				elif member == 'forEach':
					assertion(argvals, ARG_ERROR)
					assertion(len(argvals) <= 2, 'takes at-most 2 arguments')
					f, this = (argvals + [''])[:2]
					return [f((item, idx, obj), {'this': this}, allow_recursion) for idx, item in enumerate(obj)]
				elif member == 'indexOf':
					assertion(argvals, ARG_ERROR)
					assertion(len(argvals) <= 2, 'takes at-most 2 arguments')
					idx, start = (argvals + [0])[:2]
					try:
						return obj.index(idx, start)
					except ValueError:
						return -1

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
				self._functions[fname] = self.extract_function(fname)
			return self._functions[fname](argvals, allow_recursion=allow_recursion), should_return

		raise RuntimeError('Unsupported JS expression ' + (expr[:40] if expr != stmt else ''))

	def interpret_expression(self, expr, local_vars, allow_recursion):
		ret, should_return = self.interpret_statement(expr, local_vars, allow_recursion)
		if should_return:
			raise RuntimeError('Cannot return from an expression')
		return ret

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
		code, _ = self._separate_at_paren(func_m.group('code'))  # refine the match
		if func_m is None:
			raise RuntimeError('Could not find JS function "{funcname}"'.format(**locals()))
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
			global_stack[0].update(compat_zip_longest(argnames, args, fillvalue=None))
			global_stack[0].update(kwargs)
			var_stack = LocalNameSpace(*global_stack)
			ret, should_abort = self.interpret_statement(code.replace('\n', ' '), var_stack, allow_recursion - 1)
			if should_abort:
				return ret
		return resf
