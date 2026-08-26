import openpyxl

wb = openpyxl.load_workbook(r"C:\Users\MOISES\Downloads\inventario\Escaneo_Fisico_Generado.xlsx")
sheet = wb.active

print("--- PRIMERAS 15 FILAS GENERADAS ---")
for idx, r in enumerate(sheet.iter_rows(values_only=True)):
    if idx > 15: break
    print(f"Fila {idx+1}: UPC={r[0]} | Piezas={r[1]}")
