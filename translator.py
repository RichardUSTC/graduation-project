import exceptions
import re

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

class Expression(object):
	def __init__(self):
		self.value = None
	def __repr__(self):
		return self.__str__()

class Variable(Expression):
	def __init__(self, name, type="unkown"):
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
		suffix = value[-1:-2]
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

class Declarator(object):
	def __repr__(self):
		return self.__str__()

class VariableDeclarator(Declarator):
	def __init__(self):
		self.type = None
		self.variable = None
		self.initializer = None
	def __str__(self):
		s = ""
		if self.type != None:
			s += str(self.type)
		if self.variable != None:
			s += " " + str(self.variable)
		if self.initializer != None:
			s += " = " + str(self.initializer)
		return s

predefinedTypeID = (
    "uint8_t", "uint16_t", "uint32_t", "uint64_t",
    "int8_t", "int16_t", "int32_t", "int64_t", "Twin64_t",
    )

predefinedValues = {
	"Rd": PredefinedRegister("Rd", "int"),
	"Rm": PredefinedRegister("Rm", "int"),
	"Rn": PredefinedRegister("Rn", "int"),
	"SHIFT": PredefinedConstant("SHIFT", "int")
	}

class SymbolTable(object):
	symbolStack = [predefinedValues]
	@classmethod
	def find(cls, name):
		for d in cls.symbolStack[::-1]:
			try:
				var = d[name]
				return var
			except KeyError:
				pass
		return None
	@classmethod
	def put(cls, name, var):
		if len(cls.symbolStack) > 1:
			cls.symbolStack[-1][name] = var
		else:
			raise Exception()
	@classmethod
	def push(cls):
		symbolStack.append({})
	@classmethod
	def pop(cls):
		symbolStack.pop()