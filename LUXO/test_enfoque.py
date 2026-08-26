import flet as ft
from enfoque_diario import build_enfoque_diario_view, calcular_dia, generar_excel_enfoque, generar_pdf_enfoque_file

def main(page: ft.Page):
    user_info = {"rol": "admin", "user": "mx204562", "nombre": "Admin Test"}
    view = build_enfoque_diario_view(page, user_info)
    print("View built successfully!")
    
    # Test calcs
    calc = calcular_dia("DOMINGO")
    print("Calculations done successfully! Conversion:", calc["conversion_dia"])
    
    # Test PDF
    pdf_path = generar_pdf_enfoque_file("DOMINGO")
    print("PDF generated at:", pdf_path)

    # Test Excel
    generar_excel_enfoque("DOMINGO", page)
    print("Excel generated successfully!")

ft.app(target=main)
