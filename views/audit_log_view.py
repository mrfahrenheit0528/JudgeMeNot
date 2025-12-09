import flet as ft
import threading
import time
from services.admin_service import AdminService

def AuditLogView(page: ft.Page, on_back_click=None):
    admin_service = AdminService()
    
    # State for polling
    is_active = True
    
    # UI Components - Initial Setup
    data_table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID", color="white", weight="bold"), numeric=True),
            ft.DataColumn(ft.Text("User (Role)", color="white", weight="bold")),
            ft.DataColumn(ft.Text("Action", color="white", weight="bold")),
            ft.DataColumn(ft.Text("Details", color="white", weight="bold")),
            ft.DataColumn(ft.Text("Timestamp", color="white", weight="bold")),
        ],
        rows=[],
        # Modern Styling
        heading_row_color="#64AEFF", # System Blue
        heading_row_height=50,
        data_row_max_height=60,
        column_spacing=20,
        # Subtle grid lines
        vertical_lines=ft.border.BorderSide(1, "#F0F0F0"),
        horizontal_lines=ft.border.BorderSide(1, "#F0F0F0"),
        border_radius=10,
    )
    
    last_updated_text = ft.Text("Loading...", size=12, color="grey", italic=True)

    def fetch_logs():
        """Fetches logs from DB and updates the table rows"""
        try:
            # --- DYNAMIC WIDTH CALCULATION ---
            # This ensures the table tries to fill the screen width minus padding
            if page.width:
                # 120 = approx padding (40*2) + margins
                target_width = page.width - 120
                # Ensure it doesn't get too small (min 800px)
                data_table.width = max(target_width, 800)
            
            logs = admin_service.get_security_logs()
            new_rows = []
            
            for i, log in enumerate(logs):
                ts_str = log.timestamp.strftime("%Y-%m-%d %H:%M:%S")
                
                # Color code specific actions for text
                action_color = ft.Colors.BLACK87
                if "LOGIN" in log.action: action_color = ft.Colors.BLUE_700
                elif "DELETE" in log.action: action_color = ft.Colors.RED_700
                elif "SCORE" in log.action: action_color = ft.Colors.GREEN_700
                elif "CREATE" in log.action: action_color = ft.Colors.PURPLE_700

                # Handle potentially missing user (if deleted)
                user_display = "Unknown"
                if log.user:
                    user_display = f"{log.user.username} ({log.user.role})"
                else:
                    user_display = f"User ID: {log.user_id} (Deleted)"

                # Zebra Striping Logic
                row_bg_color = "#F9FAFB" if i % 2 == 0 else "white"

                new_rows.append(
                    ft.DataRow(
                        color=row_bg_color,
                        cells=[
                            ft.DataCell(ft.Text(str(log.id), size=12)),
                            ft.DataCell(ft.Text(user_display, weight="bold", size=12)),
                            ft.DataCell(ft.Container(
                                content=ft.Text(log.action, color=action_color, weight="bold", size=11),
                                padding=ft.padding.symmetric(horizontal=8, vertical=4),
                                bgcolor=ft.Colors.with_opacity(0.1, action_color),
                                border_radius=5
                            )),
                            ft.DataCell(ft.Text(log.details, size=12, overflow=ft.TextOverflow.ELLIPSIS)),
                            ft.DataCell(ft.Text(ts_str, size=12, color="grey")),
                        ]
                    )
                )
            
            data_table.rows = new_rows
            now_str = time.strftime("%H:%M:%S")
            last_updated_text.value = f"Auto-updated at: {now_str}"
            page.update()
        except Exception as e:
            print(f"Error fetching logs: {e}")

    def poll_logs():
        """Background thread to refresh logs every 3 seconds"""
        while is_active:
            fetch_logs()
            time.sleep(3)

    # Start Polling
    threading.Thread(target=poll_logs, daemon=True).start()

    # Cleanup when leaving
    def stop_polling(e):
        nonlocal is_active
        is_active = False
        if on_back_click:
            on_back_click(e)

    # Header Construction
    header_row = ft.Row(
        controls=[
            ft.IconButton(icon=ft.Icons.ARROW_BACK, icon_size=30, on_click=stop_polling), # Use stop_polling wrapper
            ft.Column([
                ft.Text("Security Audit Logs", size=24, weight="bold", color="#1A1A1A"),
                last_updated_text
            ], spacing=2)
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER
    )

    # Return Layout
    return ft.Container(
        padding=40,
        expand=True,
        content=ft.Column(
            controls=[
                header_row,
                ft.Divider(height=20, color="transparent"),
                
                # The "Card" Container for the Table
                ft.Container(
                    content=ft.Column(
                        controls=[
                            # Wrap DataTable in Row for Horizontal Scroll
                            ft.Row(
                                controls=[data_table], 
                                scroll=ft.ScrollMode.ADAPTIVE, 
                                vertical_alignment=ft.CrossAxisAlignment.START,
                                # Ensure the Row fills width if table is smaller
                                alignment=ft.MainAxisAlignment.START 
                            )
                        ], 
                        # Enable Vertical Scroll for the Column
                        scroll=ft.ScrollMode.ADAPTIVE, 
                        expand=True
                    ),
                    
                    bgcolor="white",
                    padding=0,
                    border_radius=10,
                    shadow=ft.BoxShadow(blur_radius=10, color=ft.Colors.BLACK12),
                    border=ft.border.all(1, "#E0E0E0"),
                    expand=True, # This forces the card to fill the remaining vertical space
                    clip_behavior=ft.ClipBehavior.HARD_EDGE
                )
            ],
            expand=True,
            spacing=0
        ),
    )