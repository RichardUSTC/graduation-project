import exceptions
import re
import struct

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

class UnhandledTranslationError(Exception): pass

class CodeEmitter(object):
    @classmethod
    def init(cls, fileName):
        cls.fileName = fileName
        with open(cls.fileName, "w") as f:
            f.truncate()
        Temp.reset()
    @classmethod
    def append(cls, code):
        with open(cls.fileName, "a") as f:
            f.write(code)
    @classmethod
    def appendLine(cls, code):
        with open(cls.fileName, "a") as f:
            f.write(code+"\n")

class BranchGenerator(object):
    def __init__(self, condName):
        self.state = "init"
        self.condName = condName
        self.trueBlockName = "trueBlock_%d" % Temp.getTempId()
        self.falseBlockName = "falseBlock_%d" % Temp.getTempId()
        self.exitBlockName = "exitBlock_%d" % Temp.getTempId()
        CodeEmitter.appendLine("BasicBlock *%s = createBlock()" % self.trueBlockName);
        CodeEmitter.appendLine("BasicBlock *%s = createBlock()" % self.falseBlockName);
        CodeEmitter.appendLine("BasicBlock *%s = createBlock()" % self.exitBlockName);
    def startCondition(self):
        assert self.state == "init"
        self.state = "start condition"
    def endCondition(self):
        assert self.state == "start condition"
        self.state = "end condition"
        CodeEmitter.appendLine("builder->CreateCondBr(%s, %s, %s);" % (self.condName, self.trueBlockName, self.falseBlockName))
    def startTruePart(self):
        assert self.state == "end condition"
        self.state = "start true part"
        CodeEmitter.appendLine("builder->SetInsertPoint(%s);" % self.trueBlockName)
    def endTruePart(self):
        assert self.state == "start true part"
        self.state = "end true part"
        CodeEmitter.appendLine("builder->CreateBr(%s);" % self.exitBlockName)
    def startFalsePart(self):
        assert self.state == "end true part"
        self.state = "start false part"
        CodeEmitter.appendLine("builder->SetInsertPoint(%s);" % self.falseBlockName)
    def endFalsePart(self):
        assert self.state == "start false part"
        self.state = "end false part"
        CodeEmitter.appendLine("builder->CreateBr(%s);" % self.exitBlockName)
    def startExitPart(self):
        assert self.state == "end false part"
        self.state = "start exit part"
        CodeEmitter.appendLine("builder->SetInsertPoint(%s);" % self.exitBlockName)
    def endExitPart(self):
        assert self.state == "start exit part"
        self.state = "end exit part"
    def addPhi(self, name, irType, condTrueValue, condFalseValue):
        assert self.state == "start exit part"
        CodeEmitter.appendLine("PHINode *%s = builder->CreatePHI(%s, 2);" % (name, irType))
        CodeEmitter.appendLine("%s->addIncoming(%s, %s);" % (name, condTrueValue, self.trueBlockName))
        CodeEmitter.appendLine("%s->addIncoming(%s, %s);" % (name, condFalseValue, self.falseBlockName))


class Temp(object):
    i = 0
    @classmethod
    def getTempName(cls):
        cls.i += 1
        return 't' + str(cls.i)
    @classmethod
    def getTempId(cls):
        cls.i += 1
        return cls.i
    @classmethod
    def reset(cls):
        cls.i = 0

class TranslationResult(object):
    def __init__(self, type, value):
        self.type = type
        self.value = value;
    def __str__(self):
        return "%s:%s" % (str(self.value), str(self.type))
    def __repr__(self):
        return self.__str__()

class TypeCompareError(Exception): pass
class TypeCastError(Exception): pass

