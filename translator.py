import exceptions
import re

#####################################################################
#
#                      Bitfield Operator Support
#
#####################################################################

bitOp1ArgRE = re.compile(r'<\s*(\w+)\s*:\s*>')

bitOpWordRE = re.compile(r'(?<![\w\.])([\w\.]+)<\s*(\w+)\s*:\s*(\w+)\s*>')
bitOpExprRE = re.compile(r'\)<\s*(\w+)\s*:\s*(\w+)\s*>')

def substBitOps(code):
    # first convert single-bit selectors to two-index form
    # i.e., <n> --> <n:n>
    code = bitOp1ArgRE.sub(r'<\1:\1>', code)
    # simple case: selector applied to ID (name)
    # i.e., foo<a:b> --> bits(foo, a, b)
    code = bitOpWordRE.sub(r'bits(\1, \2, \3)', code)
    # if selector is applied to expression (ending in ')'),
    # we need to search backward for matching '('
    match = bitOpExprRE.search(code)
    while match:
        exprEnd = match.start()
        here = exprEnd - 1
        nestLevel = 1
        while nestLevel > 0:
            if code[here] == '(':
                nestLevel -= 1
            elif code[here] == ')':
                nestLevel += 1
            here -= 1
            if here < 0:
                sys.exit("Didn't find '('!")
        exprStart = here+1
        newExpr = r'bits(%s, %s, %s)' % (code[exprStart:exprEnd+1],
                                         match.group(1), match.group(2))
        code = code[:exprStart] + newExpr + code[match.end():]
        match = bitOpExprRE.search(code)
    return code

def preprocess(code):
	return substBitOps(code)

class UnhandledTranslationError(Exception):
	def __init__(self, nodeName):
		self.nodeName = nodeName
	def __str__(self):
		return "Error translating " + self.nodeName
	def __repr__(self):
		return self.__repr__()

def getTempName():
	i = 0;
	while True:
		yield 't'+str(i)
		i = i+1

class TranslationResult(object):
	def __init__(self, value, code):
		self.value = value
		self.code = code
	def __str__(self):
		return "value: "+ self.value + " code:" + self.code;
	def __repr__(self):
		return self.__str__()

class Type(object):
	def __repr__(self):
		return self.__str__()

class VoidType(Type):
	def __str__(self):
		return 'void'

class CharType(Type):
	def __str__(self):
		return 'char'

class IntType(Type):
	def __init__(self, isSigned=True, size=32):
		self.isSigned = isSigned
		self.size = size
	def __str__(self):
		s = ""
		if not self.isSigned:
			s += 'u'
		s += "int%d_t" % self.size
		return s

class Twin64Type(Type):
	def __str__(self):
		return "Twin64_t"

class FloatType(Type):
	def __str__(self):
		return 'float'

class DoubleType(Type):
	def __str__(self):
		return 'double'

class StructType(Type):
	pass

class UnionType(Type):
	pass

class EnumType(Type):
	pass

class TypeIDType(Type):
	def __init__(self, typeID):
		self.typeID = typeID
	def __str__(self):
		return self.typeID

class PointerType(Type):
	def __init__(self, baseType=None, level=1):
		self.baseType = baseType
		self.level = 1
	def __str__(self):
		if self.baseType != None:
			s = str(self.baseType)
		else:
			s = "Unknown"
		for i in range(self.level):
			s += "*"
		return s

class StructOrUnionType(Type):
	structOrUnion = "unknown"
	def __init__(self, name=None, definition=None):
		self.name = name
		self.definition = definition
	def __str__(self):
		s = self.structOrUnion + " "
		if self.name != None:
			s += self.name
		if self.definition != None:
			s += "{ "
			s += str(self.definition)
			s += " }"
		return s
class StructType(StructOrUnionType):
	structOrUnion = "struct"

class UnionType(StructOrUnionType):
	structOrUnion = "union"

class Expression(object):
	def __init__(self):
		self.value = None
	def __repr__(self):
		return self.__str__()

class Variable(Expression):
	def __init__(self, name, type=None):
		super(Variable, self).__init__()
		self.name = name
		self.type = type

	def __str__(self):
		return self.name

class BinaryOperandExpression(Expression):
	def __init__(self, left, operator, right):
		self.left = left
		self.right = right
		self.operator = operator
	def __str__(self):
		return str(self.left) + self.operator + str(self.right)

class UnaryOperandExpression(Expression):
	def __init__(self, operand, operator, isPrefix):
		self.operand = operand
		self.operator = operator
		self.isPrefix = isPrefix
	def __str__(self):
		s = ""
		if self.isPrefix:
			s += self.operator
			s += str(self.operand)
		else:
			s += str(self.operand)
			s += self.operator
		return s

class CastExpression(Expression):
	def __init__(self, targetType, originalExpression):
		self.targetType = targetType
		self.originalExpression = originalExpression
	def __str__(self):
		return "(%s)(%s)" % (str(self.targetType), str(self.originalExpression))

class ConditionalExpression(Expression):
	def __init__(self, condition, truePart, falsePart):
		self.condition = condition
		self.truePart = truePart
		self.falsePart = falsePart
	def __str__(self):
		return "(%s)?(%s):(%s)" % (str(self.condition), str(self.truePart), str(self.falsePart))

class FunctionCallExpression(Expression):
	def __init__(self, function, arguments):
		self.function = function
		self.arguments = arguments
	def __str__(self):
		return "%s(%s)" %(str(self.function), str(self.arguments))

class CommaExpression(Expression):
	def __init__(self, expressionList):
		self.expressionList = expressionList
	def __str__(self):
		return str(self.expressionList)
	def append(self, expression):
		self.expressionList.append(expression)

class PredefinedRegister(Variable):
	pass

