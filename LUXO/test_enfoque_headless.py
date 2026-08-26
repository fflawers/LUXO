from enfoque_diario import calcular_dia, generar_excel_enfoque, generar_pdf_enfoque_file

print("Testing calcs...")
calc = calcular_dia("DOMINGO")
print("Calc success! Conversion:", calc["conversion_dia"])

print("Testing PDF...")
pdf = generar_pdf_enfoque_file("DOMINGO")
print("PDF success!", pdf)

print("Testing Excel...")
generar_excel_enfoque("DOMINGO", None)
print("Excel success!")

