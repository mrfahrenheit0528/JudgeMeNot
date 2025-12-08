import flet as ft
from services.admin_service import AdminService

def AuditLogView(page: ft.Page, on_back_click=None):
    admin_service = AdminService()
    
    # 1. Fetch Real Data
    logs = admin_service.get_security_logs()

    # 2. Define Columns
    columns = [
        ft.DataColumn(ft.Text("ID"), numeric=True),
        ft.DataColumn(ft.Text("User (Role)")),
        ft.DataColumn(ft.Text("Action")),
        ft.DataColumn(ft.Text("Details")),
        ft.DataColumn(ft.Text("Timestamp")),
    ]

    # 3. Generate Rows from Database
    rows = []
    for log in logs:
        # Format timestamp nicely
        ts_str = log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        
        # Color code specific actions for IAS visual cues
        action_color = ft.Colors.BLACK
        if "LOGIN" in log.action: action_color = ft.Colors.BLUE
        elif "DELETE" in log.action: action_color = ft.Colors.RED
        elif "SCORE" in log.action: action_color = ft.Colors.GREEN

        rows.append(
            ft.DataRow(cells=[
                ft.DataCell(ft.Text(str(log.id))),
                ft.DataCell(ft.Text(f"{log.user.username} ({log.user.role})")),
                ft.DataCell(ft.Text(log.action, color=action_color, weight="bold")),
                ft.DataCell(ft.Text(log.details, size=12)),
                ft.DataCell(ft.Text(ts_str, size=12)),
            ])
        )

    # 4. Header Construction (With Optional Back Button)
    header_row = ft.Row(vertical_alignment=ft.CrossAxisAlignment.CENTER)
    if on_back_click:
        header_row.controls.append(
            ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_size=30, on_click=on_back_click)
        )
    header_row.controls.append(ft.Text("Security Audit Logs", size=24, weight="bold"))

    # 5. Return Layout
    # FIX: Wrapped in Container to support 'padding', content is the Column
    return ft.Container(
        padding=20,
        expand=True,
        content=ft.Column(
            controls=[
                header_row,
                ft.Divider(),
                # Scrollable area for the table
                ft.Column(
                    controls=[
                        ft.DataTable(
                            columns=columns, 
                            rows=rows, 
                            border=ft.border.all(1, "grey"),
                            vertical_lines=ft.border.BorderSide(1, "grey"),
                            horizontal_lines=ft.border.BorderSide(1, "grey"),
                            heading_row_color=ft.Colors.BLUE_50
                        )
                    ],
                    expand=True,
                    scroll="adaptive" # This works on Column
                )
            ],
            expand=True
        )
    )