import exceptions

class UnhandledTranslationError(Exception):
	def __init__(self, nodeName):
		self.nodeName = nodeName
	def __str__(self):
		return "Error translating " + self.nodeName
	def __repr__(self):
		return self.__repr__()

def id():
	i = 0;
	while True:
		yield i
		i = i+1

def getTempName():
	return "t"+str(id())

symbolTable = {}

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