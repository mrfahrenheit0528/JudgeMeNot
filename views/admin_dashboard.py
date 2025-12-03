import flet as ft
from services.admin_service import AdminService

def AdminDashboardView(page: ft.Page, on_logout_callback):
    admin_service = AdminService()

    # Ensure assets folder is used (Good addition by your teammate!)
    page.assets_dir = "assets"

    # ---------------------------------------------------------
    # 1. HEADER (Teammate's Design)
    # ---------------------------------------------------------
    HEADER_COLOR = "#80C1FF" # Define the header color for reuse

    def about_clicked(e):
        print("ABOUT clicked")

    def contact_clicked(e):
        print("CONTACT clicked")

    # Circular logo
    header_logo = ft.Container(
        width=45,
        height=45,
        border_radius=50,
        bgcolor="transparent",
        border=ft.border.all(2, ft.Colors.BLACK),
        padding=5,
        content=ft.Image(
            src="hammer.png", # Make sure hammer.png is in your /assets folder
            fit=ft.ImageFit.CONTAIN,
            error_content=ft.Icon(ft.Icons.GAVEL) # Fallback if image missing
        )
    )

    header_left = ft.Row(
        spacing=10,
        controls=[
            header_logo,
            ft.Text("JUDGEMENOT", size=22, weight="bold", color=ft.Colors.BLACK),
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    header_right = ft.Row(
        spacing=40,
        controls=[
            ft.TextButton("ABOUT", style=ft.ButtonStyle(color=ft.Colors.BLACK), on_click=about_clicked),
            ft.TextButton("CONTACT", style=ft.ButtonStyle(color=ft.Colors.BLACK), on_click=contact_clicked),
        ],
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    header = ft.Container(
        height=75,
        padding=ft.padding.symmetric(horizontal=50),
        bgcolor=HEADER_COLOR,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[header_left, header_right],
        )
    )

    # ---------------------------------------------------------
    # 2. SIDEBAR STATE
    # ---------------------------------------------------------

    sidebar_container = ft.Container(
        width=250,
        visible=False,
        # *** CHANGED BACKGROUND COLOR TO MATCH HEADER ***
        bgcolor=HEADER_COLOR, 
        border=ft.border.only(right=ft.border.BorderSide(1, ft.Colors.GREY_300))
    )

    main_content_area = ft.Container(expand=True, padding=20)

    def toggle_sidebar(e):
        sidebar_container.visible = not sidebar_container.visible
        page.update()

    def close_sidebar(e):
        sidebar_container.visible = False
        page.update()

    hamburger_btn = ft.IconButton(
        icon=ft.Icons.MENU,
        icon_size=24,
        on_click=toggle_sidebar,
        tooltip="Open Menu"
    )

    # ---------------------------------------------------------
    # 3. DIALOGS (User & Event Creation)
    # ---------------------------------------------------------

    # --- ADD USER DIALOG ---
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
        if not new_user_user.value or not new_user_pass.value:
            page.open(ft.SnackBar(ft.Text("Please fill all fields"), bgcolor=ft.Colors.RED))
            return

        success, msg = admin_service.create_user(
            new_user_name.value, new_user_user.value,
            new_user_pass.value, new_user_role.value
        )
        
        if success:
            page.open(ft.SnackBar(ft.Text("User Added!"), bgcolor=ft.Colors.GREEN))
            page.close(user_dialog)
            load_users_view()
        else:
            page.open(ft.SnackBar(ft.Text(f"Error: {msg}"), bgcolor=ft.Colors.RED))

    user_dialog = ft.AlertDialog(
        title=ft.Text("Add New User"),
        content=ft.Column([new_user_name, new_user_user, new_user_pass, new_user_role], height=300),
        actions=[ft.TextButton("Save", on_click=save_user)]
    )

    def open_add_user_dialog(e):
        page.open(user_dialog)

    # --- ADD EVENT DIALOG ---
    new_event_name = ft.TextField(label="Event Name")
    new_event_type = ft.Dropdown(
        label="Event Type",
        options=[
            ft.dropdown.Option("Pageant"),
            ft.dropdown.Option("QuizBee"),
        ]
    )

    def save_event(e):
        if not new_event_name.value or not new_event_type.value:
            page.open(ft.SnackBar(ft.Text("Please fill all fields"), bgcolor=ft.Colors.RED))
            return

        success, msg = admin_service.create_event(new_event_name.value, new_event_type.value)

        if success:
            page.open(ft.SnackBar(ft.Text("Event Created!"), bgcolor=ft.Colors.GREEN))
            page.close(event_dialog)
            load_events_view()
        else:
            page.open(ft.SnackBar(ft.Text(f"Error: {msg}"), bgcolor=ft.Colors.RED))

    event_dialog = ft.AlertDialog(
        title=ft.Text("Create New Event"),
        content=ft.Column([new_event_name, new_event_type], height=150),
        actions=[ft.TextButton("Create", on_click=save_event)]
    )

    def open_add_event_dialog(e):
        page.open(event_dialog)

    # ---------------------------------------------------------
    # 4. CONTENT LOADING FUNCTIONS
    # ---------------------------------------------------------

    def load_welcome_view():
        # Hide the sidebar whenever a new view is loaded
        sidebar_container.visible = False
        
        content = ft.Column([
            ft.Row([hamburger_btn, ft.Text("Admin Dashboard", size=30, weight="bold")]),
            ft.Text("Select an option from the menu to get started.", size=16),
            ft.Divider(),
            ft.Container(
                padding=20,
                bgcolor=ft.Colors.BLUE_50,
                border_radius=10,
                content=ft.Column([
                    ft.Text("Quick Stats", weight="bold"),
                    ft.Text("System Status: Online"),
                    ft.Text("Database: Connected")
                ])
            )
        ])
        main_content_area.content = content
        page.update()

    def load_users_view():
        # Hide the sidebar whenever a new view is loaded
        sidebar_container.visible = False
        
        users = admin_service.get_all_users()

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
            ],
            border=ft.border.all(1, ft.Colors.GREY_300),
        )

        main_content_area.content = ft.Column([
            ft.Row([hamburger_btn, ft.Text("Manage Users", size=24, weight="bold")]),
            ft.ElevatedButton("Add New User", icon=ft.Icons.ADD, on_click=open_add_user_dialog),
            ft.Divider(),
            ft.Row([data_table], scroll="adaptive")
        ])
        page.update()

    def load_events_view():
        # Hide the sidebar whenever a new view is loaded
        sidebar_container.visible = False
        
        events = admin_service.get_all_events()

        events_grid = ft.GridView(
            runs_count=2,
            max_extent=300,
            child_aspect_ratio=1.5,
            spacing=10,
            run_spacing=10,
        )

        for e in events:
            bg_color = ft.Colors.PINK_50 if e.event_type == "Pageant" else ft.Colors.GREEN_50
            icon = ft.Icons.WOMAN if e.event_type == "Pageant" else ft.Icons.QUIZ
            border_col = ft.Colors.PINK if e.event_type == "Pageant" else ft.Colors.GREEN

            # --- THE FIX IS HERE ---
            # Added the 'on_click' logic to navigate to the Config Page
            manage_btn = ft.ElevatedButton(
                "Manage", 
                data=e.id,
                on_click=lambda e: page.go(f"/admin/event/{e.control.data}") 
            )

            card = ft.Container(
                bgcolor=bg_color,
                border=ft.border.all(1, border_col),
                border_radius=10,
                padding=15,
                content=ft.Column([
                    ft.Row([ft.Icon(icon, color=border_col), ft.Text(e.event_type, weight="bold", color=border_col)]),
                    ft.Text(e.name, size=18, weight="bold"),
                    ft.Text(f"Status: {e.status}"),
                    manage_btn # Added the working button back
                ])
            )
            events_grid.controls.append(card)

        main_content_area.content = ft.Column([
            ft.Row([hamburger_btn, ft.Text("Manage Events", size=24, weight="bold")]),
            ft.ElevatedButton("Create Event", icon=ft.Icons.ADD, on_click=open_add_event_dialog),
            ft.Divider(),
            ft.Container(content=events_grid, expand=True)
        ], expand=True)

        page.update()

    # ---------------------------------------------------------
    # 5. NAVIGATION RAIL
    # ---------------------------------------------------------

    def nav_change(e):
        index = e.control.selected_index
        if index == 0:
            load_welcome_view()
        elif index == 1:
            load_users_view()
        elif index == 2:
            load_events_view()
        page.update()

    # The rail's background color (Blue Grey 50 / light grey) remains as requested.
    rail = ft.NavigationRail(
        selected_index=0,
        label_type=ft.NavigationRailLabelType.ALL,
        expand=True,
        bgcolor=ft.Colors.BLUE_GREY_50, # The grey part you wanted to keep
        destinations=[
            ft.NavigationRailDestination(icon=ft.Icons.DASHBOARD, label="Dashboard"),
            ft.NavigationRailDestination(icon=ft.Icons.PEOPLE, label="Users"),
            ft.NavigationRailDestination(icon=ft.Icons.CALENDAR_TODAY, label="Events"),
        ],
        on_change=nav_change,
    )

    close_btn = ft.IconButton(
        icon=ft.Icons.CHEVRON_LEFT,
        icon_color="black",
        on_click=close_sidebar
    )

    logout_btn = ft.Container(
        content=ft.ElevatedButton(
            "Logout",
            icon=ft.Icons.LOGOUT,
            on_click=on_logout_callback,
            bgcolor=ft.Colors.RED,
            color=ft.Colors.WHITE,
            width=230
        ),
        padding=10,
    )

    # Sidebar content column now has the blue background from the sidebar_container
    sidebar_content = ft.Column(
        controls=[
            # This row contains the close button and will have the blue background
            ft.Row([ft.Container(expand=True), close_btn]),
            rail, # The rail itself has the grey background
            ft.Divider(),
            logout_btn # This container/button will be against the blue background
        ],
        spacing=0,
        expand=True
    )

    sidebar_container.content = sidebar_content

    # ---------------------------------------------------------
    # 6. FINAL LAYOUT ASSEMBLY
    # ---------------------------------------------------------
    
    load_welcome_view()

    return ft.Column(
        expand=True,
        controls=[
            header,
            ft.Row(
                expand=True,
                controls=[
                    sidebar_container,
                    ft.VerticalDivider(width=1),
                    main_content_area
                ]
            )
        ]
    )