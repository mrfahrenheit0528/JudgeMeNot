import flet as ft
from services.admin_service import AdminService

def AdminDashboardView(page: ft.Page, on_logout_callback):
    admin_service = AdminService()
    
    # ---------------------------------------------------------
    # UI COMPONENTS: CONTENT AREAS
    # ---------------------------------------------------------
    
    # 1. WELCOME SECTION
    welcome_content = ft.Column([
        ft.Text("Admin Dashboard", size=30, weight="bold"),
        ft.Text("Select an option from the menu to get started.", size=16),
        ft.Divider(),
        ft.Container(
            padding=20,
            bgcolor=ft.Colors.BLUE_50,
            border_radius=10,
            content=ft.Column([
                ft.Text("Quick Stats", weight="bold"),
                ft.Text("Active Events: Loading..."), # Placeholder for future stats
                ft.Text("Total Users: Loading...")
            ])
        )
    ])

    # 2. USERS SECTION (Table + Add Button)
    users_column = ft.Column(scroll="adaptive", expand=True)
    
    def load_users():
        users_column.controls.clear()
        users = admin_service.get_all_users()
        
        # Define Table
        data_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("ID")),
                ft.DataColumn(ft.Text("Name")),
                ft.DataColumn(ft.Text("Role")),
                ft.DataColumn(ft.Text("Username")),
            ],
            rows=[
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(str(u.id))),
                    ft.DataCell(ft.Text(u.name)),
                    ft.DataCell(ft.Text(u.role)),
                    ft.DataCell(ft.Text(u.username)),
                ]) for u in users
            ]
        )
        users_column.controls.append(ft.Text("Manage Users", size=24, weight="bold"))
        users_column.controls.append(ft.ElevatedButton("Add New User", icon=ft.Icons.ADD, on_click=open_add_user_dialog))
        users_column.controls.append(data_table)
        page.update()

    # 3. EVENTS SECTION
    events_column = ft.Column(scroll="adaptive", expand=True)
    
    def load_events():
        events_column.controls.clear()
        events = admin_service.get_all_events()
        
        events_grid = ft.GridView(
            runs_count=2,
            max_extent=300,
            child_aspect_ratio=1.5,
            spacing=10,
            run_spacing=10,
        )
        
        for e in events:
            # Color code based on type
            bg_color = ft.Colors.PINK_100 if e.event_type == "Pageant" else ft.Colors.GREEN_100
            icon = ft.Icons.WOMAN if e.event_type == "Pageant" else ft.Icons.QUIZ
            
            card = ft.Container(
                bgcolor=bg_color,
                border_radius=10,
                padding=15,
                content=ft.Column([
                    ft.Row([ft.Icon(icon), ft.Text(e.event_type, weight="bold")]),
                    ft.Text(e.name, size=18, weight="bold"),
                    ft.Text(f"Status: {e.status}"),
                    ft.ElevatedButton("Manage", data=e.id) # We will wire this later
                ])
            )
            events_grid.controls.append(card)

        events_column.controls.append(ft.Text("Manage Events", size=24, weight="bold"))
        events_column.controls.append(ft.ElevatedButton("Create Event", icon=ft.Icons.ADD, on_click=open_add_event_dialog))
        events_column.controls.append(events_grid)
        page.update()

    # ---------------------------------------------------------
    # DIALOGS (MODALS)
    # ---------------------------------------------------------
    
    # Add User Dialog Components
    new_user_name = ft.TextField(label="Full Name")
    new_user_user = ft.TextField(label="Username")
    new_user_pass = ft.TextField(label="Password", password=True, can_reveal_password=True)
    new_user_role = ft.Dropdown(
        label="Role",
        options=[
            ft.dropdown.Option("Judge"),
            ft.dropdown.Option("Tabulator"),
            ft.dropdown.Option("AdminViewer"),
            ft.dropdown.Option("Admin"),
        ]
    )

    def save_user(e):
        success, msg = admin_service.create_user(
            new_user_name.value, new_user_user.value, 
            new_user_pass.value, new_user_role.value
        )
        if success:
            page.snack_bar = ft.SnackBar(ft.Text("User Added!"), bgcolor=ft.Colors.GREEN)
            page.dialog.open = False
            load_users() # Refresh list
        else:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {msg}"), bgcolor=ft.Colors.RED)
        page.snack_bar.open = True
        page.update()

    user_dialog = ft.AlertDialog(
        title=ft.Text("Add New User"),
        content=ft.Column([new_user_name, new_user_user, new_user_pass, new_user_role], height=300),
        actions=[ft.TextButton("Save", on_click=save_user)]
    )

    def open_add_user_dialog(e):
        page.dialog = user_dialog
        user_dialog.open = True
        page.update()

    # Add Event Dialog Components
    new_event_name = ft.TextField(label="Event Name")
    new_event_type = ft.Dropdown(
        label="Event Type",
        options=[
            ft.dropdown.Option("Pageant"),
            ft.dropdown.Option("QuizBee"),
        ]
    )

    def save_event(e):
        success, msg = admin_service.create_event(new_event_name.value, new_event_type.value)
        if success:
            page.snack_bar = ft.SnackBar(ft.Text("Event Created!"), bgcolor=ft.Colors.GREEN)
            page.dialog.open = False
            load_events() # Refresh list
        else:
            page.snack_bar = ft.SnackBar(ft.Text(f"Error: {msg}"), bgcolor=ft.Colors.RED)
        page.snack_bar.open = True
        page.update()

    event_dialog = ft.AlertDialog(
        title=ft.Text("Create New Event"),
        content=ft.Column([new_event_name, new_event_type], height=150),
        actions=[ft.TextButton("Create", on_click=save_event)]
    )

    def open_add_event_dialog(e):
        page.dialog = event_dialog
        event_dialog.open = True
        page.update()

    # ---------------------------------------------------------
    # MAIN LAYOUT ASSEMBLY
    # ---------------------------------------------------------
    
    # Container that holds the changing content
    main_content_area = ft.Container(content=welcome_content, expand=True, padding=20)

    def nav_change(e):
        index = e.control.selected_index
        if index == 0:
            main_content_area.content = welcome_content
        elif index == 1:
            load_users()
            main_content_area.content = users_column
        elif index == 2:
            load_events()
            main_content_area.content = events_column
        page.update()

    sidebar = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        min_width=100,
        expand=True,
        min_extended_width=200,
        destinations=[
            ft.NavigationRailDestination(
                icon=ft.Icons.DASHBOARD, 
                label="Dashboard"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.PEOPLE, 
                label="Users"
            ),
            ft.NavigationRailDestination(
                icon=ft.Icons.CALENDAR_TODAY, 
                label="Events"
            ),
        ],
        on_change=nav_change,
    )

    return ft.Row(
        controls=[
            ft.Column([sidebar, ft.ElevatedButton("Logout", on_click=on_logout_callback)], width=100),
            ft.VerticalDivider(width=1),
            main_content_area
        ],
        expand=True,
    )