import flet as ft

def AdminDashboardView(page: ft.Page, on_logout_callback):
    
    # Simple Sidebar Navigation
    sidebar = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        min_extended_width=400,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.DASHBOARD, 
                selected_icon=ft.Icons.DASHBOARD_CUSTOMIZE, 
                label="Dashboard"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.PEOPLE, 
                label="Users"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.EVENT, 
                label="Events"
            ),
        ],
        on_change=lambda e: print("Nav changed to:", e.control.selected_index),
    )

    # Main Content Area
    content_area = ft.Container(
        content=ft.Column([
            ft.Text("Admin Dashboard", size=30, weight="bold"),
            ft.Text("Welcome back, Admin!", size=16),
            ft.ElevatedButton("Logout", on_click=on_logout_callback, bgcolor=ft.Colors.RED, color=ft.Colors.WHITE)
        ]),
        padding=20,
        expand=True
    )

    return ft.Row(
        controls=[
            sidebar,
            ft.VerticalDivider(width=1),
            content_area
        ],
        expand=True,
    )