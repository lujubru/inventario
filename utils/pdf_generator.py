from fpdf import FPDF

def generar_pdf(filename, data, headers):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    # Añadir encabezados
    col_width = pdf.w / len(headers)
    row_height = pdf.font_size * 1.5
    for header in headers:
        pdf.cell(col_width, row_height, header, border=1)
    pdf.ln(row_height)
    
    # Añadir datos
    for row in data:
        for item in row:
            pdf.cell(col_width, row_height, str(item), border=1)
        pdf.ln(row_height)
    
    pdf.output(filename)