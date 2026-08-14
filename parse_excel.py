import openpyxl

wb = openpyxl.load_workbook("./uploads/Enfoque_Diario_DOMINGO_SGH_2026.xlsx", data_only=False)
sheet = wb["DOMINGO"]

print("--- EXCEL DOMINGO STRUCTURE ---")
for row in sheet.iter_rows(min_row=1, max_row=40, min_col=1, max_col=15):
    for cell in row:
        if cell.value is not None:
            # check cell fill color to see if it's green or white
            fill_color = "NONE"
            if cell.fill and cell.fill.start_color and hasattr(cell.fill.start_color, 'rgb'):
                fill_color = cell.fill.start_color.rgb
            print(f"Cell {cell.coordinate}: val={cell.value}, color={fill_color}")