class TypeCaster(object):
    @classmethod
    def integralPromotion(cls, input):
        if isinstance(input, IntType):
            if input.type < IntType():
                return cls.castTo(IntType(), input)
        return input
    @classmethod
    def castForArithmetic(cls, result1, result2):
        assert isinstance(result1, TranslationResult)
        assert isinstance(result2, TranslationResult)
        try:
            result1 = cls.integralPromotion(result1)
            result2 = cls.integralPromotion(result2)
            type1 = result1.type
            type2 = result2.type
            if type1 > type2:
                newResult2 = cls.castTo(type1, result2)
                return (result1, newResult2)
            else:
                newResult1 = cls.castTo(type2, result1)
                return (newResult1, result2)
        except TypeCompareError:
            raise TypeCastError
    @classmethod
    def castTo(cls, targetType, input):
        if targetType == input.type:
            return input
        newValue = Temp.getTempName()
        typeName = targetType.getIRType()
        if isinstance(targetType, DoubleType):
            CodeEmitter.appendLine("Value *%s = builder->CreateFPCast(%s, %s);" % (newValue, input.value, typeName))
        elif isinstance(targetType, FloatType):
            CodeEmitter.appendLine("Value *%s = builder->CreateFPCast(%s, %s);" %(newValue, input.value, typeName))
        elif isinstance(targetType, IntType):
            if targetType.isSigned:
                isSigned = "true"
            else:
                isSigned = "false"
            CodeEmitter.appendLine("Value *%s = builder->CreateIntCast(%s, %s, %s);" % (newValue, input.value, typeName, isSigned))
        else:
            raise TypeCastError
        return TranslationResult(targetType, newValue)

class Type(object):
    def __repr__(self):
        return self.__str__()
    def __cmp__(self, other):
        raise TypeCompareError
    def getIRType(self):
        raise UnhandledTranslationError

class VoidType(Type):
    def __str__(self):
        return 'void'
    def getIRType(self):
        typeName = Temp.getTempName()
        CodeEmitter.appendLine("Type *%s = getVoidTy(context);" % typeName)
        return typeName

class IntType(Type):
    def __init__(self, isSigned=True, size=struct.calcsize("i")):
        self.isSigned = isSigned
        self.size = size
    def __str__(self):
        s = ""
        if not self.isSigned:
            s += 'u'
        s += "int%d_t" % self.size
        return s
    def __cmp__(self, other):
        if isinstance(other, FloatType) or isinstance(other, DoubleType):
            return -1
        elif isinstance(other, IntType):
            if self.size == other.size:
                if self.isSigned:
                    if other.isSigned:
                        return 0
                    else:
                        return -1
                else:
                    if other.isSigned:
                        return 1
                    else:
                        return 0
            else:
                return self.size - other.size
        else:
            raise TypeCompareError
    def getIRType(self):
        typeName = Temp.getTempName()
        CodeEmitter.appendLine("Type *%s = getIntNTy(context, %d);" % (typeName, self.size))
        return typeName

class Twin64Type(Type):
    def __str__(self):
        return "Twin64_t"

class FloatType(Type):
    def __str__(self):
        return 'float'
    def __cmp__(self, other):
        if isinstance(other, DoubleType):
            return -1
        elif isinstance(other, FloatType):
            return 0
        elif isinstance(other, IntType):
            return 1
        else:
            raise TypeCompareError
    def getIRType(self):
        typeName = Temp.getTempName()
        CodeEmitter.appendLine("Type *%s = getFloatTy(context);" % (typeName))
        return typeName

class DoubleType(Type):
    def __str__(self):
        return 'double'
    def __cmp__(self, other):
        if isinstance(other, DoubleType):
            return 0
        elif isinstance(other, FloatType) or isinstance(other, IntType):
            return 1
        else:
            raise TypeCompareError
    def getIRType(self):
        typeName = Temp.getTempName()
        CodeEmitter.appendLine("Type *%s = getDoubleTy(context);" % (typeName))
        return typeName

class StructType(Type):
    pass

class UnionType(Type):
    pass

class EnumType(IntType):
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
    def getIRType(self):
        baseTypeName = self.baseType.getIRType()
        typeName = Temp.getTempName()
        CodeEmitter.appendLine("PointerType *%s = %s->getPointerTo();" % (typeName, baseTypeName))
        return typeName

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
            s += "{\n"
            s += str(self.definition)
            s += "\n}"
        return s
class StructType(StructOrUnionType):
    structOrUnion = "struct"

