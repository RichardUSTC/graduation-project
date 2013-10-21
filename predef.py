import syntax_node

predefinedTypeID = (
    "uint8_t", "uint16_t", "uint32_t", "uint64_t",
    "int8_t", "int16_t", "int32_t", "int64_t", "Twin64_t",
    )

predefinedVariables = {
	"Rd": syntax_node.PredefinedVariable("Rd", "int"),
	"Rm": syntax_node.PredefinedVariable("Rm", "int"),
	"Rn": syntax_node.PredefinedVariable("Rn", "int"),
	}