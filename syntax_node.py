class Node(object):
	def __str__(self):
		return self.__class__.__name__

class Container(object):
	def __init__(self):
		self.children = []
		
	def __str__(self):
		if(self.name):
			s = '\''+self.name + "\':["
			for child in self.children:
				s += str(child) + ','
			s += ']'
		else:
			s = 'UnknownContainer'
		return s

class CompoundStatement(Container):
	def __init__(self):
		pass

class DeclarationList(Container):
	def __init_(self):
		pass

class StatementList(Container):
	def __init__(self):
		pass

class Declaration(Node):
	def __init__(self):
		pass

class Expression(Node):
	pass

class PrimaryExpression(Expression):
	pass

class PostfixExpression(Expression):
	pass

class UnaryExpression(Expression):
	pass

class CastExpression(Expression):
	pass

class ArithmeticExpression(Expression):
	pass

class Operator(Node):
	pass

class AssignmentOperator(Operator):
	pass



class Variable(PrimaryExpression):
	def __init__(self, name, type="unkown"):
		super(Variable, self).__init__()
		self.name = name
		self.type = type

class PredefinedVariable(Variable):
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