class PredefinedConstant(Variable):
	pass

class Constant(object):
	def __str__(self):
		return str(self.value)
	def __repr__(self):
		return self.__str__()

class IntConstant(Constant):
	def __init__(self, value):
		value = value.lower()
		sign = 1
		i = 0
		isSigned = True
		size = 32
		if value[i] == '+':
			i = i+1
		elif value[i] == '-':
			i = i+1
			sign = -1
		if value[i]=='0' and len(value)>i+1 : #in case it's just '0'
			if value[i+1] == 'b':
				base = 2
				i = i+2
			elif value[i+1] == 'x':
				base = 16
				i = i+2
			else:
				base = 8
				i = i+1
		else:
			base = 10
		j = len(value)
		suffix = value[-2:]
		if 'l' in suffix:
			size = 64
			j = j-1
		if 'u' in suffix:
			isSigned = False
			j = j-1
		digits = value[i:j]
		self.value = sign*int(digits, base)
		self.type = IntType(isSigned, size)

class FloatConstant(Constant):
	def __init__(self, value):
		self.type = FloatType()
		self.value = float(value)

class CharConstant(Constant):
	def __init__(self, value):
		self.type = CharType()
		self.value = value

class StringConstant(Constant):
	def __init__(self, value):
		self.type = PointerType(CharType())
		self.value = value

class Statement(object):
	def __repr__(self):
		return self.__str__()

class Declarator(Statement): pass

class VariableDeclarator(Declarator):
	def __init__(self, type=None, variable=None, initializer=None):
		self.type = type
		self.variable = variable
		self.initializer = initializer
	def __str__(self):
		s = ""
		if self.type != None:
			s += str(self.type)
		if self.variable != None:
			s += " " + str(self.variable)
		if self.initializer != None:
			s += " = " + str(self.initializer)
		return s
class TypeDeclarator(Declarator):
	def __init__(self, type=None):
		self.type = type
	def __str__(self):
		return str(self.type)

class ExpressionStatement(Statement):
	def __init__(self, statement):
		self.statement = statement
	def __str__(self):
		return str(self.statement)

class IfStatement(Statement):
	def __init__(self, condition=None, truePart=None, falsePart=None):
		self.condition = condition
		self.truePart = truePart
		self.falsePart = falsePart
	def __str__(self):
		s = "if ("
		if self.condition != None:
			s += str(self.condition)
		else:
			s += "unknown"
		s += "){ "
		if self.truePart != None:
			s += str(self.truePart)
		s += " }"
		if self.falsePart != None:
			s += "else{ "
			s += str(self.falsePart)
			s += " }"
		return s

class ForStatement(Statement):
	def __init__(self, preLoopPart=None, condition=None, postLoopBodyPart=None, loopBodyPart=None):
		self.preLoopPart = preLoopPart
		self.condition = condition
		self.postLoopBodyPart = postLoopBodyPart
		self.loopBodyPart = loopBodyPart
	def __str__(self):
		s = "for("
		if self.preLoopPart != None:
			s += str(self.preLoopPart)
		s += ";"
		if self.condition != None:
			s += str(self.condition)
		s += ";"
		if self.postLoopBodyPart != None:
			s += str(self.postLoopBodyPart)
		s += "){ "
		if self.loopBodyPart != None:
			s += str(self.loopBodyPart)
		s += " }"
		return s

class WhileStatement(Statement):
	def __init__(self, condition, loopBodyPart):
		self.condition = condition
		self.loopBodyPart = loopBodyPart
	def __str__(self):
		return "while(%s){ %s }" % (str(self.condition), str(self.loopBodyPart))

class CaseStatement(Statement):
	def __init__(self, case=None, caseBody=None, isDefault=False):
		self.isDefault = isDefault
		self.case = case
		self. caseBody = caseBody
	def __str__(self):
		if self.isDefault:
			return "default: %s" % (str(self.caseBody))
		else:
			return "case %s: %s" %(str(self.case), str(self.caseBody))

class BreakStatement(Statement):
	def __str__(self):
		return "break"

class SwitchStatement(Statement):
	def __init__(self, switcher, bodyPart):
		self.switcher = switcher
		self.bodyPart = bodyPart
	def __str__(self):
		return "switch(%s) { %s }" % (str(self.switcher), str(self.bodyPart))

class CompoundStatement(Statement):
	def __init__(self, statements=None):
		self.statements = statements
	def __str__(self):
		s = "{ "
		if self.statements != None:
			s += str(self.statements)
		s += " }"
		return s

predefinedTypeID = {
    "uint8_t":IntType(False, 8),
    "uint16_t":IntType(False, 16),
    "uint32_t":IntType(False, 32),
    "uint64_t":IntType(False, 64),
    "int8_t":IntType(True, 8),
    "int16_t":IntType(True, 16),
    "int32_t":IntType(True, 32),
    "int64_t":IntType(True, 64),
    "Twin64_t":Twin64Type(),
    }

predefinedValues = {
	"Rd": PredefinedRegister("Rd", "int"),
	"Rm": PredefinedRegister("Rm", "int"),
	"Rn": PredefinedRegister("Rn", "int"),
	"SHIFT": PredefinedConstant("SHIFT", "int")
	}

class DictStack(list):
	def push(self, item={}):
		self.append(item)
	def top(self):
		return self[-1]
	def get(self, name):
		for d in self[::-1]:
			try:
				val = d[name]
				return val
			except KeyError:
				pass
		return None
	def set(self, name, val):
		assert len(self) > 0
		self[-1][name] = val
	def has(self, name):
		if self.get(name) != None:
			return True
		else:
			return False

typeIDTable = DictStack()
typeIDTable.push(predefinedTypeID)
symbolTable = DictStack()
symbolTable.push(predefinedValues)