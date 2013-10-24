import syntax_node

predefinedTypeID = (
    "uint8_t", "uint16_t", "uint32_t", "uint64_t",
    "int8_t", "int16_t", "int32_t", "int64_t", "Twin64_t",
    )

predefinedValues = {
	"Rd": syntax_node.PredefinedRegister("Rd", "int"),
	"Rm": syntax_node.PredefinedRegister("Rm", "int"),
	"Rn": syntax_node.PredefinedRegister("Rn", "int"),
	"SHIFT": syntax_node.PredefinedConstant("SHIFT", "int")
	}