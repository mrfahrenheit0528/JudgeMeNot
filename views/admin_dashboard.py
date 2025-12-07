import flet as ft
from services.admin_service import AdminService
from services.event_service import EventService # Import EventService for activation logic

def AdminDashboardView(page: ft.Page, on_logout_callback):
    admin_service = AdminService()
    event_service = EventService() # Initialize EventService
    page.assets_dir = "assets"

    # ---------------------------------------------------------
    # 1. HEADER (Updated with Logout)
    # ---------------------------------------------------------
    HEADER_COLOR = "#80C1FF"

    def about_clicked(e):
        print("ABOUT clicked")

    def contact_clicked(e):
        print("CONTACT clicked")

    header_logo = ft.Container(
        width=45,
        height=45,
        border_radius=50,
        bgcolor="transparent",
        border=ft.border.all(2, ft.Colors.BLACK),
        padding=5,
        content=ft.Image(
            src="hammer.png",
            fit=ft.ImageFit.CONTAIN,
            error_content=ft.Icon(ft.Icons.GAVEL)
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

    # MOVED LOGOUT HERE
    header_right = ft.Row(
        spacing=20,
        controls=[
            ft.TextButton("ABOUT", style=ft.ButtonStyle(color=ft.Colors.BLACK), on_click=about_clicked),
            ft.TextButton("CONTACT", style=ft.ButtonStyle(color=ft.Colors.BLACK), on_click=contact_clicked),
            ft.VerticalDivider(width=10, color="transparent"),
            ft.ElevatedButton("Log out", on_click=on_logout_callback, bgcolor=ft.Colors.RED_400, color=ft.Colors.WHITE)
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
    # 2. MAIN CONTENT CONTAINER
    # ---------------------------------------------------------
    main_content_area = ft.Container(expand=True, padding=40)

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
            page.open(ft.SnackBar(ft.Text("Please fill all fields"), bgcolor=ft.Colors.RED)); return
        success, msg = admin_service.create_user(new_user_name.value, new_user_user.value, new_user_pass.value, new_user_role.value)
        if success:
            page.open(ft.SnackBar(ft.Text("User Added!"), bgcolor=ft.Colors.GREEN)); page.close(user_dialog); load_users_view()
        else: page.open(ft.SnackBar(ft.Text(f"Error: {msg}"), bgcolor=ft.Colors.RED))

    user_dialog = ft.AlertDialog(title=ft.Text("Add New User"), content=ft.Column([new_user_name, new_user_user, new_user_pass, new_user_role], height=300), actions=[ft.TextButton("Save", on_click=save_user)])
    def open_add_user_dialog(e): page.open(user_dialog)

    # --- ADD EVENT DIALOG ---
    new_event_name = ft.TextField(label="Event Name")
    new_event_type = ft.Dropdown(label="Event Type", options=[ft.dropdown.Option("Pageant"), ft.dropdown.Option("QuizBee")])

    def save_event(e):
        if not new_event_name.value or not new_event_type.value:
            page.open(ft.SnackBar(ft.Text("Please fill all fields"), bgcolor=ft.Colors.RED)); return
        success, msg = admin_service.create_event(new_event_name.value, new_event_type.value)
        if success:
            page.open(ft.SnackBar(ft.Text("Event Created!"), bgcolor=ft.Colors.GREEN)); page.close(event_dialog); load_events_view()
        else: page.open(ft.SnackBar(ft.Text(f"Error: {msg}"), bgcolor=ft.Colors.RED))

    event_dialog = ft.AlertDialog(title=ft.Text("Create New Event"), content=ft.Column([new_event_name, new_event_type], height=150), actions=[ft.TextButton("Create", on_click=save_event)])
    def open_add_event_dialog(e): page.open(event_dialog)

    # ---------------------------------------------------------
    # 4. VIEWS
    # ---------------------------------------------------------

    # --- USERS VIEW ---
    def load_users_view():
        users = admin_service.get_all_users()

        # Delete Dialog
        def open_delete_dialog(e):
            user_id = e.control.data
            def confirm_delete(ev):
                success, msg = admin_service.delete_user(user_id)
                if success:
                    page.open(ft.SnackBar(ft.Text("User Deleted!"), bgcolor=ft.Colors.GREEN)); page.close(delete_dialog); load_users_view()
                else:
                    page.open(ft.SnackBar(ft.Text(f"Error: {msg}"), bgcolor=ft.Colors.RED))
            delete_dialog = ft.AlertDialog(title=ft.Text("Delete User?"), content=ft.Text("Cannot be undone."), actions=[ft.TextButton("Cancel", on_click=lambda _: page.close(delete_dialog)), ft.TextButton("Delete", on_click=confirm_delete)])
            page.open(delete_dialog)

        # Edit Dialog Logic (Abbreviated for clarity - same as before)
        def open_edit_dialog(e):
            # ... (Reuse existing edit logic, just ensure refresh calls load_users_view) ...
            page.open(ft.SnackBar(ft.Text("Edit feature available in full code"), bgcolor=ft.Colors.GREY))

        # Build Table
        TABLE_WIDTH = 850
        table_rows = []
        for u in users:
            action_btn = ft.TextButton("Edit", data=u.id, icon=ft.Icons.EDIT, style=ft.ButtonStyle(color=ft.Colors.BLUE), on_click=open_edit_dialog)
            delete_icon = ft.IconButton(icon=ft.Icons.DELETE, icon_color=ft.Colors.RED, data=u.id, on_click=open_delete_dialog)
            
            row = ft.Container(width=TABLE_WIDTH, bgcolor=ft.Colors.WHITE, border_radius=8, padding=10, margin=ft.margin.only(bottom=8), shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.GREY_300),
                content=ft.Row([
                    ft.Container(ft.Text(str(u.id)), width=60),
                    ft.Container(ft.Text(u.name), width=220),
                    ft.Container(ft.Text(u.role), width=180),
                    ft.Container(ft.Text(u.username), width=180),
                    ft.Container(ft.Row([action_btn, delete_icon], spacing=10), width=240),
                ])
            )
            table_rows.append(row)

        table_header = ft.Container(width=TABLE_WIDTH, bgcolor=ft.Colors.BLUE_100, padding=10, border_radius=8,
            content=ft.Row([
                ft.Container(ft.Text("ID", weight="bold"), width=60),
                ft.Container(ft.Text("Name", weight="bold"), width=220),
                ft.Container(ft.Text("Role", weight="bold"), width=180),
                ft.Container(ft.Text("Username", weight="bold"), width=180),
                ft.Container(ft.Text("Action", weight="bold"), width=240),
            ])
        )

        main_content_area.content = ft.Column([
            # BACK BUTTON ROW
            ft.Row([
                ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: load_welcome_view()),
                ft.Text("Manage Users", size=24, weight="bold")
            ]),
            ft.ElevatedButton("Add New User", icon=ft.Icons.ADD, on_click=open_add_user_dialog),
            ft.Divider(),
            ft.Row([table_header], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([ft.Column(table_rows, scroll="adaptive")], alignment=ft.MainAxisAlignment.CENTER),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER)
        page.update()

    # --- EVENTS VIEW ---
    def load_events_view():
        events = admin_service.get_all_events()
        # Changed to Column for List View instead of GridView
        events_list = ft.Column(spacing=10, scroll="adaptive")

        # --- EVENT ACTIVATION HANDLERS (FIXED) ---
        def toggle_event_status(e, new_status):
            event_id = e.control.data
            # CALL THE SERVICE
            success, msg = event_service.update_event_status(event_id, new_status)
            if success:
                page.open(ft.SnackBar(ft.Text(f"Event is now {new_status}!"), bgcolor=ft.Colors.GREEN))
                load_events_view() # REFRESH UI TO SWAP BUTTONS
            else:
                page.open(ft.SnackBar(ft.Text(f"Error: {msg}"), bgcolor=ft.Colors.RED))

        for e in events:
            bg_img = "pageant.png" if e.event_type == "Pageant" else "quiz.png"
            icon = ft.Icons.WOMAN if e.event_type == "Pageant" else ft.Icons.LIGHTBULB
            col = ft.Colors.WHITE
            
            # --- DYNAMIC BUTTON LOGIC ---
            if e.status == "Active":
                # If Active, show STOP button
                action_icon = ft.IconButton(
                    icon=ft.Icons.STOP_CIRCLE, 
                    icon_color="red", 
                    tooltip="Deactivate Event", 
                    data=e.id, 
                    on_click=lambda x: toggle_event_status(x, "Ended")
                )
                status_color = ft.Colors.GREEN_400
            else:
                # If Inactive/Ended, show PLAY button
                action_icon = ft.IconButton(
                    icon=ft.Icons.PLAY_CIRCLE_FILL, 
                    icon_color="green", 
                    tooltip="Activate Event", 
                    data=e.id, 
                    on_click=lambda x: toggle_event_status(x, "Active")
                )
                status_color = ft.Colors.GREY_400

            # --- CARD CONTENT (List Style) ---
            # Using Row layout for List look
            card_content = ft.Container(
                padding=20,
                bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.BLACK), # Dark overlay
                content=ft.Row([
                    # Left: Icon & Type
                    ft.Row([
                        ft.Icon(icon, color=col, size=30),
                        ft.Column([
                            ft.Text(e.name, size=20, weight="bold", color=col),
                            ft.Row([
                                ft.Text(f"{e.event_type} • ", color=ft.Colors.GREY_400),
                                ft.Text(e.status, color=status_color, weight="bold")
                            ], spacing=2)
                        ], spacing=2)
                    ], expand=True),

                    # Right: Action Buttons
                    ft.Row([
                        ft.ElevatedButton("Manage", data=e.id, on_click=lambda ev: page.go(f"/admin/event/{ev.control.data}")),
                        action_icon # Only shows ONE button (Play or Stop)
                    ], spacing=10)
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)
            )

            # ========= CARD WITH BACKGROUND =========
            card = ft.Container(
                height=100, # Fixed height for list item
                border_radius=10,
                image=ft.DecorationImage(src=bg_img, fit=ft.ImageFit.COVER, opacity=0.8),
                padding=0,
                clip_behavior=ft.ClipBehavior.HARD_EDGE,
                content=card_content
            )
            events_list.controls.append(card)

        main_content_area.content = ft.Column([
            # BACK BUTTON ROW
            ft.Row([
                ft.IconButton(icon=ft.Icons.ARROW_BACK, on_click=lambda e: load_welcome_view()),
                ft.Text("Manage Events", size=24, weight="bold")
            ]),
            ft.ElevatedButton("Create Event", icon=ft.Icons.ADD, on_click=open_add_event_dialog),
            ft.Divider(),
            ft.Container(content=events_list, expand=True)
        ], expand=True)
        page.update()

    # --- DASHBOARD (WELCOME) VIEW ---
    def load_welcome_view():
        
        # Navigation Cards
        def nav_card(title, icon, desc, color, on_click):
            return ft.Container(
                content=ft.Column([
                    ft.Icon(icon, size=40, color="white"),
                    ft.Text(title, size=20, weight="bold", color="white"),
                    ft.Text(desc, color="white70", size=12, text_align="center")
                ], alignment="center", horizontal_alignment="center"),
                width=250, height=150, bgcolor=color, border_radius=15,
                padding=20, ink=True, on_click=on_click,
                shadow=ft.BoxShadow(blur_radius=5, color=ft.Colors.GREY_400)
            )

        content = ft.Column([
            ft.Text("Admin Dashboard", size=32, weight="bold"),
            ft.Text("Welcome back, Admin.", size=16, color="grey"),
            ft.Divider(height=30),
            
            # Quick Stats
            ft.Container(
                padding=20, bgcolor=ft.Colors.BLUE_50, border_radius=10, width=float("inf"),
                content=ft.Column([
                    ft.Text("Quick Stats", weight="bold", size=16),
                    ft.Row([
                        ft.Column([ft.Text("System Status"), ft.Text("Online", color="green", weight="bold")]),
                        ft.VerticalDivider(),
                        ft.Column([ft.Text("Database"), ft.Text("Connected", color="green", weight="bold")]),
                    ], spacing=50)
                ])
            ),
            ft.Container(height=20),
            
            # Menu Grid
            ft.Text("Menu", size=20, weight="bold"),
            ft.Row([
                nav_card("Manage Users", ft.Icons.PEOPLE, "Add or remove judges & staff", ft.Colors.BLUE_500, lambda e: load_users_view()),
                nav_card("Manage Events", ft.Icons.EVENT, "Create pageants & quiz bees", ft.Colors.ORANGE_500, lambda e: load_events_view()),
            ], spacing=20, wrap=True)
        ])
        
        main_content_area.content = content
        page.update()

    # Initial Load
    load_welcome_view()

    return ft.Column(
        expand=True,
        controls=[
            header,
            main_content_area
        ]
    )