class UnionType(StructOrUnionType):
    structOrUnion = "union"

class Expression(object):
    def __repr__(self):
        return self.__str__()
    def setValue(self, result):
        raise UnhandledTranslationError
    def translate(self):
        raise UnhandledTranslationError

class Variable(Expression):
    def __init__(self, name, type=None):
        self.name = name
        self.type = type
    def __str__(self):
        return self.name
    def setValue(self, result):
        v = symbolTable.get(self.name)
        if v != None:
            v.setValue(result)
        else:
            raise UnhandledTranslationError
    def translate(self):
        v = symbolTable.get(self.name)
        if v != None:
            return v.translate()
        else:
            raise UnhandledTranslationError

class IntRegister(Variable):
    def setValue(self, result):
        newResult = TypeCaster.castTo(self.type, result)
        CodeEmitter.appendLine("setIntReg(this, %s, %s);" % (self.name.upper(), newResult.value))
    def translate(self):
        value = "%s_%d" % (self.name, Temp.getTempId())
        CodeEmitter.appendLine("Value *%s = getIntReg(this, %s);" % (value, self.name.upper()))
        return TranslationResult(self.type, value)

class IntConstantVariable(Variable):
    def translate(self):
        value = "%s_%d" % (self.name, Temp.getTempId())
        CodeEmitter.appendLine("Value *%s = translator->getImm64(this, %s);" % (value, self.name))
        return TranslationResult(self.type, value)

class NormalVariable(Variable):
    def __init__(self, name, type, allocaValue):
        self.name = name
        self.type = type
        self.allocaValue = allocaValue
    def setValue(self, result):
        newResult = TypeCaster.castTo(self.type, result)
        CodeEmitter.appendLine("builder->CreateStore(%s, %s);" % (newResult.value, self.allocaValue))
    def translate(self):
        assert self.allocaValue != None
        value = "%s_%d" % (self.name, Temp.getTempId())
        CodeEmitter.appendLine("Value *%s = builder->CreateLoad(%s);" % (value, self.allocaValue))
        return TranslationResult(self.type, value)


