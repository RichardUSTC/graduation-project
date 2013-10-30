import exceptions

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

class Expression(object):
	pass

class BinaryOperandExpression(Expression):
	def __init__(self, left, operator, right):
		self.left = left
		self.right = right
		self.operator = operator
	def __str__(self):
		return str(self.left) + self.operator + str(self.right)
	def __repr__(self):
		return self.__str__()

class Variable(Expression):
	def __init__(self, name, type="unkown"):
		super(Variable, self).__init__()
		self.name = name
		self.type = type

	def __str__(self):
		return self.name

	def __repr__(self):
		return self.__str__()

class PredefinedRegister(Variable):
	def translate(self):
		if self.type == "int":
			value = self.name + str(id())
			code = "Value * %s = getIntReg(%s);" % (value, self.name.upper())
			return TranslationResult(value, code)
		else:
			raise UnhandledTranslationError("PredefinedRegister")
	pass

class PredefinedConstant(Variable):
	def translate(self):
		if self.type == "int":
			value = self.name + str(id())
			code = "Value * %s = getIntConstant(%s);" %(value, self.name)
	pass

class TempVariable(Variable):
	pass

class Constant(object):
	pass

class IntConstant(Constant):
	def __init__(self, value):
		self.type = "int"
		self.value = int(value)

class FloatConstant(Constant):
	def __init__(self, value):
		self.type = 'float'
		self.value = float(value)

class CharConstant(Constant):
	def __init__(self, value):
		self.type = 'char'
		self.value = value

class StringConstant(Constant):
	def __init__(self, value):
		self.type = 'string'
		self.value = value

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