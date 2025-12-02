"""
I need you to build the 'Audit Log' page for the Admin. 
It should display a table showing security events. 
For now, use dummy data (fake rows). I will connect the real database later.
"""
import flet as ft
from datetime import datetime

def AuditLogView(page: ft.Page):
    # 1. Define the Columns
    columns = [
        ft.DataColumn(ft.Text("ID")),
        ft.DataColumn(ft.Text("User")),
        ft.DataColumn(ft.Text("Action")),
        ft.DataColumn(ft.Text("Timestamp")),
    ]
    
    # 2. Create Dummy Rows (They can add more to test)
    rows = [
        ft.DataRow(cells=[
            ft.DataCell(ft.Text("1")),
            ft.DataCell(ft.Text("Admin")),
            ft.DataCell(ft.Text("LOGIN_SUCCESS")),
            ft.DataCell(ft.Text(str(datetime.now()))),
        ]),
        ft.DataRow(cells=[
            ft.DataCell(ft.Text("2")),
            ft.DataCell(ft.Text("Judge1")),
            ft.DataCell(ft.Text("SCORE_SUBMIT")),
            ft.DataCell(ft.Text(str(datetime.now()))),
        ]),
    ]

    # 3. Return the Layout
    return ft.Column(
        controls=[
            ft.Text("Security Audit Logs", size=24, weight="bold"),
            ft.Divider(),
            ft.DataTable(columns=columns, rows=rows, border=ft.border.all(1, "grey"))
        ],
        scroll="adaptive",
        expand=True
    )