class BinaryOperandExpression(Expression):
    def __init__(self, left, operator, right):
        self.left = left
        self.right = right
        self.operator = operator
    def __str__(self):
        return "(%s %s %s)" % (str(self.left), self.operator, str(self.right))
    
    # for '+' '-' '*' '/' '%'
    def _translateHelper1(self, opType, intSignSensitive=False):
        leftResult = self.left.translate()
        rightResult = self.right.translate()
        newLeftResult, newRightResult = TypeCaster.castForArithmetic(leftResult, rightResult)
        resultName = Temp.getTempName()
        operandType = newLeftResult.type
        if isinstance(operandType, IntType):
            if intSignSensitive:
                if operandType.isSigned:
                    function = "CreateS%s" % opType
                else:
                    function = "CreateU%s" % opType
            else:
                function = "Create%s" % opType
        elif isinstance(operandType, FloatType) or isinstance(operandType, DoubleType):
            function = "CreateF%s" % opType
        else:
            raise UnhandledTranslationError
        CodeEmitter.appendLine("Value *%s = builder->%s(%s, %s);" %(resultName, function, newLeftResult.value, newRightResult.value))
        return TranslationResult(operandType, resultName)
    # for '|' '&' '^' '<<' '>>'
    def _translateHelper2(self, opType):
        leftResult = self.left.translate()
        rightResult = self.right.translate()
        assert isinstance(leftResult.type, IntType)
        assert isinstance(rightResult.type, IntType)
        newLeftResult, newRightResult = TypeCaster.castForArithmetic(leftResult, rightResult)
        resultName = Temp.getTempName()
        operandType = newLeftResult.type
        function = "Create%s" % opType
        CodeEmitter.appendLine("Value *%s = builder->%s(%s, %s);" %(resultName, function, newLeftResult.value, newRightResult.value))
        return TranslationResult(operandType, resultName)
    # for '<' '>' '<=' '>=' '==' '!='
    def _translateHelper3(self, opType, intSignSensitive=True, floatOrder=True):
        leftResult = self.left.translate()
        rightResult = self.right.translate()
        newLeftResult, newRightResult = TypeCaster.castForArithmetic(leftResult, rightResult)
        resultName = Temp.getTempName()
        operandType = newLeftResult.type
        if isinstance(operandType, IntType):
            if intSignSensitive:
                if operandType.isSigned:
                    function = "CreateICmpS%s" % opType
                else:
                    function = "CreateICmpU%s" % opType
            else:
                function = "CreateICmp%s" % opType
        elif isinstance(operandType, FloatType) or isinstance(operandType, DoubleType):
            if floatOrder:
                function = "CreateFCmpO%s" % opType
            else:
                function = "CreateFCmpU%s" % opType
        else:
            raise UnhandledTranslationError
        CodeEmitter.appendLine("Value *%s = builder->%s(%s, %s);" %(resultName, function, newLeftResult.value, newRightResult.value))
        return TranslationResult(IntType(isSigned=False, size=1), resultName)
    def translate(self):
        CodeEmitter.appendLine("/* %s */" % str(self))
        if self.operator == "=":
            rightResult = self.right.translate()
            self.left.setValue(rightResult)
            return rightResult
        elif self.operator == "+":
            return self._translateHelper1("Add")
        elif self.operator == "-":
            return self._translateHelper1("Sub")
        elif self.operator == "*":
            return self._translateHelper1("Mul")
        elif self.operator == "/":
            return self._translateHelper1("Div", intSignSensitive=True)
        elif self.operator == "%":
            return self._translateHelper1("Rem", intSignSensitive=True)
        elif self.operator == "|":
            return self._translateHelper2("Or")
        elif self.operator == "&":
            return self._translateHelper2("And")
        elif self.operator == "^":
            return self._translateHelper2("Xor")
        elif self.operator == "<<":
            return self._translateHelper2("Shl")
        elif self.operator == ">>":
            return self._translateHelper2("LShr")
        elif self.operator == "||":
            resultName = Temp.getTempName()
            leftResult = self.left.translate()
            if not isinstance(leftResult.type, IntType):
                leftResult = TypeCaster.castTo(IntType(), leftResult)
            zero = "zero_%d" % Temp.getTempId()
            CodeEmitter.appendLine("Value *%s = translator::getImm%d(0);" % (zero, leftResult.type.size))
            leftBoolValue = Temp.getTempName()
            CodeEmitter.appendLine("Value *%s = builder->CreateICmpNE(%s, %s);" % (leftBoolValue, leftResult.value, zero))
            
            branch = BranchGenerator(leftBoolValue)
            branch.startCondition()
            branch.endCondition()
            
            branch.startTruePart()
            branch.endTruePart()

            branch.startFalsePart()
            rightResult = self.right.translate()
            if not isinstance(rightResult.type, IntType):
                rightResult = TypeCaster.castTo(IntType(), rightResult)
            rightBoolValue = Temp.getTempName()
            CodeEmitter.appendLine("Value *%s = builder->CreateICmpNE(%s, %s);" % (rightBoolValue, rightResult.value, zero))
            branch.endFalsePart()
            
            branch.startExitPart()
            resultType = IntType(isSigned=False, size=1)
            branch.addPhi(resultName, resultType.getIRType(), leftBoolValue, rightBoolValue);
            branch.endExitPart();
            return TranslationResult(resultType, resultName)
        elif self.operator == "&&":
            resultName = Temp.getTempName()
            leftResult = self.left.translate()
            if not isinstance(leftResult.type, IntType):
                leftResult = TypeCaster.castTo(IntType(), leftResult)
            zero = "zero_%d" % Temp.getTempId()
            CodeEmitter.appendLine("Value *%s = translator::getImm%d(0);" % (zero, leftResult.type.size))
            leftBoolValue = Temp.getTempName()
            CodeEmitter.appendLine("Value *%s = builder->CreateICmpNE(%s, %s);" % (leftBoolValue, leftResult.value, zero))
            
            branch = BranchGenerator(leftBoolValue)
            branch.startCondition()
            branch.endCondition()
            
            branch.startTruePart()
            rightResult = self.right.translate()
            if not isinstance(rightResult.type, IntType):
                rightResult = TypeCaster.castTo(IntType(), rightResult)
            rightBoolValue = Temp.getTempName()
            CodeEmitter.appendLine("Value *%s = builder->CreateICmpNE(%s, %s);" % (rightBoolValue, rightResult.value, zero))
            branch.endTruePart()

            branch.startFalsePart()
            branch.endFalsePart()
            
            branch.startExitPart()
            resultType = IntType(isSigned=False, size=1)
            branch.addPhi(resultName, resultType.getIRType(), rightBoolValue, leftBoolValue);
            branch.endExitPart();
            return TranslationResult(resultType, resultName)
        elif self.operator == "<":
            return self._translateHelper3("LT")
        elif self.operator == ">":
            return self._translateHelper3("GT")
        elif self.operator == "<=":
            return self._translateHelper3("LE")
        elif self.operator == ">=":
            return self._translateHelper3("GE")
        elif self.operator == "==":
            return self._translateHelper3("EQ", intSignSensitive=False)
        elif self.operator == "!=":
            return self._translateHelper3("NE", intSignSensitive=False)
        elif self.operator == "+=":
            result = self._translateHelper1("Add")
            self.left.setValue(result)
        elif self.operator == "-=":
            result = self._translateHelper1("Sub")
            self.left.setValue(result)
        elif self.operator == "*=":
            result = self._translateHelper1("Mul")
            self.left.setValue(result)
        elif self.operator == "/=":
            result = self._translateHelper1("Div", intSignSensitive=True)
            self.left.setValue(result)
        elif self.operator == "%=":
            result = self._translateHelper1("Rem", intSignSensitive=True)
            self.left.setValue(result)
        elif self.operator == "<<=":
            result = self._translateHelper2("Shl")
            self.left.setValue(result)
        elif self.operator == ">>=":
            result = self._translateHelper2("LShr")
            self.left.setValue(result)
        elif self.operator == "&=":
            result = self._translateHelper2("And")
            self.left.setValue(result)
        elif self.operator == "|=":
            result = self._translateHelper2("Or")
            self.left.setValue(result)
        elif self.operator == "^=":
            result = self._translateHelper2("Xor")
            self.left.setValue(result)
        else:
            raise UnhandledTranslationError


class UnaryOperandExpression(Expression):
    def __init__(self, operand, operator, isPrefix):
        self.operand = operand
        self.operator = operator
        self.isPrefix = isPrefix
    def __str__(self):
        s = "("
        if self.isPrefix:
            s += self.operator
            s += str(self.operand)
        else:
            s += str(self.operand)
            s += self.operator
        s += ")"
        return s
    def translate(self):
        raise UnhandledTranslationError

class CastExpression(Expression):
    def __init__(self, targetType, originalExpression):
        self.targetType = targetType
        self.originalExpression = originalExpression
    def __str__(self):
        return "(%s)(%s)" % (str(self.targetType), str(self.originalExpression))
    def translate(self):
        raise UnhandledTranslationError

class ConditionalExpression(Expression):
    def __init__(self, condition, truePart, falsePart):
        self.condition = condition
        self.truePart = truePart
        self.falsePart = falsePart
    def __str__(self):
        return "(%s)?(%s):(%s)" % (str(self.condition), str(self.truePart), str(self.falsePart))
    def translate(self):
        raise UnhandledTranslationError

class FunctionCallExpression(Expression):
    def __init__(self, function, arguments):
        self.function = function
        self.arguments = arguments
    def __str__(self):
        return "%s(%s)" %(str(self.function), str(self.arguments))
    def translate(self):
        raise UnhandledTranslationError

class CommaExpression(Expression):
    def __init__(self, expressionList):
        self.expressionList = expressionList
    def __str__(self):
        s = "("
        for item in self.expressionList:
            s += str(item)
            s += ","
        s = s[:-1] + ")"
        return s
    def append(self, expression):
        self.expressionList.append(expression)
    def translate(self):
        raise UnhandledTranslationError

class InstanceMemberAccessExpression(Expression):
    def __init__(self, instance, member):
        self.instance = instance
        self.member = member
    def __str__(self):
        return "(%s).%s" % (str(self.instance), str(self.member))
    def setValue(self, result):
        raise UnhandledTranslationError
    def translate(self):
        raise UnhandledTranslationError

class PointerMemberAccessExpression(Expression):
    def __init__(self, pointer, member):
        self.pointer = pointer
        self.member = member
    def __str__(self):
        return "(%s)->%s" % (str(self.pointer), str(self.member))
    def setValue(self, result):
        raise UnhandledTranslationError
    def translate(self):
        raise UnhandledTranslationError

class ArrayAccessExpression(Expression):
    def __init__(self, base, index):
        self.base = base
        self.index = index
    def __str__(self):
        return "(%s)[%s]" % (str(self.base), str(self.index))
    def setValue(self, result):
        raise UnhandledTranslationError
    def translate(self):
        raise UnhandledTranslationError

class Constant(object):
    def __str__(self):
        return self.value
    def __repr__(self):
        return self.__str__()

class IntConstant(Constant):
    def __init__(self, value):
        value = value.lower()
        isSigned = True
        size = struct.calcsize("i")
        suffix = value[-3:]
        if 'll' in suffix:
            size = struct.calcsize("q")
            j = j-2
        elif 'l' in suffix:
            size = struct.calcsize("l")
            j = j-1
        if 'u' in suffix:
            isSigned = False
            j = j-1
        self.value = value
        self.type = IntType(isSigned, size)

class FloatConstant(Constant):
    def __init__(self, value):
        self.type = FloatType()
        self.value = value

class CharConstant(Constant):
    def __init__(self, value):
        self.type = IntType(size=8, isSigned=True)
        self.value = value

class StringConstant(Constant):
    def __init__(self, value):
        self.type = PointerType(IntType(size=8, isSigned=True))
        self.value = value

class Statement(object):
    def __repr__(self):
        return self.__str__()
    def translate(self):
        raise UnhandledTranslationError

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
    def __init__(self, expression):
        self.expression = expression
    def __str__(self):
        return str(self.expression)
    def translate(self):
        self.expression.translate()
        return None

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
        s += "){\n"
        if self.truePart != None:
            s += str(self.truePart)
        s += "\n}"
        if self.falsePart != None:
            s += "else{\n"
            s += str(self.falsePart)
            s += "\n}"
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
        s += "){\n"
        if self.loopBodyPart != None:
            s += str(self.loopBodyPart)
        s += "\n}"
        return s

class WhileStatement(Statement):
    def __init__(self, condition, loopBodyPart):
        self.condition = condition
        self.loopBodyPart = loopBodyPart
    def __str__(self):
        return "while(%s){\n%s\n}" % (str(self.condition), str(self.loopBodyPart))

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
        return "switch(%s) {\n%s\n}" % (str(self.switcher), str(self.bodyPart))

class CompoundStatement(Statement):
    def __init__(self, statements=None):
        self.statements = statements
    def __str__(self):
        s = "{\n"
        if self.statements != None:
            assert isinstance(self.statements, list)
            for item in self.statements:
                s += str(item)
                s += ";\n"
        s += "\n}"
        return s
    def translate(self):
        if self.statements != None:
            assert isinstance(self.statements, list)
            for item in self.statements:
                item.translate()
        return None

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
    "Rd": IntRegister("Rd", IntType(True, 64)),
    "Rm": IntRegister("Rm", IntType(True, 64)),
    "Rn": IntRegister("Rn", IntType(True, 64)),
    "SHIFT": IntConstantVariable("SHIFT", IntType(True, 64))
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
    def add(self, name, val):
        assert len(self) > 0
        self[-1][name] = val
    def has(self, name):
        if self.get(name) != None:
            return True
        else:
            return False

typeIDTable = DictStack()
typeIDTable.push(predefinedTypeID)
typeIDTable.push()

symbolTable = DictStack()
symbolTable.push(predefinedValues)